import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Company, Driver
from app.schemas import DriverCreate, DriverOut
from app.security import generate_invite_token, get_current_company

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("", response_model=DriverOut)
def create_driver(
    payload: DriverCreate,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    driver = Driver(company_id=company.id, **payload.model_dump())
    if driver.email:
        driver.invite_token = generate_invite_token()
        driver.invite_expires_at = datetime.utcnow() + timedelta(
            minutes=settings.driver_invite_expire_minutes
        )
    db.add(driver)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A driver with this email already exists")
    db.refresh(driver)
    return driver


@router.get("", response_model=list[DriverOut])
def list_drivers(
    db: Session = Depends(get_db), company: Company = Depends(get_current_company)
):
    return db.query(Driver).filter(Driver.company_id == company.id).all()


@router.get("/{driver_id}", response_model=DriverOut)
def get_driver(
    driver_id: uuid.UUID,
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
    return driver
