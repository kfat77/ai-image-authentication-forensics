"""Write a preparation record; this does not extract features or execute a model."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
from typing import Any

from datasets import load_manifest
from models import EncoderAdapterRegistry


def build_environment_record(manifest_directory: str | Path, timestamp_utc: str | None = None) -> dict[str, Any]:
    manifests = [load_manifest(path) for path in sorted(Path(manifest_directory).glob("*.json"))]
    adapters = EncoderAdapterRegistry().statuses()
    return {
        "record_type": "p2_b1_experiment_environment_preparation",
        "timestamp_utc": timestamp_utc or datetime.now(timezone.utc).isoformat(),
        "dataset_manifests": [
            {"name": manifest.name, "version": manifest.version, "hash": manifest.hash, "admission_status": manifest.admission_status}
            for manifest in manifests
        ],
        "encoder_adapters": [
            {"identifier": adapter.identifier, "version": adapter.version, "feature_dimension": adapter.feature_dimension, "state": adapter.state}
            for adapter in adapters
        ],
        "hardware": {"python": platform.python_version(), "platform": platform.platform()},
        "limitations": ["No external image data is admitted or stored.", "No encoder package or checkpoint is installed.", "No feature vectors, classifier training, benchmark score, or AI probability is produced."],
    }


def write_environment_record(output_path: str | Path, manifest_directory: str | Path, timestamp_utc: str | None = None) -> dict[str, Any]:
    record = build_environment_record(manifest_directory, timestamp_utc)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record
