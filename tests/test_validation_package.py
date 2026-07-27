from dataclasses import replace

import pytest

from deployment.key_provider import LocalTestKeyProvider
from institutional import Role
from institutional_registry import ApprovalStatus, InstitutionalRegistry
from validation_package import ValidationPackageBuilder, verify_validation_package


H = "a" * 64


def _approved_registry() -> InstitutionalRegistry:
    registry = InstitutionalRegistry(LocalTestKeyProvider(b"registry-package-test"))
    registry.register_provider("ml.fixture", "v1")
    model = registry.create_model({"model_id": "fixture", "version": "v1", "architecture": "linear", "weight_hash": H, "source": "official", "license": "BSD", "training_data_reference": "dataset", "evaluation_reference": "evaluation", "calibration_id": "cal-1", "provider_id": "ml.fixture"}, "analyst", {Role.ANALYST})
    calibration = registry.create_calibration({"calibration_id": "cal-1", "model_id": "fixture", "dataset_reference": "dataset", "method": "temperature", "metrics": {"ece": 0.1}, "threshold": 0.5, "scope": ["JPEG_FILE"], "limitations": ["fixture-only"]}, "analyst", {Role.ANALYST})
    for state in (ApprovalStatus.SUBMITTED, ApprovalStatus.VALIDATED, ApprovalStatus.REVIEWED, ApprovalStatus.APPROVED):
        roles = {ApprovalStatus.SUBMITTED: {Role.ANALYST}, ApprovalStatus.VALIDATED: {Role.REVIEWER}, ApprovalStatus.REVIEWED: {Role.REVIEWER}, ApprovalStatus.APPROVED: {Role.ADMIN}}[state]
        actor = "admin" if state == ApprovalStatus.APPROVED else "reviewer"
        model = registry.transition(model.record_hash, state, actor, "fixture transition", roles)
        calibration = registry.transition(calibration.record_hash, state, actor, "fixture transition", roles)
    registry.admit_provider("ml.fixture", "v1", model.record_hash, calibration.record_hash, ("JPEG_FILE",))
    return registry


def test_signed_validation_package_binds_verified_provider_dataset_and_signature_metadata():
    registry = _approved_registry(); signer = LocalTestKeyProvider(b"package-signature")
    package = ValidationPackageBuilder(registry, signer).create(provider_id="ml.fixture", provider_version="v1", dataset_manifest_hash=H, config={"split": "holdout"}, report_hashes=("b" * 64,), metrics_schema_hash="c" * 64, limitations=("fixture-only",), signer_id="validation-reviewer")
    assert verify_validation_package(package, {signer.key_id: signer})
    assert package.content["registry"]["registry_verified"] == "true"
    assert not verify_validation_package(replace(package, content={**package.content, "dataset_manifest_hash": "d" * 64}), {signer.key_id: signer})
    assert not verify_validation_package(replace(package, signature=replace(package.signature, signer_id="other")), {signer.key_id: signer})


def test_package_cannot_be_issued_without_a_verified_provider_admission():
    registry = InstitutionalRegistry(LocalTestKeyProvider(b"empty-registry")); signer = LocalTestKeyProvider(b"package-signature")
    with pytest.raises(KeyError):
        ValidationPackageBuilder(registry, signer).create(provider_id="ml.experimental", provider_version="v1", dataset_manifest_hash=H, config={"split": "holdout"}, report_hashes=("b" * 64,), metrics_schema_hash="c" * 64, limitations=("blocked",), signer_id="validation-reviewer")
