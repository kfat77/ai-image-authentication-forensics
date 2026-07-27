"""Detection-provider interfaces, built-in adapters, and formal-report registry gate."""

from .builtin import C2paProvider, ForensicProvider, MetadataProvider
from .models import DetectionEvidence, ProviderContext, ProviderRegistryEntry, ProviderStatus, ProviderType, ScopeAttestation
from .registry import DetectionProvider, ProviderCollection, ProviderRegistrationError, ProviderRegistry
from .ml import GovernedCalibrationRecord, GovernedModelRecord, MLDetectorProvider, ModelCalibrationRegistry, ModelGovernanceError, ScopeAttestationVerifier

__all__ = [
    "C2paProvider",
    "DetectionEvidence",
    "DetectionProvider",
    "ForensicProvider",
    "GovernedCalibrationRecord",
    "GovernedModelRecord",
    "MLDetectorProvider",
    "ModelCalibrationRegistry",
    "ModelGovernanceError",
    "MetadataProvider",
    "ProviderCollection",
    "ProviderContext",
    "ProviderRegistrationError",
    "ProviderRegistry",
    "ProviderRegistryEntry",
    "ProviderStatus",
    "ProviderType",
    "ScopeAttestation",
    "ScopeAttestationVerifier",
]
