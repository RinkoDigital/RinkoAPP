import io


def _create_session(client, headers, carrier):
    return client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 50},
        headers=headers,
    ).json()


def _upload_evidence(client, headers, session_id, kind="other"):
    return client.post(
        f"/sessions/{session_id}/evidence",
        headers=headers,
        data={"kind": kind},
        files={"file": ("f.png", io.BytesIO(b"\x89PNG" + b"0" * 20), "image/png")},
    )


def test_new_driver_defaults_to_free_plan(client, driver_and_headers):
    _, headers = driver_and_headers
    resp = client.get("/account/plan", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan"] == "free"
    assert body["docx_export"] is False
    assert body["evidence_per_session_limit"] == 3


def test_upgrade_to_pro_lifts_limits(client, driver_and_headers):
    _, headers = driver_and_headers
    resp = client.post("/account/plan", json={"plan": "pro"}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan"] == "pro"
    assert body["docx_export"] is True
    assert body["evidence_per_session_limit"] is None


def test_free_plan_evidence_capped_at_three_per_session(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)

    for _ in range(3):
        resp = _upload_evidence(client, headers, session["id"])
        assert resp.status_code == 201

    resp = _upload_evidence(client, headers, session["id"])
    assert resp.status_code == 402


def test_pro_plan_evidence_has_no_cap(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    client.post("/account/plan", json={"plan": "pro"}, headers=headers)
    session = _create_session(client, headers, carrier)

    for _ in range(5):
        resp = _upload_evidence(client, headers, session["id"])
        assert resp.status_code == 201
