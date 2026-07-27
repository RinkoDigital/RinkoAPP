import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.calculation import rate_for_client
from app.database import get_db
from app.models import (
    Client,
    Company,
    Delivery,
    DeliveryStatus,
    Driver,
    Package,
    PackageOutcome,
    PackageSource,
)
from app.schemas import WebhookEventPayload, WebhookEventResult
from app.security import verify_webhook_secret

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

PLATFORM_SOURCES = {
    "uniuni": PackageSource.UNIUNI,
    "gofo": PackageSource.GOFO,
    "other": PackageSource.OTHER_PLATFORM,
}


@router.post("/{company_id}/{platform}", response_model=WebhookEventResult)
def receive_platform_event(
    company_id: uuid.UUID,
    platform: str,
    payload: WebhookEventPayload,
    db: Session = Depends(get_db),
    x_webhook_secret: str = Header(...),
):
    source = PLATFORM_SOURCES.get(platform.lower())
    if source is None:
        raise HTTPException(status_code=404, detail="Unknown platform")

    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None or not verify_webhook_secret(company, x_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook credentials")

    driver = (
        db.query(Driver)
        .filter(
            Driver.company_id == company.id,
            Driver.external_id == payload.driver_external_id,
        )
        .first()
    )
    if driver is None:
        raise HTTPException(status_code=404, detail="No driver matches driver_external_id")

    client = (
        db.query(Client)
        .filter(
            Client.company_id == company.id,
            func.lower(Client.name) == payload.client_name.lower(),
        )
        .first()
    )
    if client is None:
        raise HTTPException(status_code=404, detail="No client matches client_name")

    delivery = (
        db.query(Delivery)
        .filter(
            Delivery.driver_id == driver.id,
            Delivery.client_id == client.id,
            Delivery.batch_date == payload.batch_date,
        )
        .first()
    )
    if delivery is None:
        delivery = Delivery(
            company_id=company.id,
            driver_id=driver.id,
            client_id=client.id,
            batch_date=payload.batch_date,
            assigned_count=0,
            exceptions_count=0,
            rate_cents=rate_for_client(company, client),
            status=DeliveryStatus.PENDING,
        )
        db.add(delivery)
        db.flush()
    elif delivery.status != DeliveryStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Delivery batch already {delivery.status.value}; cannot append webhook events",
        )

    existing_package = (
        db.query(Package)
        .filter(Package.delivery_id == delivery.id, Package.tracking_code == payload.tracking_code)
        .first()
    )
    if existing_package is not None:
        return WebhookEventResult(
            status="duplicate_ignored", delivery_id=delivery.id, package_id=existing_package.id
        )

    package = Package(
        delivery_id=delivery.id,
        tracking_code=payload.tracking_code,
        outcome=payload.outcome,
        source=source,
        external_reference=payload.external_reference,
        pod_photo_url=payload.pod_photo_url,
        pod_scan_code=payload.pod_scan_code,
        pod_latitude=payload.pod_latitude,
        pod_longitude=payload.pod_longitude,
        pod_captured_at=datetime.utcnow() if payload.outcome == PackageOutcome.DELIVERED else None,
        return_reason=payload.return_reason,
        return_note=payload.return_note,
    )
    db.add(package)

    delivery.assigned_count += 1
    if payload.outcome == PackageOutcome.RETURNED:
        delivery.exceptions_count += 1

    db.commit()
    db.refresh(package)
    return WebhookEventResult(status="created", delivery_id=delivery.id, package_id=package.id)
