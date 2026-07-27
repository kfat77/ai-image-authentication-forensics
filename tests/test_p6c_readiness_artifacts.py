import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_validation_dataset_schema_is_hash_gated_and_registry_has_no_unadmitted_samples():
    schema = json.loads((ROOT / "validation-datasets/sample-schema.json").read_text(encoding="utf-8"))
    required = {"sample_id", "file_hash", "source", "license", "scenario", "label", "collection_metadata", "split"}
    assert required <= set(schema["required"])
    assert schema["properties"]["file_hash"]["pattern"] == "^[0-9a-f]{64}$"
    registry = json.loads((ROOT / "validation-datasets/registry.json").read_text(encoding="utf-8"))
    assert registry["records"] == []
    assert registry["admission_status"] == "NO_ADMITTED_SAMPLES"


def test_current_candidate_readiness_is_blocked_and_p6b_rejection_is_preserved():
    readiness = json.loads((ROOT / "validation-package/p6c-readiness-preflight.json").read_text(encoding="utf-8"))
    assert readiness["readiness_status"] == "BLOCKED"
    assert readiness["signature_status"] == "NOT_ISSUED"
    assert readiness["provider_hash"] is None and readiness["dataset_manifest_hash"] is None
    prior = json.loads((ROOT / "validation-runs/p6b-efficientnet-p2b2a-preflight-001.json").read_text(encoding="utf-8"))
    assert prior["status"] == "REJECTED"
