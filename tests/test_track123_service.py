from unittest.mock import MagicMock, patch

from app.config import settings
from app.services import track123


def test_register_trackings_noop_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "track123_api_key", "")
    with patch("app.services.track123.httpx.post") as mock_post:
        track123.register_trackings([{"trackNo": "PKG-A", "courierCode": "uniuni"}])
    mock_post.assert_not_called()


def test_register_trackings_noop_for_empty_items(monkeypatch):
    monkeypatch.setattr(settings, "track123_api_key", "test-key")
    with patch("app.services.track123.httpx.post") as mock_post:
        track123.register_trackings([])
    mock_post.assert_not_called()


def test_register_trackings_sends_expected_request(monkeypatch):
    monkeypatch.setattr(settings, "track123_api_key", "test-key")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    with patch("app.services.track123.httpx.post", return_value=mock_response) as mock_post:
        track123.register_trackings([{"trackNo": "PKG-A", "courierCode": "uniuni", "orderNo": None}])

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.track123.com/gateway/open-api/tk/v2/track/import"
    assert kwargs["headers"]["Track123-Api-Secret"] == "test-key"
    assert kwargs["json"] == [{"trackNo": "PKG-A", "courierCode": "uniuni", "orderNo": None}]


def test_register_trackings_swallows_http_errors(monkeypatch):
    import httpx

    monkeypatch.setattr(settings, "track123_api_key", "test-key")
    with patch("app.services.track123.httpx.post", side_effect=httpx.ConnectError("boom")):
        track123.register_trackings([{"trackNo": "PKG-A"}])  # must not raise


def test_query_tracking_status_noop_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "track123_api_key", "")
    assert track123.query_tracking_status(["PKG-A"]) == {}


def test_query_tracking_status_parses_flat_list_response(monkeypatch):
    monkeypatch.setattr(settings, "track123_api_key", "test-key")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = [
        {"trackNo": "PKG-A", "transitSubStatus": "In transit"},
        {"trackNo": "PKG-B", "status": "Delivered"},
    ]
    with patch("app.services.track123.httpx.post", return_value=mock_response):
        result = track123.query_tracking_status(["PKG-A", "PKG-B"])
    assert result == {"PKG-A": "In transit", "PKG-B": "Delivered"}


def test_query_tracking_status_parses_nested_envelope(monkeypatch):
    monkeypatch.setattr(settings, "track123_api_key", "test-key")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": {"content": [{"trackNo": "PKG-A", "packageStatus": "Out for delivery"}]}
    }
    with patch("app.services.track123.httpx.post", return_value=mock_response):
        result = track123.query_tracking_status(["PKG-A"])
    assert result == {"PKG-A": "Out for delivery"}


def test_query_tracking_status_unrecognized_shape_returns_empty(monkeypatch):
    monkeypatch.setattr(settings, "track123_api_key", "test-key")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"unexpected": "shape"}
    with patch("app.services.track123.httpx.post", return_value=mock_response):
        result = track123.query_tracking_status(["PKG-A"])
    assert result == {}


def test_query_tracking_status_swallows_http_errors(monkeypatch):
    import httpx

    monkeypatch.setattr(settings, "track123_api_key", "test-key")
    with patch("app.services.track123.httpx.post", side_effect=httpx.ConnectError("boom")):
        assert track123.query_tracking_status(["PKG-A"]) == {}
