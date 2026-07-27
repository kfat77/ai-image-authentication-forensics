from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from datasets import DatasetManifest, ManifestError, SplitValidationError, load_approved_manifests, load_manifest, manifest_hash, validate_admitted_dataset, validate_records_for_experiment
from datasets.splits import DatasetRecord
from experiments.p2b1_environment import build_environment_record
from models import EncoderAdapterRegistry


ROOT = Path(__file__).resolve().parents[1]
APPROVED_FIXTURE = frozenset({("fixture", "1", "sha256:test")})


def _record(sample_id: str, split: str, *, parent_id: str | None = None, source_group: str | None = None) -> DatasetRecord:
    return DatasetRecord.from_dict(
        {
            "sample_id": sample_id,
            "relative_path": f"images/{sample_id}.jpg",
            "content_sha256": sha256(sample_id.encode("utf-8")).hexdigest(),
            "image_origin": "REAL",
            "generator": "NONE",
            "edit_status": "ORIGINAL",
            "split": split,
            "generator_split": "real-reference",
            "temporal_split": "pre-2025",
            "transformation_split": "original",
            "parent_id": parent_id or sample_id,
            "source_group": source_group or sample_id,
        }
    )


def test_candidate_manifests_are_complete_and_hash_verified() -> None:
    manifests = [load_manifest(path) for path in sorted((ROOT / "manifests").glob("*.json"))]

    candidates = [manifest for manifest in manifests if manifest.name != "p2b2a-ditfake-mini"]
    assert {manifest.name for manifest in candidates} == {"cifake", "coco-2017", "diffusiondb", "genimage", "imagenet-ilsvrc-2012", "open-images-v7"}
    assert all(manifest.hash.startswith("sha256:") for manifest in manifests)
    assert all(manifest.admission_status != "approved" for manifest in candidates)


def test_p2b2a_research_manifest_has_a_matching_approval_record() -> None:
    manifest = load_manifest(ROOT / "manifests" / "p2b2a-ditfake-mini.json")
    approvals = load_approved_manifests(ROOT / "registry" / "approved-manifests.json")

    assert manifest.admission_status == "approved"
    assert (manifest.name, manifest.version, manifest.hash) in approvals


def test_manifest_hash_detects_content_change(tmp_path) -> None:
    raw = {
        "name": "fixture", "version": "1", "source": "local", "license": "test", "sample_count": 1,
        "category": "fixture", "generation_source": "NONE", "index_hash": "not_materialized", "admission_status": "pending_review", "split_strategy": "grouped_non_random",
    }
    raw["hash"] = manifest_hash(raw)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    assert load_manifest(path).name == "fixture"
    raw["sample_count"] = 2
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ManifestError):
        load_manifest(path)


def test_labels_are_validated() -> None:
    with pytest.raises(SplitValidationError):
        DatasetRecord.from_dict({**_record("a", "train").__dict__, "image_origin": "GENERATED"})
    with pytest.raises(SplitValidationError):
        DatasetRecord.from_dict({**_record("a", "train").__dict__, "generator": "SD"})
    with pytest.raises(SplitValidationError, match="content_sha256"):
        DatasetRecord.from_dict({**_record("a", "train").__dict__, "content_sha256": "not-a-hash"})
    with pytest.raises(SplitValidationError, match="AI_GENERATED"):
        DatasetRecord.from_dict({**_record("a", "train").__dict__, "image_origin": "AI_GENERATED", "generator": "NONE"})


def test_train_test_contamination_is_rejected() -> None:
    manifest = DatasetManifest("fixture", "1", "local", "test", "sha256:test", "sha256:index", 3, "fixture", "NONE", "approved", "grouped_non_random")
    records = [_record("a", "train", parent_id="same-parent"), _record("b", "validation"), _record("c", "test", parent_id="same-parent")]

    with pytest.raises(SplitValidationError, match="parent_id"):
        validate_records_for_experiment(manifest, records, APPROVED_FIXTURE)

    source_leak = [_record("a", "train", source_group="same-source"), _record("b", "validation"), _record("c", "test", source_group="same-source")]
    with pytest.raises(SplitValidationError, match="source_group"):
        validate_records_for_experiment(manifest, source_leak, APPROVED_FIXTURE)

    content_leak = [_record("a", "train"), _record("b", "validation"), _record("c", "test")]
    content_leak[2] = DatasetRecord.from_dict({**content_leak[2].__dict__, "content_sha256": content_leak[0].content_sha256})
    with pytest.raises(SplitValidationError, match="content_sha256"):
        validate_records_for_experiment(manifest, content_leak, APPROVED_FIXTURE)


def test_valid_grouped_splits_require_all_three_partitions() -> None:
    manifest = DatasetManifest("fixture", "1", "local", "test", "sha256:test", "sha256:index", 3, "fixture", "NONE", "approved", "grouped_non_random")
    validate_records_for_experiment(manifest, [_record("a", "train"), _record("b", "validation"), _record("c", "test")], APPROVED_FIXTURE)

    two_sample_manifest = DatasetManifest("fixture", "1", "local", "test", "sha256:test", "sha256:index", 2, "fixture", "NONE", "approved", "grouped_non_random")
    with pytest.raises(SplitValidationError, match="train, validation, and test"):
        validate_records_for_experiment(two_sample_manifest, [_record("a", "train"), _record("c", "test")], APPROVED_FIXTURE)


def test_manifest_marked_approved_is_rejected_without_trusted_registry_entry() -> None:
    manifest = DatasetManifest("fixture", "1", "local", "test", "sha256:test", "sha256:index", 3, "fixture", "NONE", "approved", "grouped_non_random")

    with pytest.raises(SplitValidationError, match="trusted approval index"):
        validate_records_for_experiment(manifest, [_record("a", "train"), _record("b", "validation"), _record("c", "test")], frozenset())


def test_external_approval_index_contains_only_the_documented_research_fixture() -> None:
    approvals = load_approved_manifests(ROOT / "registry" / "approved-manifests.json")

    assert len(approvals) == 1
    assert next(iter(approvals))[0] == "p2b2a-ditfake-mini"


def test_admitted_dataset_rehashes_index_and_image_files(tmp_path) -> None:
    data_root = tmp_path / "dataset"
    records = []
    for sample_id, split, content in (("a", "train", b"alpha"), ("b", "validation", b"bravo"), ("c", "test", b"charlie")):
        image_path = data_root / "images" / f"{sample_id}.jpg"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(content)
        raw = dict(_record(sample_id, split).__dict__)
        raw["content_sha256"] = sha256(content).hexdigest()
        records.append(raw)
    index_path = data_root / "index.jsonl"
    index_path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    index_hash = "sha256:" + sha256(index_path.read_bytes()).hexdigest()
    manifest = DatasetManifest("fixture", "1", "local", "test", "sha256:test", index_hash, 3, "fixture", "NONE", "approved", "grouped_non_random")

    assert len(validate_admitted_dataset(manifest, index_path, data_root, APPROVED_FIXTURE)) == 3
    (data_root / "images" / "a.jpg").write_bytes(b"tampered")
    with pytest.raises(SplitValidationError, match="file hash"):
        validate_admitted_dataset(manifest, index_path, data_root, APPROVED_FIXTURE)


def test_encoder_adapters_are_registered_but_cannot_load_weights() -> None:
    registry = EncoderAdapterRegistry()

    assert {status.identifier for status in registry.statuses()} == {"clip", "dinov2", "siglip", "convnext", "efficientnet", "vit"}
    assert all(status.state == "blocked" and status.feature_dimension is None for status in registry.statuses())
    with pytest.raises(RuntimeError, match="blocked"):
        registry.get("clip").encode(b"not-an-image")


def test_environment_record_contains_required_preparation_fields() -> None:
    record = build_environment_record(ROOT / "manifests", timestamp_utc="2026-07-27T00:00:00+00:00")

    assert record["timestamp_utc"] == "2026-07-27T00:00:00+00:00"
    assert len(record["dataset_manifests"]) == 7
    assert all("hash" in entry for entry in record["dataset_manifests"])
    assert len(record["encoder_adapters"]) == 6
    assert all("feature_dimension" in entry for entry in record["encoder_adapters"])
    assert {"python", "platform"} <= set(record["hardware"])
