from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Driver
from app.schemas import DriverAcceptInvite, DriverLogin, DriverMeOut, DriverToken
from app.security import create_driver_token, hash_password, verify_password

router = APIRouter(prefix="/auth/driver", tags=["driver-auth"])


@router.post("/accept-invite", response_model=DriverToken)
def accept_invite(payload: DriverAcceptInvite, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.invite_token == payload.invite_token).first()
    if driver is None:
        raise HTTPException(status_code=404, detail="Invalid invite token")
    if driver.invite_expires_at is not None and driver.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Invite token has expired")

    driver.password_hash = hash_password(payload.password)
    driver.invite_token = None
    driver.invite_expires_at = None
    db.commit()
    db.refresh(driver)

    return DriverToken(
        access_token=create_driver_token(driver),
        driver=DriverMeOut(
            id=driver.id, name=driver.name, email=driver.email, company_name=driver.company.name
        ),
    )


@router.post("/login", response_model=DriverToken)
def login(payload: DriverLogin, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.email == payload.email).first()
    if driver is None or driver.password_hash is None or not verify_password(
        payload.password, driver.password_hash
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return DriverToken(
        access_token=create_driver_token(driver),
        driver=DriverMeOut(
            id=driver.id, name=driver.name, email=driver.email, company_name=driver.company.name
        ),
    )
