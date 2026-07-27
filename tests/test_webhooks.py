import pytest


@pytest.fixture
def webhook_setup(client, admin_headers):
    company_resp = client.post(
        "/companies",
        json={"name": "Rinko Delivery LLC", "default_rate_cents": 170},
        headers=admin_headers,
    )
    company = company_resp.json()
    headers = {"x-api-key": company["api_key"]}

    driver = client.post(
        "/drivers",
        json={"name": "Alex Silva", "external_id": "uniuni-driver-42"},
        headers=headers,
    ).json()
    client.post("/clients", json={"name": "UniUni"}, headers=headers)

    return {
        "company_id": company["id"],
        "webhook_secret": company["webhook_secret"],
        "driver": driver,
        "headers": headers,
    }


def _event(**overrides):
    payload = {
        "driver_external_id": "uniuni-driver-42",
        "client_name": "UniUni",
        "batch_date": "2026-07-06",
        "tracking_code": "UNI-PKG-1",
        "outcome": "delivered",
        "pod_photo_url": "https://uniuni.example.com/pod/abc123.jpg",
        "external_reference": "uniuni-event-abc123",
    }
    payload.update(overrides)
    return payload


def test_webhook_creates_delivery_and_package(client, webhook_setup):
    resp = client.post(
        f"/webhooks/{webhook_setup['company_id']}/uniuni",
        json=_event(),
        headers={"x-webhook-secret": webhook_setup["webhook_secret"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "created"

    deliveries = client.get("/deliveries", headers=webhook_setup["headers"]).json()
    assert len(deliveries) == 1
    assert deliveries[0]["assigned_count"] == 1
    assert deliveries[0]["exceptions_count"] == 0
    assert deliveries[0]["status"] == "pending"

    packages = client.get(
        f"/deliveries/{deliveries[0]['id']}/packages", headers=webhook_setup["headers"]
    ).json()
    assert len(packages) == 1
    assert packages[0]["source"] == "uniuni"
    assert packages[0]["external_reference"] == "uniuni-event-abc123"
    assert packages[0]["pod_photo_url"] == "https://uniuni.example.com/pod/abc123.jpg"


def test_webhook_returned_package_increments_exceptions(client, webhook_setup):
    resp = client.post(
        f"/webhooks/{webhook_setup['company_id']}/gofo",
        json=_event(
            tracking_code="UNI-PKG-2",
            outcome="returned",
            return_reason="damaged",
            return_note="Box crushed in transit",
            pod_photo_url=None,
        ),
        headers={"x-webhook-secret": webhook_setup["webhook_secret"]},
    )
    assert resp.status_code == 200

    deliveries = client.get("/deliveries", headers=webhook_setup["headers"]).json()
    assert deliveries[0]["assigned_count"] == 1
    assert deliveries[0]["exceptions_count"] == 1


def test_webhook_accumulates_multiple_events_same_batch(client, webhook_setup):
    secret_headers = {"x-webhook-secret": webhook_setup["webhook_secret"]}
    client.post(
        f"/webhooks/{webhook_setup['company_id']}/uniuni",
        json=_event(tracking_code="UNI-PKG-A"),
        headers=secret_headers,
    )
    client.post(
        f"/webhooks/{webhook_setup['company_id']}/uniuni",
        json=_event(tracking_code="UNI-PKG-B", outcome="returned", return_reason="refused"),
        headers=secret_headers,
    )

    deliveries = client.get("/deliveries", headers=webhook_setup["headers"]).json()
    assert len(deliveries) == 1
    assert deliveries[0]["assigned_count"] == 2
    assert deliveries[0]["exceptions_count"] == 1


def test_webhook_duplicate_event_is_idempotent(client, webhook_setup):
    secret_headers = {"x-webhook-secret": webhook_setup["webhook_secret"]}
    event = _event()

    first = client.post(
        f"/webhooks/{webhook_setup['company_id']}/uniuni", json=event, headers=secret_headers
    )
    second = client.post(
        f"/webhooks/{webhook_setup['company_id']}/uniuni", json=event, headers=secret_headers
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate_ignored"
    assert second.json()["package_id"] == first.json()["package_id"]

    deliveries = client.get("/deliveries", headers=webhook_setup["headers"]).json()
    assert deliveries[0]["assigned_count"] == 1


def test_webhook_rejects_wrong_secret(client, webhook_setup):
    resp = client.post(
        f"/webhooks/{webhook_setup['company_id']}/uniuni",
        json=_event(),
        headers={"x-webhook-secret": "not-the-real-secret"},
    )
    assert resp.status_code == 401


def test_webhook_rejects_unknown_platform(client, webhook_setup):
    resp = client.post(
        f"/webhooks/{webhook_setup['company_id']}/dhl",
        json=_event(),
        headers={"x-webhook-secret": webhook_setup["webhook_secret"]},
    )
    assert resp.status_code == 404


def test_webhook_rejects_unknown_driver(client, webhook_setup):
    resp = client.post(
        f"/webhooks/{webhook_setup['company_id']}/uniuni",
        json=_event(driver_external_id="does-not-exist"),
        headers={"x-webhook-secret": webhook_setup["webhook_secret"]},
    )
    assert resp.status_code == 404


def test_webhook_rejects_unknown_client(client, webhook_setup):
    resp = client.post(
        f"/webhooks/{webhook_setup['company_id']}/uniuni",
        json=_event(client_name="DoesNotExist"),
        headers={"x-webhook-secret": webhook_setup["webhook_secret"]},
    )
    assert resp.status_code == 404


def test_webhook_cannot_append_to_validated_batch(client, webhook_setup):
    secret_headers = {"x-webhook-secret": webhook_setup["webhook_secret"]}
    client.post(
        f"/webhooks/{webhook_setup['company_id']}/uniuni",
        json=_event(tracking_code="UNI-PKG-X"),
        headers=secret_headers,
    )
    deliveries = client.get("/deliveries", headers=webhook_setup["headers"]).json()
    client.post(f"/deliveries/{deliveries[0]['id']}/validate", headers=webhook_setup["headers"])

    resp = client.post(
        f"/webhooks/{webhook_setup['company_id']}/uniuni",
        json=_event(tracking_code="UNI-PKG-Y"),
        headers=secret_headers,
    )
    assert resp.status_code == 409


def test_rotate_webhook_secret_invalidates_old_one(client, webhook_setup):
    rotate_resp = client.post(
        "/companies/me/rotate-webhook-secret", headers=webhook_setup["headers"]
    )
    assert rotate_resp.status_code == 200
    new_secret = rotate_resp.json()["webhook_secret"]
    assert new_secret != webhook_setup["webhook_secret"]

    old_resp = client.post(
        f"/webhooks/{webhook_setup['company_id']}/uniuni",
        json=_event(),
        headers={"x-webhook-secret": webhook_setup["webhook_secret"]},
    )
    assert old_resp.status_code == 401

    new_resp = client.post(
        f"/webhooks/{webhook_setup['company_id']}/uniuni",
        json=_event(),
        headers={"x-webhook-secret": new_secret},
    )
    assert new_resp.status_code == 200
