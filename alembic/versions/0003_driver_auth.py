"""add driver auth fields (password, invite token) and unique email

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("drivers", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.add_column("drivers", sa.Column("invite_token", sa.String(length=64), nullable=True))
    op.add_column("drivers", sa.Column("invite_expires_at", sa.DateTime(), nullable=True))
    op.create_unique_constraint("uq_driver_email", "drivers", ["email"])
    op.create_unique_constraint("uq_driver_invite_token", "drivers", ["invite_token"])


def downgrade() -> None:
    op.drop_constraint("uq_driver_invite_token", "drivers", type_="unique")
    op.drop_constraint("uq_driver_email", "drivers", type_="unique")
    op.drop_column("drivers", "invite_expires_at")
    op.drop_column("drivers", "invite_token")
    op.drop_column("drivers", "password_hash")
