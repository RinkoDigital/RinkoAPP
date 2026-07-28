from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Driver
from app.schemas import DriverLogin, DriverSignup, DriverToken
from app.security import create_driver_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=DriverToken)
def signup(payload: DriverSignup, db: Session = Depends(get_db)):
    driver = Driver(
        name=payload.name, email=payload.email, password_hash=hash_password(payload.password)
    )
    db.add(driver)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    db.refresh(driver)
    return DriverToken(access_token=create_driver_token(driver), driver=driver)


@router.post("/login", response_model=DriverToken)
def login(payload: DriverLogin, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.email == payload.email).first()
    if driver is None or not verify_password(payload.password, driver.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return DriverToken(access_token=create_driver_token(driver), driver=driver)
