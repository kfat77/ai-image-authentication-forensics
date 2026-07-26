"""Small, explicit security primitives for the stateless API boundary."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import hashlib
import hmac
import logging
import json
import time
from typing import Deque, Protocol

import httpx
import jwt
from fastapi import HTTPException, Request

from .settings import OidcSettings, Settings

audit_log = logging.getLogger("ai_photo_reconstructor.audit")


class JsonAuditFormatter(logging.Formatter):
    """Emit a compact, machine-readable event without request payloads."""
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "event": getattr(record, "event", record.getMessage()),
            "outcome": getattr(record, "outcome", "unknown"),
            "client_id": getattr(record, "client_id", "unknown"),
            "request_id": getattr(record, "request_id", "unknown"),
            "path": getattr(record, "path", "unknown"),
            "details": getattr(record, "details", {}),
        }, separators=(",", ":"), sort_keys=True)


def configure_audit_logger() -> None:
    if audit_log.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonAuditFormatter())
    audit_log.addHandler(handler)
    audit_log.setLevel(logging.INFO)
    audit_log.propagate = False


@dataclass(frozen=True)
class Principal:
    client_id: str
    roles: frozenset[str]


class TokenVerifier(Protocol):
    async def verify(self, token: str) -> dict[str, object]: ...


class OidcVerifier:
    """Validate RS256 access tokens against a configured issuer's JWKS endpoint."""
    def __init__(self, settings: OidcSettings) -> None:
        self.settings = settings
        self._keys: dict[str, object] = {}
        self._expires_at = 0.0

    async def verify(self, token: str) -> dict[str, object]:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid access token.", headers={"WWW-Authenticate": "Bearer"}) from exc
        if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
            raise HTTPException(status_code=401, detail="Unsupported access token.", headers={"WWW-Authenticate": "Bearer"})
        key = await self._key_for(header["kid"])
        try:
            return jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.settings.audience,
                issuer=self.settings.issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid access token.", headers={"WWW-Authenticate": "Bearer"}) from exc

    async def _key_for(self, kid: str) -> object:
        if time.monotonic() >= self._expires_at or kid not in self._keys:
            try:
                async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
                    response = await client.get(self.settings.jwks_url)
                    response.raise_for_status()
                body = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise HTTPException(status_code=503, detail="Identity provider is unavailable.") from exc
            keys = body.get("keys")
            if not isinstance(keys, list):
                raise HTTPException(status_code=503, detail="Identity provider returned an invalid JWKS document.")
            self._keys = {
                item["kid"]: jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(item))
                for item in keys
                if isinstance(item, dict) and item.get("kid") and item.get("kty") == "RSA"
            }
            self._expires_at = time.monotonic() + 300
        try:
            return self._keys[kid]
        except KeyError as exc:
            raise HTTPException(status_code=401, detail="Unknown signing key.", headers={"WWW-Authenticate": "Bearer"}) from exc


class RateLimiter:
    """Per-process guard only; production deployments need a shared edge limiter."""
    def __init__(self, requests_per_minute: int) -> None:
        self.limit = requests_per_minute
        self.windows: dict[str, Deque[float]] = defaultdict(deque)

    def check(self, subject: str) -> None:
        now = time.monotonic()
        window = self.windows[subject]
        while window and now - window[0] >= 60:
            window.popleft()
        if len(window) >= self.limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")
        window.append(now)


async def authenticate(request: Request, settings: Settings, token_verifier: TokenVerifier | None = None) -> Principal:
    supplied = request.headers.get("x-api-key", "")
    for client in settings.clients:
        if hmac.compare_digest(supplied, client.secret):
            return Principal(client_id=client.client_id, roles=frozenset({client.role}))
    authorization = request.headers.get("authorization", "")
    if authorization.startswith("Bearer ") and token_verifier and settings.oidc:
        claims = await token_verifier.verify(authorization[7:])
        subject = claims.get("sub")
        raw_roles = claims.get(settings.oidc.role_claim, [])
        roles = {raw_roles} if isinstance(raw_roles, str) else set(raw_roles) if isinstance(raw_roles, list) else set()
        allowed_roles = frozenset(str(role) for role in roles if role in {"analyst", "operator"})
        if not isinstance(subject, str) or not allowed_roles:
            raise HTTPException(status_code=403, detail="Token does not include an authorised role.")
        return Principal(client_id=f"oidc:{subject}", roles=allowed_roles)
    if not settings.clients and not settings.oidc and not settings.production:
        return Principal(client_id="local-development", roles=frozenset({"analyst"}))
    raise HTTPException(status_code=401, detail="Valid API-key or bearer-token credentials are required.", headers={"WWW-Authenticate": "Bearer, ApiKey"})


def require_role(principal: Principal, *roles: str) -> None:
    if not principal.roles.intersection(roles):
        raise HTTPException(status_code=403, detail="The identity does not have permission for this operation.")


def emit_audit(event: str, request: Request, principal: Principal, outcome: str, **details: object) -> None:
    """Write only metadata suitable for a centrally collected audit log."""
    audit_log.info(
        "audit_event",
        extra={
            "event": event,
            "outcome": outcome,
            "client_id": principal.client_id,
            "request_id": request.state.request_id,
            "path": request.url.path,
            "details": details,
        },
    )


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]
