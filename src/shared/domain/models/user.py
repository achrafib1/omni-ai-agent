# src/shared/domain/models/user.py
"""
SQLAlchemy ORM model for representing application users.

This model defines the strict schema for the users table. It acts as the
central identity anchor for the multi-tenant architecture, securely linking
external platform identities (like WhatsApp phone numbers) to an internal UUID.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Inherit from the centralized Base to ensure Alembic detects this schema
from src.shared.infrastructure.db.base import Base
from src.shared.infrastructure.observability.logger import get_logger

# Initialize our elegant rich logger for this specific domain model
logger = get_logger(__name__)

# The TYPE_CHECKING block solves linter errors ("Memory" is not defined)
# without causing circular import crashes at runtime.
if TYPE_CHECKING:
    from shared.domain.models.memory import Memory


class User(Base):
    """
    Represents an Omni-AI-Agent user.

    This model is strictly focused on multi-tenant identity. By separating
    the external `platform_user_id` from our internal `id`, we ensure the
    system can seamlessly integrate multiple platforms (WhatsApp, Telegram)
    without breaking database integrity.

    Attributes:
        id (uuid.UUID): Secure internal UUIDv4 primary key.
        platform (str): The origin platform (e.g., 'whatsapp', 'telegram').
        platform_user_id (str): The specific ID from that platform.
        name (str): Optional human-readable name extracted from the platform.
        created_at (datetime): Automatically generated creation timestamp.
        updated_at (datetime): Automatically updating modification timestamp.
        memories (List[Memory]): One-to-many relationship mapping to user facts.
    """

    __tablename__ = "users"

    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    platform: Mapped[str] = mapped_column(String(50), nullable=False)

    platform_user_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # --- Relationships ---
    # We use string annotations ("Memory") combined with TYPE_CHECKING
    # to guarantee linter satisfaction and safe runtime execution.
    # cascade="all, delete-orphan" enforces GDPR compliance: deleting a user
    # absolutely destroys all their associated AI memories.
    memories: Mapped[List["Memory"]] = relationship(
        "Memory",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",  # Eagerly load memories to prevent async N+1 query issues
    )

    def __repr__(self) -> str:
        """
        Provides an unambiguous and secure string representation of the User.
        """
        return f"<User(id='{self.id}', platform='{self.platform}', platform_user_id='{self.platform_user_id}')>"
