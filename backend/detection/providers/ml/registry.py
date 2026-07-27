"""File-backed P4-B model and calibration registry resolver."""

from __future__ import annotations

import json
from pathlib import Path

from .governance import GovernedCalibrationRecord, GovernedModelRecord, ModelGovernanceError


class ModelCalibrationRegistry:
    """Resolves immutable model/calibration records from governed registry files."""

    def __init__(self, model_directory: str | Path, calibration_directory: str | Path) -> None:
        self._models = _load_models(Path(model_directory))
        self._calibrations = _load_calibrations(Path(calibration_directory))

    def resolve(self, model_id: str, version: str) -> tuple[GovernedModelRecord, GovernedCalibrationRecord]:
        try:
            model = self._models[(model_id, version)]
        except KeyError as exc:
            raise ModelGovernanceError(f"Model {model_id}@{version} is not registered.") from exc
        try:
            calibration = self._calibrations[model.calibration_reference]
        except KeyError as exc:
            raise ModelGovernanceError(f"Calibration {model.calibration_reference} is not registered.") from exc
        return model, calibration


def _load_models(directory: Path) -> dict[tuple[str, str], GovernedModelRecord]:
    records: dict[tuple[str, str], GovernedModelRecord] = {}
    for path in sorted(directory.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        record = GovernedModelRecord(**{**raw, "validation_scope": tuple(raw["validation_scope"]), "limitations": tuple(raw["limitations"])})
        key = (record.model_id, record.version)
        if key in records:
            raise ModelGovernanceError(f"Duplicate registered model {record.model_id}@{record.version}.")
        records[key] = record
    return records


def _load_calibrations(directory: Path) -> dict[str, GovernedCalibrationRecord]:
    records: dict[str, GovernedCalibrationRecord] = {}
    for path in sorted(directory.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8") )
        record = GovernedCalibrationRecord(**{**raw, "scope": tuple(raw["scope"]), "excluded_conditions": tuple(raw["excluded_conditions"]), "limitations": tuple(raw["limitations"])})
        if record.calibration_id in records:
            raise ModelGovernanceError(f"Duplicate registered calibration {record.calibration_id}.")
        records[record.calibration_id] = record
    return records
