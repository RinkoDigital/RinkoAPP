import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.calculation import compute_amount_due_cents, rate_for_client
from app.database import get_db
from app.models import Client, Company, Delivery, DeliveryStatus, Driver, PaymentStatus
from app.schemas import DeliveryCreate, DeliveryMarkPaid, DeliveryOut, DeliveryReject
from app.security import get_current_company

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


def _get_driver(db: Session, company: Company, driver_id: uuid.UUID) -> Driver:
    driver = (
        db.query(Driver)
        .filter(Driver.id == driver_id, Driver.company_id == company.id)
        .first()
    )
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


def _get_client(db: Session, company: Company, client_id: uuid.UUID) -> Client:
    client = (
        db.query(Client)
        .filter(Client.id == client_id, Client.company_id == company.id)
        .first()
    )
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("", response_model=DeliveryOut, status_code=201)
def register_delivery(
    payload: DeliveryCreate,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    driver = _get_driver(db, company, payload.driver_id)
    client = _get_client(db, company, payload.client_id)

    if payload.exceptions_count > payload.assigned_count:
        raise HTTPException(
            status_code=422, detail="exceptions_count cannot exceed assigned_count"
        )

    delivery = Delivery(
        company_id=company.id,
        driver_id=driver.id,
        client_id=client.id,
        batch_date=payload.batch_date,
        assigned_count=payload.assigned_count,
        exceptions_count=payload.exceptions_count,
        rate_cents=rate_for_client(company, client),
        status=DeliveryStatus.PENDING,
    )
    db.add(delivery)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Delivery batch already registered for this driver/client/date"
        )
    db.refresh(delivery)
    return delivery


@router.get("", response_model=list[DeliveryOut])
def list_deliveries(
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
    driver_id: uuid.UUID | None = Query(default=None),
    client_id: uuid.UUID | None = Query(default=None),
    status: DeliveryStatus | None = Query(default=None),
    payment_status: PaymentStatus | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
):
    q = db.query(Delivery).filter(Delivery.company_id == company.id)
    if driver_id is not None:
        q = q.filter(Delivery.driver_id == driver_id)
    if client_id is not None:
        q = q.filter(Delivery.client_id == client_id)
    if status is not None:
        q = q.filter(Delivery.status == status)
    if payment_status is not None:
        q = q.filter(Delivery.payment_status == payment_status)
    if start_date is not None:
        q = q.filter(Delivery.batch_date >= start_date)
    if end_date is not None:
        q = q.filter(Delivery.batch_date <= end_date)
    return q.order_by(Delivery.batch_date.desc()).all()


def _get_delivery(db: Session, company: Company, delivery_id: uuid.UUID) -> Delivery:
    delivery = (
        db.query(Delivery)
        .filter(Delivery.id == delivery_id, Delivery.company_id == company.id)
        .first()
    )
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery


def _get_pending_delivery(db: Session, company: Company, delivery_id: uuid.UUID) -> Delivery:
    delivery = _get_delivery(db, company, delivery_id)
    if delivery.status != DeliveryStatus.PENDING:
        raise HTTPException(
            status_code=409, detail=f"Delivery already {delivery.status.value}"
        )
    return delivery


@router.post("/{delivery_id}/validate", response_model=DeliveryOut)
def validate_delivery(
    delivery_id: uuid.UUID,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    delivery = _get_pending_delivery(db, company, delivery_id)
    delivery.amount_due_cents = compute_amount_due_cents(delivery)
    delivery.status = DeliveryStatus.VALIDATED
    delivery.validated_at = datetime.utcnow()
    db.commit()
    db.refresh(delivery)
    return delivery


@router.post("/{delivery_id}/reject", response_model=DeliveryOut)
def reject_delivery(
    delivery_id: uuid.UUID,
    payload: DeliveryReject,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    delivery = _get_pending_delivery(db, company, delivery_id)
    delivery.status = DeliveryStatus.REJECTED
    delivery.rejection_reason = payload.reason
    db.commit()
    db.refresh(delivery)
    return delivery


@router.post("/{delivery_id}/mark-paid", response_model=DeliveryOut)
def mark_delivery_paid(
    delivery_id: uuid.UUID,
    payload: DeliveryMarkPaid,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    delivery = _get_delivery(db, company, delivery_id)
    if delivery.status != DeliveryStatus.VALIDATED:
        raise HTTPException(status_code=409, detail="Only validated deliveries can be marked paid")
    if delivery.payment_status == PaymentStatus.PAID:
        raise HTTPException(status_code=409, detail="Delivery already marked paid")

    delivery.payment_status = PaymentStatus.PAID
    delivery.paid_amount_cents = (
        payload.paid_amount_cents
        if payload.paid_amount_cents is not None
        else delivery.amount_due_cents
    )
    delivery.paid_at = datetime.utcnow()
    db.commit()
    db.refresh(delivery)
    return delivery
