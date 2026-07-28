def test_create_and_list_carriers(client, driver_and_headers):
    _, headers = driver_and_headers
    resp = client.post(
        "/carriers", json={"name": "UniUni", "default_rate_cents": 170}, headers=headers
    )
    assert resp.status_code == 201
    carrier = resp.json()
    assert carrier["name"] == "UniUni"
    assert carrier["default_rate_cents"] == 170

    resp = client.get("/carriers", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_carrier_without_default_rate(client, driver_and_headers):
    _, headers = driver_and_headers
    resp = client.post("/carriers", json={"name": "GOFO"}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["default_rate_cents"] is None


def test_duplicate_carrier_name_rejected(client, driver_and_headers):
    _, headers = driver_and_headers
    payload = {"name": "OnTrac"}
    assert client.post("/carriers", json=payload, headers=headers).status_code == 201
    resp = client.post("/carriers", json=payload, headers=headers)
    assert resp.status_code == 409


def test_carriers_are_scoped_per_driver(client):
    d1 = client.post(
        "/auth/signup", json={"name": "Alex", "email": "alex@example.com", "password": "pass1234"}
    ).json()
    d2 = client.post(
        "/auth/signup", json={"name": "Maria", "email": "maria@example.com", "password": "pass1234"}
    ).json()
    h1 = {"Authorization": f"Bearer {d1['access_token']}"}
    h2 = {"Authorization": f"Bearer {d2['access_token']}"}

    client.post("/carriers", json={"name": "UniUni"}, headers=h1)
    resp = client.get("/carriers", headers=h2)
    assert resp.json() == []
