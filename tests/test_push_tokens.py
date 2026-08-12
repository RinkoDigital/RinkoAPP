from app.models import PushToken


def test_register_push_token(client, driver_and_headers, db_session):
    driver, headers = driver_and_headers
    resp = client.post("/account/push-token", json={"token": "ExponentPushToken[abc123]"}, headers=headers)
    assert resp.status_code == 204

    stored = db_session.query(PushToken).filter(PushToken.token == "ExponentPushToken[abc123]").first()
    assert stored is not None
    assert str(stored.driver_id) == driver["id"]


def test_registering_same_token_twice_is_idempotent(client, driver_and_headers, db_session):
    _, headers = driver_and_headers
    token = "ExponentPushToken[dup]"
    assert client.post("/account/push-token", json={"token": token}, headers=headers).status_code == 204
    assert client.post("/account/push-token", json={"token": token}, headers=headers).status_code == 204

    count = db_session.query(PushToken).filter(PushToken.token == token).count()
    assert count == 1


def test_reregistering_token_moves_it_to_new_driver(client, driver_and_headers, db_session):
    _, headers = driver_and_headers
    token = "ExponentPushToken[shared-device]"
    client.post("/account/push-token", json={"token": token}, headers=headers)

    other = client.post(
        "/auth/signup", json={"name": "Maria", "email": "maria@example.com", "password": "pass1234"}
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    client.post("/account/push-token", json={"token": token}, headers=other_headers)

    stored = db_session.query(PushToken).filter(PushToken.token == token).first()
    assert str(stored.driver_id) == other["driver"]["id"]


def test_unregister_push_token(client, driver_and_headers, db_session):
    _, headers = driver_and_headers
    token = "ExponentPushToken[bye]"
    client.post("/account/push-token", json={"token": token}, headers=headers)

    resp = client.request("DELETE", "/account/push-token", json={"token": token}, headers=headers)
    assert resp.status_code == 204
    assert db_session.query(PushToken).filter(PushToken.token == token).count() == 0
