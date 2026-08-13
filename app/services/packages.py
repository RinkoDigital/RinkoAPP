from datetime import datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Package, PackageOutcome, PackageSource, WorkSession
from app.schemas import PackageCreate, PackageResolve
from app.services import track123
from app.storage import save_pod_photo

_COURIER_SOURCE_MAP = {"uniuni": PackageSource.UNIUNI, "gofo": PackageSource.GOFO}


def _source_for_courier(courier_code: str | None) -> PackageSource:
    if courier_code is None:
        return PackageSource.OTHER_PLATFORM
    return _COURIER_SOURCE_MAP.get(courier_code.lower(), PackageSource.OTHER_PLATFORM)


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


def bulk_import_packages(
    db: Session, session: WorkSession, tracking_codes: list[str], courier_code: str | None
) -> tuple[list[Package], list[str]]:
    """Creates one pending (outcome=None) Package per new tracking code and
    registers them with Track123 for status tracking. Codes already present
    on this session — already imported, or entered manually — are skipped
    rather than erroring, since a driver re-pasting the same route list
    shouldn't blow up. Returns (created, skipped_duplicate_codes)."""
    existing = {
        code
        for (code,) in db.query(Package.tracking_code)
        .filter(Package.session_id == session.id, Package.tracking_code.in_(tracking_codes))
        .all()
    }
    seen: set[str] = set()
    new_codes: list[str] = []
    skipped: list[str] = []
    for code in tracking_codes:
        if code in existing or code in seen:
            skipped.append(code)
            continue
        seen.add(code)
        new_codes.append(code)

    source = _source_for_courier(courier_code)
    created = [
        Package(session_id=session.id, tracking_code=code, outcome=None, source=source)
        for code in new_codes
    ]
    db.add_all(created)
    db.commit()
    for package in created:
        db.refresh(package)

    track123.register_trackings(
        [{"trackNo": code, "courierCode": courier_code, "orderNo": None} for code in new_codes]
    )
    return created, skipped


def resolve_package(db: Session, package: Package, payload: PackageResolve) -> Package:
    """Fills in the outcome for a pending (carrier-imported) package — the
    driver's own confirmation, same fields as a manually-created package."""
    package.outcome = payload.outcome
    package.pod_scan_code = payload.pod_scan_code
    package.pod_latitude = payload.pod_latitude
    package.pod_longitude = payload.pod_longitude
    package.return_reason = payload.return_reason
    package.return_note = payload.return_note
    if payload.outcome == PackageOutcome.DELIVERED and package.pod_captured_at is None:
        package.pod_captured_at = datetime.utcnow()
    db.commit()
    db.refresh(package)
    return package


def refresh_carrier_status(db: Session, session: WorkSession) -> list[Package]:
    """Polls Track123 for every non-manual package on the session and
    updates carrier_status. Returns the packages that actually changed —
    callers should re-fetch the full list to display everything."""
    packages = [p for p in session.packages if p.source != PackageSource.MANUAL]
    if not packages:
        return []
    statuses = track123.query_tracking_status([p.tracking_code for p in packages])
    if not statuses:
        return []
    now = datetime.utcnow()
    updated = []
    for package in packages:
        status = statuses.get(package.tracking_code)
        if status is not None:
            package.carrier_status = status
            package.carrier_status_updated_at = now
            updated.append(package)
    if updated:
        db.commit()
        for package in updated:
            db.refresh(package)
    return updated


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
