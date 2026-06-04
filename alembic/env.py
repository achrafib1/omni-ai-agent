# import asyncio
# from logging.config import fileConfig

# from sqlalchemy import pool
# from sqlalchemy.engine import Connection
# from sqlalchemy.ext.asyncio import async_engine_from_config

# from alembic import context

# # this is the Alembic Config object, which provides
# # access to the values within the .ini file in use.
# config = context.config

# # Interpret the config file for Python logging.
# # This line sets up loggers basically.
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# # add your model's MetaData object here
# # for 'autogenerate' support
# # from myapp import mymodel
# # target_metadata = mymodel.Base.metadata
# target_metadata = None

# # other values from the config, defined by the needs of env.py,
# # can be acquired:
# # my_important_option = config.get_main_option("my_important_option")
# # ... etc.


# def run_migrations_offline() -> None:
#     """Run migrations in 'offline' mode.

#     This configures the context with just a URL
#     and not an Engine, though an Engine is acceptable
#     here as well.  By skipping the Engine creation
#     we don't even need a DBAPI to be available.

#     Calls to context.execute() here emit the given string to the
#     script output.

#     """
#     url = config.get_main_option("sqlalchemy.url")
#     context.configure(
#         url=url,
#         target_metadata=target_metadata,
#         literal_binds=True,
#         dialect_opts={"paramstyle": "named"},
#     )

#     with context.begin_transaction():
#         context.run_migrations()


# def do_run_migrations(connection: Connection) -> None:
#     context.configure(connection=connection, target_metadata=target_metadata)

#     with context.begin_transaction():
#         context.run_migrations()


# async def run_async_migrations() -> None:
#     """In this scenario we need to create an Engine
#     and associate a connection with the context.

#     """

#     connectable = async_engine_from_config(
#         config.get_section(config.config_ini_section, {}),
#         prefix="sqlalchemy.",
#         poolclass=pool.NullPool,
#     )

#     async with connectable.connect() as connection:
#         await connection.run_sync(do_run_migrations)

#     await connectable.dispose()


# def run_migrations_online() -> None:
#     """Run migrations in 'online' mode."""

#     asyncio.run(run_async_migrations())


# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()

# alembic/env.py
# ruff: noqa: E402
"""
Alembic Environment Configuration for Omni-AI-Agent.

This module initializes the database connection using the async SQLAlchemy URL
provided via centralized Pydantic settings. It binds the metadata of the
declarative base so Alembic can autogenerate migrations.

Architectural highlights:
1. Dynamic model auto-registration prevents circular import loops in base.py.
2. Connection string driver mapping prevents synchronous psycopg2 fallbacks.
3. Schema isolation ensures Supabase internal tables (auth, storage) are protected.
"""

import asyncio
import importlib
import os
import pkgutil
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Dynamically add the 'src' directory to the Python path so Alembic can find the application code.
root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
src_dir = os.path.realpath(os.path.join(root_dir, "src"))

sys.path.insert(0, root_dir)
sys.path.insert(0, src_dir)

# Import configurations, the centralized declarative Base, and our rich logger.
# We utilize the unified 'shared' namespace to prevent Python from double-loading files.
from shared.config import settings
from shared.infrastructure.db.base import Base
from shared.infrastructure.observability.logger import get_logger

logger = get_logger("alembic.env")

# =====================================================================
# DYNAMIC MODEL AUTO-REGISTRATION
# =====================================================================
# This loop automatically discovers and imports all Python modules inside
# the domain models folder, registering them onto Base.metadata safely.
try:
    import shared.domain.models as models_package

    logger.info("[info]Scanning for domain models to register with Alembic...[/info]")
    for _, module_name, _ in pkgutil.iter_modules(models_package.__path__):
        # We skip the base module if it happens to be in there
        if module_name == "base":
            continue

        importlib.import_module(f"shared.domain.models.{module_name}")
        logger.info(f"[success]Registered model module: {module_name}[/success]")

except ImportError as e:
    logger.error("[danger]Failed to dynamically import domain models for migration.[/danger]")
    raise RuntimeError(
        "Failed to dynamically import domain models for migration metadata validation."
    ) from e
# =====================================================================

# Alembic Config object, which provides access to the values within the alembic.ini file.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Attach our models' metadata
target_metadata = Base.metadata


def get_async_database_url() -> str:
    """
    Retrieves the database connection string and ensures the asyncpg driver is specified.

    This prevents driver-resolution errors (such as missing psycopg2) by mapping
    standard synchronous connection strings into their asynchronous equivalent.
    """
    db_url = settings.POSTGRES_CONNECTION_STRING.get_secret_value()
    if not db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return db_url


def include_object(object, name, type_, reflected, compare_to):
    """
    The definitive Alembic filter hook for Schema Isolated environments.

    This ensures Alembic ONLY manages tables belonging specifically to our
    configured schema (e.g., 'omni'). It ignores Supabase's internal schemas
    like 'auth' and 'storage'.
    """
    # Explicitly ignore Alembic's own history table during the comparison phase.
    if type_ == "table" and name == "alembic_version":
        return False

    # Define the target application schema.
    target_schema = getattr(settings, "DB_SCHEMA", "public")

    # If the object is assigned to a schema, it MUST match our target schema.
    if hasattr(object, "schema") and object.schema:
        return object.schema == target_schema

    # If it lacks a schema, only include it if our target is the public default.
    return target_schema == "public"


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Configures the context with just a URL and not an Engine.
    """
    db_url = get_async_database_url()

    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        version_table_schema=getattr(settings, "DB_SCHEMA", "public"),
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Configure and run migrations for online mode.
    """
    target_schema = getattr(settings, "DB_SCHEMA", "public")

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        version_table_schema=target_schema,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create the async Engine and run migrations in a synchronous context block.
    """
    db_url = get_async_database_url()

    connectable = create_async_engine(
        db_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode by spawning the async event loop.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
