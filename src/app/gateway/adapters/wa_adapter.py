# src/app/gateway/adapters/wa_adapter.py
"""
WhatsApp Cloud API Adapter for Omni-AI-Agent.

Abstracts all interactions with the Meta WhatsApp Cloud API. Parses deeply nested 
webhook JSON payloads into our strict `OmniMessage` schema, manages secure binary 
media downloads (audio/images), and dispatches the agent's final text responses.
"""

import httpx
from typing import Dict, Any, Optional

from src.shared.config import settings
from src.shared.domain.schemas.message import OmniMessage, PlatformType, MessageType
from src.app.gateway.adapters.base import BaseChannelAdapter
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

GRAPH_API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

class WhatsAppAdapter(BaseChannelAdapter):
    """
    Adapter for handling WhatsApp platform ingress and egress.
    Utilizes asynchronous HTTPx clients for high-throughput, non-blocking I/O.
    """

    def __init__(self):
        # Retrieve securely stored credentials from Pydantic settings
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        
        token = getattr(settings, "WHATSAPP_TOKEN", None)
        token_value = token.get_secret_value() if hasattr(token, "get_secret_value") else str(token)
        
        self.headers = {
            "Authorization": f"Bearer {token_value}",
            "Content-Type": "application/json"
        }

    def get_platform_type(self) -> PlatformType:
        """Returns the strict enum identifier for this platform."""
        return PlatformType.WHATSAPP

    async def _download_media(self, media_id: str) -> Optional[bytes]:
        """
        Securely retrieves binary media (images, voice notes) from Meta's servers.
        Requires a two-step process: fetch URL, then download bytes.
        """
        logger.debug(f"Attempting to download WhatsApp media ID: {media_id}")
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                # Step 1: Request the temporary download URL from Meta
                meta_res = await client.get(f"{BASE_URL}/{media_id}", headers=self.headers)
                meta_res.raise_for_status()
                media_url = meta_res.json().get("url")
                
                if not media_url:
                    logger.error(f"[danger]Meta API did not return a URL for media {media_id}.[/danger]")
                    return None
                    
                # Step 2: Download the actual binary payload
                download_res = await client.get(media_url, headers=self.headers)
                download_res.raise_for_status()
                
                logger.info(f"[success]Successfully downloaded media {media_id} ({len(download_res.content)} bytes).[/success]")
                return download_res.content
                
            except httpx.HTTPStatusError as e:
                logger.error(f"[danger]HTTP Error downloading WhatsApp media:[/danger] {e.response.text}")
                return None
            except Exception as e:
                logger.error(f"[danger]Unexpected error downloading WhatsApp media:[/danger] {e}", exc_info=True)
                return None

    async def parse_http_payload(self, payload: Dict[str, Any]) -> Optional[OmniMessage]:
        """
        Parses an incoming WhatsApp Webhook JSON into our unified OmniMessage.
        Ignores status updates (read, delivered, sent) to prevent processing errors.
        """
        try:
            entries = payload.get("entry", [])
            if not entries:
                return None
                
            changes = entries[0].get("changes", [])
            if not changes:
                return None
                
            value = changes[0].get("value", {})
            
            # If the payload contains 'statuses' instead of 'messages', it is a read receipt.
            # We silently ignore these to avoid unnecessary processing.
            if "messages" not in value:
                logger.debug("Received non-message webhook (likely a status update). Ignoring.")
                return None
                
            message_obj = value["messages"][0]
            sender_id = message_obj.get("from")
            msg_type = message_obj.get("type")
            
            content = ""
            media_bytes = None
            omni_type = MessageType.TEXT
            
            logger.info(f"Incoming WhatsApp message [{msg_type}] from {sender_id}.")

            # Extract content based on message type
            if msg_type == "text":
                content = message_obj.get("text", {}).get("body", "")
            elif msg_type == "image":
                content = message_obj.get("image", {}).get("caption", "")
                media_id = message_obj["image"].get("id")
                media_bytes = await self._download_media(media_id)
                omni_type = MessageType.IMAGE
            elif msg_type == "audio":
                media_id = message_obj["audio"].get("id")
                media_bytes = await self._download_media(media_id)
                omni_type = MessageType.AUDIO
            else:
                logger.warning(f"Unsupported WhatsApp message type received: {msg_type}")
                return None

            # Construct our secure, unified domain object
            return OmniMessage(
                platform=PlatformType.WHATSAPP,
                platform_user_id=sender_id,
                session_id=sender_id, # In WA, the sender ID acts as the conversation thread
                message_type=omni_type,
                content=content,
                media_payload=media_bytes
            )

        except Exception as e:
            logger.error(f"[danger]Malformed WhatsApp payload encountered:[/danger] {e}", exc_info=True)
            return None

    async def parse_ws_payload(self, payload: Dict[str, Any]) -> Optional[OmniMessage]:
        """
        WhatsApp does not natively support WebSockets, but we implement this 
        interface to support local CLI/HTML Dashboard testing mocks.
        """
        try:
            return OmniMessage(
                platform=PlatformType.WHATSAPP,
                platform_user_id=payload.get("user_id", "wa_ws_user"),
                session_id=payload.get("session_id", "wa_ws_session"),
                message_type=MessageType.TEXT,
                content=payload.get("content", "")
            )
        except Exception:
            return None

    async def send_http_message(self, recipient_id: str, text: str) -> bool:
        """
        Dispatches a standard text message back to the WhatsApp user.
        """
        logger.debug(f"Dispatching text message to WhatsApp user {recipient_id}.")
        url = f"{BASE_URL}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": text}
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.post(url, headers=self.headers, json=payload)
                res.raise_for_status()
                logger.info(f"[success]Text successfully delivered to WA {recipient_id}.[/success]")
                return True
            except httpx.HTTPStatusError as e:
                logger.error(f"[danger]Failed to send WhatsApp message:[/danger] HTTP {e.response.status_code} - {e.response.text}")
                return False
            except Exception as e:
                logger.error(f"[danger]Unexpected error dispatching WA message:[/danger] {e}", exc_info=True)
                return False