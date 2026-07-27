"""ML detector provider governed by model, calibration, hash, and scope checks."""

from __future__ import annotations

from hashlib import sha256
from math import exp, log
from typing import Protocol

from governance import EvidenceProvenance

from ..models import DetectionEvidence, ProviderContext
from .governance import GovernedCalibrationRecord, GovernedModelRecord, ModelGovernanceError, validate_model_admission
from .registry import ModelCalibrationRegistry
from .scope import ScopeAttestationVerifier


class VerifiedScoreReader(Protocol):
    weight_hash: str

    def score(self, image: bytes) -> float: ...


class MLDetectorProvider:
    """Produces auxiliary model evidence only after every governance check passes."""

    def __init__(self, registry: ModelCalibrationRegistry, model_id: str, version: str, reader: VerifiedScoreReader, scope_verifier: ScopeAttestationVerifier | None = None) -> None:
        self.model, self.calibration = registry.resolve(model_id, version)
        self.reader = reader
        self.scope_verifier = scope_verifier
        self.provider_id = f"ml.{self.model.model_id}"
        self.provider_version = self.model.version

    def detect(self, image: bytes, context: ProviderContext) -> tuple[DetectionEvidence, ...]:
        if sha256(image).hexdigest() != context.input_hash:
            raise ModelGovernanceError("ML provider image hash does not match the collection context.")
        validate_model_admission(self.model, self.calibration)
        if self.reader.weight_hash != self.model.weight_hash:
            raise ModelGovernanceError("Loaded model weight hash does not match its registry record.")
        scope_status, scope_reason = _scope_status(context, self.calibration, self.scope_verifier)
        if scope_status == "OUT_OF_SCOPE":
            return (self._evidence(context, None, None, scope_status, scope_reason),)
        raw_score = self.reader.score(image)
        if not 0 <= raw_score <= 1:
            raise ModelGovernanceError("ML score reader must return a value in [0, 1].")
        score = _temperature_scale(raw_score, self.calibration.calibration_parameters["temperature"])
        return (self._evidence(context, raw_score, score, "IN_SCOPE", "Input conditions match the declared calibration scope."),)

    def _evidence(self, context: ProviderContext, raw_score: float | None, score: float | None, scope_status: str, scope_reason: str) -> DetectionEvidence:
        limitations = self.model.limitations + self.calibration.limitations + (scope_reason, "Model evidence is auxiliary review evidence and cannot directly set an authenticity status.")
        observation = {
            "model": {"model_id": self.model.model_id, "version": self.model.version, "architecture": self.model.architecture, "weight_hash": self.model.weight_hash},
            "validation": {"calibration_id": self.calibration.calibration_id, "dataset": self.calibration.validation_dataset, "date": self.calibration.validation_date, "threshold": self.calibration.threshold, "ece": self.calibration.ece, "brier": self.calibration.brier, "method": self.calibration.calibration_method, "parameters": self.calibration.calibration_parameters},
            "scope_status": scope_status,
            "raw_score": raw_score,
            "score": score,
        }
        provenance = EvidenceProvenance(
            evidence_id=f"provider.{self.provider_id}.{context.input_hash[:16]}",
            source_type="model",
            detector_version=self.provider_version,
            timestamp=context.collected_at_utc,
            input_hash=context.input_hash,
            reliability=f"calibrated auxiliary score on {self.calibration.validation_dataset}" if score is not None else "scope-excluded; no model score produced",
            observation=observation,
            limitation=" ".join(limitations),
        )
        return DetectionEvidence(self.provider_id, self.provider_version, observation, score, "calibrated_auxiliary_score" if score is not None else "out_of_scope_no_model_score", "; ".join(self.calibration.scope), limitations, provenance)


def _scope_status(context: ProviderContext, calibration: GovernedCalibrationRecord, verifier: ScopeAttestationVerifier | None) -> tuple[str, str]:
    conditions = _bundle_conditions(context)
    attestation = context.scope_attestation
    if attestation is not None:
        if verifier is None or attestation.input_hash != context.input_hash or not verifier.verify(attestation):
            return "OUT_OF_SCOPE", "Input scope attestation is absent, untrusted, invalid, or bound to another input hash."
        conditions.update(attestation.conditions)
    excluded = sorted(conditions.intersection(calibration.excluded_conditions))
    missing = sorted(set(calibration.scope) - conditions)
    undeclared = sorted(conditions - set(calibration.scope) - set(calibration.excluded_conditions))
    if excluded:
        return "OUT_OF_SCOPE", f"Input declares excluded condition(s): {', '.join(excluded)}."
    if undeclared:
        return "OUT_OF_SCOPE", f"Input declares condition(s) outside the calibration scope: {', '.join(undeclared)}."
    if missing:
        return "OUT_OF_SCOPE", f"Input lacks declared in-scope condition(s): {', '.join(missing)}."
    return "IN_SCOPE", "Input conditions match the declared calibration scope."


def _bundle_conditions(context: ProviderContext) -> set[str]:
    if context.evidence_bundle is None:
        return set()
    for detector in context.evidence_bundle.detector_results:
        for observation in detector.observations:
            if observation.id == "metadata.file_format" and isinstance(observation.value, dict) and observation.value.get("format") == "JPEG":
                return {"JPEG_FILE"}
    return set()


def _temperature_scale(score: float, temperature: float) -> float:
    clipped = min(max(score, 1e-6), 1 - 1e-6)
    logit = log(clipped / (1 - clipped))
    return 1.0 / (1.0 + exp(-logit / temperature))
