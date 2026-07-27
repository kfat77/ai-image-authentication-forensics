"""Run the first frozen-encoder, real-image research baseline. No API is exposed."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
from typing import Any

from PIL import Image
import torch
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT / "backend"))

from datasets import load_approved_manifests, load_manifest, validate_admitted_dataset
from metrics import ScoredExample, TemperatureScaler, binary_metrics, grouped_binary_metrics
from models import LogisticRegressionClassifier


EXPERIMENT_ID = "p2b2a-ditfake-efficientnet-b0-linear-baseline-v1"
CHECKPOINT_SHA256 = "7f5810bc96def8f7552d5b7e68d53c4786f81167d28291b21c0d90e1fca14934"


def run(workspace: str | Path) -> dict[str, Any]:
    root = Path(workspace)
    manifest = load_manifest(root / "manifests" / "p2b2a-ditfake-mini.json")
    approvals = load_approved_manifests(root / "registry" / "approved-manifests.json")
    data_root = root / "datasets" / manifest.name / manifest.version
    records = validate_admitted_dataset(manifest, data_root / "index.jsonl", data_root, approvals)
    weights = EfficientNet_B0_Weights.IMAGENET1K_V1
    model = efficientnet_b0(weights=None)
    checkpoint_path = _checkpoint_path()
    if _sha256(checkpoint_path) != CHECKPOINT_SHA256:
        raise RuntimeError("EfficientNet-B0 checkpoint hash does not match the approved research record.")
    model.load_state_dict(torch.load(checkpoint_path, map_location="cpu", weights_only=True))
    model.eval()
    features = _extract(model, weights, data_root, records)
    result = _fit_evaluate(records, features)
    feature_artifact = _write_feature_artifact(root, features)
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {"name": manifest.name, "version": manifest.version, "manifest_hash": manifest.hash, "index_hash": manifest.index_hash, "sample_count": manifest.sample_count},
        "encoder": {"identifier": "efficientnet_b0_imagenet1k_v1", "architecture": "EfficientNet-B0", "repository": "https://github.com/pytorch/vision", "license": "BSD-3-Clause", "checkpoint_url": weights.url, "checkpoint_sha256": _sha256(checkpoint_path), "feature_dimension": 1280, "preprocessing": "Torchvision IMAGENET1K_V1 transforms: RGB; resize short side 256 bicubic; center crop 224; scale [0,1]; ImageNet mean/std normalization", "supply_chain_note": "The approved full SHA-256 is verified before loading. The filename's Torchvision metadata token differs from this observed full SHA-256 and is retained as a review note."},
        "classifier": result,
        "feature_artifact": feature_artifact,
        "calibration": {"method": "temperature_scaling_grid_search", "fit_split": "validation only"},
        "hardware": {"python": platform.python_version(), "platform": platform.platform(), "torch": torch.__version__, "device": "cpu"},
        "limitations": ["24-image, single benchmark/release fixture; not a performance estimate.", "Real and AI samples share a curated benchmark context and may contain source-specific artifacts.", "Only FLUX is represented for generated images; no unknown-generator sample exists.", "The official checkpoint URL's observed full hash differs from Torchvision 0.16.0 metadata; it is recorded and must be independently reviewed before reuse.", "No fine-tuning, production API, AI probability, origin claim, or commercial metric is produced."],
    }
    output = root / "experiments" / "results" / EXPERIMENT_ID
    output.mkdir(parents=True, exist_ok=True)
    (output / "result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_error_analysis(root / "error-analysis" / f"{EXPERIMENT_ID}.md", result)
    return payload


def _extract(model: torch.nn.Module, weights: EfficientNet_B0_Weights, data_root: Path, records: list[object]) -> dict[str, tuple[float, ...]]:
    tensors = []
    ids = []
    for record in records:
        with Image.open(data_root / record.relative_path) as image:
            tensors.append(weights.transforms()(image.convert("RGB")))
        ids.append(record.sample_id)
    features: dict[str, tuple[float, ...]] = {}
    with torch.inference_mode():
        for offset in range(0, len(tensors), 8):
            output = torch.flatten(model.avgpool(model.features(torch.stack(tensors[offset:offset + 8]))), 1)
            for sample_id, vector in zip(ids[offset:offset + 8], output.cpu().tolist()):
                features[sample_id] = tuple(float(value) for value in vector)
    return features


def _fit_evaluate(records: list[object], features: dict[str, tuple[float, ...]]) -> dict[str, Any]:
    by_split = {name: [record for record in records if record.split == name] for name in ("train", "validation", "test")}
    labels = lambda rows: [int(record.image_origin == "AI_GENERATED") for record in rows]
    classifiers = {"linear_logistic_regression": LogisticRegressionClassifier(learning_rate=0.03, epochs=250)}
    output: dict[str, Any] = {}
    for name, classifier in classifiers.items():
        classifier.fit([features[record.sample_id] for record in by_split["train"]], labels(by_split["train"]))
        scaler = TemperatureScaler().fit(classifier.predict_proba([features[record.sample_id] for record in by_split["validation"]]), labels(by_split["validation"]))
        scores = scaler.transform(classifier.predict_proba([features[record.sample_id] for record in by_split["test"]]))
        examples = [ScoredExample(record.sample_id, int(record.image_origin == "AI_GENERATED"), score, "p2b2a-ditfake-mini", record.generator, record.edit_status) for record, score in zip(by_split["test"], scores)]
        output[name] = {"model_type": classifier.model_type, "checkpoint_sha256": sha256(json.dumps(classifier.checkpoint(), sort_keys=True).encode()).hexdigest(), "temperature": scaler.temperature, "metrics": binary_metrics(examples), "by_image_origin": {"REAL": binary_metrics([item for item in examples if item.label == 0]), "AI_GENERATED": binary_metrics([item for item in examples if item.label == 1])}, "by_generator": grouped_binary_metrics(examples, "generator"), "by_transformation": grouped_binary_metrics(examples, "transformation"), "errors": _errors(examples)}
    return output


def _write_feature_artifact(root: Path, features: dict[str, tuple[float, ...]]) -> dict[str, object]:
    path = root / "experiments" / "features" / EXPERIMENT_ID / "features.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(features, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    path.write_bytes(encoded + b"\n")
    return {"relative_path": path.relative_to(root).as_posix(), "sha256": sha256(path.read_bytes()).hexdigest(), "feature_dimension": 1280, "sample_count": len(features)}


def _errors(examples: list[ScoredExample]) -> list[dict[str, object]]:
    return [{"sample_id": item.sample_id, "label": "AI_GENERATED" if item.label else "REAL", "score": round(item.score, 6), "kind": "false_negative" if item.label else "false_positive", "generator": item.generator, "transformation": item.transformation} for item in examples if int(item.score >= 0.5) != item.label]


def _checkpoint_path() -> Path:
    matches = sorted((Path(torch.hub.get_dir()) / "checkpoints").glob("efficientnet_b0_rwightman-*.pth"))
    if not matches:
        raise RuntimeError("EfficientNet-B0 checkpoint was not present after official Torchvision load.")
    return matches[-1]


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_error_analysis(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {EXPERIMENT_ID} error analysis", "", "This is a 24-image research fixture, not evidence of detection capability.", ""]
    for name, evaluation in result.items():
        lines.extend([f"## {name}", "", "### False positive (real image classified as generated)"])
        false_positives = [error for error in evaluation["errors"] if error["kind"] == "false_positive"]
        lines.extend([f"- `{error['sample_id']}` score={error['score']}." for error in false_positives] or ["- None in this six-image test split; absence is not a performance conclusion."])
        lines.extend(["", "### False negative (generated image classified as real)"])
        false_negatives = [error for error in evaluation["errors"] if error["kind"] == "false_negative"]
        lines.extend([f"- `{error['sample_id']}` score={error['score']}, generator={error['generator']}." for error in false_negatives] or ["- None in this six-image test split; absence is not a performance conclusion."])
        lines.extend(["", "### Unknown generator", "- Not evaluated: the approved fixture contains FLUX only. Unknown-generator handling cannot be quantified until a held-out generator is approved.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    payload = run(WORKSPACE_ROOT)
    print(json.dumps({"experiment_id": payload["experiment_id"], "result": f"experiments/results/{EXPERIMENT_ID}/result.json"}, ensure_ascii=False))
