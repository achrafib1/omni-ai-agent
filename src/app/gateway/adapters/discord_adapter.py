# src/app/gateway/adapters/discord_adapter.py
"""
Discord REST API Adapter for Omni-AI-Agent.

Abstracts all direct interactions with the Discord API. It parses incoming 
Discord webhooks and WebSocket payloads into the strict `OmniMessage` schema, 
and provides asynchronous HTTP methods for dispatching the agent's outgoing responses.
"""

import httpx
from typing import Dict, Any, Optional

from src.shared.config import settings
from src.shared.domain.schemas.message import OmniMessage, PlatformType, MessageType
from src.app.gateway.adapters.base import BaseChannelAdapter
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

DISCORD_API_BASE = "https://discord.com/api/v10"

class DiscordAdapter(BaseChannelAdapter):
    """Adapter for handling Discord platform ingress and egress."""

    def __init__(self):
        # Securely fetch the bot token from our Pydantic settings
        token = getattr(settings, "DISCORD_BOT_TOKEN", None)
        token_value = token.get_secret_value() if token else ""
        self.headers = {
            "Authorization": f"Bot {token_value}",
            "Content-Type": "application/json",
        }

    def get_platform_type(self) -> PlatformType:
        return PlatformType.DISCORD

    async def parse_http_payload(self, payload: Dict[str, Any]) -> Optional[OmniMessage]:
        """Parses a Discord Webhook JSON payload into an OmniMessage."""
        try:
            # Prevent infinite feedback loops by ignoring bot messages
            author = payload.get("author", {})
            if author.get("bot", False):
                return None
                
            content = payload.get("content", "").strip()
            if not content:
                logger.debug("Received empty Discord message. Skipping processing.")
                return None

            user_id = str(author.get("id"))
            channel_id = str(payload.get("channel_id"))
            
            logger.info(f"Incoming Discord HTTP message from User ID: {user_id} in Channel: {channel_id}.")

            return OmniMessage(
                platform=PlatformType.DISCORD,
                platform_user_id=user_id,
                session_id=channel_id,
                message_type=MessageType.TEXT,
                content=content
            )

        except Exception as e:
            logger.error(f"[danger]Failed to parse Discord HTTP payload:[/danger] {e}", exc_info=True)
            return None

    async def parse_ws_payload(self, payload: Dict[str, Any]) -> Optional[OmniMessage]:
        """Parses custom JSON structures expected over WebSocket for Discord contexts."""
        try:
            # Over WebSockets, we expect our own defined JSON format
            user_id = payload.get("user_id", "unknown_discord_user")
            channel_id = payload.get("channel_id", "default_ws_session")
            content = payload.get("content", "").strip()

            if not content:
                return None

            return OmniMessage(
                platform=PlatformType.DISCORD,
                platform_user_id=user_id,
                session_id=channel_id,
                message_type=MessageType.TEXT,
                content=content
            )
        except Exception as e:
            logger.error(f"[danger]Failed to parse Discord WS payload:[/danger] {e}", exc_info=True)
            return None

    async def send_http_message(self, recipient_id: str, text: str) -> bool:
        """Sends a complete text message back to a Discord channel."""
        logger.debug(f"Dispatching text message to Discord channel {recipient_id}.")
        url = f"{DISCORD_API_BASE}/channels/{recipient_id}/messages"
        
        payload = {"content": text}
        
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(url, headers=self.headers, json=payload)
                res.raise_for_status()
                logger.info(f"[success]Message successfully delivered to Discord channel {recipient_id}.[/success]")
                return True
            except httpx.HTTPStatusError as e:
                logger.error(f"[danger]Failed to send Discord message:[/danger] HTTP {e.response.status_code} - {e.response.text}")
                return False
            except Exception as e:
                logger.error(f"[danger]Unexpected error sending Discord message:[/danger] {e}", exc_info=True)
                return False