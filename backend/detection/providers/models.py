"""Stable contracts for evidence-producing detection providers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from typing import Any, Literal

from evidence.models import EvidenceBundle
from governance import EvidenceProvenance


ProviderType = Literal["metadata", "c2pa", "forensic", "ml_detector", "external"]
ProviderStatus = Literal["experimental", "validated", "approved", "deprecated"]


@dataclass(frozen=True)
class ProviderContext:
    input_hash: str
    collected_at_utc: str
    evidence_bundle: EvidenceBundle | None = None
    scope_attestation: "ScopeAttestation | None" = None

    def __post_init__(self) -> None:
        _sha256(self.input_hash)
        _utc_timestamp(self.collected_at_utc)


@dataclass(frozen=True)
class ScopeAttestation:
    input_hash: str
    conditions: tuple[str, ...]
    issuer: str
    key_id: str
    signature: str

    def __post_init__(self) -> None:
        _sha256(self.input_hash)
        if not all((self.conditions, self.issuer, self.key_id, self.signature)):
            raise ValueError("Scope attestation requires conditions, issuer, key ID, and signature.")

    def payload(self) -> bytes:
        return json.dumps({"conditions": self.conditions, "input_hash": self.input_hash, "issuer": self.issuer, "key_id": self.key_id}, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class DetectionEvidence:
    provider_id: str
    provider_version: str
    observation: dict[str, Any]
    score: float | None
    confidence: str
    validation_scope: str
    limitations: tuple[str, ...]
    evidence_provenance: EvidenceProvenance

    def __post_init__(self) -> None:
        if not self.provider_id or not self.provider_version:
            raise ValueError("Detection evidence requires a provider ID and version.")
        if self.score is not None and not 0 <= self.score <= 1:
            raise ValueError("Detection evidence score must be in [0, 1] when supplied.")
        if not self.confidence or not self.validation_scope or not self.limitations:
            raise ValueError("Detection evidence requires confidence, validation scope, and limitations.")
        if self.evidence_provenance.detector_version != self.provider_version:
            raise ValueError("Evidence provenance detector_version must match provider_version.")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["limitations"] = list(self.limitations)
        return payload


@dataclass(frozen=True)
class ProviderRegistryEntry:
    provider_id: str
    version: str
    provider_type: ProviderType
    status: ProviderStatus
    validation_report: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.provider_id or not self.version:
            raise ValueError("A provider registry entry requires provider_id and version.")
        if self.provider_type not in {"metadata", "c2pa", "forensic", "ml_detector", "external"}:
            raise ValueError("Provider registry entry has an unsupported provider type.")
        if self.status not in {"experimental", "validated", "approved", "deprecated"}:
            raise ValueError("Provider registry entry has an unsupported status.")
        if not self.validation_report or not self.limitations:
            raise ValueError("A provider registry entry requires a validation report and limitations.")


def _sha256(value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("Input hash must be a lowercase SHA-256 hexadecimal digest.")


def _utc_timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Collection timestamp must be RFC3339 UTC.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("Collection timestamp must be RFC3339 UTC.")
