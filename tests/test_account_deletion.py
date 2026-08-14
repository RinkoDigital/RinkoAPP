import io
import uuid
from datetime import datetime

from app.models import AuthToken, AuthTokenPurpose, Carrier, Driver, Evidence, Package, WorkSession


def test_delete_account_removes_driver_and_all_related_rows(client, driver_and_headers, carrier, db_session):
    driver, headers = driver_and_headers

    session_resp = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 50},
        headers=headers,
    )
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id"]

    evidence_resp = client.post(
        f"/sessions/{session_id}/evidence",
        headers=headers,
        data={"kind": "other"},
        files={"file": ("f.png", io.BytesIO(b"\x89PNG" + b"0" * 20), "image/png")},
    )
    assert evidence_resp.status_code == 201

    package_resp = client.post(
        f"/sessions/{session_id}/packages",
        json={"tracking_code": "LV1", "outcome": "delivered"},
        headers=headers,
    )
    assert package_resp.status_code == 201

    driver_id = uuid.UUID(driver["id"])
    db_session.add(AuthToken(
        driver_id=driver_id,
        purpose=AuthTokenPurpose.EMAIL_VERIFICATION,
        token_hash="x" * 64,
        expires_at=datetime.utcnow(),
    ))
    db_session.commit()

    resp = client.request("DELETE", "/account/me", headers=headers)
    assert resp.status_code == 204

    assert db_session.query(Driver).filter(Driver.id == driver_id).count() == 0
    assert db_session.query(WorkSession).filter(WorkSession.driver_id == driver_id).count() == 0
    assert db_session.query(Carrier).filter(Carrier.driver_id == driver_id).count() == 0
    assert db_session.query(AuthToken).filter(AuthToken.driver_id == driver_id).count() == 0
    assert db_session.query(Evidence).count() == 0
    assert db_session.query(Package).count() == 0

    # The old token is now rejected — the driver row backing it is gone.
    again = client.request("DELETE", "/account/me", headers=headers)
    assert again.status_code == 401


def test_delete_account_requires_auth(client):
    resp = client.request("DELETE", "/account/me")
    assert resp.status_code in (401, 422)
