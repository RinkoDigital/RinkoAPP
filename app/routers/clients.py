from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Client, Company
from app.schemas import ClientCreate, ClientOut
from app.security import get_current_company

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientOut)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    client = Client(company_id=company.id, **payload.model_dump())
    db.add(client)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Client already exists")
    db.refresh(client)
    return client


@router.get("", response_model=list[ClientOut])
def list_clients(
    db: Session = Depends(get_db), company: Company = Depends(get_current_company)
):
    return db.query(Client).filter(Client.company_id == company.id).all()
