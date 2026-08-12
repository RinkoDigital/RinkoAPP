from unittest.mock import MagicMock, patch

from app.config import settings
from app.services.email import send_email


def test_log_backend_does_not_touch_smtp(monkeypatch):
    monkeypatch.setattr(settings, "email_backend", "log")
    with patch("app.services.email.smtplib.SMTP") as mock_smtp:
        send_email(to="alex@example.com", subject="Hi", body="body")
    mock_smtp.assert_not_called()


def test_smtp_backend_sends_via_configured_server(monkeypatch):
    monkeypatch.setattr(settings, "email_backend", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_username", "apikey")
    monkeypatch.setattr(settings, "smtp_password", "secret")
    monkeypatch.setattr(settings, "smtp_from_email", "no-reply@rinkodigital.com")
    monkeypatch.setattr(settings, "smtp_use_tls", True)

    mock_server = MagicMock()
    mock_server.__enter__.return_value = mock_server
    with patch("app.services.email.smtplib.SMTP", return_value=mock_server) as mock_smtp:
        send_email(to="alex@example.com", subject="Verify your Rinko account", body="token: abc")

    mock_smtp.assert_called_once_with("smtp.example.com", 587)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("apikey", "secret")
    assert mock_server.sendmail.call_count == 1
    from_addr, to_addrs, raw_message = mock_server.sendmail.call_args.args
    assert from_addr == "no-reply@rinkodigital.com"
    assert to_addrs == ["alex@example.com"]
    assert "token: abc" in raw_message
