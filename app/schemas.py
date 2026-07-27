import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.models import DeliveryStatus, PackageOutcome, PackageSource, PaymentStatus, ReturnReason


class CompanyCreate(BaseModel):
    name: str
    default_rate_cents: int = 3


class CompanyCreated(BaseModel):
    id: uuid.UUID
    name: str
    api_key: str
    webhook_secret: str
    default_rate_cents: int


class WebhookSecretRotated(BaseModel):
    webhook_secret: str


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
    has_account: bool
    invite_token: str | None
    created_at: datetime


class DriverAcceptInvite(BaseModel):
    invite_token: str
    password: str


class DriverLogin(BaseModel):
    email: str
    password: str


class DriverMeOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str | None
    company_name: str


class DriverToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    driver: DriverMeOut


class ClientCreate(BaseModel):
    name: str
    default_rate_cents: int | None = None


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    default_rate_cents: int | None
    created_at: datetime


class DeliveryCreate(BaseModel):
    driver_id: uuid.UUID
    client_id: uuid.UUID
    batch_date: date
    assigned_count: int
    exceptions_count: int = 0


class DeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    driver_id: uuid.UUID
    client_id: uuid.UUID
    batch_date: date
    assigned_count: int
    exceptions_count: int
    payable_count: int
    status: DeliveryStatus
    rate_cents: int
    amount_due_cents: int | None
    rejection_reason: str | None
    payment_status: PaymentStatus
    paid_amount_cents: int | None
    paid_at: datetime | None
    validated_at: datetime | None
    created_at: datetime


class DeliveryReject(BaseModel):
    reason: str


class DeliveryMarkPaid(BaseModel):
    paid_amount_cents: int | None = None


class DeliveryDetailRow(BaseModel):
    week_number: int
    batch_date: date
    client_name: str
    assigned_count: int
    exceptions_count: int
    payable_count: int
    rate_cents: int
    amount_due_cents: int
    payment_status: PaymentStatus


class ClientSummaryRow(BaseModel):
    client_name: str
    assigned_count: int
    exceptions_count: int
    payable_count: int
    completion_rate: float
    compensation_cents: int


class OverallSummary(BaseModel):
    assigned_count: int
    exceptions_count: int
    payable_count: int
    completion_rate: float
    rate_cents: int | None
    total_compensation_cents: int


class PaidItem(BaseModel):
    batch_date: date
    client_name: str
    payable_count: int
    rate_cents: int
    amount_cents: int


class PaymentReconciliation(BaseModel):
    total_earned_cents: int
    already_paid_cents: int
    outstanding_balance_cents: int
    paid_items: list[PaidItem]


class DriverPayReport(BaseModel):
    company_name: str
    driver_id: uuid.UUID
    driver_name: str
    period_start: date
    period_end: date
    delivery_detail: list[DeliveryDetailRow]
    client_summary: list[ClientSummaryRow]
    overall_summary: OverallSummary
    payment_reconciliation: PaymentReconciliation


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
    delivery_id: uuid.UUID
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


class WebhookEventPayload(BaseModel):
    """Generic shape expected from an external platform (UniUni/GOFO) webhook.

    Speculative — no real integration exists yet, so this is our own
    schema, not theirs. A translation layer can sit in front of this if
    their actual payload format differs once integration is confirmed.
    """

    driver_external_id: str
    client_name: str
    batch_date: date
    tracking_code: str
    outcome: PackageOutcome
    pod_photo_url: str | None = None
    pod_scan_code: str | None = None
    pod_latitude: float | None = None
    pod_longitude: float | None = None
    return_reason: ReturnReason | None = None
    return_note: str | None = None
    external_reference: str | None = None

    @model_validator(mode="after")
    def _validate_outcome_fields(self):
        if self.outcome == PackageOutcome.RETURNED and self.return_reason is None:
            raise ValueError("return_reason is required when outcome is 'returned'")
        if self.outcome == PackageOutcome.DELIVERED and (
            self.return_reason is not None or self.return_note is not None
        ):
            raise ValueError("return_reason/return_note are only valid when outcome is 'returned'")
        return self


class WebhookEventResult(BaseModel):
    status: str
    delivery_id: uuid.UUID
    package_id: uuid.UUID


class DeliveryProof(BaseModel):
    """Proof that a delivery batch happened — independent of whether the
    driver has been paid yet. Meant to be shown to the contracting
    platform (UniUni/GOFO) as evidence, not just to the driver."""

    proof_number: str
    company_name: str
    driver_name: str
    client_name: str
    batch_date: date
    assigned_count: int
    exceptions_count: int
    payable_count: int
    rate_cents: int
    amount_due_cents: int
    validated_at: datetime
    payment_status: PaymentStatus
    paid_amount_cents: int | None
    paid_at: datetime | None
    packages_logged: int
    packages_with_photo: int
    packages_with_scan_code: int
