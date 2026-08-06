def test_signup_creates_driver_and_returns_token(client):
    resp = client.post(
        "/auth/signup",
        json={"name": "Alex Silva", "email": "alex@example.com", "password": "s3cret-pass"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["driver"]["name"] == "Alex Silva"
    assert body["driver"]["email"] == "alex@example.com"
    assert body["driver"]["email_verified"] is False
    assert body["access_token"]


def test_signup_duplicate_email_rejected(client):
    payload = {"name": "Alex Silva", "email": "alex@example.com", "password": "s3cret-pass"}
    assert client.post("/auth/signup", json=payload).status_code == 200
    resp = client.post("/auth/signup", json=payload)
    assert resp.status_code == 409


def test_login_success(client):
    client.post(
        "/auth/signup",
        json={"name": "Alex Silva", "email": "alex@example.com", "password": "s3cret-pass"},
    )
    resp = client.post(
        "/auth/login", json={"email": "alex@example.com", "password": "s3cret-pass"}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_wrong_password_rejected(client):
    client.post(
        "/auth/signup",
        json={"name": "Alex Silva", "email": "alex@example.com", "password": "s3cret-pass"},
    )
    resp = client.post("/auth/login", json={"email": "alex@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_email_rejected(client):
    resp = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "whatever"}
    )
    assert resp.status_code == 401


def test_protected_endpoint_requires_token(client):
    resp = client.get("/carriers")
    assert resp.status_code == 422  # missing Authorization header


def test_protected_endpoint_rejects_invalid_token(client):
    resp = client.get("/carriers", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
