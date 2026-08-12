"""Verifies Google/Apple identity tokens sent by the client apps.

Both providers hand the client a signed JWT after the user authenticates;
the client forwards it here as-is and we verify it server-side rather than
trusting whatever the client claims about who signed in. Neither call
touches the database — callers turn the verified identity into a Driver.
"""

import time

import httpx
import jwt
from fastapi import HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config import settings

APPLE_ISSUER = "https://appleid.apple.com"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_KEYS_CACHE_TTL_SECONDS = 3600

_apple_keys_cache: dict | None = None
_apple_keys_fetched_at: float = 0.0


class OAuthIdentity:
    def __init__(self, subject: str, email: str | None, name: str | None):
        self.subject = subject
        self.email = email
        self.name = name


def verify_google_id_token(token: str) -> OAuthIdentity:
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google login is not configured")
    try:
        payload = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), audience=settings.google_client_id
        )
    except Exception as exc:  # google-auth raises plain ValueError/GoogleAuthError on bad tokens
        raise HTTPException(status_code=401, detail="Invalid Google token") from exc

    if not payload.get("email_verified", False):
        raise HTTPException(status_code=401, detail="Google account email is not verified")

    return OAuthIdentity(subject=payload["sub"], email=payload.get("email"), name=payload.get("name"))


def _get_apple_public_keys() -> dict:
    global _apple_keys_cache, _apple_keys_fetched_at
    now = time.monotonic()
    if _apple_keys_cache is None or now - _apple_keys_fetched_at > APPLE_KEYS_CACHE_TTL_SECONDS:
        resp = httpx.get(APPLE_KEYS_URL, timeout=10)
        resp.raise_for_status()
        _apple_keys_cache = {key["kid"]: key for key in resp.json()["keys"]}
        _apple_keys_fetched_at = now
    return _apple_keys_cache


def verify_apple_identity_token(token: str) -> OAuthIdentity:
    try:
        header = jwt.get_unverified_header(token)
        keys = _get_apple_public_keys()
        jwk = keys.get(header["kid"])
        if jwk is None:
            # Apple rotates keys occasionally — refresh once before giving up.
            global _apple_keys_cache
            _apple_keys_cache = None
            jwk = _get_apple_public_keys().get(header["kid"])
        if jwk is None:
            raise HTTPException(status_code=401, detail="Invalid Apple token (unknown key)")

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
        payload = jwt.decode(
            token,
            key=public_key,
            algorithms=["RS256"],
            audience=settings.apple_bundle_id,
            issuer=APPLE_ISSUER,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid Apple token") from exc

    return OAuthIdentity(subject=payload["sub"], email=payload.get("email"), name=None)
