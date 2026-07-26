"""Small, explicit security primitives for the stateless API boundary."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import hashlib
import hmac
import logging
import json
import time
from typing import Deque

from fastapi import HTTPException, Request

from .settings import ApiClient, Settings

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
    role: str


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


def authenticate(request: Request, settings: Settings) -> Principal:
    supplied = request.headers.get("x-api-key", "")
    if not settings.clients and not settings.production:
        return Principal(client_id="local-development", role="analyst")
    for client in settings.clients:
        if hmac.compare_digest(supplied, client.secret):
            return Principal(client_id=client.client_id, role=client.role)
    raise HTTPException(status_code=401, detail="A valid API key is required.", headers={"WWW-Authenticate": "ApiKey"})


def require_role(principal: Principal, *roles: str) -> None:
    if principal.role not in roles:
        raise HTTPException(status_code=403, detail="The API key does not have permission for this operation.")


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
