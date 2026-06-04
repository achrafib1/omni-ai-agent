# src/shared/infrastructure/db/base.py
"""
Defines the declarative base for all SQLAlchemy ORM models.

This module's single responsibility is to create and expose the `Base`
object. All ORM models in the application will inherit from this `Base`,
allowing them to be collected into a single metadata registry that Alembic
can use to detect schema changes. Separating this into its own file
prevents circular import issues with models.
"""

from sqlalchemy.orm import declarative_base

# The declarative base that all ORM models will inherit from.
Base = declarative_base()

# Note: In Phase 1, we will import our models here so Alembic can discover them.
# Example:
# from shared.domain.models.user import User
# from shared.domain.models.memory import Memory
