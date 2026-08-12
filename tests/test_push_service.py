from unittest.mock import MagicMock, patch

from app.services.push import EXPO_PUSH_URL, send_push_notification


def test_sends_expected_payload_to_expo():
    with patch("app.services.push.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        send_push_notification("ExponentPushToken[x]", "Title", "Body", {"foo": "bar"})

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == EXPO_PUSH_URL
    assert kwargs["json"] == {
        "to": "ExponentPushToken[x]",
        "title": "Title",
        "body": "Body",
        "data": {"foo": "bar"},
    }


def test_omits_data_key_when_not_given():
    with patch("app.services.push.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        send_push_notification("ExponentPushToken[x]", "Title", "Body")

    assert "data" not in mock_post.call_args.kwargs["json"]


def test_swallows_network_errors():
    import httpx

    with patch("app.services.push.httpx.post", side_effect=httpx.ConnectError("boom")):
        # Should not raise — a failed push is logged, not fatal to the caller.
        send_push_notification("ExponentPushToken[x]", "Title", "Body")
