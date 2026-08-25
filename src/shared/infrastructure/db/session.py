# src/shared/infrastructure/db/session.py
"""
Database Engine and Session Factory configuration for Omni-AI-Agent.

This module initializes the asynchronous SQLAlchemy engine using the Supabase
connection string securely loaded from centralized settings. It configures the
session factory (`AsyncSessionLocal`) used to spawn database sessions.

Security Isolation:
To comply with enterprise security standards, no part of the connection string,
hostnames, usernames, or ports are ever written to the application logs.
Only generic status indicators are emitted.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.shared.config import settings
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

# 1. Securely fetch the connection string via get_secret_value()
raw_db_url = settings.POSTGRES_CONNECTION_STRING.get_secret_value()

# 2. Ensure the asyncpg driver is specified to prevent synchronous fallbacks
if not raw_db_url.startswith("postgresql+asyncpg://"):
    raw_db_url = raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

try:
    # 3. Create the asynchronous engine.
    # pool_pre_ping=True: Checks if a connection is alive before handing it out.
    # pool_recycle=1800: Recycles connections every 30 minutes to prevent stale drops.
    # echo=settings.ENABLE_DEBUG_LOGS: Safely toggles SQL query logging.
    engine = create_async_engine(
        raw_db_url,
        echo=settings.ENABLE_DEBUG_LOGS,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=10,
        max_overflow=20,
    )

    # 4. Create the session factory bound to the async engine.
    # expire_on_commit=False is crucial for async workflows so object attributes
    # remain accessible after the session commits without triggering lazy loads.
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    # We log a completely generic, credential-free success message
    logger.info("[success]Database Async Engine successfully configured and secured.[/success]")

except Exception as e:
    # We explicitly do NOT log 'str(e)' or 'raw_db_url'.
    # We log a generic security-safe message to prevent credential dumping.
    logger.error(
        "[danger]Failed to initialize database engine. "
        "Ensure database credentials and network connectivity are correct.[/danger]",
        exc_info=False,
    )
    raise RuntimeError("Database engine initialization failed.") from e
