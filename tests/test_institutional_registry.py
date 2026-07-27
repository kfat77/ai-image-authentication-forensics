from dataclasses import replace
from io import BytesIO

import pytest
from PIL import Image

from authentication import AuthenticationReportEngine
from authentication.engine import _hash_payload
from deployment.key_provider import LocalTestKeyProvider
from detection.providers import MetadataProvider, ProviderRegistry, ProviderRegistryEntry
from institutional_registry import ApprovalStatus, InstitutionalRegistry, verify_registry_record
from institutional import Role


H = "a" * 64


def _registry() -> InstitutionalRegistry:
    return InstitutionalRegistry(LocalTestKeyProvider(b"registry-test-key"))


def _model_payload(provider_id="p1.metadata"):
    return {"model_id": "m", "version": "v1", "architecture": "linear", "weight_hash": H, "source": "official", "license": "BSD", "training_data_reference": "dataset", "evaluation_reference": "evaluation", "calibration_id": "c1", "provider_id": provider_id, "details": {"revision": "initial"}}


def _calibration_payload(model_id="m"):
    return {"calibration_id": "c1", "model_id": model_id, "dataset_reference": "dataset", "method": "temperature", "metrics": {"ece": 0.1}, "threshold": 0.5, "scope": ["JPEG_FILE"], "limitations": ["bounded"]}


def _advance(registry, record):
    for state in (ApprovalStatus.SUBMITTED, ApprovalStatus.VALIDATED, ApprovalStatus.REVIEWED, ApprovalStatus.APPROVED):
        roles = {ApprovalStatus.SUBMITTED: {Role.ANALYST}, ApprovalStatus.VALIDATED: {Role.REVIEWER}, ApprovalStatus.REVIEWED: {Role.REVIEWER}, ApprovalStatus.APPROVED: {Role.ADMIN}}[state]
        record = registry.transition(record.record_hash, state, "approver" if state == ApprovalStatus.APPROVED else "validator", "review recorded", roles)
    return record


def _approved(registry, calibration_model_id="m"):
    model = _advance(registry, registry.create_model(_model_payload(), "submitter", {Role.ANALYST}))
    calibration = _advance(registry, registry.create_calibration(_calibration_payload(calibration_model_id), "submitter", {Role.ANALYST}))
    return model, calibration


def _png():
    output = BytesIO(); Image.new("RGB", (8, 8)).save(output, format="PNG"); return output.getvalue()


def test_approval_history_is_append_only_and_detects_tampering_and_deletion():
    registry = _registry()
    draft = registry.create_model(_model_payload(), "submitter", {Role.ANALYST})
    model = _advance(registry, draft)
    history = registry.approval_history(model.record_id)
    assert len(history) == 5 and registry.verify_approval_history(model.record_id)
    assert not registry.verify_approval_history(model.record_id, history[1:])  # deleted DRAFT event
    tampered = list(history)
    tampered[2] = replace(tampered[2], reason="altered")
    assert not registry.verify_approval_history(model.record_id, tampered)
    assert draft.record_hash in registry._records and model.record_hash in registry._records
    assert len([item for item in registry._records.values() if item.record_id == model.record_id]) == 5
    with pytest.raises(TypeError, match="immutable"):
        model.payload["source"] = "altered"
    with pytest.raises(TypeError, match="immutable"):
        model.payload["details"]["revision"] = "altered"


def test_signature_covers_record_and_all_signature_metadata():
    registry = _registry(); record = registry.create_model(_model_payload(), "submitter", {Role.ANALYST})
    keys = {record.signature.key_id: LocalTestKeyProvider(b"registry-test-key")}
    assert verify_registry_record(record, keys)
    assert not verify_registry_record(replace(record, payload={**record.payload, "source": "changed"}), keys)
    assert not verify_registry_record(replace(record, signature=replace(record.signature, signer_id="other")), keys)
    assert not verify_registry_record(replace(record, signature=replace(record.signature, signing_algorithm="other-algorithm")), keys)
    assert not verify_registry_record(replace(record, signature=replace(record.signature, signing_time="2030-01-01T00:00:00+00:00")), keys)
    assert not verify_registry_record(replace(record, signature=replace(record.signature, key_provider_id="another-key")), keys)


def test_provider_admission_rejects_model_calibration_scope_and_provider_mismatches():
    registry = _registry(); registry.register_provider("p1.metadata", "v1")
    model, calibration = _approved(registry)
    admission = registry.admit_provider("p1.metadata", "v1", model.record_hash, calibration.record_hash, ("JPEG_FILE",))
    assert registry.verify_provider_admission(admission)
    with pytest.raises(ValueError, match="scope"):
        registry.admit_provider("p1.metadata", "v1", model.record_hash, calibration.record_hash, ("PNG_FILE",))
    wrong_model, wrong_calibration = _approved(registry, calibration_model_id="other-model")
    with pytest.raises(ValueError, match="inconsistent"):
        registry.admit_provider("p1.metadata", "v1", wrong_model.record_hash, wrong_calibration.record_hash, ("JPEG_FILE",))
    with pytest.raises(ValueError, match="not registered"):
        registry.admit_provider("unknown", "v1", model.record_hash, calibration.record_hash, ("JPEG_FILE",))


def test_approval_requires_separated_roles_and_actors():
    registry = _registry()
    with pytest.raises(PermissionError, match="ANALYST"):
        registry.create_model(_model_payload(), "submitter", {Role.REVIEWER})
    draft = registry.create_model(_model_payload(), "submitter", {Role.ANALYST})
    submitted = registry.transition(draft.record_hash, ApprovalStatus.SUBMITTED, "submitter", "submitted", {Role.ANALYST})
    with pytest.raises(PermissionError, match="REVIEWER"):
        registry.transition(submitted.record_hash, ApprovalStatus.VALIDATED, "submitter", "not authorized", {Role.ANALYST})


def test_unverified_registry_hash_is_rejected_before_provider_admission():
    registry = _registry(); registry.register_provider("p1.metadata", "v1")
    model, calibration = _approved(registry)
    registry._records[model.record_hash] = replace(model, signature=replace(model.signature, signer_id="forged"))
    with pytest.raises(ValueError, match="signature verification"):
        registry.admit_provider("p1.metadata", "v1", model.record_hash, calibration.record_hash, ("JPEG_FILE",))


def test_report_uses_realtime_verified_registry_references_not_caller_hashes(tmp_path):
    institutional = _registry(); institutional.register_provider("p1.metadata", "p1-adapter.1")
    model, calibration = _approved(institutional)
    admission = institutional.admit_provider("p1.metadata", "p1-adapter.1", model.record_hash, calibration.record_hash, ("JPEG_FILE",))
    provider = MetadataProvider(); provider_registry = ProviderRegistry()
    provider_registry.register(ProviderRegistryEntry(provider.provider_id, provider.provider_version, "metadata", "approved", "fixture", ("bounded",)))
    report = AuthenticationReportEngine().create(_png(), tmp_path, "reviewer", provider_registry=provider_registry, providers=(provider,), institutional_registry=institutional)
    provider_evidence = report.evidence["providers"][0]
    assert provider_evidence["registry_verified"] is True
    assert provider_evidence["verified_record_hash"] == admission.record_hash
    assert report.evidence["registry_references"][0]["model_record_hash"] == model.record_hash
    # The report output hash covers the Registry-derived references, so an
    # independent recomputation catches any subsequent report modification.
    assert _hash_payload(report.to_dict()) == report.output_sha256
    payload = report.to_dict(); payload["evidence"]["registry_references"][0]["model_record_hash"] = "0" * 64
    assert _hash_payload(payload) != report.output_sha256
