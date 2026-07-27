"""add packages table for proof of delivery and returns

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "packages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("delivery_id", sa.Uuid(), nullable=False),
        sa.Column("tracking_code", sa.String(length=255), nullable=False),
        sa.Column(
            "outcome",
            sa.Enum("DELIVERED", "RETURNED", name="packageoutcome", native_enum=False),
            nullable=False,
        ),
        sa.Column("pod_photo_url", sa.String(length=500), nullable=True),
        sa.Column("pod_scan_code", sa.String(length=255), nullable=True),
        sa.Column("pod_captured_at", sa.DateTime(), nullable=True),
        sa.Column("pod_latitude", sa.Float(), nullable=True),
        sa.Column("pod_longitude", sa.Float(), nullable=True),
        sa.Column(
            "return_reason",
            sa.Enum(
                "REFUSED",
                "WRONG_ADDRESS",
                "DAMAGED",
                "UNDELIVERABLE",
                "OTHER",
                name="returnreason",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("return_note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["delivery_id"], ["deliveries.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "delivery_id", "tracking_code", name="uq_package_delivery_tracking_code"
        ),
    )


def downgrade() -> None:
    op.drop_table("packages")
