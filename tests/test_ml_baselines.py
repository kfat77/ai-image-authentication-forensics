from __future__ import annotations

import json

import pytest

from experiments.run_p2a_smoke import EXPERIMENT_ID, _fixture_manifest_hash, _make_fixture, run
from metrics import ScoredExample, TemperatureScaler, binary_metrics, grouped_binary_metrics
from models import DatasetManifest, EncoderRegistry, LinearLayerClassifier, LogisticRegressionClassifier, SoftmaxLinearClassifier, UnavailableEncoder, choose_attribution, require_training_approval
from models.datasets import DatasetApprovalError
from models.encoders import EncoderUnavailableError


def test_encoder_registry_declares_all_requested_families_without_loading_weights() -> None:
    registry = EncoderRegistry()

    assert {descriptor.identifier for descriptor in registry.descriptors()} == {"clip", "dinov2", "siglip", "convnext", "efficientnet", "vit"}
    assert all(descriptor.availability == "unavailable" for descriptor in registry.descriptors())
    with pytest.raises(EncoderUnavailableError):
        registry.get("clip").encode([b"not-an-image"])


def test_training_gate_rejects_unreviewed_dataset() -> None:
    manifest = DatasetManifest("candidate", "v1", "pending_review", False, False, "abc")

    with pytest.raises(DatasetApprovalError):
        require_training_approval(manifest)

    with pytest.raises(DatasetApprovalError):
        require_training_approval(DatasetManifest("candidate", "v1", "approved", True, True, "forged"))


def test_small_binary_baselines_produce_bounded_scores() -> None:
    features = [(-2.0, -1.0), (-1.0, -0.5), (1.0, 0.5), (2.0, 1.0)]
    labels = [0, 0, 1, 1]

    for classifier in (LogisticRegressionClassifier(epochs=80), LinearLayerClassifier(epochs=80)):
        scores = classifier.fit(features, labels).predict_proba(features)
        assert all(0 <= score <= 1 for score in scores)
        assert scores[0] < scores[-1]
        with pytest.raises(ValueError):
            classifier.predict_proba([(0.0,)])


def test_unknown_handling_never_forces_known_generator() -> None:
    prediction = choose_attribution({"sd": 0.52, "midjourney": 0.48}, minimum_known_confidence=0.7)

    assert prediction.prediction == "unknown"
    assert prediction.confidence == 0.52
    assert prediction.unknown_score == 0.48
    with pytest.raises(ValueError):
        choose_attribution({"sd": 1.2}, minimum_known_confidence=0.7)
    with pytest.raises(ValueError):
        choose_attribution({"sd": 0.5, "unknown": 0.2}, minimum_known_confidence=0.7)


def test_softmax_baseline_can_include_explicit_unknown_label() -> None:
    classifier = SoftmaxLinearClassifier(epochs=50).fit([(-2.0,), (-1.0,), (1.0,), (2.0,)], ["unknown", "unknown", "sd", "sd"])

    scores = classifier.predict_proba([(0.0,)])[0]
    assert set(scores) == {"sd", "unknown"}
    assert sum(scores.values()) == pytest.approx(1.0)


def test_metrics_include_calibration_and_required_groupings() -> None:
    records = [
        ScoredExample("a", 0, 0.1, "set-a", "real", "none"),
        ScoredExample("b", 1, 0.8, "set-a", "sd", "jpeg"),
        ScoredExample("c", 0, 0.4, "set-b", "real", "resize"),
        ScoredExample("d", 1, 0.6, "set-b", "sd", "resize"),
    ]
    metrics = binary_metrics(records)
    calibrated = TemperatureScaler().fit([record.score for record in records], [record.label for record in records]).transform([record.score for record in records])

    assert {"accuracy", "precision", "recall", "f1", "auroc", "pr_auc", "ece", "brier_score"} <= set(metrics)
    assert set(grouped_binary_metrics(records, "dataset")) == {"set-a", "set-b"}
    assert set(grouped_binary_metrics(records, "generator")) == {"real", "sd"}
    assert set(grouped_binary_metrics(records, "transformation")) == {"jpeg", "none", "resize"}
    assert all(0 <= score <= 1 for score in calibrated)


def test_pr_auc_does_not_depend_on_tied_score_order() -> None:
    positive = ScoredExample("positive", 1, 0.5, "set", "sd", "none")
    negative = ScoredExample("negative", 0, 0.5, "set", "real", "none")

    assert binary_metrics([positive, negative])["pr_auc"] == binary_metrics([negative, positive])["pr_auc"]


def test_fixture_manifest_hash_changes_with_fixture_content() -> None:
    fixture = _make_fixture()
    original = _fixture_manifest_hash(fixture)
    fixture["train"][0]["features"] = (999.0, 0.0, 0.0, 0.0)

    assert _fixture_manifest_hash(fixture) != original


def test_smoke_experiment_writes_reproducible_research_record(tmp_path) -> None:
    payload = run(tmp_path)
    saved = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))

    assert payload == saved
    assert saved["experiment_id"] == EXPERIMENT_ID
    assert saved["dataset"]["approval_scope"].startswith("repository-owned synthetic")
    assert len(saved["dataset"]["manifest_hash"]) == 64
    assert saved["code"]["version"] == "p2a-smoke-v1"
    assert len(saved["code"]["source_sha256"]) == 64
    assert saved["encoder"]["identifier"] == "none"
    assert saved["calibration"]["method"] == "temperature_scaling_grid_search"
    assert "AI-image detection accuracy" in saved["prohibited_claims"]
    assert set(saved["models"]) == {"logistic_regression", "linear_layer", "tiny_mlp"}
    assert (tmp_path / "model-comparison.md").is_file()
    assert (tmp_path / "error-analysis.md").is_file()
