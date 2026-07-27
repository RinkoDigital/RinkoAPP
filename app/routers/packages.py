import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, Delivery, DeliveryStatus, Package, PackageOutcome
from app.schemas import PackageCreate, PackageOut
from app.security import get_current_company
from app.storage import save_pod_photo

router = APIRouter(prefix="/deliveries/{delivery_id}/packages", tags=["packages"])


def _get_delivery(db: Session, company: Company, delivery_id: uuid.UUID) -> Delivery:
    delivery = (
        db.query(Delivery)
        .filter(Delivery.id == delivery_id, Delivery.company_id == company.id)
        .first()
    )
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery


@router.post("", response_model=PackageOut, status_code=201)
def register_package(
    delivery_id: uuid.UUID,
    payload: PackageCreate,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    delivery = _get_delivery(db, company, delivery_id)
    if delivery.status == DeliveryStatus.REJECTED:
        raise HTTPException(status_code=409, detail="Cannot add packages to a rejected delivery")

    package = Package(
        delivery_id=delivery.id,
        tracking_code=payload.tracking_code,
        outcome=payload.outcome,
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
            status_code=409, detail="Package already registered for this delivery batch"
        )
    db.refresh(package)
    return package


@router.get("", response_model=list[PackageOut])
def list_packages(
    delivery_id: uuid.UUID,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    delivery = _get_delivery(db, company, delivery_id)
    return delivery.packages


@router.post("/{package_id}/pod-photo", response_model=PackageOut)
def upload_pod_photo(
    delivery_id: uuid.UUID,
    package_id: uuid.UUID,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
    file: UploadFile = File(...),
):
    delivery = _get_delivery(db, company, delivery_id)
    package = next((p for p in delivery.packages if p.id == package_id), None)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    if package.outcome != PackageOutcome.DELIVERED:
        raise HTTPException(status_code=409, detail="Proof of delivery photo requires outcome 'delivered'")

    package.pod_photo_url = save_pod_photo(str(package.id), file)
    if package.pod_captured_at is None:
        package.pod_captured_at = datetime.utcnow()
    db.commit()
    db.refresh(package)
    return package
