import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, Enum, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class WorkSessionStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    RECEIVED = "received"


class PackageOutcome(str, enum.Enum):
    DELIVERED = "delivered"
    RETURNED = "returned"


class ReturnReason(str, enum.Enum):
    REFUSED = "refused"
    WRONG_ADDRESS = "wrong_address"
    DAMAGED = "damaged"
    UNDELIVERABLE = "undeliverable"
    OTHER = "other"


class PackageSource(str, enum.Enum):
    """Where a package's delivery/return record came from."""

    MANUAL = "manual"
    UNIUNI = "uniuni"
    GOFO = "gofo"
    OTHER_PLATFORM = "other_platform"


class EvidenceKind(str, enum.Enum):
    ROUTE_SCREENSHOT = "route_screenshot"
    RATE_SCREENSHOT = "rate_screenshot"
    GPS_SESSION = "gps_session"
    COMPLETION_RECORD = "completion_record"
    SETTLEMENT_STATEMENT = "settlement_statement"
    OTHER = "other"


class PlanTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"


class AuthTokenPurpose(str, enum.Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


class Driver(Base):
    """An independent driver — the root account. Not owned by any company."""

    __tablename__ = "drivers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(nullable=False, default=False)
    plan: Mapped[PlanTier] = mapped_column(
        Enum(PlanTier, native_enum=False), nullable=False, default=PlanTier.FREE
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    carriers: Mapped[list["Carrier"]] = relationship(back_populates="driver")
    sessions: Mapped[list["WorkSession"]] = relationship(back_populates="driver")


class AuthToken(Base):
    """Single-use token backing email verification and password reset.

    The raw token is only ever handed to app.services.email.send_email — a
    placeholder that logs instead of delivering mail, since no real
    provider is wired up yet. Only its salted hash is stored here.
    """

    __tablename__ = "auth_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    purpose: Mapped[AuthTokenPurpose] = mapped_column(
        Enum(AuthTokenPurpose, native_enum=False), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    driver: Mapped["Driver"] = relationship()


class PushToken(Base):
    """An Expo push token for one of the driver's devices.

    A driver can have more than one device registered (phone + tablet,
    reinstall, etc.) — the token itself is the unique key, re-registering
    the same token from a different login just moves it to that driver.
    """

    __tablename__ = "push_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    driver: Mapped["Driver"] = relationship()


class Carrier(Base):
    """A contracting company the driver works routes for (e.g. UniUni, GOFO, OnTrac).

    Owned by the driver who logged it — not a shared/global directory. Two
    drivers each logging "UniUni" get two independent Carrier rows; there is
    no central authority reconciling them, by design.
    """

    __tablename__ = "carriers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_rate_cents: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    driver: Mapped["Driver"] = relationship(back_populates="carriers")
    sessions: Mapped[list["WorkSession"]] = relationship(back_populates="carrier")

    __table_args__ = (
        UniqueConstraint("driver_id", "name", name="uq_carrier_driver_name"),
    )


class WorkSession(Base):
    """One route/shift worked for one carrier — the independent work record."""

    __tablename__ = "work_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    carrier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("carriers.id"), nullable=False)
    route_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[datetime | None] = mapped_column(nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(nullable=True)

    packages_assigned: Mapped[int] = mapped_column(nullable=False, default=0)
    exceptions_count: Mapped[int] = mapped_column(nullable=False, default=0)
    mileage: Mapped[float | None] = mapped_column(Float, nullable=True)

    agreed_rate_cents: Mapped[int] = mapped_column(nullable=False)
    expected_gross_cents: Mapped[int | None] = mapped_column(nullable=True)

    status: Mapped[WorkSessionStatus] = mapped_column(
        Enum(WorkSessionStatus, native_enum=False), nullable=False, default=WorkSessionStatus.OPEN
    )

    payment_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_received_cents: Mapped[int | None] = mapped_column(nullable=True)
    payment_received_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Each reminder fires at most once — set the first time it's sent, never
    # cleared, so the job that sends them is idempotent on repeated runs.
    payment_reminder_sent_at: Mapped[datetime | None] = mapped_column(nullable=True)
    stale_session_reminder_sent_at: Mapped[datetime | None] = mapped_column(nullable=True)

    driver: Mapped["Driver"] = relationship(back_populates="sessions")
    carrier: Mapped["Carrier"] = relationship(back_populates="sessions")
    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="session", order_by="Evidence.uploaded_at"
    )
    packages: Mapped[list["Package"]] = relationship(
        back_populates="session", order_by="Package.created_at"
    )

    __table_args__ = (
        UniqueConstraint(
            "driver_id", "carrier_id", "route_id", "service_date",
            name="uq_session_driver_carrier_route_date",
        ),
    )

    @property
    def packages_completed(self) -> int:
        return self.packages_assigned - self.exceptions_count

    @property
    def difference_cents(self) -> int | None:
        if self.payment_received_cents is None or self.expected_gross_cents is None:
            return None
        return self.payment_received_cents - self.expected_gross_cents

    @property
    def payment_status(self) -> PaymentStatus:
        if self.payment_received_cents is None:
            return PaymentStatus.PENDING
        if self.expected_gross_cents is not None and self.payment_received_cents >= self.expected_gross_cents:
            return PaymentStatus.RECEIVED
        return PaymentStatus.PARTIAL

    @property
    def outstanding_cents(self) -> int:
        """How much is still owed on this session (0 if closed and fully paid or still open)."""
        if self.expected_gross_cents is None:
            return 0
        received = self.payment_received_cents or 0
        return max(self.expected_gross_cents - received, 0)


class Evidence(Base):
    """A supporting document attached to a work session — route screenshot,
    rate screenshot, GPS export, settlement statement, etc."""

    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_sessions.id"), nullable=False)
    kind: Mapped[EvidenceKind] = mapped_column(Enum(EvidenceKind, native_enum=False), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now())

    session: Mapped["WorkSession"] = relationship(back_populates="evidence")


class Package(Base):
    """Optional per-package detail within a work session — proof of delivery
    or return detail, for drivers who want finer-grained evidence than the
    session-level assigned/exceptions counts."""

    __tablename__ = "packages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_sessions.id"), nullable=False)
    tracking_code: Mapped[str] = mapped_column(String(255), nullable=False)
    outcome: Mapped[PackageOutcome] = mapped_column(
        Enum(PackageOutcome, native_enum=False), nullable=False
    )
    source: Mapped[PackageSource] = mapped_column(
        Enum(PackageSource, native_enum=False), nullable=False, default=PackageSource.MANUAL
    )
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    pod_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pod_scan_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pod_captured_at: Mapped[datetime | None] = mapped_column(nullable=True)
    pod_latitude: Mapped[float | None] = mapped_column(nullable=True)
    pod_longitude: Mapped[float | None] = mapped_column(nullable=True)

    return_reason: Mapped[ReturnReason | None] = mapped_column(
        Enum(ReturnReason, native_enum=False), nullable=True
    )
    return_note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    session: Mapped["WorkSession"] = relationship(back_populates="packages")

    __table_args__ = (
        UniqueConstraint("session_id", "tracking_code", name="uq_package_session_tracking_code"),
    )
