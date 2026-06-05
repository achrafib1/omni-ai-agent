# src/app/mcp_server/tools/memory_rag.py
"""
Long-Term Memory RAG Tools for Omni-AI-Agent.

This module provides the agent with the ability to store and retrieve semantic 
facts about specific users. It utilizes Google Generative AI for lightning-fast 
embeddings and executes asynchronous pgvector cosine similarity searches against 
the isolated Supabase database.
"""

import os
import uuid
from typing import Sequence

from sqlalchemy import select
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from shared.config import settings
from shared.domain.models.memory import Memory
from shared.infrastructure.db.session import AsyncSessionLocal
from shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# EMBEDDING ENGINE INITIALIZATION
# ============================================================================
try:
    # Use api_key (the Pydantic alias) instead of google_api_key
    embedder = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview",
        api_key=settings.GEMINI_API_KEY
    )
except Exception as e:
    logger.error(f"[danger]Failed to initialize Gemini Embedder:[/danger] {e}")
    embedder = None


# ============================================================================
# TOOL FUNCTIONS
# ============================================================================

async def store_user_memory(user_id: str, fact: str) -> str:
    """
    Stores a permanent, long-term memory about a specific user.
    
    Args:
        user_id (str): The strictly formatted UUID string of the user.
        fact (str): The isolated, concise fact to remember.
        
    Returns:
        str: A status message indicating success or failure.
    """
    if not embedder:
        return "Error: Embedding engine is offline. Cannot store memory."

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        logger.warning(f"Attempted to store memory with invalid UUID format: {user_id}")
        return "Error: Invalid user_id format."

    try:
        logger.debug(f"Generating embedding for fact: '{fact}'")
        vector = await embedder.aembed_query(fact)
        
        async with AsyncSessionLocal() as session:
            new_memory = Memory(
                user_id=user_uuid,
                content=fact,
                embedding=vector
            )
            session.add(new_memory)
            await session.commit()
            
            logger.info(f"[success]Stored new memory for user {user_id}[/success]")
            return f"Successfully stored memory: '{fact}'"
            
    except Exception as e:
        logger.error(f"[danger]Failed to store user memory:[/danger] {e}", exc_info=True)
        return "Error: Database transaction failed."


async def retrieve_user_memories(user_id: str, query: str) -> str:
    """
    Retrieves the most relevant past memories about a user based on a query.
    
    Args:
        user_id (str): The strictly formatted UUID string of the user.
        query (str): The subject you are trying to remember (e.g., "favorite food").
        
    Returns:
        str: A formatted string of relevant facts, or a message if none are found.
    """
    if not embedder:
        return "System Notification: Embedding engine offline."

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return "System Notification: Invalid user identifier."

    try:
        query_vector = await embedder.aembed_query(query)
        
        async with AsyncSessionLocal() as session:
            stmt = (
                select(Memory.content)
                .where(Memory.user_id == user_uuid)
                .order_by(Memory.embedding.cosine_distance(query_vector))
                .limit(3)
            )
            
            result = await session.execute(stmt)
            memories: Sequence[str] = result.scalars().all()
            
            if not memories:
                logger.debug(f"No relevant memories found for user {user_id} regarding '{query}'")
                return "No relevant memories found regarding this topic."
                
            formatted_memories = "\n".join([f"- {mem}" for mem in memories])
            logger.info(f"[success]Retrieved {len(memories)} memories for user {user_id}[/success]")
            
            return f"Relevant facts recalled:\n{formatted_memories}"
            
    except Exception as e:
        logger.error(f"[danger]Failed to retrieve user memories:[/danger] {e}", exc_info=True)
        return "System Notification: Memory retrieval failed."