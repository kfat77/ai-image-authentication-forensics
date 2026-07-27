from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

import pytest
from PIL import Image

from authentication import AuthenticationReportEngine
from detection.providers import ProviderContext, ProviderRegistrationError, ProviderRegistry, ProviderRegistryEntry, ScopeAttestation
from detection.providers.ml import MLDetectorProvider, ModelCalibrationRegistry, ModelGovernanceError
from detection.providers.ml import ScopeAttestationVerifier
from deployment.key_provider import LocalTestKeyProvider
from institutional_registry import ApprovalStatus, InstitutionalRegistry


HASH = "a" * 64


@dataclass(frozen=True)
class FixtureReader:
    weight_hash: str = HASH
    value: float = 0.63

    def score(self, image: bytes) -> float:
        return self.value


def _image() -> bytes:
    output = BytesIO()
    Image.new("RGB", (32, 24), (20, 40, 60)).save(output, format="JPEG")
    return output.getvalue()


def _write_registry(tmp_path: Path, *, status: str = "approved", calibration_id: str = "cal.fixture.v1", temperature: float = 1.0) -> ModelCalibrationRegistry:
    tmp_path.mkdir(parents=True, exist_ok=True)
    models = tmp_path / "models"; calibrations = tmp_path / "calibration"
    models.mkdir(); calibrations.mkdir()
    model = {"model_id": "fixture-efficientnet", "version": "v1", "architecture": "EfficientNet-B0 + linear logistic regression", "weight_hash": HASH, "source": "official-fixture-source", "license": "BSD-3-Clause", "dataset_reference": "licensed-fixture-dataset", "evaluation_reference": "experiments/p4b/fixture.json", "calibration_reference": calibration_id, "status": status, "validation_scope": ["JPEG_FILE", "ORIGINAL_CAPTURE_ATTESTED"], "limitations": ["Fixture model is test-only and not a detection claim."]}
    calibration = {"calibration_id": "cal.fixture.v1", "model_id": "fixture-efficientnet", "model_version": "v1", "threshold": 0.5, "ece": 0.1, "brier": 0.1, "validation_dataset": "licensed-fixture-validation", "validation_date": "2026-07-27T00:00:00+00:00", "scope": ["JPEG_FILE", "ORIGINAL_CAPTURE_ATTESTED"], "excluded_conditions": ["SCREENSHOT", "AI_EDITED", "LOW_RESOLUTION"], "limitations": ["Fixture calibration is test-only."], "metrics": {"accuracy": 0.5, "f1": 0.5, "auroc": 0.5}, "calibration_method": "temperature_scaling", "calibration_parameters": {"temperature": temperature}}
    (models / "fixture.json").write_text(json.dumps(model), encoding="utf-8")
    (calibrations / "fixture.json").write_text(json.dumps(calibration), encoding="utf-8")
    return ModelCalibrationRegistry(models, calibrations)


def _context(image: bytes, conditions: tuple[str, ...] = ("ORIGINAL_CAPTURE_ATTESTED",)) -> ProviderContext:
    digest = sha256(image).hexdigest()
    key = _scope_key()
    unsigned = ScopeAttestation(digest, conditions, "test signed intake fixture", key.key_id, "fixture")
    return ProviderContext(digest, "2026-07-27T00:00:00+00:00", scope_attestation=replace(unsigned, signature=key.sign(unsigned.payload())))


def _scope_key() -> LocalTestKeyProvider:
    return LocalTestKeyProvider(b"p4b-scope-test-key")


def _scope_verifier() -> ScopeAttestationVerifier:
    key = _scope_key()
    return ScopeAttestationVerifier({key.key_id: key})


def _institutional_admission() -> InstitutionalRegistry:
    """A test-only Registry of Record admission for the P4-B fixture provider."""
    registry = InstitutionalRegistry(LocalTestKeyProvider(b"p4c-registry-key"))
    registry.register_provider("ml.fixture-efficientnet", "v1")
    model = registry.create_model({"model_id": "fixture-efficientnet", "version": "v1", "architecture": "EfficientNet-B0 + linear logistic regression", "weight_hash": HASH, "source": "official-fixture-source", "license": "BSD-3-Clause", "training_data_reference": "licensed-fixture-dataset", "evaluation_reference": "experiments/p4b/fixture.json", "calibration_id": "cal.fixture.v1", "provider_id": "ml.fixture-efficientnet"}, "submitter")
    calibration = registry.create_calibration({"calibration_id": "cal.fixture.v1", "model_id": "fixture-efficientnet", "dataset_reference": "licensed-fixture-validation", "method": "temperature_scaling", "metrics": {"ece": 0.1, "brier": 0.1}, "threshold": 0.5, "scope": ["JPEG_FILE", "ORIGINAL_CAPTURE_ATTESTED"], "limitations": ["Fixture calibration is test-only."]}, "submitter")
    for state in (ApprovalStatus.SUBMITTED, ApprovalStatus.VALIDATED, ApprovalStatus.REVIEWED, ApprovalStatus.APPROVED):
        model = registry.transition(model.record_hash, state, "approver" if state == ApprovalStatus.APPROVED else "validator", "fixture review")
        calibration = registry.transition(calibration.record_hash, state, "approver" if state == ApprovalStatus.APPROVED else "validator", "fixture review")
    registry.admit_provider("ml.fixture-efficientnet", "v1", model.record_hash, calibration.record_hash, ("JPEG_FILE", "ORIGINAL_CAPTURE_ATTESTED"))
    return registry


def test_unapproved_or_uncalibrated_model_is_rejected(tmp_path):
    image = _image()
    with pytest.raises(ModelGovernanceError, match="approved"):
        MLDetectorProvider(_write_registry(tmp_path, status="validated"), "fixture-efficientnet", "v1", FixtureReader(), _scope_verifier()).detect(image, _context(image))
    with pytest.raises(ModelGovernanceError, match="not registered"):
        MLDetectorProvider(_write_registry(tmp_path / "missing", calibration_id="other"), "fixture-efficientnet", "v1", FixtureReader(), _scope_verifier())


def test_unregistered_ml_provider_is_rejected_by_provider_registry(tmp_path):
    image = _image()
    provider = MLDetectorProvider(_write_registry(tmp_path), "fixture-efficientnet", "v1", FixtureReader(), _scope_verifier())
    with pytest.raises(ProviderRegistrationError, match="not registered"):
        ProviderRegistry().collect_for_formal_report((provider,), image, _context(image))


def test_weight_hash_mismatch_is_rejected_before_out_of_scope_evidence(tmp_path):
    image = _image()
    with pytest.raises(ModelGovernanceError, match="weight hash"):
        MLDetectorProvider(_write_registry(tmp_path), "fixture-efficientnet", "v1", FixtureReader(weight_hash="b" * 64), _scope_verifier()).detect(image, _context(image, ("SCREENSHOT",)))


def test_out_of_scope_suppresses_score_and_preserves_provenance(tmp_path):
    image = _image()
    evidence = MLDetectorProvider(_write_registry(tmp_path), "fixture-efficientnet", "v1", FixtureReader(), _scope_verifier()).detect(image, _context(image, ("SCREENSHOT",)))
    assert evidence[0].observation["scope_status"] == "OUT_OF_SCOPE"
    assert evidence[0].score is None
    assert evidence[0].evidence_provenance.input_hash == sha256(image).hexdigest()
    assert evidence[0].evidence_provenance.timestamp == "2026-07-27T00:00:00+00:00"
    untrusted = MLDetectorProvider(_write_registry(tmp_path / "untrusted"), "fixture-efficientnet", "v1", FixtureReader()).detect(image, _context(image))
    assert untrusted[0].observation["scope_status"] == "OUT_OF_SCOPE"
    assert untrusted[0].confidence == "out_of_scope_no_model_score"


def test_approved_ml_provider_enters_report_as_calibrated_auxiliary_evidence(tmp_path):
    image = _image(); registry_path = _write_registry(tmp_path / "records")
    provider = MLDetectorProvider(registry_path, "fixture-efficientnet", "v1", FixtureReader(), _scope_verifier())
    registry = ProviderRegistry()
    registry.register(ProviderRegistryEntry(provider.provider_id, provider.provider_version, "ml_detector", "approved", "tests/test_ml_detector_provider.py", ("Fixture admission only; not an institutional approval.",)))
    report = AuthenticationReportEngine().create(image, tmp_path / "report", submitter_id="reviewer", provider_registry=registry, providers=(provider,), provider_scope_attestation=_context(image).scope_attestation, institutional_registry=_institutional_admission())
    assert report.assessment.authenticity_status == "uncertain"
    model_evidence = report.evidence["model_evidence"]
    assert model_evidence[0]["observation"]["score"] == pytest.approx(0.63)
    assert model_evidence[0]["observation"]["scope_status"] == "IN_SCOPE"
    assert model_evidence[0]["observation"]["validation"]["method"] == "temperature_scaling"
    assert model_evidence[0]["registry_verified"] is True


def test_ml_provider_without_registry_of_record_is_rejected_by_report_engine(tmp_path):
    image = _image(); provider = MLDetectorProvider(_write_registry(tmp_path / "records"), "fixture-efficientnet", "v1", FixtureReader(), _scope_verifier())
    registry = ProviderRegistry()
    registry.register(ProviderRegistryEntry(provider.provider_id, provider.provider_version, "ml_detector", "approved", "fixture", ("fixture",)))
    with pytest.raises(ValueError, match="Registry of Record"):
        AuthenticationReportEngine().create(image, tmp_path / "report", submitter_id="reviewer", provider_registry=registry, providers=(provider,), provider_scope_attestation=_context(image).scope_attestation)


def test_registered_temperature_transform_changes_non_unit_score(tmp_path):
    image = _image()
    records = _write_registry(tmp_path, temperature=2.0)
    provider = MLDetectorProvider(records, "fixture-efficientnet", "v1", FixtureReader(value=0.8), _scope_verifier())
    assert provider.detect(image, _context(image, ("JPEG_FILE", "ORIGINAL_CAPTURE_ATTESTED")))[0].score == pytest.approx(2 / 3)


def test_recorded_p4b_candidate_is_loadable_but_not_admitted():
    root = Path(__file__).parents[1]
    registry = ModelCalibrationRegistry(root / "models/registry", root / "calibration")
    image = _image()
    with pytest.raises(ModelGovernanceError, match="approved"):
        MLDetectorProvider(registry, "efficientnet_b0_linear_logistic_p2b2a", "p4b-candidate-1", FixtureReader(weight_hash="7f5810bc96def8f7552d5b7e68d53c4786f81167d28291b21c0d90e1fca14934"), _scope_verifier()).detect(image, _context(image))
