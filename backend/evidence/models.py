"""Stable P1 evidence records with no origin or AI-generation verdict fields."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


EvidenceLevel = Literal["E0", "E1", "E2", "E3", "E4"]
DetectorStatus = Literal["available", "unavailable", "unsupported", "failed"]
_EVIDENCE_RANK = {"E0": 0, "E1": 1, "E2": 2, "E3": 3, "E4": 4}


@dataclass(frozen=True)
class Observation:
    id: str
    type: str
    value: Any
    source: str
    confidence: str
    limitation: str
    evidence_level: EvidenceLevel
    method_version: str
    scope: str


@dataclass(frozen=True)
class ArtifactFile:
    name: str
    path: str
    sha256: str
    media_type: str
    byte_size: int
    transform: str
    color_mapping: str
    coordinate_system: str
    source_observation_ids: tuple[str, ...]
    limitation: str


@dataclass(frozen=True)
class SuspiciousRegion:
    region_id: str
    x: float
    y: float
    width: float
    height: float
    detector: str
    description: str
    relative_strength: float
    source_observation_id: str
    limitation: str


@dataclass(frozen=True)
class DetectorResult:
    name: str
    version: str
    status: DetectorStatus
    evidence_ceiling: EvidenceLevel
    parameters: dict[str, Any]
    observations: tuple[Observation, ...]
    artifacts: tuple[ArtifactFile, ...]
    suspicious_regions: tuple[SuspiciousRegion, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceBundle:
    input_sha256: str
    processing_version: str
    parameters: dict[str, Any]
    detector_results: tuple[DetectorResult, ...]
    artifacts: tuple[ArtifactFile, ...]
    limitations: tuple[str, ...]
    manifest_path: str = "evidence-bundle.json"

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe evidence only; the P1 contract intentionally has no verdict fields."""
        return {
            "input_sha256": self.input_sha256,
            "processing_version": self.processing_version,
            "parameters": self.parameters,
            "detectors": [
                {
                    "name": result.name,
                    "version": result.version,
                    "status": result.status,
                    "evidence_ceiling": result.evidence_ceiling,
                    "parameters": result.parameters,
                    "observations": [asdict(observation) for observation in result.observations],
                    "artifacts": [asdict(artifact) for artifact in result.artifacts],
                    "suspicious_regions": [asdict(region) for region in result.suspicious_regions],
                    "limitations": list(result.limitations),
                }
                for result in self.detector_results
            ],
            "output_files": [asdict(artifact) for artifact in self.artifacts],
            "limitations": list(self.limitations),
            "manifest_path": self.manifest_path,
        }


def validate_bundle(bundle: EvidenceBundle) -> None:
    """Enforce the P0 evidence and visualization traceability invariants before persistence."""
    observation_ids: set[str] = set()
    for result in bundle.detector_results:
        if result.status not in {"available", "unavailable", "unsupported", "failed"}:
            raise ValueError(f"Unsupported detector status: {result.status}")
        if result.evidence_ceiling not in _EVIDENCE_RANK:
            raise ValueError(f"Unsupported evidence ceiling: {result.evidence_ceiling}")
        if result.status != "available" and not result.observations:
            raise ValueError(f"Unavailable detector {result.name} must emit an explicit E0 observation.")
        for observation in result.observations:
            if observation.id in observation_ids:
                raise ValueError(f"Duplicate observation ID: {observation.id}")
            observation_ids.add(observation.id)
            if observation.evidence_level not in _EVIDENCE_RANK:
                raise ValueError(f"Unsupported evidence level: {observation.evidence_level}")
            if _EVIDENCE_RANK[observation.evidence_level] > _EVIDENCE_RANK[result.evidence_ceiling]:
                raise ValueError(f"Observation {observation.id} exceeds {result.name} evidence ceiling.")
            if result.status != "available" and observation.evidence_level != "E0":
                raise ValueError(f"Unavailable detector {result.name} may only emit E0 observations.")
        for region in result.suspicious_regions:
            if region.source_observation_id not in observation_ids:
                raise ValueError(f"Region {region.region_id} references an unknown observation.")
    for artifact in bundle.artifacts:
        if not artifact.source_observation_ids:
            raise ValueError(f"Artifact {artifact.path} must reference at least one observation.")
        if not set(artifact.source_observation_ids) <= observation_ids:
            raise ValueError(f"Artifact {artifact.path} references an unknown observation.")
