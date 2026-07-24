import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, Delivery, DeliveryStatus, Driver, PaymentStatus
from app.report_docx import render_driver_pay_report_docx
from app.schemas import (
    ClientSummaryRow,
    DeliveryDetailRow,
    DriverPayReport,
    OverallSummary,
    PaidItem,
    PaymentReconciliation,
)
from app.security import get_current_company

router = APIRouter(prefix="/reports", tags=["reports"])


def _build_driver_pay_report(
    db: Session, company: Company, driver: Driver, period_start: date, period_end: date
) -> DriverPayReport:
    deliveries = (
        db.query(Delivery)
        .filter(
            Delivery.driver_id == driver.id,
            Delivery.company_id == company.id,
            Delivery.status == DeliveryStatus.VALIDATED,
            Delivery.batch_date >= period_start,
            Delivery.batch_date <= period_end,
        )
        .order_by(Delivery.batch_date)
        .all()
    )

    delivery_detail = [
        DeliveryDetailRow(
            week_number=((d.batch_date - period_start).days // 7) + 1,
            batch_date=d.batch_date,
            client_name=d.client.name,
            assigned_count=d.assigned_count,
            exceptions_count=d.exceptions_count,
            payable_count=d.payable_count,
            rate_cents=d.rate_cents,
            amount_due_cents=d.amount_due_cents,
            payment_status=d.payment_status,
        )
        for d in deliveries
    ]

    client_names = sorted({row.client_name for row in delivery_detail})
    client_summary = []
    for name in client_names:
        rows = [r for r in delivery_detail if r.client_name == name]
        assigned = sum(r.assigned_count for r in rows)
        exceptions = sum(r.exceptions_count for r in rows)
        payable = sum(r.payable_count for r in rows)
        compensation = sum(r.amount_due_cents for r in rows)
        client_summary.append(
            ClientSummaryRow(
                client_name=name,
                assigned_count=assigned,
                exceptions_count=exceptions,
                payable_count=payable,
                completion_rate=round((payable / assigned * 100), 2) if assigned else 0.0,
                compensation_cents=compensation,
            )
        )

    total_assigned = sum(r.assigned_count for r in delivery_detail)
    total_exceptions = sum(r.exceptions_count for r in delivery_detail)
    total_payable = sum(r.payable_count for r in delivery_detail)
    total_compensation = sum(r.amount_due_cents for r in delivery_detail)
    distinct_rates = {r.rate_cents for r in delivery_detail}

    overall_summary = OverallSummary(
        assigned_count=total_assigned,
        exceptions_count=total_exceptions,
        payable_count=total_payable,
        completion_rate=round((total_payable / total_assigned * 100), 2) if total_assigned else 0.0,
        rate_cents=distinct_rates.pop() if len(distinct_rates) == 1 else None,
        total_compensation_cents=total_compensation,
    )

    paid_deliveries = [d for d in deliveries if d.payment_status == PaymentStatus.PAID]
    already_paid_cents = sum(d.paid_amount_cents or 0 for d in paid_deliveries)
    payment_reconciliation = PaymentReconciliation(
        total_earned_cents=total_compensation,
        already_paid_cents=already_paid_cents,
        outstanding_balance_cents=total_compensation - already_paid_cents,
        paid_items=[
            PaidItem(
                batch_date=d.batch_date,
                client_name=d.client.name,
                payable_count=d.payable_count,
                rate_cents=d.rate_cents,
                amount_cents=d.paid_amount_cents or 0,
            )
            for d in paid_deliveries
        ],
    )

    return DriverPayReport(
        company_name=company.name,
        driver_id=driver.id,
        driver_name=driver.name,
        period_start=period_start,
        period_end=period_end,
        delivery_detail=delivery_detail,
        client_summary=client_summary,
        overall_summary=overall_summary,
        payment_reconciliation=payment_reconciliation,
    )


@router.get("/drivers/{driver_id}/pay-report", response_model=DriverPayReport)
def driver_pay_report(
    driver_id: uuid.UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
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
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")

    return _build_driver_pay_report(db, company, driver, start_date, end_date)


@router.get("/drivers/{driver_id}/pay-report.docx")
def driver_pay_report_docx(
    driver_id: uuid.UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
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
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")

    report = _build_driver_pay_report(db, company, driver, start_date, end_date)
    docx_bytes = render_driver_pay_report_docx(report)
    filename = f"{driver.name.replace(' ', '_')}_pay_report_{start_date}_{end_date}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
