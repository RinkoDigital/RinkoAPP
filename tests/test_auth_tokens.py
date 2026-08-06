import re

from app.routers import auth as auth_router


def _capture_emails(monkeypatch):
    sent = []
    monkeypatch.setattr(
        auth_router,
        "send_email",
        lambda to, subject, body: sent.append({"to": to, "subject": subject, "body": body}),
    )
    return sent


def _extract_token(body: str) -> str:
    match = re.search(r"token: (\S+)", body)
    assert match, f"no token found in email body: {body}"
    return match.group(1)


def test_signup_sends_verification_email(client, monkeypatch):
    sent = _capture_emails(monkeypatch)
    client.post(
        "/auth/signup",
        json={"name": "Alex Silva", "email": "alex@example.com", "password": "s3cret-pass"},
    )
    assert len(sent) == 1
    assert sent[0]["to"] == "alex@example.com"
    assert "Verify" in sent[0]["subject"]


def test_verify_email_marks_driver_verified(client, monkeypatch):
    sent = _capture_emails(monkeypatch)
    client.post(
        "/auth/signup",
        json={"name": "Alex Silva", "email": "alex@example.com", "password": "s3cret-pass"},
    )
    token = _extract_token(sent[0]["body"])

    resp = client.post("/auth/verify-email", json={"token": token})
    assert resp.status_code == 204

    login = client.post(
        "/auth/login", json={"email": "alex@example.com", "password": "s3cret-pass"}
    )
    assert login.json()["driver"]["email_verified"] is True


def test_verify_email_rejects_invalid_token(client):
    resp = client.post("/auth/verify-email", json={"token": "not-a-real-token"})
    assert resp.status_code == 400


def test_verify_email_token_is_single_use(client, monkeypatch):
    sent = _capture_emails(monkeypatch)
    client.post(
        "/auth/signup",
        json={"name": "Alex Silva", "email": "alex@example.com", "password": "s3cret-pass"},
    )
    token = _extract_token(sent[0]["body"])

    assert client.post("/auth/verify-email", json={"token": token}).status_code == 204
    resp = client.post("/auth/verify-email", json={"token": token})
    assert resp.status_code == 400


def test_resend_verification_is_silent_about_account_existence(client):
    resp = client.post("/auth/resend-verification", json={"email": "nobody@example.com"})
    assert resp.status_code == 202


def test_password_reset_flow(client, monkeypatch):
    sent = _capture_emails(monkeypatch)
    client.post(
        "/auth/signup",
        json={"name": "Alex Silva", "email": "alex@example.com", "password": "old-pass"},
    )
    sent.clear()

    resp = client.post("/auth/request-password-reset", json={"email": "alex@example.com"})
    assert resp.status_code == 202
    assert len(sent) == 1
    token = _extract_token(sent[0]["body"])

    resp = client.post("/auth/reset-password", json={"token": token, "new_password": "new-pass"})
    assert resp.status_code == 204

    assert (
        client.post(
            "/auth/login", json={"email": "alex@example.com", "password": "old-pass"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/login", json={"email": "alex@example.com", "password": "new-pass"}
        ).status_code
        == 200
    )


def test_request_password_reset_is_silent_about_account_existence(client):
    resp = client.post("/auth/request-password-reset", json={"email": "nobody@example.com"})
    assert resp.status_code == 202


def test_reset_password_rejects_invalid_token(client):
    resp = client.post(
        "/auth/reset-password", json={"token": "not-a-real-token", "new_password": "whatever"}
    )
    assert resp.status_code == 400
