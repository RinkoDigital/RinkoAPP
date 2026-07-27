def _setup_validated_delivery(client, headers, assigned=130, exceptions=0):
    driver = client.post("/drivers", json={"name": "Alex Silva"}, headers=headers).json()
    uniuni = client.post("/clients", json={"name": "UniUni"}, headers=headers).json()
    delivery = client.post(
        "/deliveries",
        json={
            "driver_id": driver["id"],
            "client_id": uniuni["id"],
            "batch_date": "2026-07-06",
            "assigned_count": assigned,
            "exceptions_count": exceptions,
        },
        headers=headers,
    ).json()

    client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={"tracking_code": "PKG-1", "outcome": "delivered", "pod_scan_code": "SCAN-1"},
        headers=headers,
    )
    client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={"tracking_code": "PKG-2", "outcome": "delivered"},
        headers=headers,
    )

    client.post(f"/deliveries/{delivery['id']}/validate", headers=headers)
    return driver, uniuni, delivery


def test_proof_unavailable_before_validation(client, company_and_key):
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

    resp = client.get(f"/deliveries/{delivery['id']}/proof", headers=headers)
    assert resp.status_code == 409


def test_proof_available_once_validated_even_if_unpaid(client, company_and_key):
    company, headers = company_and_key
    driver, uniuni, delivery = _setup_validated_delivery(client, headers)

    resp = client.get(f"/deliveries/{delivery['id']}/proof", headers=headers)
    assert resp.status_code == 200
    proof = resp.json()
    assert proof["proof_number"].startswith("PRF-")
    assert proof["driver_name"] == "Alex Silva"
    assert proof["client_name"] == "UniUni"
    assert proof["payable_count"] == 130
    assert proof["payment_status"] == "pending"
    assert proof["paid_amount_cents"] is None
    assert proof["paid_at"] is None
    assert proof["packages_logged"] == 2
    assert proof["packages_with_scan_code"] == 1


def test_proof_reflects_payment_once_paid(client, company_and_key):
    company, headers = company_and_key
    driver, uniuni, delivery = _setup_validated_delivery(client, headers)
    client.post(f"/deliveries/{delivery['id']}/mark-paid", json={}, headers=headers)

    resp = client.get(f"/deliveries/{delivery['id']}/proof", headers=headers)
    assert resp.status_code == 200
    proof = resp.json()
    assert proof["payment_status"] == "paid"
    assert proof["paid_amount_cents"] == company["default_rate_cents"] * 130
    assert proof["paid_at"] is not None


def test_proof_docx_download_before_payment(client, company_and_key):
    company, headers = company_and_key
    driver, uniuni, delivery = _setup_validated_delivery(client, headers)

    resp = client.get(f"/deliveries/{delivery['id']}/proof.docx", headers=headers)
    assert resp.status_code == 200
    assert (
        resp.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert resp.content[:2] == b"PK"


def test_driver_can_view_own_proof_before_payment(client, company_and_key):
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

    login = client.post(
        "/auth/driver/accept-invite",
        json={"invite_token": driver["invite_token"], "password": "s3cret-pass"},
    ).json()
    driver_headers = {"Authorization": f"Bearer {login['access_token']}"}

    resp = client.get(f"/me/deliveries/{delivery['id']}/proof", headers=driver_headers)
    assert resp.status_code == 200
    assert resp.json()["payment_status"] == "pending"

    resp = client.get(f"/me/deliveries/{delivery['id']}/proof.docx", headers=driver_headers)
    assert resp.status_code == 200
    assert resp.content[:2] == b"PK"


def test_driver_cannot_view_other_drivers_proof(client, company_and_key):
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

    login = client.post(
        "/auth/driver/accept-invite",
        json={"invite_token": driver["invite_token"], "password": "s3cret-pass"},
    ).json()
    driver_headers = {"Authorization": f"Bearer {login['access_token']}"}

    resp = client.get(f"/me/deliveries/{other_delivery['id']}/proof", headers=driver_headers)
    assert resp.status_code == 404
