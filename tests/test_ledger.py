def test_ledger_empty_when_no_closed_sessions(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 10},
        headers=headers,
    )
    resp = client.get("/ledger", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"outstanding_total_cents": 0, "entries": []}


def test_ledger_shows_outstanding_for_unpaid_and_partial(client, driver_and_headers, carrier):
    _, headers = driver_and_headers

    unpaid = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-06", "packages_assigned": 50},
        headers=headers,
    ).json()
    client.post(f"/sessions/{unpaid['id']}/close", json={"exceptions_count": 0}, headers=headers)
    # expected = 50 * 170 = 8500, unpaid

    partial = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-07", "packages_assigned": 100},
        headers=headers,
    ).json()
    client.post(f"/sessions/{partial['id']}/close", json={"exceptions_count": 0}, headers=headers)
    client.post(
        f"/sessions/{partial['id']}/record-payment",
        json={"payment_received_cents": 15000},
        headers=headers,
    )
    # expected = 100 * 170 = 17000, received 15000, outstanding 2000

    paid = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-08", "packages_assigned": 20},
        headers=headers,
    ).json()
    client.post(f"/sessions/{paid['id']}/close", json={"exceptions_count": 0}, headers=headers)
    client.post(
        f"/sessions/{paid['id']}/record-payment",
        json={"payment_received_cents": 20 * 170},
        headers=headers,
    )

    resp = client.get("/ledger", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["outstanding_total_cents"] == 8500 + 2000
    session_ids = {e["session_id"] for e in body["entries"]}
    assert session_ids == {unpaid["id"], partial["id"]}
    assert paid["id"] not in session_ids


def test_ledger_scoped_per_driver(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 10},
        headers=headers,
    ).json()
    client.post(f"/sessions/{session['id']}/close", json={"exceptions_count": 0}, headers=headers)

    other = client.post(
        "/auth/signup", json={"name": "Maria", "email": "maria@example.com", "password": "pass1234"}
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    resp = client.get("/ledger", headers=other_headers)
    assert resp.json() == {"outstanding_total_cents": 0, "entries": []}
