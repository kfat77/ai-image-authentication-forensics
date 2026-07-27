from __future__ import annotations

import pytest

from governance import AuditEvent, CalibrationRegistryEntry, EvidenceProvenance, ModelRegistryEntry, validate_evidence_provenance, validate_model_calibration_integrity
from governance.schemas import validate_audit_chain


HASH = "a" * 64


def test_registry_requires_calibration_and_conditions() -> None:
    with pytest.raises(ValueError):
        ModelRegistryEntry("m", "model", "1", "linear", HASH, "source", "license", "data", "evaluation", "", "scope", ("limit",), "approved")
    with pytest.raises(ValueError):
        CalibrationRegistryEntry("c", "1", "dataset", 0.5, {}, 0.1, 0.1, "2026-07-27", (), ("excluded",))


def test_evidence_provenance_requires_hash() -> None:
    with pytest.raises(ValueError):
        EvidenceProvenance("e", "noise", "v1", "2026-07-27T00:00:00Z", "not-a-hash", "bounded", {}, "limit")
    with pytest.raises(ValueError, match="missing fields"):
        validate_evidence_provenance({"evidence_id": "e"})


def test_audit_chain_detects_breaks() -> None:
    first = AuditEvent("1", "2026-07-27T00:00:00Z", "submitter", "submit", "case", HASH, HASH, None, None)
    second = AuditEvent("2", "2026-07-27T00:01:00Z", "reviewer", "review", "case", HASH, HASH, first.event_hash(), None)
    validate_audit_chain([first, second])
    with pytest.raises(ValueError):
        validate_audit_chain([first, AuditEvent("3", "2026-07-27T00:02:00Z", "reviewer", "sign", "case", HASH, HASH, HASH, None)])


def test_approved_model_requires_matching_calibration_registry_entry() -> None:
    model = ModelRegistryEntry("m", "model", "1", "linear", HASH, "source", "license", "data", "evaluation", "c", "scope", ("limit",), "approved")
    calibration = CalibrationRegistryEntry("c", "1", "dataset", 0.5, {"fpr": 0.1}, 0.1, 0.1, "2026-07-27", ("original",), ("screenshots",))
    validate_model_calibration_integrity(model, [calibration])
    with pytest.raises(ValueError):
        validate_model_calibration_integrity(model, [])
