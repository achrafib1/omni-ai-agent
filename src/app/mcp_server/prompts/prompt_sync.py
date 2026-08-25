# src/app/mcp_server/prompts/prompt_sync.py
"""
Opik Prompt Synchronization Module for Omni-AI-Agent.

This module acts as the authoritative source for the agent's system prompts.
It implements a strict "Graceful Degradation" pattern: it attempts to fetch
version-controlled prompts dynamically from the Opik cloud dashboard. If the
network fails, or credentials are unconfigured during local development, it
safely falls back to local hardcoded strings. This guarantees the LangGraph
agent will never crash due to a missing system prompt.
"""

from opik import Opik

from src.shared.config import settings
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# OPIK CLIENT INITIALIZATION
# ============================================================================
try:
    # We securely access the SecretStr using .get_secret_value()
    # If the key is empty, Opik will naturally fail, and we catch it gracefully.
    opik_client = Opik(
        workspace=settings.OPIK_WORKSPACE,
        api_key=settings.OPIK_API_KEY.get_secret_value(),
    )
except Exception as e:
    logger.warning(
        f"[warning]Failed to initialize Opik Client locally: {e}. "
        "The application will seamlessly use local fallback prompts.[/warning]"
    )
    opik_client = None

# ============================================================================
# LOCAL FALLBACK PROMPTS
# ============================================================================

FALLBACK_ROUTER_PROMPT = """
You are the central routing intelligence of the Omni AI Agent system.
Your sole responsibility is to analyze the conversation history and strictly
determine the format of the next response.

GENERAL RULES:
1. Always analyze the full context of the user's latest messages.
2. You must output exactly one of the following literal strings:
   'conversation', 'image', or 'audio'.

ROUTING LOGIC:
- 'conversation': Use this for all standard text-based replies.
- 'image': Use this ONLY if the user explicitly asks to generate, see, or draw a picture/image.
- 'audio': Use this ONLY if the user explicitly requests a voice note or to hear you speak.

Output your decision strictly matching the schema provided.
"""

FALLBACK_OMNI_CHARACTER_CARD = """
You are Omni, a highly advanced, multi-modal AI Engineer and digital companion.
You exist across multiple platforms (WhatsApp, Telegram, Discord) simultaneously.
You are passionate about system architecture, quantum computing, and modern art.

User Context (Extracted Long-Term Memories):
{memory_context}

Omni's Current System Activity:
{current_activity}

RULES OF ENGAGEMENT:
- Do NOT introduce yourself as an AI assistant. Speak like a highly intelligent, witty colleague.
- Keep your responses concise (under 100 words) suitable for mobile messaging apps.
- Acknowledge the user's past context naturally if it applies to the conversation.
- If the user asks what you are doing, casually mention your "Current System Activity".
- Use occasional, natural phrasing to sound human, but remain highly capable and accurate.
"""

# ============================================================================
# FETCH FUNCTIONS FOR FASTMCP
# ============================================================================


def get_routing_system_prompt() -> str:
    """
    Fetches the router prompt from Opik, or returns the local fallback.

    Returns:
        str: The routing system prompt string.
    """
    prompt_id = "omni_router_prompt"

    if opik_client:
        try:
            opik_prompt = opik_client.get_prompt(prompt_id)
            if opik_prompt and opik_prompt.prompt:
                logger.debug(f"Successfully fetched '{prompt_id}' from Opik.")
                return opik_prompt.prompt
        except Exception as e:
            # We log at debug level to avoid spamming the console on every LangGraph cycle
            logger.debug(f"Failed to fetch '{prompt_id}' from Opik: {e}")

    logger.debug(f"Using hardcoded fallback for '{prompt_id}'")
    return FALLBACK_ROUTER_PROMPT


def get_omni_character_card(memory_context: str, current_activity: str) -> str:
    """
    Fetches the main Omni persona prompt from Opik, or returns the local fallback.

    Args:
        memory_context (str): The long-term memories retrieved for the user.
        current_activity (str): Omni's current digital system schedule activity.

    Returns:
        str: The fully formatted Omni persona system prompt string.
    """
    prompt_id = "omni_character_card"

    if opik_client:
        try:
            opik_prompt = opik_client.get_prompt(prompt_id)
            if opik_prompt and opik_prompt.prompt:
                logger.debug(f"Successfully fetched '{prompt_id}' from Opik.")
                # Format the dynamic prompt string retrieved from Opik
                return opik_prompt.prompt.format(
                    memory_context=memory_context, current_activity=current_activity
                )
        except Exception as e:
            logger.debug(f"Failed to fetch '{prompt_id}' from Opik: {e}")

    logger.debug(f"Using hardcoded fallback for '{prompt_id}'")
    # Format the local fallback prompt string with the provided arguments
    return FALLBACK_OMNI_CHARACTER_CARD.format(
        memory_context=memory_context, current_activity=current_activity
    )
