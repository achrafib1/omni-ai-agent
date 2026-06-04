# src/shared/infrastructure/db/__init__.py
"""
Exposes key database components for easy access throughout the application.
"""

from .base import Base
from .dependencies import get_db_session
from .session import AsyncSessionLocal, engine

# __all__ explicitly defines the public API of this package.
__all__ = ["Base", "engine", "AsyncSessionLocal", "get_db_session"]
