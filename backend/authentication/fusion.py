"""Conservative, declared evidence-fusion rules for reviewer-facing reports."""
from __future__ import annotations

from evidence.models import EvidenceBundle

from .models import AuthenticityAssessment, ModelEvidence

ADMITTED_MODEL_EVIDENCE_IDS = frozenset()

def assess(bundle: EvidenceBundle, model_evidence: ModelEvidence | None = None) -> AuthenticityAssessment:
    provenance = _provenance_observations(bundle)
    summary = ["Deterministic metadata, frequency, noise, compression, and artifact observations were extracted."]
    limitations = ["The assessment is an aid to human review, not an origin fact or judicial conclusion.", "Absence of EXIF, C2PA, or provenance data is not evidence that an image is AI-generated."]
    if provenance:
        summary.append("Source/provenance observations are included without converting them into a truth claim.")
    if model_evidence is None:
        limitations.append("No admitted calibrated vision-model evidence was available; no model score was used in fusion.")
        return AuthenticityAssessment("uncertain", "low", tuple(summary), tuple(limitations))
    observation_ids = {observation.id for detector in bundle.detector_results for observation in detector.observations}
    if not model_evidence.calibrated or model_evidence.score is None or model_evidence.admission_id not in ADMITTED_MODEL_EVIDENCE_IDS or not set(model_evidence.corroborating_observation_ids) <= observation_ids:
        limitations.append("Model evidence was excluded because it is absent, uncalibrated, or outside its declared population scope.")
        return AuthenticityAssessment("uncertain", "low", tuple(summary), tuple(limitations))
    summary.append(f"Calibrated auxiliary model evidence {model_evidence.identifier}@{model_evidence.version} was considered within its declared scope.")
    limitations.append(model_evidence.limitation)
    if model_evidence.score >= 0.9 and _has_validated_c2pa(bundle) and model_evidence.corroborating_observation_ids:
        return AuthenticityAssessment("likely_ai_generated", "moderate", tuple(summary), tuple(limitations))
    if model_evidence.score <= 0.1 and _has_validated_c2pa(bundle):
        return AuthenticityAssessment("likely_real", "moderate", tuple(summary), tuple(limitations))
    return AuthenticityAssessment("uncertain", "low", tuple(summary), tuple(limitations))


def _provenance_observations(bundle: EvidenceBundle) -> list[str]:
    return [observation.type for detector in bundle.detector_results for observation in detector.observations if "c2pa" in observation.type.lower() or "provenance" in observation.type.lower()]


def _has_validated_c2pa(bundle: EvidenceBundle) -> bool:
    return any(observation.type == "c2pa_declaration_read" and observation.value == "cryptographically_validated" for detector in bundle.detector_results for observation in detector.observations)
