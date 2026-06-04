# src/shared/infrastructure/db/dependencies.py
"""
FastAPI dependencies related to database sessions.

This module provides dependency functions that can be injected into API
endpoints to manage the lifecycle of database sessions per request.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from shared.infrastructure.db.session import AsyncSessionLocal
from shared.infrastructure.observability.logger import get_logger

# Initialize logger for this module.
logger = get_logger(__name__)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to provide and manage an asynchronous database session.

    This function is designed for use with FastAPI's `Depends` system. It creates
    a new `AsyncSession` for each request, yields it to the endpoint, and
    guarantees that the session is closed afterward, even if errors occur.

    Yields:
        AsyncSession: An asynchronous SQLAlchemy session ready for use in a request.
    """
    session: AsyncSession = AsyncSessionLocal()
    try:
        logger.debug("Database session opened for request.")
        yield session
    except Exception as e:
        logger.error(
            f"[danger]Database session error during request:[/danger] {str(e)}"
        )
        await session.rollback()
        raise
    finally:
        logger.debug("Database session for request closed.")
        await session.close()
