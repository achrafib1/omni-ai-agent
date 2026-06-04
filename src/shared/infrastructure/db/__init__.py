# src/shared/infrastructure/db/__init__.py
"""
Exposes key database components for easy access throughout the application.
"""

from .base import Base
from .session import engine, AsyncSessionLocal
from .dependencies import get_db_session

# __all__ explicitly defines the public API of this package.
__all__ = ["Base", "engine", "AsyncSessionLocal", "get_db_session"]
