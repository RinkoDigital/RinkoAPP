from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Driver, PaymentStatus, WorkSession, WorkSessionStatus
from app.schemas import LedgerEntry, LedgerSummary
from app.security import get_current_driver

router = APIRouter(prefix="/ledger", tags=["payment-ledger"])


@router.get("", response_model=LedgerSummary)
def get_ledger(db: Session = Depends(get_db), driver: Driver = Depends(get_current_driver)):
    sessions = (
        db.query(WorkSession)
        .filter(WorkSession.driver_id == driver.id, WorkSession.status == WorkSessionStatus.CLOSED)
        .order_by(WorkSession.service_date.desc())
        .all()
    )

    entries = [
        LedgerEntry(
            session_id=s.id,
            carrier_name=s.carrier.name,
            route_id=s.route_id,
            service_date=s.service_date,
            expected_gross_cents=s.expected_gross_cents,
            payment_received_cents=s.payment_received_cents,
            outstanding_cents=s.outstanding_cents,
            payment_due_date=s.payment_due_date,
            payment_status=s.payment_status,
        )
        for s in sessions
        if s.payment_status != PaymentStatus.RECEIVED
    ]

    return LedgerSummary(
        outstanding_total_cents=sum(e.outstanding_cents for e in entries),
        entries=entries,
    )
