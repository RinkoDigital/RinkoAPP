from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuthTokenPurpose, Driver
from app.schemas import (
    DriverLogin,
    DriverSignup,
    DriverToken,
    EmailVerifyRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    ResendVerificationRequest,
)
from app.security import create_driver_token, hash_password, verify_password
from app.services.auth_tokens import (
    EMAIL_VERIFICATION_TTL_MINUTES,
    PASSWORD_RESET_TTL_MINUTES,
    consume_token,
    issue_token,
)
from app.services.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _send_verification_email(db: Session, driver: Driver) -> None:
    token = issue_token(
        db, driver, AuthTokenPurpose.EMAIL_VERIFICATION, EMAIL_VERIFICATION_TTL_MINUTES
    )
    send_email(
        to=driver.email,
        subject="Verify your Rinko account",
        body=f"Confirm your email with this token: {token}\n(POST /auth/verify-email)",
    )


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
    _send_verification_email(db, driver)
    return DriverToken(access_token=create_driver_token(driver), driver=driver)


@router.post("/login", response_model=DriverToken)
def login(payload: DriverLogin, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.email == payload.email).first()
    if driver is None or not verify_password(payload.password, driver.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return DriverToken(access_token=create_driver_token(driver), driver=driver)


@router.post("/verify-email", status_code=204)
def verify_email(payload: EmailVerifyRequest, db: Session = Depends(get_db)):
    driver = consume_token(db, payload.token, AuthTokenPurpose.EMAIL_VERIFICATION)
    if driver is None:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    driver.email_verified = True
    db.commit()


@router.post("/resend-verification", status_code=202)
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.email == payload.email).first()
    if driver is not None and not driver.email_verified:
        _send_verification_email(db, driver)
    # Always 202: this endpoint never reveals whether an account exists
    # for the given email, or whether it's already verified.


@router.post("/request-password-reset", status_code=202)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.email == payload.email).first()
    if driver is not None:
        token = issue_token(
            db, driver, AuthTokenPurpose.PASSWORD_RESET, PASSWORD_RESET_TTL_MINUTES
        )
        send_email(
            to=driver.email,
            subject="Reset your Rinko password",
            body=f"Reset your password with this token: {token}\n(POST /auth/reset-password)",
        )
    # Always 202, same reasoning as resend-verification above.


@router.post("/reset-password", status_code=204)
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    driver = consume_token(db, payload.token, AuthTokenPurpose.PASSWORD_RESET)
    if driver is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    driver.password_hash = hash_password(payload.new_password)
    db.commit()
