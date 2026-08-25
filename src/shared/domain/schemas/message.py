# src/shared/domain/schemas/message.py
"""
Universal Messaging Schema for Omni-AI-Agent.

This module defines the standard data structures for all inbound and
outbound messages. Regardless of whether a message originates from WhatsApp,
Telegram, or Discord, it is parsed into an `OmniMessage` before entering
the LangGraph agent pipeline. This enforces strict decoupling between the
gateway and the core AI logic.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)


class PlatformType(str, Enum):
    """Enumeration of supported messaging platforms."""

    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    CLI = "cli"  # For local terminal testing


class MessageType(str, Enum):
    """Enumeration of supported media types in messages."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"


class OmniMessage(BaseModel):
    """
    The universal message object passed throughout the application.

    Attributes:
        platform (PlatformType): The origin platform of the message.
        platform_user_id (str): The unique identifier from the source platform (e.g., WA phone number).
        session_id (str): A unique ID for the conversation thread (crucial for LangGraph memory).
        message_type (MessageType): Indicates if this is text, an image, or an audio voice note.
        content (str): The parsed text content, or image caption, or transcribed audio text.
        media_payload (Optional[bytes]): The raw binary data if an image or audio was sent.
    """

    platform: PlatformType = Field(..., description="The origin platform of the message.")
    platform_user_id: str = Field(..., description="Unique user ID from the platform.")
    session_id: str = Field(..., description="Conversation thread identifier for agent memory.")
    message_type: MessageType = Field(
        default=MessageType.TEXT, description="Type of message payload."
    )
    content: str = Field(default="", description="Text body, transcript, or image caption.")
    media_payload: Optional[bytes] = Field(
        default=None, description="Binary data for images/audio."
    )

    class Config:
        # Prevent validation mutation overhead for binary payloads
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        # Log the creation of the message object cleanly at the DEBUG level
        logger.debug(
            f"OmniMessage instantiated: [{self.platform.value}] "
            f"User:{self.platform_user_id} | Type:{self.message_type.value}"
        )
