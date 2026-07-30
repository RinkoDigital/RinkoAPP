import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.models import (
    EvidenceKind,
    PackageOutcome,
    PackageSource,
    PaymentStatus,
    PlanTier,
    ReturnReason,
    WorkSessionStatus,
)


# ---------- Auth / Driver ----------


class DriverSignup(BaseModel):
    name: str
    email: str
    password: str


class DriverLogin(BaseModel):
    email: str
    password: str


class DriverOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    plan: PlanTier
    created_at: datetime


class DriverToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    driver: DriverOut


class PlanUpdate(BaseModel):
    plan: PlanTier


class PlanInfo(BaseModel):
    plan: PlanTier
    docx_export: bool
    evidence_per_session_limit: int | None


# ---------- Carrier ----------


class CarrierCreate(BaseModel):
    name: str
    default_rate_cents: int | None = None


class CarrierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    default_rate_cents: int | None
    created_at: datetime


# ---------- Work session ----------


class WorkSessionCreate(BaseModel):
    carrier_id: uuid.UUID
    route_id: str | None = None
    service_date: date
    start_time: datetime | None = None
    packages_assigned: int = 0
    agreed_rate_cents: int | None = None
    payment_due_date: date | None = None


class WorkSessionClose(BaseModel):
    end_time: datetime | None = None
    packages_assigned: int | None = None
    exceptions_count: int = 0
    mileage: float | None = None
    payment_due_date: date | None = None


class WorkSessionRecordPayment(BaseModel):
    payment_received_cents: int
    payment_received_at: datetime | None = None


class WorkSessionOut(BaseModel):
    id: uuid.UUID
    carrier_id: uuid.UUID
    carrier_name: str
    route_id: str | None
    service_date: date
    start_time: datetime | None
    end_time: datetime | None
    packages_assigned: int
    exceptions_count: int
    packages_completed: int
    mileage: float | None
    agreed_rate_cents: int
    expected_gross_cents: int | None
    status: WorkSessionStatus
    payment_due_date: date | None
    payment_status: PaymentStatus
    payment_received_cents: int | None
    payment_received_at: datetime | None
    difference_cents: int | None
    outstanding_cents: int
    created_at: datetime
    closed_at: datetime | None


# ---------- Evidence ----------


class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    kind: EvidenceKind
    file_url: str
    note: str | None
    uploaded_at: datetime


# ---------- Package (optional granular detail) ----------


class PackageCreate(BaseModel):
    tracking_code: str
    outcome: PackageOutcome
    source: PackageSource = PackageSource.MANUAL
    external_reference: str | None = None
    pod_scan_code: str | None = None
    pod_latitude: float | None = None
    pod_longitude: float | None = None
    return_reason: ReturnReason | None = None
    return_note: str | None = None

    @model_validator(mode="after")
    def _validate_outcome_fields(self):
        if self.outcome == PackageOutcome.RETURNED and self.return_reason is None:
            raise ValueError("return_reason is required when outcome is 'returned'")
        if self.outcome == PackageOutcome.DELIVERED and (
            self.return_reason is not None or self.return_note is not None
        ):
            raise ValueError("return_reason/return_note are only valid when outcome is 'returned'")
        return self


class PackageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    tracking_code: str
    outcome: PackageOutcome
    source: PackageSource
    external_reference: str | None
    pod_photo_url: str | None
    pod_scan_code: str | None
    pod_captured_at: datetime | None
    pod_latitude: float | None
    pod_longitude: float | None
    return_reason: ReturnReason | None
    return_note: str | None
    created_at: datetime


# ---------- Work report ----------


class WorkReportRecord(BaseModel):
    route_started: datetime | None
    route_completed: datetime | None
    packages_assigned: int
    packages_completed: int
    exceptions: int
    mileage: float | None


class WorkReportCompensation(BaseModel):
    agreed_rate_cents: int
    expected_gross_cents: int | None
    payment_due_date: date | None
    payment_status: PaymentStatus
    payment_received_cents: int | None
    payment_received_at: datetime | None
    difference_cents: int | None


class WorkReport(BaseModel):
    report_number: str
    driver_name: str
    carrier_name: str
    service_date: date
    route_id: str | None
    work_record: WorkReportRecord
    compensation: WorkReportCompensation
    supporting_records: list[EvidenceOut]


# ---------- Payment ledger ----------


class LedgerEntry(BaseModel):
    session_id: uuid.UUID
    carrier_name: str
    route_id: str | None
    service_date: date
    expected_gross_cents: int
    payment_received_cents: int | None
    outstanding_cents: int
    payment_due_date: date | None
    payment_status: PaymentStatus


class LedgerSummary(BaseModel):
    outstanding_total_cents: int
    entries: list[LedgerEntry]
