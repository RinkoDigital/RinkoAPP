import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, Driver
from app.schemas import DriverCreate, DriverOut
from app.security import get_current_company

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("", response_model=DriverOut)
def create_driver(
    payload: DriverCreate,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    driver = Driver(company_id=company.id, **payload.model_dump())
    db.add(driver)
    db.commit()
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
