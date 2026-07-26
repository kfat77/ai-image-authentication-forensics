"""Adapter for an institution-operated C2PA verification service."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx
from fastapi import HTTPException

from .settings import ProvenanceProviderSettings

VALID_STATUSES = frozenset({"valid", "invalid", "not_present", "unsupported"})


@dataclass(frozen=True)
class ProvenanceReport:
    status: str
    claim_generator: str | None = None
    validation_errors: tuple[str, ...] = ()


class ProvenanceProvider(Protocol):
    async def verify(self, image: bytes, mime_type: str) -> ProvenanceReport: ...


class C2paVerificationProvider:
    """Delegates C2PA trust-list and manifest verification to an approved internal service."""
    def __init__(self, settings: ProvenanceProviderSettings) -> None:
        self.settings = settings

    async def verify(self, image: bytes, mime_type: str) -> ProvenanceReport:
        try:
            async with httpx.AsyncClient(timeout=20.0, trust_env=False) as client:
                response = await client.post(
                    self.settings.url,
                    headers={"Authorization": f"Bearer {self.settings.token}"},
                    files={"image": ("upload", image, mime_type)},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=503, detail="The configured provenance service is unavailable.") from exc
        return _parse_report(payload)


def _parse_report(payload: object) -> ProvenanceReport:
    if not isinstance(payload, dict) or payload.get("status") not in VALID_STATUSES:
        raise HTTPException(status_code=503, detail="The configured provenance service returned an invalid response.")
    claim_generator = payload.get("claim_generator")
    if not isinstance(claim_generator, str):
        claim_generator = None
    errors = payload.get("validation_errors", [])
    if not isinstance(errors, list):
        errors = []
    return ProvenanceReport(
        status=payload["status"],
        claim_generator=claim_generator[:160] if claim_generator else None,
        validation_errors=tuple(item[:240] for item in errors if isinstance(item, str))[:10],
    )
