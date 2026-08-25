"""Upgrade to Gemini 768 dimensions

Revision ID: 57cbf9972254
Revises: b82751a97948
Create Date: 2026-06-22 12:18:25.342350

"""

from typing import Sequence, Union

import pgvector.sqlalchemy
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "57cbf9972254"
down_revision: Union[str, Sequence[str], None] = "b82751a97948"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 2. Manually alter the column to 768 dimensions
    op.alter_column(
        "agent_memories",
        "embedding",
        type_=pgvector.sqlalchemy.Vector(768),
        existing_type=pgvector.sqlalchemy.Vector(384),
        schema="omni",
    )


def downgrade() -> None:
    # 3. Rollback safety: alter back to 384 dimensions if downgraded
    op.alter_column(
        "agent_memories",
        "embedding",
        type_=pgvector.sqlalchemy.Vector(384),
        existing_type=pgvector.sqlalchemy.Vector(768),
        schema="omni",
    )
