"""allow pending packages (carrier-imported, unresolved) + carrier status

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "packages", "outcome",
        existing_type=sa.Enum("DELIVERED", "RETURNED", name="packageoutcome", native_enum=False),
        nullable=True,
    )
    op.add_column("packages", sa.Column("carrier_status", sa.String(length=100), nullable=True))
    op.add_column("packages", sa.Column("carrier_status_updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("packages", "carrier_status_updated_at")
    op.drop_column("packages", "carrier_status")
    op.alter_column(
        "packages", "outcome",
        existing_type=sa.Enum("DELIVERED", "RETURNED", name="packageoutcome", native_enum=False),
        nullable=False,
    )
