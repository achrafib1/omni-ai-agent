# src/shared/domain/models/memory.py
"""
SQLAlchemy ORM model for representing Long-Term Semantic Memory.

This module defines the relational structure for the agent's knowledge base.
By embedding the pgvector extension natively within SQLAlchemy, we guarantee
strict multi-tenant data isolation via Foreign Key constraints.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

# Natively integrate the pgvector extension into SQLAlchemy
from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.db.base import Base
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

# Prevent circular imports while satisfying Pylance/Mypy strict typing
if TYPE_CHECKING:
    from src.shared.domain.models.user import User


class Memory(Base):
    """
    Represents a semantic fact stored for a specific user.

    Every memory is mathematically bound to a `User` via `user_id`. This
    architecture makes it physically impossible for the agent to accidentally
    leak Bob's memories into Alice's conversation.

    Attributes:
        id (uuid.UUID): Secure internal UUIDv4 primary key.
        user_id (uuid.UUID): Strict foreign key binding this fact to an owner.
        content (str): The textual extraction (e.g., "User loves techno music.").
        embedding (list[float]): The 768-dimensional vector representation (Gemini).
        created_at (datetime): Automatically generated creation timestamp.
        user (User): Back-reference to the User model.
    """

    __tablename__ = "agent_memories"

    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Define vector column mapping to the Gemini text-embedding-004 dimensions (768)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # --- Relationships ---
    # Back-populates explicitly links this model to the User.memories list.
    user: Mapped["User"] = relationship("User", back_populates="memories")

    def __repr__(self) -> str:
        """
        Provides a secure string representation.
        Truncates the content to prevent massive log dumps of user data.
        """
        truncated_content = (self.content[:30] + "...") if len(self.content) > 30 else self.content
        return f"<Memory(id='{self.id}', user_id='{self.user_id}', content='{truncated_content}')>"
