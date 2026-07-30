"""add driver plan tier (free/pro) — manual flag, no billing integration yet

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "drivers",
        sa.Column(
            "plan",
            sa.Enum("FREE", "PRO", name="plantier", native_enum=False),
            nullable=False,
            server_default="FREE",
        ),
    )
    op.alter_column("drivers", "plan", server_default=None)


def downgrade() -> None:
    op.drop_column("drivers", "plan")
