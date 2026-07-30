from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Driver
from app.plans import can_export_docx, evidence_limit
from app.schemas import PlanInfo, PlanUpdate
from app.security import get_current_driver

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/plan", response_model=PlanInfo)
def get_plan(driver: Driver = Depends(get_current_driver)):
    return PlanInfo(
        plan=driver.plan,
        docx_export=can_export_docx(driver.plan),
        evidence_per_session_limit=evidence_limit(driver.plan),
    )


@router.post("/plan", response_model=PlanInfo)
def set_plan(
    payload: PlanUpdate,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    """Manually flips the driver's plan. There's no billing integration yet —
    same call the product made about payments in general (see README). This
    is a placeholder until real billing exists."""
    driver.plan = payload.plan
    db.commit()
    return PlanInfo(
        plan=driver.plan,
        docx_export=can_export_docx(driver.plan),
        evidence_per_session_limit=evidence_limit(driver.plan),
    )
