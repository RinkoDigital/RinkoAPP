"""add push tokens and reminder-sent tracking on work sessions

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "push_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )

    op.add_column("work_sessions", sa.Column("payment_reminder_sent_at", sa.DateTime(), nullable=True))
    op.add_column(
        "work_sessions", sa.Column("stale_session_reminder_sent_at", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("work_sessions", "stale_session_reminder_sent_at")
    op.drop_column("work_sessions", "payment_reminder_sent_at")
    op.drop_table("push_tokens")
