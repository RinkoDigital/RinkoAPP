"""add Google/Apple social login (nullable password, oauth identity)

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("drivers", "password_hash", existing_type=sa.String(length=255), nullable=True)
    op.add_column("drivers", sa.Column("oauth_provider", sa.String(length=20), nullable=True))
    op.add_column("drivers", sa.Column("oauth_subject", sa.String(length=255), nullable=True))
    op.create_unique_constraint(
        "uq_driver_oauth_identity", "drivers", ["oauth_provider", "oauth_subject"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_driver_oauth_identity", "drivers", type_="unique")
    op.drop_column("drivers", "oauth_subject")
    op.drop_column("drivers", "oauth_provider")
    op.alter_column("drivers", "password_hash", existing_type=sa.String(length=255), nullable=False)
