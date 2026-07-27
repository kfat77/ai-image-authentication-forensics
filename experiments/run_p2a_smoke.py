"""Run a mechanics-only synthetic-feature baseline; this is not an AI-image detection experiment."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import platform
from random import Random
from typing import Any

from metrics import ScoredExample, TemperatureScaler, binary_metrics, grouped_binary_metrics
from models import DatasetManifest, LinearLayerClassifier, LogisticRegressionClassifier, TinyMLPClassifier, require_training_approval


EXPERIMENT_ID = "p2a-synthetic-feature-pipeline-smoke-v1"
DATASET_ID = "synthetic-feature-fixture-v1"


def run(output_directory: str | Path) -> dict[str, Any]:
    """Execute deterministic feature->model->calibration->metrics plumbing with synthetic labels only."""
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    splits = _make_fixture()
    fixture_hash = _fixture_manifest_hash(splits)
    manifest = DatasetManifest(
        dataset_id=DATASET_ID,
        version="1",
        approval_status="approved",
        training_permitted=True,
        commercial_use_permitted=False,
        manifest_hash=fixture_hash,
    )
    require_training_approval(manifest)
    model_factories = {
        "logistic_regression": lambda: LogisticRegressionClassifier(learning_rate=0.08, epochs=300),
        "linear_layer": lambda: LinearLayerClassifier(learning_rate=0.05, epochs=250),
        "tiny_mlp": lambda: TinyMLPClassifier(hidden_width=6, learning_rate=0.03, epochs=350, seed=20260727),
    }
    results: dict[str, Any] = {}
    for name, factory in model_factories.items():
        model = factory().fit(_features(splits["train"]), _labels(splits["train"]))
        calibration = TemperatureScaler().fit(model.predict_proba(_features(splits["validation"])), _labels(splits["validation"]))
        test_records = _scored_examples(splits["test"], calibration.transform(model.predict_proba(_features(splits["test"]))))
        results[name] = {
            "model_type": model.model_type,
            "model_implementation_version": "p2a-baseline-v1",
            "hyperparameters": _public_attributes(model),
            "checkpoint_sha256": _checkpoint_hash(model.checkpoint()),
            "temperature": calibration.temperature,
            "overall_metrics": binary_metrics(test_records),
            "by_dataset": grouped_binary_metrics(test_records, "dataset"),
            "by_generator": grouped_binary_metrics(test_records, "generator"),
            "by_transformation": grouped_binary_metrics(test_records, "transformation"),
            "error_cases": _error_cases(test_records),
        }
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "purpose": "pipeline mechanics validation only; not a scientific or product detection result",
        "prohibited_claims": ["AI-image detection accuracy", "generator attribution accuracy", "model comparison beyond this synthetic fixture", "production suitability"],
        "dataset": {"id": DATASET_ID, "version": "1", "approval_status": "approved", "approval_scope": "repository-owned synthetic feature fixture only; no external images", "manifest_hash": manifest.manifest_hash, "sample_counts": {name: len(rows) for name, rows in splits.items()}},
        "code": {"version": "p2a-smoke-v1", "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest()},
        "encoder": {"identifier": "none", "version": "not-applicable", "feature_settings": {"source": "deterministic synthetic numeric fixture", "dimensions": 4}},
        "calibration": {"method": "temperature_scaling_grid_search", "version": "v1", "split": "validation", "candidate_range": "0.25..6.00 step 0.05"},
        "tasks_exercised": ["Task A binary pipeline mechanics", "metric grouping mechanics"],
        "tasks_not_exercised": ["Task B generator attribution requires an approved labelled image dataset.", "Task C robustness requires approved images and real JPEG, resize, crop, screenshot, and AI-edit transformations."],
        "hardware": {"python": platform.python_version(), "platform": platform.platform()},
        "random_seed": 20260727,
        "models": results,
    }
    (output_path / "result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_path / "error-analysis.md").write_text(_error_analysis_markdown(payload), encoding="utf-8")
    (output_path / "model-comparison.md").write_text(_comparison_markdown(payload), encoding="utf-8")
    return payload


def _make_fixture() -> dict[str, list[dict[str, Any]]]:
    random = Random(20260727)
    splits = {"train": [], "validation": [], "test": []}
    transformations = ("none", "jpeg_q75_fixture", "resize_075_fixture")
    for index in range(120):
        label = index % 2
        centre = 0.55 if label else -0.55
        features = (centre + random.gauss(0, 0.72), centre * 0.7 + random.gauss(0, 0.72), random.gauss(0, 0.55), random.gauss(0, 0.55))
        split = "train" if index < 72 else "validation" if index < 96 else "test"
        splits[split].append(
            {
                "sample_id": f"fixture-{index:03d}",
                "features": features,
                "label": label,
                "dataset": DATASET_ID,
                "generator": "synthetic-generator-fixture" if label else "synthetic-real-fixture",
                "transformation": transformations[index % len(transformations)],
            }
        )
    return splits


def _fixture_manifest_hash(splits: dict[str, list[dict[str, Any]]]) -> str:
    canonical_fixture = json.dumps(splits, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical_fixture.encode("utf-8")).hexdigest()


def _features(rows: list[dict[str, Any]]) -> list[tuple[float, ...]]:
    return [tuple(row["features"]) for row in rows]


def _labels(rows: list[dict[str, Any]]) -> list[int]:
    return [int(row["label"]) for row in rows]


def _scored_examples(rows: list[dict[str, Any]], scores: list[float]) -> list[ScoredExample]:
    return [ScoredExample(row["sample_id"], int(row["label"]), score, row["dataset"], row["generator"], row["transformation"]) for row, score in zip(rows, scores)]


def _checkpoint_hash(checkpoint: dict[str, object]) -> str:
    return sha256(json.dumps(checkpoint, sort_keys=True).encode("utf-8")).hexdigest()


def _public_attributes(model: object) -> dict[str, object]:
    return {key: value for key, value in vars(model).items() if key in {"learning_rate", "epochs", "hidden_width", "seed"}}


def _error_cases(records: list[ScoredExample]) -> list[dict[str, object]]:
    return [
        {"sample_id": record.sample_id, "label": record.label, "score": round(record.score, 6), "prediction": int(record.score >= 0.5), "dataset": record.dataset, "generator": record.generator, "transformation": record.transformation}
        for record in sorted((item for item in records if (item.score >= 0.5) != bool(item.label)), key=lambda item: abs(item.score - 0.5))[:5]
    ]


def _error_analysis_markdown(payload: dict[str, Any]) -> str:
    lines = ["# P2-A synthetic pipeline smoke: error analysis", "", "This file is a mechanics-only fixture result. It contains no real or AI-generated images and supports no detection claim.", ""]
    for name, result in payload["models"].items():
        lines.append(f"## {name}")
        lines.append("")
        cases = result["error_cases"]
        if not cases:
            lines.append("No fixture misclassifications; this is not evidence of real-world performance.")
        else:
            for case in cases:
                lines.append(f"- `{case['sample_id']}`: label={case['label']}, score={case['score']}, transformation={case['transformation']}.")
            counts: dict[str, int] = {}
            for case in cases:
                counts[str(case["transformation"])] = counts.get(str(case["transformation"]), 0) + 1
            summary = ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))
            lines.append(f"- Fixture error slice: {summary}.")
            lines.append("- Interpretation limit: the inputs are synthetic numeric features, so no visual, generator, or transformation cause can be inferred from these errors.")
        lines.append("")
    return "\n".join(lines)


def _comparison_markdown(payload: dict[str, Any]) -> str:
    lines = ["# P2-A synthetic pipeline smoke: model comparison", "", "All values below are from a deterministic, repository-owned synthetic feature fixture. They validate only experiment plumbing; they are not measurements of AI-image detection, generator attribution, or real-world robustness.", "", "| Baseline | Accuracy | F1 | AUROC | PR-AUC | ECE | Brier score |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, result in payload["models"].items():
        metric = result["overall_metrics"]
        lines.append(f"| {name} | {metric['accuracy']:.6f} | {metric['f1']:.6f} | {metric['auroc']:.6f} | {metric['pr_auc']:.6f} | {metric['ece']:.6f} | {metric['brier_score']:.6f} |")
    lines.extend(["", "Do not select a production model from this table. P2-B requires approved image data, frozen splits, real transformations, and review of failure modes.", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    run(Path(__file__).parent / "results" / EXPERIMENT_ID)
