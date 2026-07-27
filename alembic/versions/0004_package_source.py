"""add package source/external_reference for future platform integrations

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "packages",
        sa.Column(
            "source",
            sa.Enum(
                "MANUAL", "UNIUNI", "GOFO", "OTHER_PLATFORM",
                name="packagesource", native_enum=False,
            ),
            nullable=False,
            server_default="MANUAL",
        ),
    )
    op.add_column("packages", sa.Column("external_reference", sa.String(length=255), nullable=True))
    op.alter_column("packages", "source", server_default=None)


def downgrade() -> None:
    op.drop_column("packages", "external_reference")
    op.drop_column("packages", "source")
