from datetime import datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Package, PackageOutcome, PackageSource, WorkSession
from app.schemas import PackageCreate
from app.storage import save_pod_photo


def create_package(db: Session, session: WorkSession, payload: PackageCreate) -> Package:
    package = Package(
        session_id=session.id,
        tracking_code=payload.tracking_code,
        outcome=payload.outcome,
        source=payload.source,
        external_reference=payload.external_reference if payload.source != PackageSource.MANUAL else None,
        pod_scan_code=payload.pod_scan_code,
        pod_latitude=payload.pod_latitude,
        pod_longitude=payload.pod_longitude,
        pod_captured_at=datetime.utcnow() if payload.outcome == PackageOutcome.DELIVERED else None,
        return_reason=payload.return_reason,
        return_note=payload.return_note,
    )
    db.add(package)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Package already registered for this work session"
        )
    db.refresh(package)
    return package


def attach_pod_photo(db: Session, package: Package, file: UploadFile) -> Package:
    if package.outcome != PackageOutcome.DELIVERED:
        raise HTTPException(
            status_code=409, detail="Proof of delivery photo requires outcome 'delivered'"
        )

    package.pod_photo_url = save_pod_photo(str(package.id), file)
    if package.pod_captured_at is None:
        package.pod_captured_at = datetime.utcnow()
    db.commit()
    db.refresh(package)
    return package
