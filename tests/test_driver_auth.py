import io


def _create_driver_with_email(client, headers, email="alex@example.com"):
    resp = client.post(
        "/drivers", json={"name": "Alex Silva", "email": email}, headers=headers
    )
    assert resp.status_code == 200
    return resp.json()


def _accept_invite(client, invite_token, password="s3cret-pass"):
    resp = client.post(
        "/auth/driver/accept-invite",
        json={"invite_token": invite_token, "password": password},
    )
    assert resp.status_code == 200
    return resp.json()


def test_creating_driver_with_email_generates_invite_token(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver_with_email(client, headers)
    assert driver["invite_token"] is not None
    assert driver["has_account"] is False


def test_creating_driver_without_email_has_no_invite(client, company_and_key):
    company, headers = company_and_key
    resp = client.post("/drivers", json={"name": "No Email Driver"}, headers=headers)
    driver = resp.json()
    assert driver["invite_token"] is None
    assert driver["has_account"] is False


def test_accept_invite_and_login_flow(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver_with_email(client, headers)

    token_body = _accept_invite(client, driver["invite_token"])
    assert token_body["driver"]["email"] == "alex@example.com"
    assert token_body["driver"]["company_name"] == company["name"]
    driver_token = token_body["access_token"]

    resp = client.get("/me", headers={"Authorization": f"Bearer {driver_token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alex Silva"

    login_resp = client.post(
        "/auth/driver/login",
        json={"email": "alex@example.com", "password": "s3cret-pass"},
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["access_token"]


def test_login_with_wrong_password_rejected(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver_with_email(client, headers)
    _accept_invite(client, driver["invite_token"])

    resp = client.post(
        "/auth/driver/login",
        json={"email": "alex@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_invite_token_is_single_use(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver_with_email(client, headers)
    _accept_invite(client, driver["invite_token"])

    resp = client.post(
        "/auth/driver/accept-invite",
        json={"invite_token": driver["invite_token"], "password": "another-pass"},
    )
    assert resp.status_code == 404


def test_driver_cannot_use_company_endpoints(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver_with_email(client, headers)
    token_body = _accept_invite(client, driver["invite_token"])
    driver_headers = {"Authorization": f"Bearer {token_body['access_token']}"}

    # Company endpoints require x-api-key; a driver bearer token doesn't satisfy it.
    resp = client.post("/drivers", json={"name": "Someone"}, headers=driver_headers)
    assert resp.status_code == 422


def test_company_endpoints_reject_driver_token_as_api_key(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver_with_email(client, headers)
    token_body = _accept_invite(client, driver["invite_token"])

    resp = client.get("/deliveries", headers={"x-api-key": token_body["access_token"]})
    assert resp.status_code == 401


def test_driver_sees_only_own_deliveries_and_can_submit_pod(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver_with_email(client, headers, email="alex@example.com")
    other_driver = client.post("/drivers", json={"name": "Other Driver"}, headers=headers).json()

    uniuni = client.post("/clients", json={"name": "UniUni"}, headers=headers).json()

    own_delivery = client.post(
        "/deliveries",
        json={
            "driver_id": driver["id"],
            "client_id": uniuni["id"],
            "batch_date": "2026-07-06",
            "assigned_count": 5,
            "exceptions_count": 0,
        },
        headers=headers,
    ).json()
    other_delivery = client.post(
        "/deliveries",
        json={
            "driver_id": other_driver["id"],
            "client_id": uniuni["id"],
            "batch_date": "2026-07-06",
            "assigned_count": 5,
            "exceptions_count": 0,
        },
        headers=headers,
    ).json()

    token_body = _accept_invite(client, driver["invite_token"])
    driver_headers = {"Authorization": f"Bearer {token_body['access_token']}"}

    resp = client.get("/me/deliveries", headers=driver_headers)
    assert resp.status_code == 200
    ids = {d["id"] for d in resp.json()}
    assert ids == {own_delivery["id"]}

    resp = client.get(
        f"/me/deliveries/{other_delivery['id']}/packages", headers=driver_headers
    )
    assert resp.status_code == 404

    resp = client.post(
        f"/me/deliveries/{own_delivery['id']}/packages",
        json={"tracking_code": "PKG-100", "outcome": "delivered", "pod_scan_code": "SCAN-1"},
        headers=driver_headers,
    )
    assert resp.status_code == 201
    package = resp.json()

    fake_jpeg = io.BytesIO(b"\xff\xd8\xff\xe0" + b"0" * 50)
    resp = client.post(
        f"/me/deliveries/{own_delivery['id']}/packages/{package['id']}/pod-photo",
        headers=driver_headers,
        files={"file": ("proof.jpg", fake_jpeg, "image/jpeg")},
    )
    assert resp.status_code == 200

    resp = client.post(
        f"/me/deliveries/{other_delivery['id']}/packages",
        json={"tracking_code": "PKG-200", "outcome": "delivered"},
        headers=driver_headers,
    )
    assert resp.status_code == 404


def test_driver_pay_report_own_data_only(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver_with_email(client, headers)
    uniuni = client.post("/clients", json={"name": "UniUni"}, headers=headers).json()

    delivery = client.post(
        "/deliveries",
        json={
            "driver_id": driver["id"],
            "client_id": uniuni["id"],
            "batch_date": "2026-07-06",
            "assigned_count": 10,
            "exceptions_count": 0,
        },
        headers=headers,
    ).json()
    client.post(f"/deliveries/{delivery['id']}/validate", headers=headers)

    token_body = _accept_invite(client, driver["invite_token"])
    driver_headers = {"Authorization": f"Bearer {token_body['access_token']}"}

    resp = client.get(
        "/me/pay-report",
        params={"start_date": "2026-07-06", "end_date": "2026-07-12"},
        headers=driver_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["driver_id"] == driver["id"]
    assert body["overall_summary"]["payable_count"] == 10
