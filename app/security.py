import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Company, Driver

DRIVER_TOKEN_TYPE = "driver_access"


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def require_admin(x_admin_key: str = Header(...)) -> None:
    if not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")


def get_current_company(
    x_api_key: str = Header(...), db: Session = Depends(get_db)
) -> Company:
    company = (
        db.query(Company).filter(Company.api_key_hash == hash_api_key(x_api_key)).first()
    )
    if company is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return company


def verify_webhook_secret(company: Company, provided_secret: str) -> bool:
    if company.webhook_secret_hash is None:
        return False
    return secrets.compare_digest(hash_api_key(provided_secret), company.webhook_secret_hash)


def generate_invite_token() -> str:
    return secrets.token_urlsafe(24)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_driver_token(driver: Driver) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "type": DRIVER_TOKEN_TYPE,
        "sub": str(driver.id),
        "company_id": str(driver.company_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.driver_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def get_current_driver(
    authorization: str = Header(...), db: Session = Depends(get_db)
) -> Driver:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") != DRIVER_TOKEN_TYPE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    driver = db.query(Driver).filter(Driver.id == uuid.UUID(payload["sub"])).first()
    if driver is None or driver.password_hash is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Driver account not found")
    return driver
