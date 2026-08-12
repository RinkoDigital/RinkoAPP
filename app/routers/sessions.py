import csv
import io
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Carrier,
    Driver,
    Evidence,
    EvidenceKind,
    WorkSession,
    WorkSessionStatus,
)
from app.plans import can_export_docx, evidence_limit
from app.report_docx import render_work_report_docx
from app.schemas import (
    EvidenceOut,
    PackageCreate,
    PackageOut,
    WorkReport,
    WorkSessionClose,
    WorkSessionCreate,
    WorkSessionOut,
    WorkSessionRecordPayment,
)
from app.security import get_current_driver
from app.services.packages import attach_pod_photo, create_package
from app.services.work_report import build_work_report
from app.storage import save_evidence_file

router = APIRouter(prefix="/sessions", tags=["work-sessions"])


def _to_out(session: WorkSession) -> WorkSessionOut:
    return WorkSessionOut(
        id=session.id,
        carrier_id=session.carrier_id,
        carrier_name=session.carrier.name,
        route_id=session.route_id,
        service_date=session.service_date,
        start_time=session.start_time,
        end_time=session.end_time,
        packages_assigned=session.packages_assigned,
        exceptions_count=session.exceptions_count,
        packages_completed=session.packages_completed,
        mileage=session.mileage,
        agreed_rate_cents=session.agreed_rate_cents,
        expected_gross_cents=session.expected_gross_cents,
        status=session.status,
        payment_due_date=session.payment_due_date,
        payment_status=session.payment_status,
        payment_received_cents=session.payment_received_cents,
        payment_received_at=session.payment_received_at,
        difference_cents=session.difference_cents,
        outstanding_cents=session.outstanding_cents,
        created_at=session.created_at,
        closed_at=session.closed_at,
    )


def _get_session(db: Session, driver: Driver, session_id: uuid.UUID) -> WorkSession:
    session = (
        db.query(WorkSession)
        .filter(WorkSession.id == session_id, WorkSession.driver_id == driver.id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Work session not found")
    return session


@router.post("", response_model=WorkSessionOut, status_code=201)
def start_session(
    payload: WorkSessionCreate,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    carrier = (
        db.query(Carrier)
        .filter(Carrier.id == payload.carrier_id, Carrier.driver_id == driver.id)
        .first()
    )
    if carrier is None:
        raise HTTPException(status_code=404, detail="Carrier not found")

    rate_cents = payload.agreed_rate_cents or carrier.default_rate_cents
    if rate_cents is None:
        raise HTTPException(
            status_code=422,
            detail="agreed_rate_cents is required (carrier has no default rate set)",
        )

    session = WorkSession(
        driver_id=driver.id,
        carrier_id=carrier.id,
        route_id=payload.route_id,
        service_date=payload.service_date,
        start_time=payload.start_time or datetime.utcnow(),
        packages_assigned=payload.packages_assigned,
        agreed_rate_cents=rate_cents,
        payment_due_date=payload.payment_due_date,
        status=WorkSessionStatus.OPEN,
    )
    db.add(session)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A work session already exists for this carrier/route/date",
        )
    db.refresh(session)
    return _to_out(session)


@router.get("", response_model=list[WorkSessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
    status: WorkSessionStatus | None = Query(default=None),
    carrier_id: uuid.UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
):
    q = db.query(WorkSession).filter(WorkSession.driver_id == driver.id)
    if status is not None:
        q = q.filter(WorkSession.status == status)
    if carrier_id is not None:
        q = q.filter(WorkSession.carrier_id == carrier_id)
    if start_date is not None:
        q = q.filter(WorkSession.service_date >= start_date)
    if end_date is not None:
        q = q.filter(WorkSession.service_date <= end_date)
    sessions = q.order_by(WorkSession.service_date.desc()).all()
    return [_to_out(s) for s in sessions]


@router.get("/export.csv")
def export_sessions_csv(
    db: Session = Depends(get_db), driver: Driver = Depends(get_current_driver)
):
    """Full export of the driver's own work sessions — no lock-in."""
    sessions = (
        db.query(WorkSession)
        .filter(WorkSession.driver_id == driver.id)
        .order_by(WorkSession.service_date)
        .all()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "service_date", "carrier", "route_id", "status", "start_time", "end_time",
            "packages_assigned", "exceptions", "packages_completed", "mileage",
            "agreed_rate_cents", "expected_gross_cents", "payment_status",
            "payment_received_cents", "payment_due_date", "difference_cents",
        ]
    )
    for s in sessions:
        writer.writerow(
            [
                s.service_date, s.carrier.name, s.route_id or "", s.status.value,
                s.start_time.isoformat() if s.start_time else "",
                s.end_time.isoformat() if s.end_time else "",
                s.packages_assigned, s.exceptions_count, s.packages_completed, s.mileage or "",
                s.agreed_rate_cents, s.expected_gross_cents or "", s.payment_status.value,
                s.payment_received_cents or "", s.payment_due_date or "",
                s.difference_cents if s.difference_cents is not None else "",
            ]
        )

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="rinko_work_sessions.csv"'},
    )


@router.get("/{session_id}", response_model=WorkSessionOut)
def get_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    return _to_out(_get_session(db, driver, session_id))


@router.post("/{session_id}/close", response_model=WorkSessionOut)
def close_session(
    session_id: uuid.UUID,
    payload: WorkSessionClose,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    session = _get_session(db, driver, session_id)
    if session.status != WorkSessionStatus.OPEN:
        raise HTTPException(status_code=409, detail="Work session is already closed")

    if payload.packages_assigned is not None:
        session.packages_assigned = payload.packages_assigned
    session.exceptions_count = payload.exceptions_count
    session.mileage = payload.mileage
    if payload.payment_due_date is not None:
        session.payment_due_date = payload.payment_due_date
    session.end_time = payload.end_time or datetime.utcnow()
    session.expected_gross_cents = session.packages_completed * session.agreed_rate_cents
    session.status = WorkSessionStatus.CLOSED
    session.closed_at = datetime.utcnow()

    db.commit()
    db.refresh(session)
    return _to_out(session)


@router.post("/{session_id}/record-payment", response_model=WorkSessionOut)
def record_payment(
    session_id: uuid.UUID,
    payload: WorkSessionRecordPayment,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    session = _get_session(db, driver, session_id)
    if session.status != WorkSessionStatus.CLOSED:
        raise HTTPException(
            status_code=409, detail="Work session must be closed before recording payment"
        )

    session.payment_received_cents = payload.payment_received_cents
    session.payment_received_at = payload.payment_received_at or datetime.utcnow()
    db.commit()
    db.refresh(session)
    return _to_out(session)


@router.post("/{session_id}/evidence", response_model=EvidenceOut, status_code=201)
def upload_evidence(
    session_id: uuid.UUID,
    kind: EvidenceKind = Form(...),
    note: str | None = Form(default=None),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    address: str | None = Form(default=None),
    captured_at: datetime | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    session = _get_session(db, driver, session_id)

    limit = evidence_limit(driver.plan)
    if limit is not None and len(session.evidence) >= limit:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Free plan is limited to {limit} evidence files per session. "
                "Upgrade to Rinko Pro for unlimited evidence storage."
            ),
        )

    evidence = Evidence(
        session_id=session.id,
        kind=kind,
        note=note,
        file_url="",
        latitude=latitude,
        longitude=longitude,
        address=address,
        captured_at=captured_at,
    )
    db.add(evidence)
    db.flush()
    evidence.file_url = save_evidence_file(str(evidence.id), file)
    db.commit()
    db.refresh(evidence)
    return evidence


@router.get("/{session_id}/evidence", response_model=list[EvidenceOut])
def list_evidence(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    session = _get_session(db, driver, session_id)
    return session.evidence


@router.post("/{session_id}/packages", response_model=PackageOut, status_code=201)
def register_package(
    session_id: uuid.UUID,
    payload: PackageCreate,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    session = _get_session(db, driver, session_id)
    return create_package(db, session, payload)


@router.get("/{session_id}/packages", response_model=list[PackageOut])
def list_packages(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    session = _get_session(db, driver, session_id)
    return session.packages


@router.post("/{session_id}/packages/{package_id}/pod-photo", response_model=PackageOut)
def upload_pod_photo(
    session_id: uuid.UUID,
    package_id: uuid.UUID,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
    file: UploadFile = File(...),
):
    session = _get_session(db, driver, session_id)
    package = next((p for p in session.packages if p.id == package_id), None)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return attach_pod_photo(db, package, file)


@router.get("/{session_id}/work-report", response_model=WorkReport)
def get_work_report(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    session = _get_session(db, driver, session_id)
    return build_work_report(session)


@router.get("/{session_id}/work-report.docx")
def get_work_report_docx(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    if not can_export_docx(driver.plan):
        raise HTTPException(
            status_code=402,
            detail="Formatted .docx export is a Rinko Pro feature. The JSON report stays free — see /sessions/{id}/work-report.",
        )

    session = _get_session(db, driver, session_id)
    report = build_work_report(session)
    docx_bytes = render_work_report_docx(report)
    filename = f"work_report_{report.report_number}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
