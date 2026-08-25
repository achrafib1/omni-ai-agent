# src/app/gateway/adapters/base.py
"""
Abstract Channel Adapter Interface for Omni-AI-Agent.

This module defines the contract for all messaging platform adapters. By adhering
to this interface, the central Message Bus can operate entirely agnostically,
parsing inbound payloads and dispatching outbound messages across any platform
without coupling to proprietary JSON structures.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.shared.domain.schemas.message import OmniMessage, PlatformType


class BaseChannelAdapter(ABC):
    """
    Abstract Base Class representing the required capabilities of a platform adapter.
    """

    @abstractmethod
    def get_platform_type(self) -> PlatformType:
        """
        Returns the specific platform identifier enum (e.g., PlatformType.DISCORD).
        """
        pass

    @abstractmethod
    async def parse_http_payload(self, payload: Dict[str, Any]) -> Optional[OmniMessage]:
        """
        Parses raw HTTP JSON webhooks into the unified OmniMessage structure.

        Args:
            payload: The raw JSON dictionary received from the platform.

        Returns:
            Optional[OmniMessage]: The standardized message, or None if the payload
                                   is an irrelevant event (e.g., read receipts).
        """
        pass

    @abstractmethod
    async def parse_ws_payload(self, payload: Dict[str, Any]) -> Optional[OmniMessage]:
        """
        Parses raw WebSocket JSON payloads into the unified OmniMessage structure.

        Args:
            payload: The raw JSON dictionary received over the socket.

        Returns:
            Optional[OmniMessage]: The standardized message.
        """
        pass

    @abstractmethod
    async def send_http_message(self, recipient_id: str, text: str) -> bool:
        """
        Dispatches a final, synchronous text reply back to the platform via its REST API.

        Args:
            recipient_id: The platform-specific identifier for the user or channel.
            text: The final assembled text response from the LangGraph agent.

        Returns:
            bool: True if delivery was successful, False otherwise.
        """
        pass
