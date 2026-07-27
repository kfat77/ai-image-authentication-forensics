"""Detection-provider interfaces, built-in adapters, and formal-report registry gate."""

from .builtin import C2paProvider, ForensicProvider, MetadataProvider
from .models import DetectionEvidence, ProviderContext, ProviderRegistryEntry, ProviderStatus, ProviderType
from .registry import DetectionProvider, ProviderCollection, ProviderRegistrationError, ProviderRegistry

__all__ = [
    "C2paProvider",
    "DetectionEvidence",
    "DetectionProvider",
    "ForensicProvider",
    "MetadataProvider",
    "ProviderCollection",
    "ProviderContext",
    "ProviderRegistrationError",
    "ProviderRegistry",
    "ProviderRegistryEntry",
    "ProviderStatus",
    "ProviderType",
]
