"""Run permitted P2-B2-B robustness slices; uncovered holdouts remain explicit gaps."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Callable

from PIL import Image, ImageEnhance
import torch
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT / "backend"))

from datasets import load_approved_manifests, load_manifest, validate_admitted_dataset
from metrics import IsotonicScaler, PlattScaler, ScoredExample, TemperatureScaler, binary_metrics, grouped_binary_metrics
from models import LinearSVMClassifier, LogisticRegressionClassifier, TinyMLPClassifier


EXPERIMENT_ID = "p2b2b-permitted-robustness-efficientnet-v1"
CHECKPOINT_SHA256 = "7f5810bc96def8f7552d5b7e68d53c4786f81167d28291b21c0d90e1fca14934"
TRANSFORMS: dict[str, Callable[[Image.Image], Image.Image]] = {
    "ORIGINAL": lambda image: image.copy(),
    "JPEG_Q75": lambda image: _jpeg(image, 75),
    "RESIZED_075": lambda image: image.resize((max(1, image.width * 3 // 4), max(1, image.height * 3 // 4)), Image.Resampling.LANCZOS),
    "CENTER_CROP_080": lambda image: _crop(image, 0.8),
    "COLOR_BRIGHTNESS_115": lambda image: ImageEnhance.Brightness(image).enhance(1.15),
}


def run(workspace: str | Path) -> dict[str, Any]:
    root = Path(workspace)
    manifest = load_manifest(root / "manifests" / "p2b2a-ditfake-mini.json")
    records = validate_admitted_dataset(manifest, root / "datasets" / manifest.name / manifest.version / "index.jsonl", root / "datasets" / manifest.name / manifest.version, load_approved_manifests(root / "registry" / "approved-manifests.json"))
    model, weights = _encoder()
    by_split = {split: [row for row in records if row.split == split] for split in ("train", "validation", "test")}
    train_features = _features(model, weights, root, manifest, by_split["train"], TRANSFORMS["ORIGINAL"])
    validation_features = _features(model, weights, root, manifest, by_split["validation"], TRANSFORMS["ORIGINAL"])
    evaluations: dict[str, Any] = {}
    for classifier_name, factory in _classifier_factories().items():
        classifier = factory().fit(_vectors(train_features, by_split["train"]), _labels(by_split["train"]))
        validation_scores = classifier.predict_proba(_vectors(validation_features, by_split["validation"]))
        transform_results: dict[str, Any] = {}
        for transform_name, transform in TRANSFORMS.items():
            features = _features(model, weights, root, manifest, by_split["test"], transform)
            raw_scores = classifier.predict_proba(_vectors(features, by_split["test"]))
            transform_results[transform_name] = _calibration_comparison(by_split["test"], raw_scores, validation_scores, _labels(by_split["validation"]), transform_name)
        evaluations[classifier_name] = {"model_type": classifier.model_type, "hyperparameters": _hyperparameters(classifier), "checkpoint_sha256": _sha(classifier.checkpoint()), "robustness": transform_results}
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "research-only robustness and calibration mechanics on a restricted 24-image fixture; not a detection claim",
        "dataset": {"name": manifest.name, "version": manifest.version, "manifest_hash": manifest.hash, "index_hash": manifest.index_hash, "actual_coverage": {"real_sources": ["COCO-referenced via DiTFake"], "generators": ["FLUX"], "datasets": [manifest.name]}},
        "encoder_comparison": {"efficientnet_b0": {"state": "run", "feature_dimension": 1280, "checkpoint_sha256": CHECKPOINT_SHA256}, "dinov2": {"state": "not_run", "reason": "No independently hash-pinned official checkpoint has been materialised in this research environment."}, "clip": {"state": "not_run", "reason": "Checkpoint-specific licence and hash admission remain incomplete."}},
        "reproducibility": {"git_revision": _git_revision(root), "script_sha256": _sha_path(Path(__file__)), "python": platform.python_version(), "platform": platform.platform(), "torch": torch.__version__, "torchvision": __import__("torchvision").__version__, "device": "cpu", "preprocessing": "IMAGENET1K_V1 RGB resize-256 bicubic, center-crop-224, ImageNet normalization", "transform_parameters": {"JPEG_Q75": "quality=75, subsampling=0", "RESIZED_075": "Lanczos, 0.75", "CENTER_CROP_080": "center, 0.80", "COLOR_BRIGHTNESS_115": "Pillow brightness=1.15"}},
        "holdout_coverage": {"generator_holdout": {"state": "uncovered", "reason": "Only FLUX is admitted; no SD/SDXL, Midjourney, DALL-E, or Imagen test generator."}, "dataset_holdout": {"state": "uncovered", "reason": "Only one approved fixture dataset is available."}, "unknown_generator": {"state": "uncovered", "reason": "No held-out generated source is admitted."}, "transformation_holdout": {"state": "run", "variants": list(TRANSFORMS), "uncovered": ["SCREENSHOT", "AI_EDITED"]}},
        "classifier_evaluations": evaluations,
        "limitations": ["Small, single-dataset/single-generator fixture; metrics are not generalization estimates.", "Upstream source-rights and checkpoint licence review remain recorded governance constraints.", "No cross-generator, cross-dataset, unknown-generator, screenshot, or AI-edit result is available.", "No production API, real-world probability, attribution conclusion, or commercial metric is produced."],
    }
    output = root / "experiments" / "results" / EXPERIMENT_ID
    output.mkdir(parents=True, exist_ok=True)
    (output / "result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _encoder() -> tuple[torch.nn.Module, EfficientNet_B0_Weights]:
    checkpoint = Path(torch.hub.get_dir()) / "checkpoints" / "efficientnet_b0_rwightman-3dd342df.pth"
    if not checkpoint.is_file() or _sha_path(checkpoint) != CHECKPOINT_SHA256:
        raise RuntimeError("Approved EfficientNet checkpoint is absent or has a different SHA-256.")
    model = efficientnet_b0(weights=None)
    model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True))
    model.eval()
    return model, EfficientNet_B0_Weights.IMAGENET1K_V1


def _features(model: torch.nn.Module, weights: EfficientNet_B0_Weights, root: Path, manifest: Any, records: list[Any], transform: Callable[[Image.Image], Image.Image]) -> dict[str, tuple[float, ...]]:
    data_root = root / "datasets" / manifest.name / manifest.version
    tensors = []
    for row in records:
        with Image.open(data_root / row.relative_path) as image:
            tensors.append(weights.transforms()(transform(image.convert("RGB"))))
    with torch.inference_mode():
        vectors = torch.flatten(model.avgpool(model.features(torch.stack(tensors))), 1).cpu().tolist()
    return {row.sample_id: tuple(float(value) for value in vector) for row, vector in zip(records, vectors)}


def _calibration_comparison(records: list[Any], raw_scores: list[float], validation_scores: list[float], validation_labels: list[int], transformation: str) -> dict[str, Any]:
    mappings = {"before": lambda scores: scores}
    for name, scaler in (("temperature", TemperatureScaler()), ("platt", PlattScaler()), ("isotonic", IsotonicScaler())):
        mappings[name] = scaler.fit(validation_scores, validation_labels).transform
    output: dict[str, Any] = {}
    for name, mapper in mappings.items():
        scores = mapper(raw_scores)
        examples = [ScoredExample(row.sample_id, int(row.image_origin == "AI_GENERATED"), score, "p2b2a-ditfake-mini", row.generator, transformation) for row, score in zip(records, scores)]
        output[name] = {"overall": binary_metrics(examples), "by_generator": grouped_binary_metrics(examples, "generator")}
    return output


def _classifier_factories() -> dict[str, Callable[[], Any]]:
    return {"linear_logistic_regression": lambda: LogisticRegressionClassifier(learning_rate=0.03, epochs=250), "linear_svm": lambda: LinearSVMClassifier(learning_rate=0.03, epochs=250), "tiny_mlp": lambda: TinyMLPClassifier(hidden_width=6, learning_rate=0.02, epochs=250, seed=20260727)}


def _vectors(features: dict[str, tuple[float, ...]], records: list[Any]) -> list[tuple[float, ...]]:
    return [features[row.sample_id] for row in records]


def _labels(records: list[Any]) -> list[int]:
    return [int(row.image_origin == "AI_GENERATED") for row in records]


def _jpeg(image: Image.Image, quality: int) -> Image.Image:
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=quality, subsampling=0)
    output.seek(0)
    with Image.open(output) as decoded:
        return decoded.convert("RGB").copy()


def _crop(image: Image.Image, ratio: float) -> Image.Image:
    width, height = int(image.width * ratio), int(image.height * ratio)
    return image.crop(((image.width - width) // 2, (image.height - height) // 2, (image.width + width) // 2, (image.height + height) // 2))


def _sha(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=list).encode()).hexdigest()


def _sha_path(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hyperparameters(classifier: Any) -> dict[str, object]:
    return {name: getattr(classifier, name) for name in ("learning_rate", "epochs", "hidden_width", "seed") if hasattr(classifier, name)}


def _git_revision(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


if __name__ == "__main__":
    print(json.dumps({"experiment_id": run(WORKSPACE_ROOT)["experiment_id"]}))
