def _create_driver(client, headers, name="Jane Driver"):
    resp = client.post("/drivers", json={"name": name}, headers=headers)
    assert resp.status_code == 200
    return resp.json()


def test_register_validate_and_report_flow(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver(client, headers)

    resp = client.post(
        "/deliveries",
        json={"driver_id": driver["id"], "external_id": "PKG-1", "package_count": 3},
        headers=headers,
    )
    assert resp.status_code == 201
    delivery = resp.json()
    assert delivery["status"] == "pending"
    assert delivery["amount_due_cents"] is None
    assert delivery["rate_cents"] == company["default_rate_cents"]

    resp = client.post(f"/deliveries/{delivery['id']}/validate", headers=headers)
    assert resp.status_code == 200
    validated = resp.json()
    assert validated["status"] == "validated"
    assert validated["amount_due_cents"] == company["default_rate_cents"] * 3

    resp = client.get(f"/reports/drivers/{driver['id']}", headers=headers)
    assert resp.status_code == 200
    report = resp.json()
    assert report["validated_deliveries"] == 1
    assert report["total_packages"] == 3
    assert report["amount_due_cents"] == company["default_rate_cents"] * 3

    resp = client.get("/reports/summary", headers=headers)
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["total_deliveries"] == 1
    assert summary["validated"] == 1
    assert summary["pending"] == 0
    assert summary["total_amount_due_cents"] == company["default_rate_cents"] * 3


def test_reject_delivery_excludes_it_from_payment(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver(client, headers)

    resp = client.post(
        "/deliveries",
        json={"driver_id": driver["id"], "external_id": "PKG-2"},
        headers=headers,
    )
    delivery = resp.json()

    resp = client.post(
        f"/deliveries/{delivery['id']}/reject",
        json={"reason": "Package damaged on arrival"},
        headers=headers,
    )
    assert resp.status_code == 200
    rejected = resp.json()
    assert rejected["status"] == "rejected"
    assert rejected["amount_due_cents"] is None

    resp = client.get(f"/reports/drivers/{driver['id']}", headers=headers)
    report = resp.json()
    assert report["validated_deliveries"] == 0
    assert report["amount_due_cents"] == 0


def test_cannot_validate_delivery_twice(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver(client, headers)
    resp = client.post(
        "/deliveries",
        json={"driver_id": driver["id"], "external_id": "PKG-3"},
        headers=headers,
    )
    delivery_id = resp.json()["id"]

    assert client.post(f"/deliveries/{delivery_id}/validate", headers=headers).status_code == 200
    resp = client.post(f"/deliveries/{delivery_id}/validate", headers=headers)
    assert resp.status_code == 409


def test_duplicate_external_id_rejected(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver(client, headers)
    payload = {"driver_id": driver["id"], "external_id": "PKG-DUP"}

    assert client.post("/deliveries", json=payload, headers=headers).status_code == 201
    resp = client.post("/deliveries", json=payload, headers=headers)
    assert resp.status_code == 409


def test_invalid_api_key_rejected(client):
    resp = client.get("/deliveries", headers={"x-api-key": "not-a-real-key"})
    assert resp.status_code == 401


def test_company_creation_requires_admin_key(client):
    resp = client.post("/companies", json={"name": "No Auth Co"})
    assert resp.status_code == 422  # missing header

    resp = client.post(
        "/companies", json={"name": "No Auth Co"}, headers={"x-admin-key": "wrong"}
    )
    assert resp.status_code == 401
