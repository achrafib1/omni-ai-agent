# src/shared/domain/models/__init__.py
"""
Centralized Model Registry for Omni-AI-Agent.

Explicitly loads all domain models so SQLAlchemy's declarative Base 
can map all relationships (e.g., User -> Memory) prior to querying.
Using relative imports prevents sys.path namespace duplication.
"""

from .user import User
from .memory import Memory

__all__ = ["User", "Memory"]