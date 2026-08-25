"""
Deterministic Routing Edges for Omni-AI-Agent.

This module defines the traffic controllers of the LangGraph state machine.
Edges execute instantaneously. They inspect the current `OmniAgentState` 
and return a literal string indicating the precise next node to execute.

This separation of concerns makes the AI's decision tree fully visible, 
testable, and immune to LLM hallucinations.
"""

from typing import Literal

from src.app.agent.state import OmniAgentState
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)


def route_workflow(state: OmniAgentState) -> Literal["conversation_node", "image_node", "audio_node"]:
    """
    Routes the execution graph based on the validated LLM router decision.
    
    The 'router_node' (executed prior to this edge) forces the LLM to output 
    a strictly typed Pydantic schema dictating the workflow. This edge blindly 
    trusts that schema and directs traffic accordingly.
    
    Args:
        state (OmniAgentState): The current graph state.
        
    Returns:
        Literal: The string identifier of the next node to execute.
    """
    # Default to conversation if the key is missing to prevent graph crashes
    workflow = state.get("current_workflow", "conversation")
    
    logger.debug(f"[Routing Edge] Transitioning workflow to: {workflow}_node")
    
    if workflow == "image":
        return "image_node"
    elif workflow == "audio":
        return "audio_node"
        
    return "conversation_node"


def should_summarize(state: OmniAgentState) -> Literal["summarize_node", "__end__"]:
    """
    Evaluates whether the conversation history has exceeded the token safety limit.
    
    To prevent Context Window Overflow and reduce API costs, we trigger a 
    background summarization node if the message array grows too large.
    
    Args:
        state (OmniAgentState): The current graph state.
        
    Returns:
        Literal: The summarize node if limits are breached, otherwise END ("__end__").
    """
    messages = state.get("messages", [])
    
    # We trigger summarization if the conversation exceeds 20 messages.
    # Note: In a production tuning phase, we might count actual tokens here.
    if len(messages) > 20:
        logger.info("[Routing Edge] Message limit exceeded (20+). Triggering summarize_node.")
        return "summarize_node"
    
    logger.debug("[Routing Edge] Graph cycle complete. Halting execution until next user input.")
    # Return string literal value directly to satisfy strict typing Lit annotations
    return "__end__"