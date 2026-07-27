import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Delivery, DeliveryStatus, Driver, PackageSource, PaymentStatus
from app.report_docx import render_delivery_proof_docx
from app.routers.reports import _build_driver_pay_report
from app.schemas import (
    DeliveryOut,
    DeliveryProof,
    DriverMeOut,
    DriverPayReport,
    PackageCreate,
    PackageOut,
)
from app.security import get_current_driver
from app.services.delivery_proof import build_delivery_proof
from app.services.packages import attach_pod_photo, create_package

router = APIRouter(prefix="/me", tags=["driver-self-service"])


def get_own_delivery(db: Session, driver: Driver, delivery_id: uuid.UUID) -> Delivery:
    delivery = (
        db.query(Delivery)
        .filter(Delivery.id == delivery_id, Delivery.driver_id == driver.id)
        .first()
    )
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery


@router.get("", response_model=DriverMeOut)
def read_profile(driver: Driver = Depends(get_current_driver)):
    return DriverMeOut(
        id=driver.id, name=driver.name, email=driver.email, company_name=driver.company.name
    )


@router.get("/deliveries", response_model=list[DeliveryOut])
def list_own_deliveries(
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
    status: DeliveryStatus | None = Query(default=None),
    payment_status: PaymentStatus | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
):
    q = db.query(Delivery).filter(Delivery.driver_id == driver.id)
    if status is not None:
        q = q.filter(Delivery.status == status)
    if payment_status is not None:
        q = q.filter(Delivery.payment_status == payment_status)
    if start_date is not None:
        q = q.filter(Delivery.batch_date >= start_date)
    if end_date is not None:
        q = q.filter(Delivery.batch_date <= end_date)
    return q.order_by(Delivery.batch_date.desc()).all()


@router.get("/deliveries/{delivery_id}/packages", response_model=list[PackageOut])
def list_own_packages(
    delivery_id: uuid.UUID,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    delivery = get_own_delivery(db, driver, delivery_id)
    return delivery.packages


@router.post("/deliveries/{delivery_id}/packages", response_model=PackageOut, status_code=201)
def register_own_package(
    delivery_id: uuid.UUID,
    payload: PackageCreate,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    delivery = get_own_delivery(db, driver, delivery_id)
    return create_package(db, delivery, payload, force_source=PackageSource.MANUAL)


@router.post("/deliveries/{delivery_id}/packages/{package_id}/pod-photo", response_model=PackageOut)
def upload_own_pod_photo(
    delivery_id: uuid.UUID,
    package_id: uuid.UUID,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
    file: UploadFile = File(...),
):
    delivery = get_own_delivery(db, driver, delivery_id)
    package = next((p for p in delivery.packages if p.id == package_id), None)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return attach_pod_photo(db, package, file)


@router.get("/pay-report", response_model=DriverPayReport)
def own_pay_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    return _build_driver_pay_report(db, driver.company, driver, start_date, end_date)


@router.get("/deliveries/{delivery_id}/proof", response_model=DeliveryProof)
def own_delivery_proof(
    delivery_id: uuid.UUID,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    delivery = get_own_delivery(db, driver, delivery_id)
    return build_delivery_proof(delivery)


@router.get("/deliveries/{delivery_id}/proof.docx")
def own_delivery_proof_docx(
    delivery_id: uuid.UUID,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    delivery = get_own_delivery(db, driver, delivery_id)
    proof = build_delivery_proof(delivery)
    docx_bytes = render_delivery_proof_docx(proof)
    filename = f"proof_{proof.proof_number}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
