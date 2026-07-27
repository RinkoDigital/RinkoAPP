"""add company webhook secret for inbound platform webhooks

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "companies", sa.Column("webhook_secret_hash", sa.String(length=64), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("companies", "webhook_secret_hash")
