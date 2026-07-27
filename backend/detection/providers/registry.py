"""Registry gate that admits only approved provider evidence to formal fusion."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from .models import DetectionEvidence, ProviderContext, ProviderRegistryEntry


class DetectionProvider(Protocol):
    provider_id: str
    provider_version: str

    def detect(self, image: bytes, context: ProviderContext) -> tuple[DetectionEvidence, ...]: ...


class ProviderRegistrationError(ValueError):
    """Raised when a provider has no matching registry admission."""


@dataclass(frozen=True)
class ProviderCollection:
    evidence: tuple[DetectionEvidence, ...]
    exclusions: tuple[dict[str, str], ...]


class ProviderRegistry:
    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], ProviderRegistryEntry] = {}

    def register(self, entry: ProviderRegistryEntry) -> None:
        key = (entry.provider_id, entry.version)
        if key in self._entries:
            raise ProviderRegistrationError(f"Provider {entry.provider_id}@{entry.version} is already registered.")
        self._entries[key] = entry

    def get(self, provider_id: str, version: str) -> ProviderRegistryEntry:
        try:
            return self._entries[(provider_id, version)]
        except KeyError as exc:
            raise ProviderRegistrationError(f"Provider {provider_id}@{version} is not registered.") from exc

    def collect_for_formal_report(self, providers: tuple[DetectionProvider, ...], image: bytes, context: ProviderContext) -> ProviderCollection:
        image_hash = sha256(image).hexdigest()
        admitted: list[DetectionEvidence] = []
        evidence_ids: set[str] = set()
        exclusions: list[dict[str, str]] = []
        for provider in providers:
            entry = self.get(provider.provider_id, provider.provider_version)
            if image_hash != context.input_hash:
                raise ProviderRegistrationError("Provider collection context input hash does not match image bytes.")
            if entry.status != "approved":
                exclusions.append({"provider_id": entry.provider_id, "provider_version": entry.version, "status": entry.status, "reason": "Provider is not approved and cannot influence a formal authentication report."})
                continue
            provider_evidence = provider.detect(image, context)
            for evidence in provider_evidence:
                if evidence.provider_id != entry.provider_id or evidence.provider_version != entry.version:
                    raise ProviderRegistrationError("Provider evidence does not match its registry entry.")
                if evidence.evidence_provenance.input_hash != context.input_hash:
                    raise ProviderRegistrationError("Provider evidence input hash does not match the collection context.")
                if evidence.evidence_provenance.evidence_id in evidence_ids:
                    raise ProviderRegistrationError("Provider evidence IDs must be unique within a collection.")
                evidence_ids.add(evidence.evidence_provenance.evidence_id)
            admitted.extend(provider_evidence)
        return ProviderCollection(tuple(admitted), tuple(exclusions))
