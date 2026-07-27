import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, Delivery
from app.schemas import PackageCreate, PackageOut
from app.security import get_current_company
from app.services.packages import attach_pod_photo, create_package

router = APIRouter(prefix="/deliveries/{delivery_id}/packages", tags=["packages"])


def get_company_delivery(db: Session, company: Company, delivery_id: uuid.UUID) -> Delivery:
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
    delivery = get_company_delivery(db, company, delivery_id)
    return create_package(db, delivery, payload)


@router.get("", response_model=list[PackageOut])
def list_packages(
    delivery_id: uuid.UUID,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    delivery = get_company_delivery(db, company, delivery_id)
    return delivery.packages


@router.post("/{package_id}/pod-photo", response_model=PackageOut)
def upload_pod_photo(
    delivery_id: uuid.UUID,
    package_id: uuid.UUID,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
    file: UploadFile = File(...),
):
    delivery = get_company_delivery(db, company, delivery_id)
    package = next((p for p in delivery.packages if p.id == package_id), None)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return attach_pod_photo(db, package, file)
