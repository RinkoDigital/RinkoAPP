"""add optional GPS location fields to evidence

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evidence", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("evidence", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("evidence", sa.Column("captured_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("evidence", "captured_at")
    op.drop_column("evidence", "longitude")
    op.drop_column("evidence", "latitude")
