def _create_driver(client, headers, name="Jane Driver"):
    resp = client.post("/drivers", json={"name": name}, headers=headers)
    assert resp.status_code == 200
    return resp.json()


def _create_delivery_client(client, headers, name="UniUni", default_rate_cents=None):
    resp = client.post(
        "/clients", json={"name": name, "default_rate_cents": default_rate_cents}, headers=headers
    )
    assert resp.status_code == 200
    return resp.json()


def _register_batch(client, headers, driver_id, client_id, batch_date, assigned, exceptions=0):
    resp = client.post(
        "/deliveries",
        json={
            "driver_id": driver_id,
            "client_id": client_id,
            "batch_date": batch_date,
            "assigned_count": assigned,
            "exceptions_count": exceptions,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


def test_register_validate_and_pay_report_flow(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver(client, headers)
    uniuni = _create_delivery_client(client, headers, "UniUni")

    delivery = _register_batch(client, headers, driver["id"], uniuni["id"], "2026-07-06", 138, 8)
    assert delivery["status"] == "pending"
    assert delivery["payable_count"] == 130
    assert delivery["amount_due_cents"] is None
    assert delivery["rate_cents"] == company["default_rate_cents"]

    resp = client.post(f"/deliveries/{delivery['id']}/validate", headers=headers)
    assert resp.status_code == 200
    validated = resp.json()
    assert validated["status"] == "validated"
    assert validated["amount_due_cents"] == company["default_rate_cents"] * 130

    resp = client.get(
        f"/reports/drivers/{driver['id']}/pay-report",
        params={"start_date": "2026-07-06", "end_date": "2026-07-12"},
        headers=headers,
    )
    assert resp.status_code == 200
    report = resp.json()
    assert len(report["delivery_detail"]) == 1
    assert report["delivery_detail"][0]["payable_count"] == 130
    assert report["client_summary"][0]["client_name"] == "UniUni"
    assert report["overall_summary"]["payable_count"] == 130
    assert report["overall_summary"]["total_compensation_cents"] == company["default_rate_cents"] * 130
    assert report["payment_reconciliation"]["total_earned_cents"] == company["default_rate_cents"] * 130
    assert report["payment_reconciliation"]["already_paid_cents"] == 0
    assert report["payment_reconciliation"]["outstanding_balance_cents"] == company["default_rate_cents"] * 130


def test_mark_paid_updates_reconciliation(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver(client, headers)
    gofo = _create_delivery_client(client, headers, "GOFO")

    delivery = _register_batch(client, headers, driver["id"], gofo["id"], "2026-07-06", 122, 2)
    client.post(f"/deliveries/{delivery['id']}/validate", headers=headers)

    resp = client.post(f"/deliveries/{delivery['id']}/mark-paid", json={}, headers=headers)
    assert resp.status_code == 200
    paid = resp.json()
    assert paid["payment_status"] == "paid"
    assert paid["paid_amount_cents"] == company["default_rate_cents"] * 120

    resp = client.get(
        f"/reports/drivers/{driver['id']}/pay-report",
        params={"start_date": "2026-07-06", "end_date": "2026-07-06"},
        headers=headers,
    )
    report = resp.json()
    expected = company["default_rate_cents"] * 120
    assert report["payment_reconciliation"]["already_paid_cents"] == expected
    assert report["payment_reconciliation"]["outstanding_balance_cents"] == 0
    assert len(report["payment_reconciliation"]["paid_items"]) == 1


def test_cannot_mark_paid_before_validation(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver(client, headers)
    gofo = _create_delivery_client(client, headers, "GOFO")
    delivery = _register_batch(client, headers, driver["id"], gofo["id"], "2026-07-06", 50)

    resp = client.post(f"/deliveries/{delivery['id']}/mark-paid", json={}, headers=headers)
    assert resp.status_code == 409


def test_reject_delivery_excludes_it_from_payment(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver(client, headers)
    uniuni = _create_delivery_client(client, headers, "UniUni")
    delivery = _register_batch(client, headers, driver["id"], uniuni["id"], "2026-07-07", 50)

    resp = client.post(
        f"/deliveries/{delivery['id']}/reject",
        json={"reason": "Package damaged on arrival"},
        headers=headers,
    )
    assert resp.status_code == 200
    rejected = resp.json()
    assert rejected["status"] == "rejected"
    assert rejected["amount_due_cents"] is None

    resp = client.get(
        f"/reports/drivers/{driver['id']}/pay-report",
        params={"start_date": "2026-07-07", "end_date": "2026-07-07"},
        headers=headers,
    )
    report = resp.json()
    assert report["delivery_detail"] == []
    assert report["overall_summary"]["total_compensation_cents"] == 0


def test_cannot_validate_delivery_twice(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver(client, headers)
    uniuni = _create_delivery_client(client, headers, "UniUni")
    delivery = _register_batch(client, headers, driver["id"], uniuni["id"], "2026-07-08", 60)

    assert client.post(f"/deliveries/{delivery['id']}/validate", headers=headers).status_code == 200
    resp = client.post(f"/deliveries/{delivery['id']}/validate", headers=headers)
    assert resp.status_code == 409


def test_duplicate_batch_rejected(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver(client, headers)
    uniuni = _create_delivery_client(client, headers, "UniUni")

    resp = client.post(
        "/deliveries",
        json={
            "driver_id": driver["id"],
            "client_id": uniuni["id"],
            "batch_date": "2026-07-09",
            "assigned_count": 60,
            "exceptions_count": 0,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    resp = client.post(
        "/deliveries",
        json={
            "driver_id": driver["id"],
            "client_id": uniuni["id"],
            "batch_date": "2026-07-09",
            "assigned_count": 10,
            "exceptions_count": 0,
        },
        headers=headers,
    )
    assert resp.status_code == 409


def test_client_specific_rate_overrides_company_default(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver(client, headers)
    premium_client = _create_delivery_client(client, headers, "PremiumCo", default_rate_cents=10)

    delivery = _register_batch(client, headers, driver["id"], premium_client["id"], "2026-07-10", 20)
    assert delivery["rate_cents"] == 10


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


def test_pay_report_docx_download(client, company_and_key):
    company, headers = company_and_key
    driver = _create_driver(client, headers)
    uniuni = _create_delivery_client(client, headers, "UniUni")
    delivery = _register_batch(client, headers, driver["id"], uniuni["id"], "2026-07-06", 100, 5)
    client.post(f"/deliveries/{delivery['id']}/validate", headers=headers)

    resp = client.get(
        f"/reports/drivers/{driver['id']}/pay-report.docx",
        params={"start_date": "2026-07-06", "end_date": "2026-07-12"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert (
        resp.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert resp.content[:2] == b"PK"  # docx is a zip archive
