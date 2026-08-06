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


def test_new_driver_gets_full_access_while_billing_is_disabled(client, driver_and_headers):
    _, headers = driver_and_headers
    resp = client.get("/account/plan", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan"] == "free"
    assert body["docx_export"] is True
    assert body["evidence_per_session_limit"] is None


def test_switching_plan_stays_unrestricted(client, driver_and_headers):
    _, headers = driver_and_headers
    resp = client.post("/account/plan", json={"plan": "pro"}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan"] == "pro"
    assert body["docx_export"] is True
    assert body["evidence_per_session_limit"] is None


def test_evidence_has_no_cap_on_default_plan(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)

    for _ in range(5):
        resp = _upload_evidence(client, headers, session["id"])
        assert resp.status_code == 201
