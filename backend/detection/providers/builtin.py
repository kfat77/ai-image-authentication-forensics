"""Adapters that re-express existing P1 observations as governed provider evidence."""

from __future__ import annotations

from dataclasses import dataclass

from governance import EvidenceProvenance

from .models import DetectionEvidence, ProviderContext


@dataclass(frozen=True)
class MetadataProvider:
    provider_id: str = "p1.metadata"
    provider_version: str = "p1-adapter.1"

    def detect(self, image: bytes, context: ProviderContext) -> tuple[DetectionEvidence, ...]:
        return _from_bundle(self.provider_id, self.provider_version, context, {"metadata"}, include_c2pa=False)


@dataclass(frozen=True)
class C2paProvider:
    provider_id: str = "p1.c2pa"
    provider_version: str = "p1-adapter.1"

    def detect(self, image: bytes, context: ProviderContext) -> tuple[DetectionEvidence, ...]:
        return _from_bundle(self.provider_id, self.provider_version, context, {"metadata"}, include_c2pa=True, only_c2pa=True)


@dataclass(frozen=True)
class ForensicProvider:
    provider_id: str = "p1.forensic"
    provider_version: str = "p1-adapter.1"

    def detect(self, image: bytes, context: ProviderContext) -> tuple[DetectionEvidence, ...]:
        return _from_bundle(self.provider_id, self.provider_version, context, {"frequency", "noise", "artifact"}, include_c2pa=False)


def _from_bundle(provider_id: str, provider_version: str, context: ProviderContext, detector_names: set[str], *, include_c2pa: bool, only_c2pa: bool = False) -> tuple[DetectionEvidence, ...]:
    if context.evidence_bundle is None:
        raise ValueError("Built-in P1 provider adapters require an EvidenceBundle in their context.")
    collected: list[DetectionEvidence] = []
    for detector in context.evidence_bundle.detector_results:
        if detector.name not in detector_names:
            continue
        for observation in detector.observations:
            is_c2pa = "c2pa" in observation.type.lower()
            if only_c2pa != is_c2pa:
                continue
            if is_c2pa and not include_c2pa:
                continue
            source_type = "c2pa" if is_c2pa else _source_type(detector.name, observation.type)
            value = _c2pa_status(observation.value) if is_c2pa else observation.value
            limitation = observation.limitation
            provenance = EvidenceProvenance(
                evidence_id=f"provider.{provider_id}.{observation.id}",
                source_type=source_type,
                detector_version=provider_version,
                timestamp=context.collected_at_utc,
                input_hash=context.input_hash,
                reliability=observation.confidence,
                observation={"source_observation_id": observation.id, "type": observation.type, "value": value},
                limitation=limitation,
            )
            collected.append(
                DetectionEvidence(
                    provider_id=provider_id,
                    provider_version=provider_version,
                    observation={"source_observation_id": observation.id, "type": observation.type, "value": value, "source": observation.source},
                    score=None,
                    confidence=observation.confidence,
                    validation_scope=observation.scope,
                    limitations=(limitation,),
                    evidence_provenance=provenance,
                )
            )
    return tuple(collected)


def _source_type(detector_name: str, observation_type: str) -> str:
    if observation_type.startswith("exif"):
        return "exif"
    return {"metadata": "metadata", "frequency": "frequency", "noise": "noise", "artifact": "artifact"}[detector_name]


def _c2pa_status(value: object) -> str:
    if value == "no_embedded_marker_observed":
        return "NOT_PRESENT"
    return "UNKNOWN"
