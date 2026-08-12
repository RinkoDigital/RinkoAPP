from unittest.mock import patch

from app.services.oauth import OAuthIdentity


def test_google_login_creates_driver(client):
    identity = OAuthIdentity(subject="google-sub-1", email="ana@example.com", name="Ana Souza")
    with patch("app.routers.auth.verify_google_id_token", return_value=identity):
        resp = client.post("/auth/oauth/google", json={"id_token": "fake"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["driver"]["name"] == "Ana Souza"
    assert body["driver"]["email"] == "ana@example.com"
    assert body["driver"]["email_verified"] is True
    assert body["access_token"]


def test_google_login_reuses_existing_oauth_driver(client):
    identity = OAuthIdentity(subject="google-sub-2", email="bea@example.com", name="Bea Lima")
    with patch("app.routers.auth.verify_google_id_token", return_value=identity):
        first = client.post("/auth/oauth/google", json={"id_token": "fake"}).json()
        second = client.post("/auth/oauth/google", json={"id_token": "fake"}).json()
    assert first["driver"]["id"] == second["driver"]["id"]


def test_google_login_links_existing_password_account_by_email(client):
    client.post(
        "/auth/signup",
        json={"name": "Caio Reis", "email": "caio@example.com", "password": "s3cret-pass"},
    )
    identity = OAuthIdentity(subject="google-sub-3", email="caio@example.com", name="Caio Reis")
    with patch("app.routers.auth.verify_google_id_token", return_value=identity):
        resp = client.post("/auth/oauth/google", json={"id_token": "fake"})
    assert resp.status_code == 200
    assert resp.json()["driver"]["email"] == "caio@example.com"

    # The password login still works after linking — we didn't wipe it.
    login_resp = client.post(
        "/auth/login", json={"email": "caio@example.com", "password": "s3cret-pass"}
    )
    assert login_resp.status_code == 200


def test_apple_login_creates_driver_using_client_supplied_name(client):
    identity = OAuthIdentity(subject="apple-sub-1", email="dan@example.com", name=None)
    with patch("app.routers.auth.verify_apple_identity_token", return_value=identity):
        resp = client.post(
            "/auth/oauth/apple", json={"identity_token": "fake", "name": "Dan Nunes"}
        )
    assert resp.status_code == 200
    assert resp.json()["driver"]["name"] == "Dan Nunes"


def test_apple_login_without_email_is_rejected(client):
    identity = OAuthIdentity(subject="apple-sub-2", email=None, name=None)
    with patch("app.routers.auth.verify_apple_identity_token", return_value=identity):
        resp = client.post("/auth/oauth/apple", json={"identity_token": "fake"})
    assert resp.status_code == 422


def test_oauth_only_driver_has_no_password_login(client):
    identity = OAuthIdentity(subject="google-sub-4", email="eli@example.com", name="Eli Costa")
    with patch("app.routers.auth.verify_google_id_token", return_value=identity):
        client.post("/auth/oauth/google", json={"id_token": "fake"})

    resp = client.post(
        "/auth/login", json={"email": "eli@example.com", "password": "whatever"}
    )
    assert resp.status_code == 401
