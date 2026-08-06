"""Placeholder email sender.

No real provider (SES, SendGrid, Postmark...) is wired up yet, so this
just logs the message. Verification and password-reset flows are fully
functional end-to-end — only the delivery mechanism is a stand-in, same
pattern as the manual plan flag in app/plans.py.
"""

import logging

logger = logging.getLogger("rinko.email")


def send_email(to: str, subject: str, body: str) -> None:
    logger.info("EMAIL to=%s subject=%r\n%s", to, subject, body)
