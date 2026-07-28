def test_start_session_uses_carrier_default_rate(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    resp = client.post(
        "/sessions",
        json={
            "carrier_id": carrier["id"],
            "route_id": "SEA-4821",
            "service_date": "2026-07-28",
            "packages_assigned": 147,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    session = resp.json()
    assert session["agreed_rate_cents"] == 170
    assert session["status"] == "open"
    assert session["expected_gross_cents"] is None
    assert session["packages_completed"] == 147  # no exceptions yet


def test_start_session_without_rate_and_no_carrier_default_fails(client, driver_and_headers):
    _, headers = driver_and_headers
    carrier = client.post("/carriers", json={"name": "GOFO"}, headers=headers).json()
    resp = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_start_session_explicit_rate_overrides_default(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    resp = client.post(
        "/sessions",
        json={
            "carrier_id": carrier["id"],
            "service_date": "2026-07-28",
            "agreed_rate_cents": 200,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["agreed_rate_cents"] == 200


def test_close_session_computes_expected_gross(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = client.post(
        "/sessions",
        json={
            "carrier_id": carrier["id"],
            "route_id": "SEA-4821",
            "service_date": "2026-07-28",
            "packages_assigned": 147,
        },
        headers=headers,
    ).json()

    resp = client.post(
        f"/sessions/{session['id']}/close",
        json={"packages_assigned": 147, "exceptions_count": 6, "mileage": 83.4},
        headers=headers,
    )
    assert resp.status_code == 200
    closed = resp.json()
    assert closed["status"] == "closed"
    assert closed["packages_completed"] == 141
    assert closed["expected_gross_cents"] == 141 * 170
    assert closed["mileage"] == 83.4
    assert closed["payment_status"] == "pending"


def test_cannot_close_session_twice(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 50},
        headers=headers,
    ).json()
    client.post(f"/sessions/{session['id']}/close", json={"exceptions_count": 0}, headers=headers)
    resp = client.post(f"/sessions/{session['id']}/close", json={"exceptions_count": 0}, headers=headers)
    assert resp.status_code == 409


def test_cannot_record_payment_before_close(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 50},
        headers=headers,
    ).json()
    resp = client.post(
        f"/sessions/{session['id']}/record-payment",
        json={"payment_received_cents": 8500},
        headers=headers,
    )
    assert resp.status_code == 409


def test_record_partial_payment_computes_difference(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = client.post(
        "/sessions",
        json={
            "carrier_id": carrier["id"],
            "service_date": "2026-07-28",
            "packages_assigned": 147,
        },
        headers=headers,
    ).json()
    client.post(
        f"/sessions/{session['id']}/close",
        json={"packages_assigned": 147, "exceptions_count": 6},
        headers=headers,
    )
    # expected_gross = 141 * 170 = 23970

    resp = client.post(
        f"/sessions/{session['id']}/record-payment",
        json={"payment_received_cents": 21960},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["payment_status"] == "partial"
    assert body["difference_cents"] == 21960 - 23970
    assert body["outstanding_cents"] == 23970 - 21960


def test_record_full_payment_marks_received(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 50},
        headers=headers,
    ).json()
    client.post(
        f"/sessions/{session['id']}/close", json={"exceptions_count": 0}, headers=headers
    )
    resp = client.post(
        f"/sessions/{session['id']}/record-payment",
        json={"payment_received_cents": 50 * 170},
        headers=headers,
    )
    body = resp.json()
    assert body["payment_status"] == "received"
    assert body["outstanding_cents"] == 0


def test_list_sessions_filters_by_status(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    open_session = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 10},
        headers=headers,
    ).json()
    closed_session = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-29", "packages_assigned": 20},
        headers=headers,
    ).json()
    client.post(f"/sessions/{closed_session['id']}/close", json={"exceptions_count": 0}, headers=headers)

    resp = client.get("/sessions", params={"status": "open"}, headers=headers)
    ids = {s["id"] for s in resp.json()}
    assert ids == {open_session["id"]}


def test_sessions_scoped_per_driver(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 10},
        headers=headers,
    )
    other = client.post(
        "/auth/signup", json={"name": "Maria", "email": "maria@example.com", "password": "pass1234"}
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    resp = client.get("/sessions", headers=other_headers)
    assert resp.json() == []


def test_export_csv(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 10},
        headers=headers,
    ).json()
    client.post(f"/sessions/{session['id']}/close", json={"exceptions_count": 0}, headers=headers)

    resp = client.get("/sessions/export.csv", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "UniUni" in resp.text
