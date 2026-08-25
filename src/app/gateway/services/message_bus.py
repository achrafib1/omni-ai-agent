# src/app/gateway/services/message_bus.py
"""
Omni-Channel Message Bus Service.

This service houses the core business logic for processing inbound messages,
resolving user identities in the database, executing the LangGraph state machine,
and managing synchronous or WebSocket streaming pipelines.
"""

import contextlib
import uuid
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from langgraph.graph.state import CompiledStateGraph
from opik.integrations.langchain import OpikTracer

from src.app.gateway.adapters.base import BaseChannelAdapter
from src.app.gateway.crud.user_crud import get_or_create_user
from src.shared.infrastructure.db.session import AsyncSessionLocal
from src.shared.infrastructure.observability.logger import get_logger
from src.shared.config import settings

logger = get_logger(__name__)

class MessageBus:
    """Orchestrates interactions between Channel Adapters, DB, and LangGraph."""

    def __init__(self, agent: CompiledStateGraph) -> None:
        self.agent = agent

    async def handle_http_webhook(self, adapter: BaseChannelAdapter, payload: Dict[str, Any]) -> bool:
        """
        Handles a complete, synchronous execution pipeline for HTTP webhooks.
        Designed to be run as a FastAPI BackgroundTask.
        
        Args:
            adapter: The injected platform-specific adapter.
            payload: The raw JSON webhook payload.
        """
        platform_name = adapter.get_platform_type().value
        logger.info(f"[{platform_name}] MessageBus starting HTTP Webhook processing.")

        # 1. Parse payload
        omni_msg = await adapter.parse_http_payload(payload)
        if not omni_msg:
            return True  # Ignore non-actionable events safely

        # 2. Open an isolated DB Session (Crucial for Background Tasks to prevent DetachedInstanceError)
        async with AsyncSessionLocal() as db_session:
            user_record = await get_or_create_user(db_session, omni_msg.platform, omni_msg.platform_user_id)
            user_uuid_str = str(user_record.id)

        # 3. Prepare LangGraph State
        initial_state = {
            "messages": [("user", omni_msg.content)],
            "session_id": omni_msg.session_id,
            "user_id": user_uuid_str
        }
        
        opik_tracer = OpikTracer(
            project_name=settings.OPIK_PROJECT_NAME,  
            tags=["stream_execution", platform_name]
        )

        config = {
            "configurable": {"thread_id": omni_msg.session_id},
            "callbacks": [opik_tracer]
        }

        # 4. Execute LangGraph to completion
        final_message = "I am processing a heavy cognitive load. Could you repeat that?"
        try:
            logger.debug(f"[{platform_name}] Awaiting LangGraph resolution for session {omni_msg.session_id}")
            async for state_update in self.agent.astream(initial_state, config=config, stream_mode="updates"):
                for node_name, node_output in state_update.items():
                    # Safeguard against None or non-dictionary node outputs
                    if isinstance(node_output, dict) and "messages" in node_output and node_output["messages"]:
                        last_msg = node_output["messages"][-1]
                        if getattr(last_msg, "content", None):
                            final_message = last_msg.content

            # 5. Dispatch the final response via the injected adapter
            return await adapter.send_http_message(omni_msg.session_id, final_message)

        except Exception as e:
            logger.error(f"[danger]LangGraph execution failed during Sync Webhook:[/danger] {e}", exc_info=True)
            return False

    async def handle_websocket_stream(self, adapter: BaseChannelAdapter, websocket: WebSocket) -> None:
        """
        Handles a persistent, token-by-token streaming session over WebSockets.
        
        Args:
            adapter: The injected platform-specific adapter.
            websocket: The active FastAPI WebSocket connection.
        """
        platform_name = adapter.get_platform_type().value
        await websocket.accept()
        
        # We generate a unique WS session thread so LangGraph memory doesn't cross-contaminate
        session_id = str(uuid.uuid4())
        logger.info(f"[{platform_name}] WebSocket connection established. Thread assigned: {session_id}")

        try:
            await websocket.send_json({"type": "status", "content": "Neural link established. Ready."})

            while True:
                # 1. Wait for incoming WS message
                data = await websocket.receive_json()
                
                # 2. Parse payload using adapter
                omni_msg = await adapter.parse_ws_payload(data)
                if not omni_msg:
                    continue
                
                omni_msg.session_id = session_id  # Force session lock

                # 3. DB Identity resolution (Safe here as we are holding the socket route open)
                async with AsyncSessionLocal() as db_session:
                    user_record = await get_or_create_user(db_session, omni_msg.platform, omni_msg.platform_user_id)
                    user_uuid_str = str(user_record.id)

                initial_state = {
                    "messages": [("user", omni_msg.content)],
                    "session_id": omni_msg.session_id,
                    "user_id": user_uuid_str
                }

                opik_tracer = OpikTracer(
                    project_name=settings.OPIK_PROJECT_NAME, 
                    tags=["sync_execution", platform_name]
                )

                config = {
                    "configurable": {"thread_id": omni_msg.session_id},
                    "callbacks": [opik_tracer]
                }

                logger.info(f"[{platform_name}] Streaming LangGraph execution for {session_id}")
                
                # 4. Stream LangGraph output (requires nodes to use get_stream_writer())
                async for token in self.agent.astream(initial_state, config=config, stream_mode="custom"):
                    if isinstance(token, str) and token:
                        await websocket.send_json({
                            "type": "token",
                            "content": token,
                            "is_final": False
                        })

                # Signal completion of this turn
                await websocket.send_json({
                    "type": "token",
                    "content": "",
                    "is_final": True
                })

        except WebSocketDisconnect:
            logger.info(f"[{platform_name}] WebSocket client disconnected. (Session: {session_id}).")
        except Exception as e:
            logger.error(f"[{platform_name}] WebSocket exception:[/danger] {e}", exc_info=True)
            with contextlib.suppress(Exception):
                await websocket.send_json({"type": "error", "content": "Internal cognitive failure."})