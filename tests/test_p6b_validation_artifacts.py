import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_p6b_rejected_preflight_has_complete_identity_and_no_fabricated_admission():
    run = json.loads((ROOT / "validation-runs/p6b-efficientnet-p2b2a-preflight-001.json").read_text(encoding="utf-8"))
    for field in ("run_id", "model_record_hash", "calibration_record_hash", "provider_record_hash", "dataset_manifest_hash", "code_version", "timestamp"):
        assert field in run
    assert run["model_record_hash"] is None == run["candidate"]["model_record_hash"]
    assert run["calibration_record_hash"] is None == run["calibration"]["calibration_record_hash"]
    assert run["provider_record_hash"] is None == run["provider"]["provider_record_hash"]
    assert run["dataset_manifest_hash"] == run["dataset"]["dataset_manifest_hash"]
    assert run["status"] == "REJECTED"
    assert all(value is None for key, value in run["metrics"].items() if key != "not_evaluated_reason")


def test_p6b_failure_records_are_retained_and_linked_from_run():
    run = json.loads((ROOT / "validation-runs/p6b-efficientnet-p2b2a-preflight-001.json").read_text(encoding="utf-8"))
    records = [json.loads((ROOT / "validation-failures" / f"{failure_id}.json").read_text(encoding="utf-8")) for failure_id in run["failure_record_ids"]]
    assert {record["category"] for record in records} == {"out_of_scope", "uncertain"}
    assert all(record["created_at"] == run["timestamp"] for record in records)
