import io


def _create_session(client, headers, carrier):
    return client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 50},
        headers=headers,
    ).json()


def test_upload_route_screenshot_evidence(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)

    fake_png = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 50)
    resp = client.post(
        f"/sessions/{session['id']}/evidence",
        headers=headers,
        data={"kind": "route_screenshot", "note": "Assigned route from UniUni app"},
        files={"file": ("route.png", fake_png, "image/png")},
    )
    assert resp.status_code == 201
    evidence = resp.json()
    assert evidence["kind"] == "route_screenshot"
    assert evidence["file_url"].startswith("/uploads/evidence/")
    assert evidence["note"] == "Assigned route from UniUni app"

    photo_resp = client.get(evidence["file_url"])
    assert photo_resp.status_code == 200


def test_upload_evidence_with_gps_location(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)

    fake_png = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 50)
    resp = client.post(
        f"/sessions/{session['id']}/evidence",
        headers=headers,
        data={
            "kind": "completion_record",
            "latitude": "40.712776",
            "longitude": "-74.005974",
            "address": "150 Greenwich St, New York, NY",
            "captured_at": "2026-07-28T14:32:00",
        },
        files={"file": ("proof.png", fake_png, "image/png")},
    )
    assert resp.status_code == 201
    evidence = resp.json()
    assert evidence["latitude"] == 40.712776
    assert evidence["longitude"] == -74.005974
    assert evidence["address"] == "150 Greenwich St, New York, NY"
    assert evidence["captured_at"] == "2026-07-28T14:32:00"


def test_evidence_location_is_optional(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)

    fake_png = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 50)
    resp = client.post(
        f"/sessions/{session['id']}/evidence",
        headers=headers,
        data={"kind": "settlement_statement"},
        files={"file": ("statement.png", fake_png, "image/png")},
    )
    assert resp.status_code == 201
    evidence = resp.json()
    assert evidence["latitude"] is None
    assert evidence["longitude"] is None
    assert evidence["address"] is None
    assert evidence["captured_at"] is None


def test_upload_settlement_statement_pdf(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)

    fake_pdf = io.BytesIO(b"%PDF-1.4" + b"0" * 50)
    resp = client.post(
        f"/sessions/{session['id']}/evidence",
        headers=headers,
        data={"kind": "settlement_statement"},
        files={"file": ("statement.pdf", fake_pdf, "application/pdf")},
    )
    assert resp.status_code == 201
    assert resp.json()["file_url"].endswith(".pdf")


def test_reject_unsupported_evidence_type(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)

    fake_exe = io.BytesIO(b"MZ" + b"0" * 50)
    resp = client.post(
        f"/sessions/{session['id']}/evidence",
        headers=headers,
        data={"kind": "other"},
        files={"file": ("virus.exe", fake_exe, "application/octet-stream")},
    )
    assert resp.status_code == 422


def test_list_evidence_for_session(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)

    for kind in ["route_screenshot", "rate_screenshot"]:
        client.post(
            f"/sessions/{session['id']}/evidence",
            headers=headers,
            data={"kind": kind},
            files={"file": ("f.png", io.BytesIO(b"\x89PNG" + b"0" * 20), "image/png")},
        )

    resp = client.get(f"/sessions/{session['id']}/evidence", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_register_delivered_package(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)

    resp = client.post(
        f"/sessions/{session['id']}/packages",
        json={"tracking_code": "PKG-1", "outcome": "delivered", "pod_scan_code": "SCAN-1"},
        headers=headers,
    )
    assert resp.status_code == 201
    package = resp.json()
    assert package["source"] == "manual"
    assert package["pod_captured_at"] is not None


def test_register_returned_package_requires_reason(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)

    resp = client.post(
        f"/sessions/{session['id']}/packages",
        json={"tracking_code": "PKG-2", "outcome": "returned"},
        headers=headers,
    )
    assert resp.status_code == 422

    resp = client.post(
        f"/sessions/{session['id']}/packages",
        json={
            "tracking_code": "PKG-2",
            "outcome": "returned",
            "return_reason": "wrong_address",
        },
        headers=headers,
    )
    assert resp.status_code == 201


def test_duplicate_tracking_code_rejected(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)
    payload = {"tracking_code": "PKG-DUP", "outcome": "delivered"}

    assert client.post(
        f"/sessions/{session['id']}/packages", json=payload, headers=headers
    ).status_code == 201
    resp = client.post(f"/sessions/{session['id']}/packages", json=payload, headers=headers)
    assert resp.status_code == 409


def test_upload_pod_photo(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)
    package = client.post(
        f"/sessions/{session['id']}/packages",
        json={"tracking_code": "PKG-3", "outcome": "delivered"},
        headers=headers,
    ).json()

    fake_jpeg = io.BytesIO(b"\xff\xd8\xff\xe0" + b"0" * 50)
    resp = client.post(
        f"/sessions/{session['id']}/packages/{package['id']}/pod-photo",
        headers=headers,
        files={"file": ("proof.jpg", fake_jpeg, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["pod_photo_url"].startswith("/uploads/pod/")
