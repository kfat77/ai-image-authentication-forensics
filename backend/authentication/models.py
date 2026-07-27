"""Stable, JSON-safe contracts for authentication reporting."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


AuthenticityStatus = Literal["likely_real", "likely_ai_generated", "uncertain"]
ConfidenceLevel = Literal["low", "moderate", "high"]


@dataclass(frozen=True)
class ModelEvidence:
    identifier: str
    version: str
    calibrated: bool
    population_scope: str
    score: float | None
    admission_id: str
    corroborating_observation_ids: tuple[str, ...]
    limitation: str


@dataclass(frozen=True)
class AuthenticityAssessment:
    authenticity_status: AuthenticityStatus
    confidence_level: ConfidenceLevel
    evidence_summary: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class AuthenticationReport:
    report_version: str
    analysis_id: str
    analysis_time_utc: str
    input_sha256: str
    tool_versions: dict[str, str]
    assessment: AuthenticityAssessment
    risk_level: Literal["low", "moderate", "high"]
    evidence: dict[str, Any]
    audit_trail: dict[str, str]
    output_files: dict[str, str]
    limitations: tuple[str, ...]
    output_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["assessment"]["evidence_summary"] = list(self.assessment.evidence_summary)
        payload["assessment"]["limitations"] = list(self.assessment.limitations)
        payload["limitations"] = list(self.limitations)
        return payload
