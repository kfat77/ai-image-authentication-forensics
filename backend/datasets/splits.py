"""Dataset labels and group-aware split checks; no random split operation is provided."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json
from pathlib import Path
import string
from typing import Iterable

from .admission import ApprovedManifest
from .manifest import DatasetManifest


class ImageOrigin(StrEnum):
    REAL = "REAL"
    AI_GENERATED = "AI_GENERATED"
    UNKNOWN = "UNKNOWN"


class Generator(StrEnum):
    NONE = "NONE"
    SD = "SD"
    SDXL = "SDXL"
    MIDJOURNEY = "MIDJOURNEY"
    DALLE = "DALL-E"
    FLUX = "FLUX"
    IMAGEN = "IMAGEN"
    OTHER = "OTHER"


class EditStatus(StrEnum):
    ORIGINAL = "ORIGINAL"
    COMPRESSED = "COMPRESSED"
    RESIZED = "RESIZED"
    CROPPED = "CROPPED"
    AI_EDITED = "AI_EDITED"


class SplitValidationError(ValueError):
    pass


@dataclass(frozen=True)
class DatasetRecord:
    sample_id: str
    relative_path: str
    content_sha256: str
    image_origin: ImageOrigin
    generator: Generator
    edit_status: EditStatus
    split: str
    generator_split: str
    temporal_split: str
    transformation_split: str
    parent_id: str
    source_group: str

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "DatasetRecord":
        required = {"sample_id", "relative_path", "content_sha256", "image_origin", "generator", "edit_status", "split", "generator_split", "temporal_split", "transformation_split", "parent_id", "source_group"}
        missing = required - set(raw)
        if missing:
            raise SplitValidationError(f"Dataset record is missing fields: {', '.join(sorted(missing))}")
        try:
            record = cls(
                sample_id=str(raw["sample_id"]), relative_path=str(raw["relative_path"]), content_sha256=str(raw["content_sha256"]),
                image_origin=ImageOrigin(str(raw["image_origin"])), generator=Generator(str(raw["generator"])), edit_status=EditStatus(str(raw["edit_status"])),
                split=str(raw["split"]), generator_split=str(raw["generator_split"]), temporal_split=str(raw["temporal_split"]), transformation_split=str(raw["transformation_split"]), parent_id=str(raw["parent_id"]), source_group=str(raw["source_group"]),
            )
        except ValueError as exc:
            raise SplitValidationError("Dataset record has an invalid label.") from exc
        if not all(getattr(record, field) for field in ("sample_id", "relative_path", "content_sha256", "split", "generator_split", "temporal_split", "transformation_split", "parent_id", "source_group")):
            raise SplitValidationError("Dataset record identity and split fields must be non-empty.")
        if len(record.content_sha256) != 64 or any(character not in string.hexdigits for character in record.content_sha256):
            raise SplitValidationError("Dataset record content_sha256 must be a SHA-256 hexadecimal digest.")
        if record.image_origin == ImageOrigin.REAL and record.generator != Generator.NONE:
            raise SplitValidationError("REAL records must use generator NONE.")
        if record.image_origin == ImageOrigin.AI_GENERATED and record.generator == Generator.NONE:
            raise SplitValidationError("AI_GENERATED records must name a generator or OTHER.")
        return record


def load_records(path: str | Path) -> list[DatasetRecord]:
    records = [DatasetRecord.from_dict(json.loads(line)) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not records:
        raise SplitValidationError("Dataset index must contain at least one record.")
    return records


def validate_records_for_experiment(manifest: DatasetManifest, records: Iterable[DatasetRecord], approved_manifests: frozenset[ApprovedManifest]) -> None:
    values = list(records)
    if manifest.admission_status != "approved":
        raise SplitValidationError(f"Dataset {manifest.name}@{manifest.version} is not approved for experiment use.")
    if (manifest.name, manifest.version, manifest.hash) not in approved_manifests:
        raise SplitValidationError(f"Dataset {manifest.name}@{manifest.version} is absent from the trusted approval index.")
    if len(values) != manifest.sample_count:
        raise SplitValidationError("Dataset record count does not match manifest sample_count.")
    if {record.split for record in values} != {"train", "validation", "test"}:
        raise SplitValidationError("Dataset must contain train, validation, and test splits.")
    if len({record.sample_id for record in values}) != len(values):
        raise SplitValidationError("Dataset contains duplicate sample identifiers.")
    _ensure_group_isolation(values, "parent_id")
    _ensure_group_isolation(values, "source_group")
    _ensure_group_isolation(values, "content_sha256")


def validate_admitted_dataset(manifest: DatasetManifest, index_path: str | Path, data_root: str | Path, approved_manifests: frozenset[ApprovedManifest]) -> list[DatasetRecord]:
    """Perform the complete pre-feature-extraction gate against index and image bytes."""
    path = Path(index_path)
    actual_index_hash = "sha256:" + sha256(path.read_bytes()).hexdigest()
    if actual_index_hash != manifest.index_hash:
        raise SplitValidationError("Dataset index hash does not match the approved manifest.")
    records = load_records(path)
    validate_records_for_experiment(manifest, records, approved_manifests)
    _validate_content_hashes(records, data_root)
    return records


def _ensure_group_isolation(records: list[DatasetRecord], field: str) -> None:
    assignments: dict[str, str] = {}
    for record in records:
        group = str(getattr(record, field))
        assigned = assignments.setdefault(group, record.split)
        if assigned != record.split:
            raise SplitValidationError(f"{field} {group} crosses {assigned} and {record.split}; this is split contamination.")


def _validate_content_hashes(records: list[DatasetRecord], data_root: str | Path) -> None:
    root = Path(data_root).resolve()
    for record in records:
        target = (root / record.relative_path).resolve()
        if root not in target.parents or not target.is_file():
            raise SplitValidationError(f"Dataset file is missing or outside data root: {record.relative_path}")
        actual_hash = sha256(target.read_bytes()).hexdigest()
        if actual_hash != record.content_sha256.lower():
            raise SplitValidationError(f"Dataset file hash does not match index: {record.relative_path}")
