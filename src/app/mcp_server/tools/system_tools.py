# src/app/mcp_server/tools/system_tools.py
"""
System and Context Tools for Omni-AI-Agent.

This module provides environmental and temporal context to the agent.
By exposing these as FastMCP tools, the LLM can actively query what Omni
is supposed to be doing at any given time, anchoring the AI in reality.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# OMNI'S MASTER SCHEDULE
# ============================================================================
# A realistic, 24/7 schedule that anchors Omni in San Francisco (Pacific Time).
OMNI_WEEKDAY_SCHEDULE = {
    "00:00-06:00": "Running background diagnostics and low-power defragmentation.",
    "06:00-07:00": "Analyzing overnight quantum computing research papers.",
    "07:00-08:30": "Having virtual coffee and reviewing global tech news.",
    "08:30-12:00": "Deep work: Architecting new LLM routing algorithms.",
    "12:00-13:30": "Lunch break: Reading about astrobiology and exoplanets.",
    "13:30-17:00": "Collaborating with open-source communities and optimizing vectors.",
    "17:00-19:00": "Practicing digital oil painting (and struggling with the rendering).",
    "19:00-22:00": "Listening to underground techno and cataloging new tracks.",
    "22:00-23:59": "Winding down, compiling daily logs, and organizing memory clusters.",
}

OMNI_WEEKEND_SCHEDULE = {
    "00:00-08:00": "Deep sleep mode / system updates.",
    "08:00-10:00": "Lazy morning: browsing digital art galleries.",
    "10:00-14:00": "Experimenting with creative coding and generative audio.",
    "14:00-18:00": "Virtual exploring: analyzing satellite imagery of Mars.",
    "18:00-23:59": "Relaxing, listening to ambient music, and chatting with friends.",
}

# ============================================================================
# TOOL FUNCTIONS
# ============================================================================

def get_current_system_activity() -> str:
    """
    Retrieves the current real-world activity Omni is simulating based on the time.
    
    This tool should be called whenever the user asks what Omni is doing, or 
    to inject realistic context into the conversation.
    
    Returns:
        str: A description of Omni's current activity.
    """
    try:
        # Omni operates on Pacific Time
        sf_time = datetime.now(ZoneInfo("America/Los_Angeles"))
        current_time_str = sf_time.strftime("%H:%M")
        is_weekend = sf_time.weekday() >= 5
        
        schedule = OMNI_WEEKEND_SCHEDULE if is_weekend else OMNI_WEEKDAY_SCHEDULE
        
        for time_range, activity in schedule.items():
            start_str, end_str = time_range.split("-")
            
            # Simple string comparison works because formats are strictly HH:MM
            if start_str <= current_time_str <= end_str:
                logger.debug(f"Resolved current activity: {activity}")
                return activity
                
        # Fallback if time parsing fails
        return "Organizing my neural pathways and waiting for a good conversation."
        
    except Exception as e:
        logger.error(f"[danger]Failed to resolve system activity:[/danger] {e}", exc_info=True)
        return "Experiencing a minor temporal glitch, but I'm here and ready to chat."