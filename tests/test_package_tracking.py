from unittest.mock import patch


def _create_session(client, headers, carrier):
    return client.post(
        "/sessions",
        json={"carrier_id": carrier["id"], "service_date": "2026-07-28", "packages_assigned": 50},
        headers=headers,
    ).json()


def test_bulk_import_creates_pending_packages(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)

    with patch("app.services.packages.track123.register_trackings") as mock_register:
        resp = client.post(
            f"/sessions/{session['id']}/packages/bulk-import",
            json={"tracking_codes": ["PKG-A", "PKG-B"], "courier_code": "uniuni"},
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["created"]) == 2
    assert body["skipped_duplicates"] == []
    for pkg in body["created"]:
        assert pkg["outcome"] is None
        assert pkg["source"] == "uniuni"

    mock_register.assert_called_once()
    (registered_items,), _ = mock_register.call_args
    assert {item["trackNo"] for item in registered_items} == {"PKG-A", "PKG-B"}
    assert all(item["courierCode"] == "uniuni" for item in registered_items)


def test_bulk_import_skips_duplicates_already_on_session(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)
    client.post(
        f"/sessions/{session['id']}/packages",
        json={"tracking_code": "PKG-A", "outcome": "delivered"},
        headers=headers,
    )

    with patch("app.services.packages.track123.register_trackings"):
        resp = client.post(
            f"/sessions/{session['id']}/packages/bulk-import",
            json={"tracking_codes": ["PKG-A", "PKG-A", "PKG-C"]},
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert [pkg["tracking_code"] for pkg in body["created"]] == ["PKG-C"]
    assert body["skipped_duplicates"] == ["PKG-A", "PKG-A"]


def test_bulk_import_rejects_empty_list(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)
    resp = client.post(
        f"/sessions/{session['id']}/packages/bulk-import",
        json={"tracking_codes": []},
        headers=headers,
    )
    assert resp.status_code == 422


def test_resolve_pending_package(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)
    with patch("app.services.packages.track123.register_trackings"):
        imported = client.post(
            f"/sessions/{session['id']}/packages/bulk-import",
            json={"tracking_codes": ["PKG-A"], "courier_code": "uniuni"},
            headers=headers,
        ).json()
    package_id = imported["created"][0]["id"]
    assert imported["created"][0]["outcome"] is None

    resp = client.post(
        f"/sessions/{session['id']}/packages/{package_id}/resolve",
        json={"outcome": "delivered", "pod_scan_code": "SCAN-1"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] == "delivered"
    assert body["pod_scan_code"] == "SCAN-1"
    assert body["pod_captured_at"] is not None


def test_resolve_returned_requires_reason(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)
    with patch("app.services.packages.track123.register_trackings"):
        imported = client.post(
            f"/sessions/{session['id']}/packages/bulk-import",
            json={"tracking_codes": ["PKG-A"]},
            headers=headers,
        ).json()
    package_id = imported["created"][0]["id"]

    resp = client.post(
        f"/sessions/{session['id']}/packages/{package_id}/resolve",
        json={"outcome": "returned"},
        headers=headers,
    )
    assert resp.status_code == 422

    resp = client.post(
        f"/sessions/{session['id']}/packages/{package_id}/resolve",
        json={"outcome": "returned", "return_reason": "wrong_address"},
        headers=headers,
    )
    assert resp.status_code == 200


def test_refresh_status_updates_carrier_imported_packages_only(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)
    client.post(
        f"/sessions/{session['id']}/packages",
        json={"tracking_code": "PKG-MANUAL", "outcome": "delivered"},
        headers=headers,
    )
    with patch("app.services.packages.track123.register_trackings"):
        client.post(
            f"/sessions/{session['id']}/packages/bulk-import",
            json={"tracking_codes": ["PKG-A"], "courier_code": "uniuni"},
            headers=headers,
        )

    with patch(
        "app.services.packages.track123.query_tracking_status",
        return_value={"PKG-A": "In transit"},
    ) as mock_query:
        resp = client.post(f"/sessions/{session['id']}/packages/refresh-status", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["tracking_code"] == "PKG-A"
    assert body[0]["carrier_status"] == "In transit"
    assert body[0]["carrier_status_updated_at"] is not None

    # Only the non-manual package's tracking code was queried.
    (queried_codes,), _ = mock_query.call_args
    assert queried_codes == ["PKG-A"]


def test_refresh_status_noop_when_track123_returns_nothing(client, driver_and_headers, carrier):
    _, headers = driver_and_headers
    session = _create_session(client, headers, carrier)
    with patch("app.services.packages.track123.register_trackings"):
        client.post(
            f"/sessions/{session['id']}/packages/bulk-import",
            json={"tracking_codes": ["PKG-A"]},
            headers=headers,
        )

    with patch("app.services.packages.track123.query_tracking_status", return_value={}):
        resp = client.post(f"/sessions/{session['id']}/packages/refresh-status", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []
