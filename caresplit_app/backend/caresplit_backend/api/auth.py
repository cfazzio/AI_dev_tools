"""Password hashing and bearer-token issuance/validation.

Deliberately stdlib-only (hashlib/hmac/secrets) rather than pulling in
passlib+bcrypt: PBKDF2-HMAC-SHA256 with a random salt and a high iteration
count is a NIST-approved KDF and needs no compiled dependency. Tokens are
opaque random strings held server-side (not JWTs) — this is a single local
backend process, so there's nothing for a client to gain from a
self-contained token, and opaque tokens are trivially revocable (just
forget them) since the server is the only party that ever inspects one.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

PBKDF2_ITERATIONS = 260_000
TOKEN_TTL = timedelta(hours=24)

_bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    )
    return f"{salt}${digest.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    salt, _, expected_hex = hashed.partition("$")
    if not salt or not expected_hex:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    )
    return hmac.compare_digest(digest.hex(), expected_hex)


@dataclass
class _TokenEntry:
    username: str
    expires_at: datetime


class TokenStore:
    """In-memory bearer-token store: token string -> (username, expiry)."""

    def __init__(self) -> None:
        self._tokens: dict[str, _TokenEntry] = {}

    def issue(self, username: str) -> tuple[str, datetime]:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + TOKEN_TTL
        self._tokens[token] = _TokenEntry(username=username, expires_at=expires_at)
        return token, expires_at

    def resolve(self, token: str) -> str | None:
        entry = self._tokens.get(token)
        if entry is None:
            return None
        if datetime.now(timezone.utc) >= entry.expires_at:
            del self._tokens[token]
            return None
        return entry.username

    def reset(self) -> None:
        self._tokens.clear()


_token_store = TokenStore()


def get_token_store() -> TokenStore:
    return _token_store


def get_current_username(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    token_store: TokenStore = Depends(get_token_store),
) -> str:
    """FastAPI dependency: require a valid bearer token, return its username.

    Attach via a router's ``dependencies=[Depends(get_current_username)]``
    to protect every route on that router in one place, or per-route if a
    handler also needs the username.
    """
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = token_store.resolve(credentials.credentials)
    if username is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username
