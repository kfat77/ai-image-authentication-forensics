from __future__ import annotations

import json
from hashlib import sha256

from PIL import Image

from authentication import AuthenticationReportEngine


def _png() -> bytes:
    from io import BytesIO

    output = BytesIO()
    Image.new("RGB", (32, 24), (32, 96, 160)).save(output, format="PNG")
    return output.getvalue()


def test_authentication_report_is_hash_bound_auditable_and_uncertain_without_model(tmp_path) -> None:
    report = AuthenticationReportEngine().create(_png(), tmp_path, submitter_id="agency-reviewer-1")
    case_root = tmp_path / report.analysis_id

    assert report.assessment.authenticity_status == "uncertain"
    assert report.output_sha256 == report.audit_trail["output_sha256"]
    assert (case_root / "authentication-report.pdf").read_bytes().startswith(b"%PDF")
    saved = json.loads((case_root / "authentication-report.json").read_text(encoding="utf-8"))
    assert saved["input_sha256"] == report.input_sha256
    assert saved["evidence"]["evidence_completeness"] == 0.5
    assert {item["name"] for item in saved["evidence"]["methods"]} == {"metadata", "frequency", "noise", "artifact"}
    assert saved["output_files"]["evidence_manifest_sha256"] == sha256((case_root / "evidence" / "evidence-bundle.json").read_bytes()).hexdigest()
    assert "absence of exif" in " ".join(saved["limitations"]).lower()
    AuthenticationReportEngine().create(_png(), tmp_path, submitter_id="agency-reviewer-2")
    audit_entries = [json.loads(line) for line in (tmp_path / "audit-trail.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(audit_entries) == 2
    assert audit_entries[0]["json_sha256"] == sha256((case_root / "authentication-report.json").read_bytes()).hexdigest()
    assert audit_entries[0]["pdf_sha256"] == sha256((case_root / "authentication-report.pdf").read_bytes()).hexdigest()
