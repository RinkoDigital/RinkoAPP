def _setup_paid_delivery(client, headers):
    driver = client.post("/drivers", json={"name": "Alex Silva"}, headers=headers).json()
    uniuni = client.post("/clients", json={"name": "UniUni"}, headers=headers).json()
    delivery = client.post(
        "/deliveries",
        json={
            "driver_id": driver["id"],
            "client_id": uniuni["id"],
            "batch_date": "2026-07-06",
            "assigned_count": 130,
            "exceptions_count": 0,
        },
        headers=headers,
    ).json()

    client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={"tracking_code": "PKG-1", "outcome": "delivered", "pod_scan_code": "SCAN-1"},
        headers=headers,
    )
    package_2 = client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={"tracking_code": "PKG-2", "outcome": "delivered"},
        headers=headers,
    ).json()

    client.post(f"/deliveries/{delivery['id']}/validate", headers=headers)
    client.post(f"/deliveries/{delivery['id']}/mark-paid", json={}, headers=headers)

    return driver, uniuni, delivery, package_2


def test_receipt_requires_paid_delivery(client, company_and_key):
    company, headers = company_and_key
    driver = client.post("/drivers", json={"name": "Alex Silva"}, headers=headers).json()
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

    resp = client.get(f"/deliveries/{delivery['id']}/receipt", headers=headers)
    assert resp.status_code == 409

    client.post(f"/deliveries/{delivery['id']}/validate", headers=headers)
    resp = client.get(f"/deliveries/{delivery['id']}/receipt", headers=headers)
    assert resp.status_code == 409


def test_receipt_reflects_amount_and_proof_of_delivery(client, company_and_key):
    company, headers = company_and_key
    driver, uniuni, delivery, _ = _setup_paid_delivery(client, headers)

    resp = client.get(f"/deliveries/{delivery['id']}/receipt", headers=headers)
    assert resp.status_code == 200
    receipt = resp.json()
    assert receipt["receipt_number"].startswith("RCT-")
    assert receipt["driver_name"] == "Alex Silva"
    assert receipt["client_name"] == "UniUni"
    assert receipt["payable_count"] == 130
    assert receipt["paid_amount_cents"] == company["default_rate_cents"] * 130
    assert receipt["packages_logged"] == 2
    assert receipt["packages_with_scan_code"] == 1
    assert receipt["packages_with_photo"] == 0


def test_receipt_docx_download(client, company_and_key):
    company, headers = company_and_key
    driver, uniuni, delivery, _ = _setup_paid_delivery(client, headers)

    resp = client.get(f"/deliveries/{delivery['id']}/receipt.docx", headers=headers)
    assert resp.status_code == 200
    assert (
        resp.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert resp.content[:2] == b"PK"


def test_driver_can_view_own_receipt(client, company_and_key):
    company, headers = company_and_key
    driver_resp = client.post(
        "/drivers", json={"name": "Alex Silva", "email": "alex@example.com"}, headers=headers
    )
    driver = driver_resp.json()
    uniuni = client.post("/clients", json={"name": "UniUni"}, headers=headers).json()
    delivery = client.post(
        "/deliveries",
        json={
            "driver_id": driver["id"],
            "client_id": uniuni["id"],
            "batch_date": "2026-07-06",
            "assigned_count": 50,
            "exceptions_count": 0,
        },
        headers=headers,
    ).json()
    client.post(f"/deliveries/{delivery['id']}/validate", headers=headers)
    client.post(f"/deliveries/{delivery['id']}/mark-paid", json={}, headers=headers)

    login = client.post(
        "/auth/driver/accept-invite",
        json={"invite_token": driver["invite_token"], "password": "s3cret-pass"},
    ).json()
    driver_headers = {"Authorization": f"Bearer {login['access_token']}"}

    resp = client.get(f"/me/deliveries/{delivery['id']}/receipt", headers=driver_headers)
    assert resp.status_code == 200
    assert resp.json()["payable_count"] == 50

    resp = client.get(f"/me/deliveries/{delivery['id']}/receipt.docx", headers=driver_headers)
    assert resp.status_code == 200
    assert resp.content[:2] == b"PK"


def test_driver_cannot_view_other_drivers_receipt(client, company_and_key):
    company, headers = company_and_key
    driver_resp = client.post(
        "/drivers", json={"name": "Alex Silva", "email": "alex@example.com"}, headers=headers
    )
    driver = driver_resp.json()
    other_driver = client.post("/drivers", json={"name": "Maria Costa"}, headers=headers).json()
    uniuni = client.post("/clients", json={"name": "UniUni"}, headers=headers).json()

    other_delivery = client.post(
        "/deliveries",
        json={
            "driver_id": other_driver["id"],
            "client_id": uniuni["id"],
            "batch_date": "2026-07-06",
            "assigned_count": 20,
            "exceptions_count": 0,
        },
        headers=headers,
    ).json()
    client.post(f"/deliveries/{other_delivery['id']}/validate", headers=headers)
    client.post(f"/deliveries/{other_delivery['id']}/mark-paid", json={}, headers=headers)

    login = client.post(
        "/auth/driver/accept-invite",
        json={"invite_token": driver["invite_token"], "password": "s3cret-pass"},
    ).json()
    driver_headers = {"Authorization": f"Bearer {login['access_token']}"}

    resp = client.get(f"/me/deliveries/{other_delivery['id']}/receipt", headers=driver_headers)
    assert resp.status_code == 404
