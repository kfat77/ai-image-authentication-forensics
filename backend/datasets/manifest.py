"""Validation for self-hashed, admission-controlled dataset manifests."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


_REQUIRED_FIELDS = {"name", "version", "source", "license", "hash", "index_hash", "sample_count", "category", "generation_source", "admission_status", "split_strategy"}
_ADMISSION_STATUSES = {"pending_review", "blocked", "approved"}


class ManifestError(ValueError):
    pass


@dataclass(frozen=True)
class DatasetManifest:
    name: str
    version: str
    source: str
    license: str
    hash: str
    index_hash: str
    sample_count: int
    category: str
    generation_source: str
    admission_status: str
    split_strategy: str


def manifest_hash(raw: dict[str, Any]) -> str:
    """Hash the canonical manifest content while excluding its declared hash field."""
    content = {key: value for key, value in raw.items() if key != "hash"}
    encoded = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def load_manifest(path: str | Path) -> DatasetManifest:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or _REQUIRED_FIELDS - set(raw):
        missing = sorted(_REQUIRED_FIELDS - set(raw) if isinstance(raw, dict) else _REQUIRED_FIELDS)
        raise ManifestError(f"Manifest is missing required fields: {', '.join(missing)}")
    if raw["hash"] != manifest_hash(raw):
        raise ManifestError("Manifest hash does not match its canonical content.")
    if not all(isinstance(raw[field], str) and raw[field].strip() for field in _REQUIRED_FIELDS - {"sample_count"}):
        raise ManifestError("Manifest text fields must be non-empty strings.")
    if not isinstance(raw["sample_count"], int) or raw["sample_count"] < 0:
        raise ManifestError("Manifest sample_count must be a non-negative integer.")
    if raw["admission_status"] not in _ADMISSION_STATUSES:
        raise ManifestError("Manifest admission_status is invalid.")
    if raw["admission_status"] == "approved" and not _is_sha256(raw["index_hash"]):
        raise ManifestError("Approved manifests must bind a SHA-256 index_hash.")
    if raw["split_strategy"] != "grouped_non_random":
        raise ManifestError("Manifest must declare grouped_non_random split strategy.")
    return DatasetManifest(**{field: raw[field] for field in _REQUIRED_FIELDS})


def _is_sha256(value: str) -> bool:
    return value.startswith("sha256:") and len(value) == 71 and all(character in "0123456789abcdef" for character in value[7:])
