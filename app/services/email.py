"""Outbound email.

Defaults to logging (nothing is delivered) — set EMAIL_BACKEND=smtp and the
SMTP_* settings to actually send, via any provider's SMTP endpoint
(SendGrid, Postmark, SES, Mailgun, or a plain mailbox). Uses only the
standard library, so no provider-specific SDK/dependency is needed.
"""

import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("rinko.email")


def send_email(to: str, subject: str, body: str) -> None:
    if settings.email_backend != "smtp":
        logger.info("EMAIL to=%s subject=%r\n%s", to, subject, body)
        return

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = to

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.sendmail(settings.smtp_from_email, [to], message.as_string())
