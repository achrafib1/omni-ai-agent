# src/shared/infrastructure/db/dependencies.py
"""
FastAPI dependencies related to database sessions.

This module provides dependency functions that can be injected into API
endpoints to manage the lifecycle of database sessions per request.
"""

from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import settings
from shared.infrastructure.db.session import AsyncSessionLocal
from shared.infrastructure.observability.logger import get_logger

# Initialize logger for this module.
logger = get_logger(__name__)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to provide and manage an asynchronous database session.

    Designed for use with FastAPI's `Depends` injection system. It guarantees
    that a new `AsyncSession` is yielded per request and safely closed afterward.
    If a database error occurs mid-request, it intercepts it, rolls back the
    transaction to prevent locks, and raises a secure exception.

    Yields:
        AsyncSession: An asynchronous SQLAlchemy session ready for use.
    """
    session: AsyncSession = AsyncSessionLocal()
    try:
        if settings.ENABLE_DEBUG_LOGS:
            logger.debug("Database session opened for incoming request.")

        yield session

    except SQLAlchemyError as db_err:
        # We catch SQLAlchemy specific errors to rollback and log safely.
        # We avoid logging the raw query string which might contain user PII.
        logger.error(
            "[danger]Database transaction failed during request. Rolling back session.[/danger]"
        )
        await session.rollback()
        raise RuntimeError("A database transaction error occurred.") from db_err

    except Exception:
        # Catch any other unexpected python errors
        logger.error(
            "[danger]Unexpected error during database session lifecycle. Rolling back.[/danger]"
        )
        await session.rollback()
        raise

    finally:
        if settings.ENABLE_DEBUG_LOGS:
            logger.debug("Database session for request closed.")

        await session.close()
