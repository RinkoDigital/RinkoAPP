import io


def _setup_delivery(client, headers):
    driver = client.post("/drivers", json={"name": "Jane Driver"}, headers=headers).json()
    uniuni = client.post("/clients", json={"name": "UniUni"}, headers=headers).json()
    delivery = client.post(
        "/deliveries",
        json={
            "driver_id": driver["id"],
            "client_id": uniuni["id"],
            "batch_date": "2026-07-06",
            "assigned_count": 3,
            "exceptions_count": 1,
        },
        headers=headers,
    ).json()
    return driver, uniuni, delivery


def test_register_delivered_package(client, company_and_key):
    company, headers = company_and_key
    _, _, delivery = _setup_delivery(client, headers)

    resp = client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={
            "tracking_code": "PKG-001",
            "outcome": "delivered",
            "pod_scan_code": "SCAN-9001",
            "pod_latitude": 47.6062,
            "pod_longitude": -122.3321,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    package = resp.json()
    assert package["outcome"] == "delivered"
    assert package["pod_scan_code"] == "SCAN-9001"
    assert package["pod_captured_at"] is not None
    assert package["pod_photo_url"] is None
    assert package["return_reason"] is None
    assert package["source"] == "manual"
    assert package["external_reference"] is None


def test_admin_can_register_package_from_external_platform(client, company_and_key):
    company, headers = company_and_key
    _, _, delivery = _setup_delivery(client, headers)

    resp = client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={
            "tracking_code": "PKG-EXT-1",
            "outcome": "delivered",
            "source": "uniuni",
            "external_reference": "uniuni-order-88213",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    package = resp.json()
    assert package["source"] == "uniuni"
    assert package["external_reference"] == "uniuni-order-88213"


def test_manual_source_ignores_external_reference(client, company_and_key):
    company, headers = company_and_key
    _, _, delivery = _setup_delivery(client, headers)

    resp = client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={
            "tracking_code": "PKG-MAN-1",
            "outcome": "delivered",
            "external_reference": "should-be-dropped",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    package = resp.json()
    assert package["source"] == "manual"
    assert package["external_reference"] is None


def test_register_returned_package_requires_reason(client, company_and_key):
    company, headers = company_and_key
    _, _, delivery = _setup_delivery(client, headers)

    resp = client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={"tracking_code": "PKG-002", "outcome": "returned"},
        headers=headers,
    )
    assert resp.status_code == 422

    resp = client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={
            "tracking_code": "PKG-002",
            "outcome": "returned",
            "return_reason": "wrong_address",
            "return_note": "Address does not exist",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    package = resp.json()
    assert package["outcome"] == "returned"
    assert package["return_reason"] == "wrong_address"
    assert package["pod_captured_at"] is None


def test_delivered_package_rejects_return_fields(client, company_and_key):
    company, headers = company_and_key
    _, _, delivery = _setup_delivery(client, headers)

    resp = client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={
            "tracking_code": "PKG-003",
            "outcome": "delivered",
            "return_reason": "damaged",
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_duplicate_tracking_code_in_same_batch_rejected(client, company_and_key):
    company, headers = company_and_key
    _, _, delivery = _setup_delivery(client, headers)
    payload = {"tracking_code": "PKG-DUP", "outcome": "delivered"}

    assert client.post(
        f"/deliveries/{delivery['id']}/packages", json=payload, headers=headers
    ).status_code == 201
    resp = client.post(f"/deliveries/{delivery['id']}/packages", json=payload, headers=headers)
    assert resp.status_code == 409


def test_upload_pod_photo(client, company_and_key):
    company, headers = company_and_key
    _, _, delivery = _setup_delivery(client, headers)

    package = client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={"tracking_code": "PKG-004", "outcome": "delivered"},
        headers=headers,
    ).json()

    fake_jpeg = io.BytesIO(b"\xff\xd8\xff\xe0" + b"0" * 100)
    resp = client.post(
        f"/deliveries/{delivery['id']}/packages/{package['id']}/pod-photo",
        headers=headers,
        files={"file": ("proof.jpg", fake_jpeg, "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["pod_photo_url"].startswith("/uploads/")

    photo_resp = client.get(body["pod_photo_url"])
    assert photo_resp.status_code == 200


def test_pod_photo_rejected_for_returned_package(client, company_and_key):
    company, headers = company_and_key
    _, _, delivery = _setup_delivery(client, headers)

    package = client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={
            "tracking_code": "PKG-005",
            "outcome": "returned",
            "return_reason": "refused",
        },
        headers=headers,
    ).json()

    fake_jpeg = io.BytesIO(b"\xff\xd8\xff\xe0" + b"0" * 100)
    resp = client.post(
        f"/deliveries/{delivery['id']}/packages/{package['id']}/pod-photo",
        headers=headers,
        files={"file": ("proof.jpg", fake_jpeg, "image/jpeg")},
    )
    assert resp.status_code == 409


def test_list_packages_for_batch(client, company_and_key):
    company, headers = company_and_key
    _, _, delivery = _setup_delivery(client, headers)

    client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={"tracking_code": "PKG-006", "outcome": "delivered"},
        headers=headers,
    )
    client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={
            "tracking_code": "PKG-007",
            "outcome": "returned",
            "return_reason": "damaged",
        },
        headers=headers,
    )

    resp = client.get(f"/deliveries/{delivery['id']}/packages", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_cannot_add_package_to_rejected_delivery(client, company_and_key):
    company, headers = company_and_key
    _, _, delivery = _setup_delivery(client, headers)
    client.post(
        f"/deliveries/{delivery['id']}/reject", json={"reason": "bad batch"}, headers=headers
    )

    resp = client.post(
        f"/deliveries/{delivery['id']}/packages",
        json={"tracking_code": "PKG-008", "outcome": "delivered"},
        headers=headers,
    )
    assert resp.status_code == 409
