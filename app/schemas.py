import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import DeliveryStatus


class CompanyCreate(BaseModel):
    name: str
    default_rate_cents: int = 3


class CompanyCreated(BaseModel):
    id: uuid.UUID
    name: str
    api_key: str
    default_rate_cents: int


class DriverCreate(BaseModel):
    name: str
    email: str | None = None
    external_id: str | None = None


class DriverOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str | None
    external_id: str | None
    created_at: datetime


class DeliveryCreate(BaseModel):
    driver_id: uuid.UUID
    external_id: str
    package_count: int = 1


class DeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    driver_id: uuid.UUID
    external_id: str
    package_count: int
    status: DeliveryStatus
    rate_cents: int
    amount_due_cents: int | None
    rejection_reason: str | None
    validated_at: datetime | None
    created_at: datetime


class DeliveryReject(BaseModel):
    reason: str


class DriverEarningsReport(BaseModel):
    driver_id: uuid.UUID
    driver_name: str
    validated_deliveries: int
    total_packages: int
    amount_due_cents: int


class CompanySummaryReport(BaseModel):
    total_deliveries: int
    pending: int
    validated: int
    rejected: int
    total_amount_due_cents: int
