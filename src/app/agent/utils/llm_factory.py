"""
LLM Dependency Injection Factory for Omni-AI-Agent.

This module is responsible for securely instantiating and configuring our 
Core Language Models. By utilizing a factory pattern, we can seamlessly 
inject different models (Groq for high-speed routing, Gemini for heavy logic) 
into our LangGraph nodes without hardcoding configurations.
"""

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from src.shared.config import settings
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)


def get_fast_routing_model(temperature: float = 0.1) -> ChatGroq:
    """
    Initializes a high-speed, low-latency LLM optimized for strict JSON output.
    
    We use Groq's Llama-3.3-70b here because it offers near-instantaneous 
    time-to-first-token (TTFT), which is critical for the invisible routing 
    and memory extraction nodes that the user waits for.
    
    Args:
        temperature (float): Creativity threshold. Low default ensures strict schema adherence.
        
    Returns:
        ChatGroq: A configured LangChain chat model instance.
    """
    try:
        groq_api_key = settings.GROQ_API_KEY.get_secret_value() if hasattr(settings.GROQ_API_KEY, "get_secret_value") else settings.GROQ_API_KEY
        return ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model="llama-3.3-70b-versatile",
            temperature=temperature,
            max_retries=2,
        )
    except Exception as e:
        logger.error(f"[danger]Failed to initialize Fast Routing LLM (Groq):[/danger] {e}")
        raise RuntimeError("LLM Initialization Error") from e


def get_core_reasoning_model(temperature: float = 0.7) -> ChatGoogleGenerativeAI:
    """
    Initializes a highly capable, large-context LLM for conversational generation.
    
    We use Gemini here for the core conversation node because of its massive 
    context window and native multimodal (image/audio) understanding capabilities.
    
    Args:
        temperature (float): Creativity threshold. Higher default allows for natural banter.
        
    Returns:
        ChatGoogleGenerativeAI: A configured LangChain chat model instance.
    """
    try:
        return ChatGoogleGenerativeAI(
            api_key=settings.GEMINI_API_KEY.get_secret_value(),
            model="gemini-3.1-flash-lite",
            temperature=temperature,
            max_retries=2,
        )
    except Exception as e:
        logger.error(f"[danger]Failed to initialize Core Reasoning LLM (Gemini):[/danger] {e}")
        raise RuntimeError("LLM Initialization Error") from e