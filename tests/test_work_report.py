def _create_and_close_session(client, headers, carrier, **overrides):
    payload = {
        "carrier_id": carrier["id"],
        "route_id": "SEA-4821",
        "service_date": "2026-07-28",
        "packages_assigned": 147,
    }
    payload.update(overrides)
    session = client.post("/sessions", json=payload, headers=headers).json()
    client.post(
        f"/sessions/{session['id']}/close",
        json={"packages_assigned": 147, "exceptions_count": 6, "mileage": 83.4},
        headers=headers,
    )
    return session


def test_report_unavailable_before_close(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 10},
        headers=headers,
    ).json()
    resp = client.get(f"/sessions/{session['id']}/work-report", headers=headers)
    assert resp.status_code == 409


def test_report_reflects_work_and_pending_payment(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_and_close_session(client, headers, carrier)

    client.post(
        f"/sessions/{session['id']}/evidence",
        headers=headers,
        data={"kind": "route_screenshot"},
        files={"file": ("r.png", __import__("io").BytesIO(b"\x89PNG" + b"0" * 20), "image/png")},
    )

    resp = client.get(f"/sessions/{session['id']}/work-report", headers=headers)
    assert resp.status_code == 200
    report = resp.json()
    assert report["report_number"].startswith("WR-")
    assert report["carrier_name"] == "UniUni"
    assert report["route_id"] == "SEA-4821"
    assert report["work_record"]["packages_completed"] == 141
    assert report["work_record"]["mileage"] == 83.4
    assert report["compensation"]["expected_gross_cents"] == 141 * 170
    assert report["compensation"]["payment_status"] == "pending"
    assert report["compensation"]["difference_cents"] is None
    assert len(report["supporting_records"]) == 1


def test_report_shows_difference_after_partial_payment(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_and_close_session(client, headers, carrier)
    client.post(
        f"/sessions/{session['id']}/record-payment",
        json={"payment_received_cents": 21960},
        headers=headers,
    )

    resp = client.get(f"/sessions/{session['id']}/work-report", headers=headers)
    report = resp.json()
    assert report["compensation"]["payment_status"] == "partial"
    assert report["compensation"]["difference_cents"] == 21960 - 141 * 170


def test_report_docx_download(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_and_close_session(client, headers, carrier)

    resp = client.get(f"/sessions/{session['id']}/work-report.docx", headers=headers)
    assert resp.status_code == 200
    assert (
        resp.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert resp.content[:2] == b"PK"


def test_driver_cannot_view_other_drivers_report(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_and_close_session(client, headers, carrier)

    other = client.post(
        "/auth/signup", json={"name": "Maria", "email": "maria@example.com", "password": "pass1234"}
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    resp = client.get(f"/sessions/{session['id']}/work-report", headers=other_headers)
    assert resp.status_code == 404
