# P5-B Failure Analysis Process

## Immutable failure register

`pilot-failure-analysis/` is the reserved repository location for versioned, non-image-content pilot failure records. It contains no real institution data in P5-B design. Each observed failure is appended; reclassification or remediation creates a linked follow-up and never deletes the original record.

## Categories and handling

| Category | Definition | Required handling |
|---|---|---|
| False alert | system output conflicts with documented reference/normal-process comparison within declared scope | preserve report/evidence hashes, record scenario and comparison limitation, review scope/calibration before any repeat |
| Missed alert | system does not surface an expected concern within declared scope | preserve all evidence and note whether the reference is sufficiently documented |
| Insufficient evidence | provenance, deterministic observations, or admitted model evidence cannot support a bounded review | retain as `uncertain` or return for more evidence; do not force a conclusion |
| Input anomaly | malformed, unsupported, corrupted, oversized, or unsafe input prevents normal analysis | retain technical error and input hash; do not retry outside safety limits |
| Out of scope | sample conditions do not satisfy declared validation/calibration scope | record scope reason; exclude from comparable metrics rather than relabeling it |

## Record schema

```yaml
failure_record_id: immutable-id
pilot_batch_id: frozen-batch-id
case_id: internal-reference
input_hash: sha256
report_hash: optional-if-generated
category: FALSE_ALERT | MISSED_ALERT | INSUFFICIENT_EVIDENCE | INPUT_ANOMALY | OUT_OF_SCOPE
scenario_type: declared-scenario
analysis_version: immutable-version-id
registry_references: optional-approved-chain-hashes
description: factual-observation-only
limitation: required
disposition: OPEN | REVIEWED | REMEDIATION_PROPOSED | CLOSED_WITHOUT_CHANGE
created_at: RFC3339-UTC
supersedes: optional-prior-failure-record-id
```

## Governance loop

The pilot lead periodically reviews grouped records with analysts, reviewers, security/audit representatives, and data governance. Permitted outcomes are: retain the limitation, narrow the pilot scope, correct a non-model operational defect, propose a separately governed model/calibration review, or halt the pilot. No failure record may be deleted to improve a metric.
