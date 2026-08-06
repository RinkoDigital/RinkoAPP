import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import AuthToken, AuthTokenPurpose, Driver

EMAIL_VERIFICATION_TTL_MINUTES = 60 * 24
PASSWORD_RESET_TTL_MINUTES = 30


def _hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def issue_token(
    db: Session, driver: Driver, purpose: AuthTokenPurpose, ttl_minutes: int
) -> str:
    raw_token = secrets.token_urlsafe(32)
    db.add(
        AuthToken(
            driver_id=driver.id,
            purpose=purpose,
            token_hash=_hash(raw_token),
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
        )
    )
    db.commit()
    return raw_token


def consume_token(db: Session, raw_token: str, purpose: AuthTokenPurpose) -> Driver | None:
    """Marks the token used and returns its driver — or None if the token
    doesn't exist, was already used, or has expired."""
    token = (
        db.query(AuthToken)
        .filter(AuthToken.token_hash == _hash(raw_token), AuthToken.purpose == purpose)
        .first()
    )
    if token is None or token.used_at is not None or token.expires_at < datetime.utcnow():
        return None
    token.used_at = datetime.utcnow()
    db.commit()
    return token.driver
