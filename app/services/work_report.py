from fastapi import HTTPException

from app.models import WorkSession, WorkSessionStatus
from app.schemas import WorkReport, WorkReportCompensation, WorkReportRecord


def build_work_report(session: WorkSession) -> WorkReport:
    if session.status != WorkSessionStatus.CLOSED:
        raise HTTPException(
            status_code=409, detail="Work session must be closed before generating a report"
        )

    return WorkReport(
        report_number=f"WR-{session.id.hex[:8].upper()}",
        driver_name=session.driver.name,
        carrier_name=session.carrier.name,
        service_date=session.service_date,
        route_id=session.route_id,
        work_record=WorkReportRecord(
            route_started=session.start_time,
            route_completed=session.end_time,
            packages_assigned=session.packages_assigned,
            packages_completed=session.packages_completed,
            exceptions=session.exceptions_count,
            mileage=session.mileage,
        ),
        compensation=WorkReportCompensation(
            agreed_rate_cents=session.agreed_rate_cents,
            expected_gross_cents=session.expected_gross_cents,
            payment_due_date=session.payment_due_date,
            payment_status=session.payment_status,
            payment_received_cents=session.payment_received_cents,
            payment_received_at=session.payment_received_at,
            difference_cents=session.difference_cents,
        ),
        supporting_records=list(session.evidence),
    )
