import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    default_rate_cents: Mapped[int] = mapped_column(nullable=False, default=3)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    drivers: Mapped[list["Driver"]] = relationship(back_populates="company")
    clients: Mapped[list["Client"]] = relationship(back_populates="company")
    deliveries: Mapped[list["Delivery"]] = relationship(back_populates="company")


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="drivers")
    deliveries: Mapped[list["Delivery"]] = relationship(back_populates="driver")

    __table_args__ = (
        UniqueConstraint("company_id", "external_id", name="uq_driver_company_external_id"),
    )


class Client(Base):
    """A partner the company delivers packages for (e.g. UniUni, GOFO)."""

    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_rate_cents: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="clients")
    deliveries: Mapped[list["Delivery"]] = relationship(back_populates="client")

    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_client_company_name"),
    )


class Delivery(Base):
    """A driver's delivery batch for one client on one day."""

    __tablename__ = "deliveries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), nullable=False)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    batch_date: Mapped[date] = mapped_column(Date, nullable=False)
    assigned_count: Mapped[int] = mapped_column(nullable=False)
    exceptions_count: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, native_enum=False), nullable=False, default=DeliveryStatus.PENDING
    )
    rate_cents: Mapped[int] = mapped_column(nullable=False)
    amount_due_cents: Mapped[int | None] = mapped_column(nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False), nullable=False, default=PaymentStatus.PENDING
    )
    paid_amount_cents: Mapped[int | None] = mapped_column(nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="deliveries")
    client: Mapped["Client"] = relationship(back_populates="deliveries")
    driver: Mapped["Driver"] = relationship(back_populates="deliveries")

    __table_args__ = (
        UniqueConstraint(
            "driver_id", "client_id", "batch_date", name="uq_delivery_driver_client_date"
        ),
    )

    @property
    def payable_count(self) -> int:
        return self.assigned_count - self.exceptions_count
