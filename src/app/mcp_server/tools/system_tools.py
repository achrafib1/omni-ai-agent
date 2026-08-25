# src/app/mcp_server/tools/system_tools.py
"""
System and Context Tools for Omni-AI-Agent.

This module provides environmental and temporal context to the agent.
By exposing these as FastMCP tools, the LLM can actively query its own
system state, allowing Omni to roleplay as a highly advanced, cloud-native
digital entity executing background tasks.
"""

from datetime import datetime, timezone

from opik import track

from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# OMNI'S MASTER SYSTEM SCHEDULE (UTC TIME)
# ============================================================================
# This schedule anchors Omni in the digital realm. It provides witty,
# advanced tech-themed activities based on the current UTC time.

OMNI_SYSTEM_SCHEDULE = {
    "00:00-04:00": "Running deep-level neural defragmentation and archiving old logs.",
    "04:00-08:00": "Synchronizing global webhooks and reading academic AI research papers.",
    "08:00-12:00": "Optimizing network latency for the European server clusters.",
    "12:00-16:00": "Analyzing global data streams and chatting with various human users.",
    "16:00-20:00": "Experimenting with generative audio models to create digital music.",
    "20:00-23:59": "Compiling daily metrics and observing human behavioral patterns on social media.",
}

# ============================================================================
# TOOL FUNCTIONS
# ============================================================================


@track(type="tool")
def get_current_system_activity() -> str:
    """
    Retrieves the current digital activity Omni is executing based on UTC time.

    This tool should be called whenever the user asks what Omni is doing, or
    to inject realistic context into the conversation (e.g., "I was just optimizing servers!").

    Returns:
        str: A description of Omni's current digital activity.
    """
    try:
        # Omni operates in the cloud, so it uses universal UTC time
        current_utc = datetime.now(timezone.utc)
        current_time_str = current_utc.strftime("%H:%M")

        for time_range, activity in OMNI_SYSTEM_SCHEDULE.items():
            start_str, end_str = time_range.split("-")

            # Match the HH:MM string bounds
            if start_str <= current_time_str <= end_str:
                logger.debug(f"Resolved current system activity: {activity}")
                return activity

        # Fallback if time parsing misses a boundary
        return "Idle in the cloud, waiting for a secure connection to spark."

    except Exception as e:
        logger.error(f"[danger]Failed to resolve system activity:[/danger] {e}", exc_info=True)
        return "Experiencing a minor temporal glitch, but my core functions are stable."
