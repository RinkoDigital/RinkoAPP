"""Sends push notifications through Expo's push service.

Expo's push API is provider-agnostic on our side — it's the same HTTP
endpoint regardless of iOS/Android, and Expo handles routing to APNs/FCM.
No API key is required for the free tier this app is on.
"""

import logging

import httpx

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

logger = logging.getLogger("rinko.push")


def send_push_notification(
    token: str, title: str, body: str, data: dict | None = None
) -> None:
    payload = {"to": token, "title": title, "body": body}
    if data:
        payload["data"] = data

    try:
        resp = httpx.post(EXPO_PUSH_URL, json=payload, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Failed to send push notification to %s", token)
