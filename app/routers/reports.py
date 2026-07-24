import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, Delivery, DeliveryStatus, Driver
from app.schemas import CompanySummaryReport, DriverEarningsReport
from app.security import get_current_company

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/drivers/{driver_id}", response_model=DriverEarningsReport)
def driver_earnings_report(
    driver_id: uuid.UUID,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    driver = (
        db.query(Driver)
        .filter(Driver.id == driver_id, Driver.company_id == company.id)
        .first()
    )
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")

    row = (
        db.query(
            func.count(Delivery.id),
            func.coalesce(func.sum(Delivery.package_count), 0),
            func.coalesce(func.sum(Delivery.amount_due_cents), 0),
        )
        .filter(
            Delivery.driver_id == driver.id,
            Delivery.status == DeliveryStatus.VALIDATED,
        )
        .one()
    )
    validated_deliveries, total_packages, total_amount_due_cents = row

    return DriverEarningsReport(
        driver_id=driver.id,
        driver_name=driver.name,
        validated_deliveries=validated_deliveries,
        total_packages=total_packages,
        amount_due_cents=total_amount_due_cents,
    )


@router.get("/summary", response_model=CompanySummaryReport)
def company_summary_report(
    db: Session = Depends(get_db), company: Company = Depends(get_current_company)
):
    rows = (
        db.query(Delivery.status, func.count(Delivery.id))
        .filter(Delivery.company_id == company.id)
        .group_by(Delivery.status)
        .all()
    )
    counts = {status: count for status, count in rows}

    total_amount_due_cents = (
        db.query(func.coalesce(func.sum(Delivery.amount_due_cents), 0))
        .filter(
            Delivery.company_id == company.id,
            Delivery.status == DeliveryStatus.VALIDATED,
        )
        .scalar()
    )

    return CompanySummaryReport(
        total_deliveries=sum(counts.values()),
        pending=counts.get(DeliveryStatus.PENDING, 0),
        validated=counts.get(DeliveryStatus.VALIDATED, 0),
        rejected=counts.get(DeliveryStatus.REJECTED, 0),
        total_amount_due_cents=total_amount_due_cents,
    )
