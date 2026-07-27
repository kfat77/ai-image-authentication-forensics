# P5-B Reviewer Feedback Protocol

## Comparison rules

Reviewer feedback compares the system's bounded Authenticity Assessment with the normal human workflow's recorded disposition. It does not transform either value into a claim of image-origin truth.

- `AGREE`: the predefined pilot comparison rubric finds the two outputs compatible.
- `DISAGREE`: the rubric finds them incompatible; a reason and failure-record reference are required.
- `UNDETERMINED`: either side is inconclusive, out of scope, unavailable, or not semantically comparable. This is a valid, reportable result.

The charter must define its compatible/incompatible mapping before data collection. It must not be changed mid-batch; a changed rubric starts a new pilot batch.

## Schema

```json
{
  "feedback_id": "institution-assigned-id",
  "case_id": "pilot-case-reference",
  "pilot_record_id": "admitted-record-id",
  "system_assessment": "likely_real | likely_ai_generated | uncertain | out_of_scope | analysis_failed",
  "human_assessment": "institution-defined-normal-process-disposition | unavailable",
  "agreement": "AGREE | DISAGREE | UNDETERMINED",
  "reason": "required non-empty reviewer rationale",
  "reviewer": "authorized-reviewer-id",
  "timestamp": "RFC3339 UTC",
  "report_hash": "authentication-report-hash",
  "analysis_version": "immutable-version-id",
  "failure_record_id": "required-for-disagreement-or-failure | null"
}
```

## Controls

- The feedback reviewer cannot be the analyst who submitted the pilot copy.
- Feedback is append-only; corrections create a superseding feedback record referencing the prior record.
- A report hash, analysis version, and case/pilot record reference are mandatory.
- Feedback is visible to authorised pilot reviewers and auditors only. It must not be sent to the normal workflow in a way that changes the outcome.
