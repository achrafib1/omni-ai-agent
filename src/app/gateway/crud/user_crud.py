# src/app/gateway/crud/user_crud.py
"""
User Database Operations for Omni-AI-Agent.

This module encapsulates all SQLAlchemy ORM operations related to the User entity.
By isolating database interactions into a dedicated CRUD (Create, Read, Update, Delete)
layer, we ensure our API routes and business logic services remain agnostic to
the underlying database schema and query syntax.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.models.user import User
from src.shared.domain.schemas.message import PlatformType
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)


async def get_or_create_user(
    db: AsyncSession, platform: PlatformType, platform_user_id: str, name: Optional[str] = None
) -> User:
    """
    Retrieves an existing user by their platform ID, or creates a new one.

    This function utilizes a select-then-insert pattern. It gracefully catches
    IntegrityErrors in highly concurrent environments (e.g., if a user sends
    two messages simultaneously on their first interaction).

    Args:
        db (AsyncSession): The active asynchronous database session.
        platform (PlatformType): The messaging platform (e.g., WhatsApp).
        platform_user_id (str): The unique ID from the platform (e.g., phone number).
        name (Optional[str]): The human-readable name provided by the platform.

    Returns:
        User: The SQLAlchemy User model instance.
    """
    logger.debug(
        f"Querying database for user on platform '{platform.value}' with ID '{platform_user_id}'."
    )

    # 1. Attempt to find the existing user
    stmt = select(User).where(
        User.platform == platform.value, User.platform_user_id == platform_user_id
    )
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.debug(f"User found in database. Internal UUID: {existing_user.id}")
        return existing_user

    # 2. If not found, create a new user entity
    logger.info(
        f"[info]New user detected on '{platform.value}'. Provisioning database record.[/info]"
    )
    new_user = User(platform=platform.value, platform_user_id=platform_user_id, name=name)
    db.add(new_user)

    try:
        await db.commit()
        await db.refresh(new_user)
        logger.info(
            f"[success]Successfully created new user. Internal UUID: {new_user.id}[/success]"
        )
        return new_user
    except IntegrityError as e:
        # Handle concurrent race conditions where the user was created milliseconds ago
        await db.rollback()
        logger.warning(
            f"IntegrityError during user creation. Attempting to fetch existing record: {e}"
        )

        retry_result = await db.execute(stmt)
        race_user = retry_result.scalar_one_or_none()

        if race_user:
            return race_user
        raise RuntimeError("Critical database conflict during user provisioning.") from e
