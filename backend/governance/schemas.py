"""Validation-only protocol contracts for P3-A institutional architecture."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Literal


def _hash(value: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("Hash must be a lowercase SHA-256 hexadecimal digest.")
    return value


@dataclass(frozen=True)
class ModelRegistryEntry:
    model_id: str
    model_name: str
    version: str
    architecture: str
    weight_hash: str
    source: str
    license: str
    training_data_reference: str
    evaluation_report: str
    calibration_reference: str
    validation_scope: str
    limitations: tuple[str, ...]
    approved_status: Literal["draft", "approved", "rejected", "retired"]

    def __post_init__(self) -> None:
        _hash(self.weight_hash)
        if self.approved_status == "approved" and not self.calibration_reference:
            raise ValueError("An approved model requires a calibration reference.")


@dataclass(frozen=True)
class CalibrationRegistryEntry:
    calibration_id: str
    model_version: str
    dataset: str
    threshold: float
    metrics: dict[str, float]
    ece: float
    brier: float
    validation_date: str
    applicable_conditions: tuple[str, ...]
    excluded_conditions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not 0 <= self.threshold <= 1 or self.ece < 0 or self.brier < 0:
            raise ValueError("Calibration threshold and metrics must be non-negative probabilities.")
        if not self.applicable_conditions or not self.excluded_conditions:
            raise ValueError("Calibration must declare both applicable and excluded conditions.")


@dataclass(frozen=True)
class EvidenceProvenance:
    evidence_id: str
    source_type: Literal["c2pa", "exif", "metadata", "frequency", "noise", "artifact", "model", "external"]
    detector_version: str
    timestamp: str
    input_hash: str
    reliability: str
    observation: object
    limitation: str

    def __post_init__(self) -> None:
        _hash(self.input_hash)
        if not all((self.evidence_id, self.detector_version, self.timestamp, self.reliability, self.limitation)):
            raise ValueError("Evidence provenance requires non-empty identity, time, reliability, and limitation fields.")
        _utc_timestamp(self.timestamp)
        if self.source_type not in {"c2pa", "exif", "metadata", "frequency", "noise", "artifact", "model", "external"}:
            raise ValueError("Evidence provenance source_type is unsupported.")


def _utc_timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Timestamp must be RFC3339 UTC.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("Timestamp must be RFC3339 UTC.")


def validate_evidence_provenance(raw: dict[str, object]) -> EvidenceProvenance:
    required = {"evidence_id", "source_type", "detector_version", "timestamp", "input_hash", "reliability", "observation", "limitation"}
    missing = required - set(raw)
    if missing:
        raise ValueError(f"Evidence provenance is missing fields: {', '.join(sorted(missing))}")
    return EvidenceProvenance(**{name: raw[name] for name in required})


@dataclass(frozen=True)
class CaseRecord:
    case_id: str
    submitter: str
    submission_time: str
    original_file_hash: str
    evidence_bundle: str
    analysis_version: str
    reviewer: str | None
    final_report_hash: str | None

    def __post_init__(self) -> None:
        _hash(self.original_file_hash)
        if self.final_report_hash is not None:
            _hash(self.final_report_hash)


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp: str
    actor: str
    action: str
    case_id: str
    input_hash: str
    output_hash: str
    previous_event_hash: str | None
    signature: str | None

    def __post_init__(self) -> None:
        _hash(self.input_hash)
        _hash(self.output_hash)
        if self.previous_event_hash is not None:
            _hash(self.previous_event_hash)

    def event_hash(self) -> str:
        payload = {**self.__dict__, "signature": None}
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_audit_chain(events: list[AuditEvent]) -> None:
    previous: str | None = None
    for event in events:
        if event.previous_event_hash != previous:
            raise ValueError("Audit chain previous_event_hash does not match.")
        previous = event.event_hash()


def validate_model_calibration_integrity(model: ModelRegistryEntry, calibrations: list[CalibrationRegistryEntry]) -> None:
    if model.approved_status != "approved":
        return
    matching = [entry for entry in calibrations if entry.calibration_id == model.calibration_reference and entry.model_version == model.version]
    if not matching:
        raise ValueError("Approved model calibration reference must resolve to the same model version.")
