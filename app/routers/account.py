from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuthToken, Carrier, Driver, Evidence, Package, PushToken, WorkSession
from app.plans import can_export_docx, evidence_limit
from app.schemas import PlanInfo, PlanUpdate, PushTokenRegister
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


@router.post("/push-token", status_code=204)
def register_push_token(
    payload: PushTokenRegister,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    """Registers a device's Expo push token for this driver. The token is
    the unique key — re-registering the same token (e.g. a different
    driver logging in on the same phone) just reassigns it."""
    existing = db.query(PushToken).filter(PushToken.token == payload.token).first()
    if existing is not None:
        existing.driver_id = driver.id
    else:
        db.add(PushToken(driver_id=driver.id, token=payload.token))
    db.commit()


@router.delete("/push-token", status_code=204)
def unregister_push_token(
    payload: PushTokenRegister,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    db.query(PushToken).filter(
        PushToken.token == payload.token, PushToken.driver_id == driver.id
    ).delete()
    db.commit()


@router.delete("/me", status_code=204)
def delete_account(
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    """Permanently deletes the driver and everything tied to their account.

    No cascade is configured at the DB/ORM level, so children are removed
    explicitly in FK-safe order before the driver row itself. Once the
    driver row is gone, get_current_driver rejects any outstanding token
    for this account on its next use.
    """
    session_ids = [
        row.id for row in db.query(WorkSession.id).filter(WorkSession.driver_id == driver.id)
    ]
    if session_ids:
        db.query(Evidence).filter(Evidence.session_id.in_(session_ids)).delete(synchronize_session=False)
        db.query(Package).filter(Package.session_id.in_(session_ids)).delete(synchronize_session=False)
    db.query(WorkSession).filter(WorkSession.driver_id == driver.id).delete(synchronize_session=False)
    db.query(Carrier).filter(Carrier.driver_id == driver.id).delete(synchronize_session=False)
    db.query(AuthToken).filter(AuthToken.driver_id == driver.id).delete(synchronize_session=False)
    db.query(PushToken).filter(PushToken.driver_id == driver.id).delete(synchronize_session=False)
    db.delete(driver)
    db.commit()
