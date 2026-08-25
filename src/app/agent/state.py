"""
Graph State Contract for Omni-AI-Agent.

This module defines the immutable data structure that flows through the 
LangGraph state machine. Every node receives this state, performs its specific 
operation, and returns updates that are merged back into this central object.

By strictly typing the state using `TypedDict`, we guarantee that nodes 
can only pass authorized variables to each other, preventing runtime key errors.
"""

from typing import Annotated, Optional, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class OmniAgentState(TypedDict):
    """
    The master state object for the LangGraph execution.

    Attributes:
        messages (Sequence[BaseMessage]): The core conversation history. 
            The `add_messages` reducer ensures new messages are appended, 
            never overwritten, preserving the exact chain of thought.
        session_id (str): The unique thread identifier mapping to our 
            PostgreSQL checkpointer for cross-request short-term memory.
        user_id (str): The secure UUID of the user, used for database 
            queries and strict multi-tenant isolation.
        current_workflow (str): The explicit path the agent is executing 
            ('conversation', 'image', or 'audio').
        omni_activity (Optional[str]): The temporal real-world context 
            injected via the FastMCP system schedule tools.
        image_path (Optional[str]): Temporary storage path if an image 
            generation workflow was executed.
        audio_buffer (Optional[bytes]): Temporary binary storage if an 
            audio transcription or TTS workflow was executed.
        summary (Optional[str]): An active, rolling summary of the 
            conversation to prevent context-window overflow.
    """
    
    # Core Chat History
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Identity & Tracking
    session_id: str
    user_id: str
    
    # Routing & Context
    current_workflow: str
    omni_activity: Optional[str]
    
    # Media Payloads
    image_path: Optional[str]
    audio_buffer: Optional[bytes]
    
    # Context Management
    summary: Optional[str]