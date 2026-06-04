# src/shared/infrastructure/db/session.py
"""
Database Engine and Session Factory configuration.

This module initializes the asynchronous SQLAlchemy engine using the Supabase
connection string and configures the session factory (`AsyncSessionLocal`)
that will be used to spawn database sessions for incoming requests.
"""

import os
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# We dynamically add the project root to sys.path if needed, though uv handles this well.
# We import our rich logger to maintain elegant observability.
from shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

# Fetch the Supabase Postgres connection string.
# We replace the default 'postgresql://' with 'postgresql+asyncpg://' for async support.
DATABASE_URL = os.environ.get(
    "POSTGRES_CONNECTION_STRING",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
)

if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

try:
    # Create the asynchronous engine.
    # pool_pre_ping=True ensures connections are alive before using them.
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,  # Set to True only for deep SQL debugging
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

    # Create the session factory bound to the async engine.
    # expire_on_commit=False is crucial for async workflows so we can access object attributes after commit.
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    logger.info("[success]Database Async Engine successfully initialized.[/success]")

except Exception as e:
    logger.error(
        f"[danger]Failed to initialize database engine:[/danger] {str(e)}",
        exc_info=True,
    )
    raise
