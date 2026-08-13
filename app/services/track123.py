"""Client for Track123 (open.track123.com) — a carrier tracking aggregator.

Registers tracking numbers for monitoring and polls their status. This is
supplementary/informational only: it never decides `Package.outcome` — the
driver's own confirmation (with photo, for deliveries) stays the actual
evidence. A Track123 outage or bad response should never block the driver
from using their own records, so every function here is best-effort and
swallows errors rather than raising.

The exact response shape of /track/query wasn't verified against a live
call while building this (no network path to api.track123.com from the dev
sandbox) — `_extract_status` tries several plausible field names and falls
back to leaving the status unset rather than guessing wrong. If Track123's
real response uses different field names, only that function needs fixing.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger("shiftproof.track123")

BASE_URL = "https://api.track123.com/gateway/open-api/tk/v2"


def _headers() -> dict:
    return {
        "Track123-Api-Secret": settings.track123_api_key,
        "accept": "application/json",
        "content-type": "application/json",
    }


def is_configured() -> bool:
    return bool(settings.track123_api_key)


def register_trackings(items: list[dict]) -> None:
    """Registers tracking numbers for monitoring. Each item:
    {"trackNo": str, "courierCode": str | None, "orderNo": str | None}.
    No-ops without an API key. Never raises — a failed registration just
    means status refresh won't find anything for that package later,
    which is a degraded experience, not a broken one."""
    if not is_configured() or not items:
        return
    try:
        resp = httpx.post(f"{BASE_URL}/track/import", headers=_headers(), json=items, timeout=10)
        resp.raise_for_status()
    except httpx.HTTPError:
        logger.warning("Track123 register_trackings failed for %d item(s)", len(items), exc_info=True)


def _extract_status(item: dict) -> str | None:
    for key in ("transitSubStatus", "packageStatus", "deliveryStatus", "status", "latestEvent"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def query_tracking_status(track_nos: list[str]) -> dict[str, str | None]:
    """Returns {track_no: status_string_or_None}. Missing/unrecognized
    entries are simply absent from the result — callers should leave
    those packages' carrier_status untouched rather than clearing it."""
    if not is_configured() or not track_nos:
        return {}
    try:
        resp = httpx.post(
            f"{BASE_URL}/track/query",
            headers=_headers(),
            json={"trackNos": track_nos},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        logger.warning("Track123 query_tracking_status failed for %d item(s)", len(track_nos), exc_info=True)
        return {}

    # Response envelope shape is unverified (see module docstring) — try the
    # plausible container keys, falling back to the payload itself if it's
    # already a list.
    items = data
    for key in ("data", "content", "result"):
        if isinstance(data, dict) and key in data:
            items = data[key]
            break
    if isinstance(items, dict):
        for key in ("content", "list", "items"):
            if key in items:
                items = items[key]
                break

    if not isinstance(items, list):
        logger.warning("Track123 query response had an unrecognized shape: %r", data)
        return {}

    results: dict[str, str | None] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        track_no = item.get("trackNo") or item.get("trackNumber")
        if not track_no:
            continue
        results[track_no] = _extract_status(item)
    return results
