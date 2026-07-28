"""rebuild schema around the independent driver work record model

Drops the company/admin-tenant model (companies, clients, deliveries) in
favor of a driver-owned schema: drivers sign up directly, log their own
carriers, and keep work sessions with evidence attachments. No production
data exists on this schema yet, so this is a clean rebuild rather than a
column-by-column migration.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("packages")
    op.drop_table("deliveries")
    op.drop_table("clients")
    op.drop_table("drivers")
    op.drop_table("companies")

    op.create_table(
        "drivers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "carriers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("default_rate_cents", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("driver_id", "name", name="uq_carrier_driver_name"),
    )

    op.create_table(
        "work_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column("carrier_id", sa.Uuid(), nullable=False),
        sa.Column("route_id", sa.String(length=255), nullable=True),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("packages_assigned", sa.Integer(), nullable=False),
        sa.Column("exceptions_count", sa.Integer(), nullable=False),
        sa.Column("mileage", sa.Float(), nullable=True),
        sa.Column("agreed_rate_cents", sa.Integer(), nullable=False),
        sa.Column("expected_gross_cents", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("OPEN", "CLOSED", name="worksessionstatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("payment_due_date", sa.Date(), nullable=True),
        sa.Column("payment_received_cents", sa.Integer(), nullable=True),
        sa.Column("payment_received_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
        sa.ForeignKeyConstraint(["carrier_id"], ["carriers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "driver_id", "carrier_id", "route_id", "service_date",
            name="uq_session_driver_carrier_route_date",
        ),
    )

    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "ROUTE_SCREENSHOT", "RATE_SCREENSHOT", "GPS_SESSION",
                "COMPLETION_RECORD", "SETTLEMENT_STATEMENT", "OTHER",
                name="evidencekind", native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["work_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "packages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("tracking_code", sa.String(length=255), nullable=False),
        sa.Column(
            "outcome",
            sa.Enum("DELIVERED", "RETURNED", name="packageoutcome", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.Enum(
                "MANUAL", "UNIUNI", "GOFO", "OTHER_PLATFORM",
                name="packagesource", native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("pod_photo_url", sa.String(length=500), nullable=True),
        sa.Column("pod_scan_code", sa.String(length=255), nullable=True),
        sa.Column("pod_captured_at", sa.DateTime(), nullable=True),
        sa.Column("pod_latitude", sa.Float(), nullable=True),
        sa.Column("pod_longitude", sa.Float(), nullable=True),
        sa.Column(
            "return_reason",
            sa.Enum(
                "REFUSED", "WRONG_ADDRESS", "DAMAGED", "UNDELIVERABLE", "OTHER",
                name="returnreason", native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("return_note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["work_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "tracking_code", name="uq_package_session_tracking_code"),
    )


def downgrade() -> None:
    op.drop_table("packages")
    op.drop_table("evidence")
    op.drop_table("work_sessions")
    op.drop_table("carriers")
    op.drop_table("drivers")
