from __future__ import annotations

from hashlib import sha256
from io import BytesIO

import pytest
from PIL import Image

from authentication import AuthenticationReportEngine
from detection.providers import (
    C2paProvider,
    DetectionEvidence,
    ForensicProvider,
    MetadataProvider,
    ProviderContext,
    ProviderRegistrationError,
    ProviderRegistry,
    ProviderRegistryEntry,
)
from governance import EvidenceProvenance


def _png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (24, 16), (16, 32, 64)).save(output, format="PNG")
    return output.getvalue()


def _entry(provider, status="approved") -> ProviderRegistryEntry:
    provider_type = {"p1.metadata": "metadata", "p1.c2pa": "c2pa", "p1.forensic": "forensic"}[provider.provider_id]
    return ProviderRegistryEntry(provider.provider_id, provider.provider_version, provider_type, status, "docs/validation/provider-fixture.md", ("Fixture-only provider registration; not a model validation claim.",))


def test_detection_evidence_requires_complete_matching_provenance():
    provenance = EvidenceProvenance("provider.example.obs", "external", "v1", "2026-07-27T00:00:00+00:00", "a" * 64, "declared", {"value": "x"}, "bounded")
    evidence = DetectionEvidence("example", "v1", {"value": "x"}, None, "declared", "fixture", ("bounded",), provenance)
    assert evidence.to_dict()["evidence_provenance"]["input_hash"] == "a" * 64
    with pytest.raises(ValueError, match="detector_version"):
        DetectionEvidence("example", "v2", {"value": "x"}, None, "declared", "fixture", ("bounded",), provenance)
    with pytest.raises(ValueError, match="unsupported status"):
        ProviderRegistryEntry("example", "v1", "external", "unreviewed", "fixture", ("bounded",))
    with pytest.raises(ValueError, match="requires non-empty"):
        EvidenceProvenance("provider.example.obs", "external", "v1", "", "a" * 64, "declared", {"value": "x"}, "bounded")


def test_unregistered_provider_is_rejected_before_collection():
    registry = ProviderRegistry()
    provider = MetadataProvider()
    with pytest.raises(ProviderRegistrationError, match="not registered"):
        registry.collect_for_formal_report((provider,), _png(), ProviderContext("a" * 64, "2026-07-27T00:00:00+00:00"))


def test_collection_rejects_context_hash_not_bound_to_image_bytes():
    registry = ProviderRegistry()
    provider = MetadataProvider()
    registry.register(_entry(provider))
    with pytest.raises(ProviderRegistrationError, match="does not match image bytes"):
        registry.collect_for_formal_report((provider,), _png(), ProviderContext("a" * 64, "2026-07-27T00:00:00+00:00"))


def test_validated_but_unapproved_provider_is_excluded_without_execution():
    registry = ProviderRegistry()
    provider = MetadataProvider()
    registry.register(_entry(provider, "validated"))
    image = _png()
    collection = registry.collect_for_formal_report((provider,), image, ProviderContext(sha256(image).hexdigest(), "2026-07-27T00:00:00+00:00"))
    assert collection.evidence == ()
    assert collection.exclusions[0]["status"] == "validated"


def test_approved_p1_providers_enter_fusion_without_changing_status(tmp_path):
    registry = ProviderRegistry()
    providers = (MetadataProvider(), C2paProvider(), ForensicProvider())
    for provider in providers:
        registry.register(_entry(provider))
    report = AuthenticationReportEngine().create(_png(), tmp_path, submitter_id="reviewer", provider_registry=registry, providers=providers)
    assert report.assessment.authenticity_status == "uncertain"
    assert report.evidence["providers"]
    assert all(item["evidence_provenance"]["input_hash"] == report.input_sha256 for item in report.evidence["providers"])
    assert all(item["evidence_provenance"]["timestamp"] == report.analysis_time_utc for item in report.evidence["providers"])
    assert len(report.evidence["fusion_trace_evidence_ids"]) == len(report.evidence["providers"])
    c2pa = next(item for item in report.evidence["providers"] if item["provider_id"] == "p1.c2pa")
    assert c2pa["observation"]["value"] == "NOT_PRESENT"


def test_engine_records_unapproved_provider_isolation(tmp_path):
    registry = ProviderRegistry()
    provider = MetadataProvider()
    registry.register(_entry(provider, "experimental"))
    report = AuthenticationReportEngine().create(_png(), tmp_path, submitter_id="reviewer", provider_registry=registry, providers=(provider,))
    assert report.evidence["providers"] == []
    assert report.evidence["provider_exclusions"][0]["status"] == "experimental"
    assert report.assessment.authenticity_status == "uncertain"
