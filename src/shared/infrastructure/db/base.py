# src/shared/infrastructure/db/base.py
"""
Defines the declarative base for all SQLAlchemy ORM models.

This module creates the `Base` object bound to our isolated database schema
(loaded dynamically from config settings). Because the Alembic environment
now utilizes a dynamic module scanner, this file no longer needs to import
individual domain models, completely eliminating circular dependency risks.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

# Import our centralized settings to fetch the schema namespace dynamically
from shared.config import settings

# Bind metadata explicitly to our schema for clean Postgres-level isolation
# This ensures that all tables inherit the 'omni' (or custom) schema automatically.
metadata = MetaData(schema=settings.DB_SCHEMA)

# The declarative base that all ORM models will inherit from.
Base = declarative_base(metadata=metadata)
