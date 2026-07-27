from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company
from app.schemas import CompanyCreate, CompanyCreated, WebhookSecretRotated
from app.security import generate_api_key, get_current_company, hash_api_key, require_admin

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyCreated, dependencies=[Depends(require_admin)])
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    api_key = generate_api_key()
    webhook_secret = generate_api_key()
    company = Company(
        name=payload.name,
        default_rate_cents=payload.default_rate_cents,
        api_key_hash=hash_api_key(api_key),
        webhook_secret_hash=hash_api_key(webhook_secret),
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return CompanyCreated(
        id=company.id,
        name=company.name,
        api_key=api_key,
        webhook_secret=webhook_secret,
        default_rate_cents=company.default_rate_cents,
    )


@router.post("/me/rotate-webhook-secret", response_model=WebhookSecretRotated)
def rotate_webhook_secret(
    db: Session = Depends(get_db), company: Company = Depends(get_current_company)
):
    webhook_secret = generate_api_key()
    company.webhook_secret_hash = hash_api_key(webhook_secret)
    db.commit()
    return WebhookSecretRotated(webhook_secret=webhook_secret)
