"""Bounded adapter for an institution-approved internal vision service."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx
from fastapi import HTTPException

from .settings import VisionProviderSettings


@dataclass(frozen=True)
class VisionContext:
    description: str
    tags: tuple[str, ...]


class VisionProvider(Protocol):
    async def analyze(self, image: bytes, mime_type: str) -> VisionContext: ...


class InternalVisionProvider:
    """Calls a reviewed in-network endpoint; it never persists the source image locally."""
    def __init__(self, settings: VisionProviderSettings) -> None:
        self.settings = settings

    async def analyze(self, image: bytes, mime_type: str) -> VisionContext:
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
            raise HTTPException(status_code=503, detail="The configured vision service is unavailable.") from exc
        return _parse_context(payload)


def _parse_context(payload: object) -> VisionContext:
    if not isinstance(payload, dict) or not isinstance(payload.get("description"), str):
        raise HTTPException(status_code=503, detail="The configured vision service returned an invalid response.")
    description = payload["description"].strip()[:1200]
    raw_tags = payload.get("tags", [])
    if not isinstance(raw_tags, list):
        raw_tags = []
    tags = tuple(tag.strip()[:80] for tag in raw_tags if isinstance(tag, str) and tag.strip())[:12]
    return VisionContext(description=description, tags=tags)
