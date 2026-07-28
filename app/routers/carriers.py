from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Carrier, Driver
from app.schemas import CarrierCreate, CarrierOut
from app.security import get_current_driver

router = APIRouter(prefix="/carriers", tags=["carriers"])


@router.post("", response_model=CarrierOut, status_code=201)
def create_carrier(
    payload: CarrierCreate,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    carrier = Carrier(driver_id=driver.id, **payload.model_dump())
    db.add(carrier)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="You already have a carrier with this name")
    db.refresh(carrier)
    return carrier


@router.get("", response_model=list[CarrierOut])
def list_carriers(db: Session = Depends(get_db), driver: Driver = Depends(get_current_driver)):
    return db.query(Carrier).filter(Carrier.driver_id == driver.id).all()
