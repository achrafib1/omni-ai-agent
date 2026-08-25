# src/app/mcp_server/tools/memory_rag.py
"""
Long-Term Memory RAG Tools for Omni-AI-Agent.

Executes asynchronous pgvector cosine similarity searches.
Utilizes Google's Gemini embeddings (`text-embedding-004`) to generate 
rich, 768-dimensional semantic vectors for superior context retrieval.
"""

import uuid
from typing import Sequence
from sqlalchemy import select
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.shared.config import settings
from src.shared.domain.models.memory import Memory
from src.shared.infrastructure.db.session import AsyncSessionLocal
from src.shared.infrastructure.observability.logger import get_logger
from opik import track


logger = get_logger(__name__)

# ============================================================================
# EMBEDDING ENGINE INITIALIZATION (768 Dimensions)
# ============================================================================
try:
    # We use Google's advanced text embedding model
    embedder = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2", 
        output_dimensionality=768,
        api_key=settings.GEMINI_API_KEY
    )
    logger.info("[success]Gemini Embeddings (768-dim) initialized successfully.[/success]")
except Exception as e:
    logger.error(f"[danger]Failed to initialize Gemini Embedder:[/danger] {e}", exc_info=True)
    embedder = None

# ============================================================================
# TOOL FUNCTIONS
# ============================================================================

@track(type="tool")
async def store_user_memory(user_id: str, fact: str) -> str:
    """
    Generates a 768-D semantic vector from a fact and saves it to pgvector.
    Exposed as an MCP Tool.
    """
    if not embedder:
        return "System Notification: Embedding engine offline."

    try:
        user_uuid = uuid.UUID(user_id)
        
        # Await the external Google API to generate the vector
        logger.debug(f"Generating Gemini embedding for fact: '{fact}'")
        vector = await embedder.aembed_query(fact)
        
        # Isolate the database transaction
        async with AsyncSessionLocal() as session:
            new_memory = Memory(user_id=user_uuid, content=fact, embedding=vector)
            session.add(new_memory)
            await session.commit()
            
            logger.info(f"[success]Stored new permanent memory for User {user_id}[/success]")
            return f"Successfully stored memory: '{fact}'"
            
    except Exception as e:
        logger.error(f"[danger]Failed to store user memory:[/danger] {e}", exc_info=True)
        return "Error: Database transaction failed."

@track(type="tool")
async def retrieve_user_memories(user_id: str, query: str) -> str:
    """
    Performs a pgvector Cosine Distance search against the user's memories.
    Exposed as an MCP Tool.
    """
    if not embedder:
        return ""

    try:
        user_uuid = uuid.UUID(user_id)
        query_vector = await embedder.aembed_query(query)
        
        async with AsyncSessionLocal() as session:
            # Performs highly-optimized pgvector cosine distance search (<=>)
            stmt = (
                select(Memory.content)
                .where(Memory.user_id == user_uuid)
                .order_by(Memory.embedding.cosine_distance(query_vector))
                .limit(3)
            )
            
            result = await session.execute(stmt)
            memories: Sequence[str] = result.scalars().all()
            
            if not memories:
                logger.debug(f"No relevant memories found for user {user_id}.")
                return "No highly relevant past memories found."
                
            formatted_memories = "\n".join([f"- {mem}" for mem in memories])
            logger.info(f"[success]Retrieved {len(memories)} semantic memories for User {user_id}[/success]")
            
            return formatted_memories
            
    except Exception as e:
        logger.error(f"[danger]Failed to retrieve user memories:[/danger] {e}", exc_info=True)
        return ""