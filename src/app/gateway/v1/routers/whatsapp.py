# src/app/gateway/v1/routers/whatsapp.py
"""
WhatsApp Cloud API Router for Omni-AI-Agent.

Defines the explicit HTTP webhook endpoints for WhatsApp.
Delegates heavy cognitive orchestration to the MessageBus via BackgroundTasks
to strictly adhere to Meta's 3-second timeout requirements.
"""

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    WebSocket,
    status,
)
from fastapi.requests import HTTPConnection
from fastapi.responses import PlainTextResponse
from src.app.gateway.adapters.wa_adapter import WhatsAppAdapter
from src.app.gateway.services.message_bus import MessageBus
from src.shared.config import settings
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

# Initialize router and instantiate our specific adapter
router = APIRouter()
wa_adapter = WhatsAppAdapter()


def get_message_bus(connection: HTTPConnection) -> MessageBus:
    """
    FastAPI Dependency to retrieve the active MessageBus from app state.

    Annotated with HTTPConnection to elegantly support both HTTP Requests
    and WebSocket Handshakes in a single, unified dependency.
    """
    return connection.app.state.message_bus


@router.get("/webhook", summary="WhatsApp Hub Verification", status_code=status.HTTP_200_OK)
async def verify_whatsapp_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Verifies the webhook registration with Meta's Graph API.
    Meta hits this endpoint once when you configure the webhook in the Developer Portal.
    """
    verify_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", None)
    expected_token = (
        verify_token.get_secret_value()
        if hasattr(verify_token, "get_secret_value")
        else str(verify_token)
    )

    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("[success]WhatsApp Webhook handshake verified successfully by Meta.[/success]")
        # Meta strictly requires a plain text response of the challenge string
        return PlainTextResponse(content=hub_challenge, status_code=status.HTTP_200_OK)

    logger.error("[danger]WhatsApp Webhook verification failed: Token mismatch.[/danger]")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed")


@router.post("/webhook", status_code=status.HTTP_200_OK, summary="WhatsApp Inbound Webhook")
async def receive_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    message_bus: MessageBus = Depends(get_message_bus),
):
    """
    Receives inbound messages from WhatsApp users.
    Passes execution to a BackgroundTask to immediately return a 200 OK to Meta.
    """
    try:
        payload = await request.json()

        # Hand the payload off to the central Message Bus
        background_tasks.add_task(
            message_bus.handle_http_webhook, adapter=wa_adapter, payload=payload
        )
        # Always return 200 OK to Meta to acknowledge receipt
        return {"status": "processing"}

    except Exception as e:
        logger.error(
            f"[danger]Failed to read WhatsApp Webhook payload:[/danger] {e}", exc_info=True
        )
        # Still return 200 OK so Meta doesn't retry a corrupted payload
        return {"status": "error"}


@router.websocket("/stream")
async def whatsapp_stream(websocket: WebSocket, message_bus: MessageBus = Depends(get_message_bus)):
    """
    WebSocket endpoint for real-time WhatsApp streaming simulations.
    Used for local HTML Dashboard testing since WhatsApp doesn't natively support WS.
    """
    await message_bus.handle_websocket_stream(adapter=wa_adapter, websocket=websocket)
