"""Governed model and calibration records for ML detector providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from governance import CalibrationRegistryEntry, ModelRegistryEntry, validate_model_calibration_integrity


ModelStatus = Literal["experimental", "validated", "approved"]


class ModelGovernanceError(ValueError):
    """Raised before an ML model can produce formal provider evidence."""


@dataclass(frozen=True)
class GovernedModelRecord:
    model_id: str
    version: str
    architecture: str
    weight_hash: str
    source: str
    license: str
    dataset_reference: str
    evaluation_reference: str
    calibration_reference: str
    status: ModelStatus
    validation_scope: tuple[str, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in {"experimental", "validated", "approved"}:
            raise ModelGovernanceError("Model status must be experimental, validated, or approved.")
        if not self.validation_scope or not self.limitations:
            raise ModelGovernanceError("A governed model requires scope and limitations.")
        ModelRegistryEntry(
            self.model_id,
            self.model_id,
            self.version,
            self.architecture,
            self.weight_hash,
            self.source,
            self.license,
            self.dataset_reference,
            self.evaluation_reference,
            self.calibration_reference,
            "; ".join(self.validation_scope),
            self.limitations,
            "approved" if self.status == "approved" else "draft",
        )


@dataclass(frozen=True)
class GovernedCalibrationRecord:
    calibration_id: str
    model_id: str
    model_version: str
    threshold: float
    ece: float
    brier: float
    validation_dataset: str
    validation_date: str
    scope: tuple[str, ...]
    excluded_conditions: tuple[str, ...]
    limitations: tuple[str, ...]
    metrics: dict[str, float]
    calibration_method: Literal["temperature_scaling"]
    calibration_parameters: dict[str, float]

    def __post_init__(self) -> None:
        if not self.scope or not self.excluded_conditions or not self.limitations:
            raise ModelGovernanceError("A calibration record requires scope, excluded conditions, and limitations.")
        if self.calibration_method != "temperature_scaling" or self.calibration_parameters.get("temperature", 0) <= 0:
            raise ModelGovernanceError("P4-B requires a positive registered temperature-scaling calibration transform.")
        CalibrationRegistryEntry(
            self.calibration_id,
            self.model_version,
            self.validation_dataset,
            self.threshold,
            self.metrics,
            self.ece,
            self.brier,
            self.validation_date,
            self.scope,
            self.excluded_conditions,
        )


def validate_model_admission(model: GovernedModelRecord, calibration: GovernedCalibrationRecord) -> None:
    if model.status != "approved":
        raise ModelGovernanceError("Only an approved model may produce formal ML provider evidence.")
    if model.calibration_reference != calibration.calibration_id or model.model_id != calibration.model_id or model.version != calibration.model_version:
        raise ModelGovernanceError("Model and calibration registry records do not match.")
    p3_model = ModelRegistryEntry(model.model_id, model.model_id, model.version, model.architecture, model.weight_hash, model.source, model.license, model.dataset_reference, model.evaluation_reference, model.calibration_reference, "; ".join(model.validation_scope), model.limitations, "approved")
    p3_calibration = CalibrationRegistryEntry(calibration.calibration_id, calibration.model_version, calibration.validation_dataset, calibration.threshold, calibration.metrics, calibration.ece, calibration.brier, calibration.validation_date, calibration.scope, calibration.excluded_conditions)
    validate_model_calibration_integrity(p3_model, [p3_calibration])
