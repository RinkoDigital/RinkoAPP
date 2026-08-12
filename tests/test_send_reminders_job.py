import uuid
from datetime import date, datetime, timedelta

from app.jobs.send_reminders import run
from app.models import WorkSession


def _create_and_close_session(client, headers, carrier, payment_due_date=None):
    payload = {
        "carrier_id": carrier["id"],
        "service_date": "2026-07-28",
        "packages_assigned": 10,
    }
    if payment_due_date:
        payload["payment_due_date"] = payment_due_date
    session = client.post("/sessions", json=payload, headers=headers).json()
    client.post(f"/sessions/{session['id']}/close", json={"exceptions_count": 0}, headers=headers)
    return session["id"]


def test_sends_reminder_for_overdue_unpaid_session(client, driver_and_headers, carrier, db_session):
    _, headers = driver_and_headers
    client.post("/account/push-token", json={"token": "ExponentPushToken[a]"}, headers=headers)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    _create_and_close_session(client, headers, carrier, payment_due_date=yesterday)

    sent = []
    run(db_session, send_fn=lambda token, title, body, data: sent.append((token, title, body)))

    assert sent == [("ExponentPushToken[a]", "Payment overdue", sent[0][2])]
    assert "UniUni" in sent[0][2]


def test_does_not_resend_payment_reminder(client, driver_and_headers, carrier, db_session):
    _, headers = driver_and_headers
    client.post("/account/push-token", json={"token": "ExponentPushToken[a]"}, headers=headers)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    _create_and_close_session(client, headers, carrier, payment_due_date=yesterday)

    first_sent = []
    run(db_session, send_fn=lambda token, title, body, data: first_sent.append(token))
    assert len(first_sent) == 1

    second_sent = []
    run(db_session, send_fn=lambda token, title, body, data: second_sent.append(token))
    assert second_sent == []


def test_no_reminder_for_session_already_paid(client, driver_and_headers, carrier, db_session):
    _, headers = driver_and_headers
    client.post("/account/push-token", json={"token": "ExponentPushToken[a]"}, headers=headers)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    session_id = _create_and_close_session(client, headers, carrier, payment_due_date=yesterday)
    client.post(
        f"/sessions/{session_id}/record-payment",
        json={"payment_received_cents": 1700},
        headers=headers,
    )

    sent = []
    run(db_session, send_fn=lambda token, title, body, data: sent.append(token))
    assert sent == []


def test_sends_reminder_for_stale_open_session(client, driver_and_headers, carrier, db_session):
    _, headers = driver_and_headers
    client.post("/account/push-token", json={"token": "ExponentPushToken[b]"}, headers=headers)
    session = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 10},
        headers=headers,
    ).json()

    # Can't create a WorkSession already-old through the API — created_at is
    # server-assigned — so backdate it directly for the test.
    row = db_session.query(WorkSession).filter(WorkSession.id == uuid.UUID(session["id"])).first()
    row.created_at = datetime.utcnow() - timedelta(hours=20)
    db_session.commit()

    sent = []
    run(db_session, send_fn=lambda token, title, body, data: sent.append((token, title)))

    assert sent == [("ExponentPushToken[b]", "Session still open")]


def test_no_stale_reminder_for_recently_opened_session(client, driver_and_headers, carrier, db_session):
    _, headers = driver_and_headers
    client.post("/account/push-token", json={"token": "ExponentPushToken[b]"}, headers=headers)
    client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 10},
        headers=headers,
    )

    sent = []
    run(db_session, send_fn=lambda token, title, body, data: sent.append(token))
    assert sent == []
