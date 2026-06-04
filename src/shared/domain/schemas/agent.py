# src/shared/domain/schemas/agent.py
"""
Agent Schema definitions for Omni-AI-Agent.

This module contains the strict Pydantic models utilized by LangGraph
to force the LLM into generating structured outputs (e.g., ensuring the
Router Node always replies with a valid workflow path).
"""

from enum import Enum

from pydantic import BaseModel, Field


class RouterResponseType(str, Enum):
    """Strictly defined paths the LLM router can take."""

    CONVERSATION = "conversation"
    IMAGE = "image"
    AUDIO = "audio"


class RouterResponse(BaseModel):
    """
    Structured output definition for the LangGraph Router Node.

    This model forces the LLM to categorize its intended response into one
    of the explicitly supported workflows. It utilizes Pydantic validation
    to guarantee the Graph edges will not receive hallucinated routing logic.
    """

    response_type: RouterResponseType = Field(
        ...,
        description="The response type to give to the user. "
        "MUST be 'conversation', 'image', or 'audio'.",
    )
