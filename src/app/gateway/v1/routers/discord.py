"""
Discord Router for Omni-AI-Agent.

Defines the explicit HTTP and WebSocket endpoints for Discord.
Delegates all heavy lifting and orchestration to the central MessageBus.
"""

from fastapi import APIRouter, Depends, Request, WebSocket, BackgroundTasks, status
from fastapi.requests import HTTPConnection

from src.app.gateway.services.message_bus import MessageBus
from src.app.gateway.adapters.discord_adapter import DiscordAdapter

router = APIRouter()
discord_adapter = DiscordAdapter()

def get_message_bus(connection: HTTPConnection) -> MessageBus:
    """
    FastAPI Dependency to retrieve the active MessageBus from app state.
    
    Annotated with HTTPConnection to elegantly support both HTTP Requests 
    and WebSocket Handshakes in a single, unified dependency.
    """
    return connection.app.state.message_bus

@router.post("/webhook", status_code=status.HTTP_200_OK, summary="Discord Webhook")
async def discord_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    message_bus: MessageBus = Depends(get_message_bus)
):
    """
    HTTP POST Webhook for Discord.
    
    Processes the payload asynchronously via BackgroundTasks to immediately 
    return a 200 OK to Discord, preventing timeout disconnects.
    """
    payload = await request.json()
    
    # Hand off to the bus, passing our specific adapter
    background_tasks.add_task(
        message_bus.handle_http_webhook, 
        adapter=discord_adapter, 
        payload=payload
    )
    return {"status": "processing"}

@router.websocket("/stream")
async def discord_stream(
    websocket: WebSocket,
    message_bus: MessageBus = Depends(get_message_bus)
):
    """
    WebSocket endpoint for real-time Discord streaming simulations.
    
    Holds the connection open and yields token-by-token responses.
    """
    await message_bus.handle_websocket_stream(
        adapter=discord_adapter,
        websocket=websocket
    )