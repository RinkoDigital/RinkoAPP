"""Finds sessions needing a push reminder and sends them.

Meant to run on a schedule (cron, Render Cron Job, GitHub Actions
scheduled workflow...) — nothing in this app triggers it on its own.
Run it directly with:

    python -m app.jobs.send_reminders

Each reminder fires at most once per session (see the *_reminder_sent_at
columns on WorkSession), so running this job more often than the
schedule requires is harmless — it just finds nothing new to send.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Callable

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import PaymentStatus, PushToken, WorkSession, WorkSessionStatus
from app.services.push import send_push_notification

logger = logging.getLogger("rinko.jobs.send_reminders")

STALE_SESSION_HOURS = 12

SendFn = Callable[[str, str, str, dict | None], None]


def _format_cents(cents: int) -> str:
    return f"${cents / 100:.2f}"


def find_due_payment_sessions(db: Session, today: date) -> list[WorkSession]:
    candidates = (
        db.query(WorkSession)
        .filter(
            WorkSession.status == WorkSessionStatus.CLOSED,
            WorkSession.payment_due_date.isnot(None),
            WorkSession.payment_due_date <= today,
            WorkSession.payment_reminder_sent_at.is_(None),
        )
        .all()
    )
    return [s for s in candidates if s.payment_status != PaymentStatus.RECEIVED]


def find_stale_open_sessions(db: Session, now: datetime) -> list[WorkSession]:
    cutoff = now - timedelta(hours=STALE_SESSION_HOURS)
    return (
        db.query(WorkSession)
        .filter(
            WorkSession.status == WorkSessionStatus.OPEN,
            WorkSession.created_at < cutoff,
            WorkSession.stale_session_reminder_sent_at.is_(None),
        )
        .all()
    )


def _notify_driver(db: Session, driver_id, title: str, body: str, send_fn: SendFn) -> None:
    tokens = db.query(PushToken).filter(PushToken.driver_id == driver_id).all()
    for t in tokens:
        send_fn(t.token, title, body, None)


def run(db: Session, send_fn: SendFn = send_push_notification, now: datetime | None = None) -> dict:
    now = now or datetime.utcnow()
    sent = {"payment_due": 0, "stale_session": 0}

    for session in find_due_payment_sessions(db, now.date()):
        overdue = session.payment_due_date < now.date()
        title = "Payment overdue" if overdue else "Payment due today"
        body = (
            f"{session.carrier.name} — {_format_cents(session.outstanding_cents)} "
            f"was due {session.payment_due_date.isoformat()}."
        )
        _notify_driver(db, session.driver_id, title, body, send_fn)
        session.payment_reminder_sent_at = now
        sent["payment_due"] += 1

    for session in find_stale_open_sessions(db, now):
        title = "Session still open"
        body = (
            f"Your {session.carrier.name} session from {session.service_date.isoformat()} "
            "has been open a while — close it out to generate the Work Report."
        )
        _notify_driver(db, session.driver_id, title, body, send_fn)
        session.stale_session_reminder_sent_at = now
        sent["stale_session"] += 1

    db.commit()
    logger.info("Sent reminders: %s", sent)
    return sent


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        run(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
