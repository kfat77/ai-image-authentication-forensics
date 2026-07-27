"""Governed ML detector provider contracts; no model weights are bundled here."""

from .governance import GovernedCalibrationRecord, GovernedModelRecord, ModelGovernanceError, validate_model_admission
from .provider import MLDetectorProvider, VerifiedScoreReader
from .registry import ModelCalibrationRegistry
from .scope import ScopeAttestationVerifier

__all__ = ["GovernedCalibrationRecord", "GovernedModelRecord", "MLDetectorProvider", "ModelCalibrationRegistry", "ModelGovernanceError", "ScopeAttestationVerifier", "VerifiedScoreReader", "validate_model_admission"]
