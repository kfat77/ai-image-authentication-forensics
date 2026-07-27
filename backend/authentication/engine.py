"""Build hash-bound JSON reports from the deterministic P1 evidence engine."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from evidence import extract_evidence
from detection.providers import DetectionProvider, ProviderContext, ProviderRegistry, ScopeAttestation

from .fusion import ADMITTED_MODEL_EVIDENCE_IDS, assess
from .models import AuthenticationReport, ModelEvidence
from .pdf_report import render_pdf


REPORT_VERSION = "p4a.authentication.1"


class AuthenticationReportEngine:
    def create(self, contents: bytes, output_directory: str | Path, submitter_id: str, model_evidence: ModelEvidence | None = None, provider_registry: ProviderRegistry | None = None, providers: tuple[DetectionProvider, ...] = (), provider_scope_attestation: ScopeAttestation | None = None) -> AuthenticationReport:
        root = Path(output_directory)
        root.mkdir(parents=True, exist_ok=True)
        analysis_time = datetime.now(timezone.utc).isoformat()
        analysis_id = sha256((sha256(contents).hexdigest() + analysis_time).encode()).hexdigest()[:24]
        case_root = root / analysis_id
        bundle = extract_evidence(contents, case_root / "evidence")
        if providers and provider_registry is None:
            raise ValueError("Provider collection requires a registry.")
        collection = provider_registry.collect_for_formal_report(providers, contents, ProviderContext(bundle.input_sha256, analysis_time, bundle, provider_scope_attestation)) if providers else None
        provider_evidence = () if collection is None else collection.evidence
        assessment = assess(bundle, model_evidence, provider_evidence)
        observation_trace_ids = _fusion_trace_observations(model_evidence)
        provider_trace_ids = [item.evidence_provenance.evidence_id for item in provider_evidence]
        evidence = {"methods": [{"name": detector.name, "version": detector.version, "status": detector.status} for detector in bundle.detector_results], "provenance": _observations(bundle, "metadata"), "image": _image_observations(bundle), "providers": [item.to_dict() for item in provider_evidence], "provider_exclusions": [] if collection is None else list(collection.exclusions), "model_evidence": [item.to_dict() for item in provider_evidence if item.evidence_provenance.source_type == "model"], "model": None if model_evidence is None else model_evidence.__dict__, "fusion_trace_observation_ids": observation_trace_ids, "fusion_trace_evidence_ids": provider_trace_ids, "evidence_completeness": _completeness(bundle, model_evidence), "explainability_score": _explainability(bundle, observation_trace_ids, provider_trace_ids, provider_evidence), "evaluation_metrics": {"false_positive_rate": "not_evaluated_without_approved_labeled_population", "false_negative_rate": "not_evaluated_without_approved_labeled_population", "report_reproducibility": "input_hash_plus_versioned_methods"}}
        evidence_manifest = case_root / "evidence" / bundle.manifest_path
        provisional = AuthenticationReport(REPORT_VERSION, analysis_id, analysis_time, bundle.input_sha256, {"authentication": REPORT_VERSION, "evidence": bundle.processing_version, "provider_layer": "p4a.provider.1"}, assessment, _risk_level(assessment.authenticity_status), evidence, {"submitter_id": submitter_id, "input_sha256": bundle.input_sha256, "analysis_time_utc": analysis_time, "tool_version": REPORT_VERSION, "output_sha256": "pending"}, {"evidence_manifest_sha256": _sha_path(evidence_manifest)}, tuple(bundle.limitations) + assessment.limitations)
        pdf_path = case_root / "authentication-report.pdf"
        output_hash = _hash_payload(provisional.to_dict())
        report = AuthenticationReport(**{**provisional.__dict__, "output_sha256": output_hash, "audit_trail": {**provisional.audit_trail, "output_sha256": output_hash}})
        json_path = case_root / "authentication-report.json"
        json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        render_pdf(report, pdf_path)
        audit_entry = {**report.audit_trail, "json_sha256": _sha_path(json_path), "pdf_sha256": _sha_path(pdf_path), "case_directory": analysis_id}
        with (root / "audit-trail.jsonl").open("a", encoding="utf-8") as audit_stream:
            audit_stream.write(json.dumps(audit_entry, sort_keys=True) + "\n")
        return report


def _hash_payload(payload: dict[str, object]) -> str:
    payload = {**payload, "output_sha256": "", "audit_trail": {**payload["audit_trail"], "output_sha256": ""}}
    return sha256(json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _observations(bundle, detector_name: str) -> list[dict[str, object]]:
    return [observation.__dict__ for detector in bundle.detector_results if detector.name == detector_name for observation in detector.observations]


def _image_observations(bundle) -> list[dict[str, object]]:
    return [observation.__dict__ for detector in bundle.detector_results if detector.name != "metadata" for observation in detector.observations]


def _completeness(bundle, model_evidence: ModelEvidence | None) -> float:
    metadata = _observations(bundle, "metadata")
    categories = {"metadata": any(item["type"] not in {"exif_status", "c2pa_declaration_read"} for item in metadata), "validated_provenance": any(item["type"] == "c2pa_declaration_read" and item["value"] == "cryptographically_validated" for item in metadata), "image": any(detector.name in {"frequency", "noise", "artifact"} and detector.status == "available" for detector in bundle.detector_results), "model": model_evidence is not None and model_evidence.calibrated and model_evidence.admission_id in ADMITTED_MODEL_EVIDENCE_IDS and bool(model_evidence.corroborating_observation_ids)}
    return round(sum(categories.values()) / len(categories), 3)


def _explainability(bundle, observation_trace_ids: list[str], provider_trace_ids: list[str], provider_evidence=()) -> float:
    observations = [observation for detector in bundle.detector_results for observation in detector.observations]
    traced = [item for item in observations if item.id in observation_trace_ids]
    provider_complete = [item for item in provider_evidence if item.evidence_provenance.evidence_id in provider_trace_ids]
    complete = sum(bool(item.limitation and item.source and item.method_version) for item in traced) + sum(bool(item.evidence_provenance.timestamp and item.evidence_provenance.input_hash and item.limitations) for item in provider_complete)
    total = len(traced) + len(provider_evidence)
    return round(complete / total, 3) if total else 0.0


def _fusion_trace_observations(model_evidence: ModelEvidence | None) -> list[str]:
    return [] if model_evidence is None else list(model_evidence.corroborating_observation_ids)


def _sha_path(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _risk_level(status: str) -> str:
    return {"likely_real": "low", "likely_ai_generated": "high", "uncertain": "moderate"}[status]
