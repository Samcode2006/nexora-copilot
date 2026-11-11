import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Protocol

import jwt
from jwt import PyJWKClient, PyJWKClientError

from app.core.config import Settings
from app.core.errors import AppError

logger = logging.getLogger("nexora.security")

ASYMMETRIC_ALGS = {"ES256", "RS256"}
SYMMETRIC_ALGS = {"HS256"}
ALLOWED_ALGS = ASYMMETRIC_ALGS | SYMMETRIC_ALGS
JWKS_FORCE_REFRESH_MIN_INTERVAL = 30.0  # seconds; limits refresh abuse via random `kid`s


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str | None = None


class JWKSClient(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> Any: ...


def unauthenticated() -> AppError:
    """Single generic error for every auth failure so nothing about the cause leaks."""
    return AppError(401, "UNAUTHENTICATED", "Authentication required.")


class TokenVerifier:
    def __init__(self, settings: Settings, jwks_client: JWKSClient | None = None):
        self._settings = settings
        self._jwks: JWKSClient = jwks_client or PyJWKClient(
            settings.jwks_url, cache_keys=True, lifespan=600, timeout=5
        )
        self._last_forced_refresh = 0.0

    def _signing_key_asymmetric(self, token: str) -> Any:
        try:
            return self._jwks.get_signing_key_from_jwt(token).key
        except PyJWKClientError:
            # Unknown kid: keys may have rotated. Refresh at most once per interval.
            now = time.monotonic()
            if now - self._last_forced_refresh < JWKS_FORCE_REFRESH_MIN_INTERVAL:
                raise
            self._last_forced_refresh = now
            refresh = getattr(self._jwks, "get_signing_keys", None)
            if callable(refresh):
                refresh(refresh=True)
            return self._jwks.get_signing_key_from_jwt(token).key

    def _verify_sync(self, token: str) -> dict[str, Any]:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        if alg not in ALLOWED_ALGS:  # rejects "none" and anything unexpected
            raise jwt.InvalidAlgorithmError("algorithm not allowed")

        if alg in SYMMETRIC_ALGS:
            secret = self._settings.supabase_jwt_secret
            if not secret:
                raise jwt.InvalidKeyError("HS256 not configured")
            key: Any = secret
        else:
            key = self._signing_key_asymmetric(token)

        return jwt.decode(
            token,
            key=key,
            algorithms=[alg],  # only the (allow-listed) header alg, bound to its key source
            audience=self._settings.supabase_jwt_audience,
            issuer=self._settings.jwt_issuer,
            options={"require": ["exp", "sub", "iss", "aud"]},
        )

    async def verify(self, token: str) -> AuthUser:
        try:
            # JWKS fetch is blocking network I/O; keep it off the event loop.
            claims = await asyncio.to_thread(self._verify_sync, token)
        except (jwt.PyJWTError, PyJWKClientError, ValueError, TypeError) as exc:
            logger.info("JWT rejected: %s", type(exc).__name__)
            raise unauthenticated() from None
        sub = claims.get("sub")
        if not isinstance(sub, str) or not sub:
            raise unauthenticated()
        email = claims.get("email")
        return AuthUser(id=sub, email=email if isinstance(email, str) else None)
