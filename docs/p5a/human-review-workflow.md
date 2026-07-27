# P5-A Human Review Workflow

## Controlled workflow

```text
Admitted validation sample
        ↓
Automatic analysis and hash-bound report
        ↓
Scope and risk presentation (not an automatic verdict)
        ↓
Independent human review
        ↓
Recorded review decision and rationale
        ↓
Agreement analysis and validation report
```

## Reviewer protocol

1. The system operator runs the approved analysis version. They cannot approve their own review.
2. A reviewer confirms report input hash, report hash, evidence-manifest hash, versions, Registry references (if model evidence is present), scope status, evidence summary, and stated limitations.
3. The reviewer chooses exactly one decision:
   - `ACCEPT_WITHIN_SCOPE`: evidence and limitations are adequately represented for the declared validation scenario. This does not endorse an origin conclusion.
   - `RETURN_FOR_MORE_EVIDENCE`: the report needs additional permitted evidence, provenance verification, or a technical re-run.
   - `EXCLUDE_OUT_OF_SCOPE`: the sample/report cannot be evaluated under the declared validation scope.
4. The reviewer records a non-empty reason. A second independent reviewer processes the agreement subset without being shown the first review decision.
5. A designated validation lead records disagreements and their disposition. Disagreement is a result, not a failure to be hidden.

## Review record

```json
{
  "review_id": "institution-assigned-id",
  "validation_batch_id": "frozen-batch-id",
  "sample_sha256": "input-hash",
  "report_hash": "authentication-report-hash",
  "reviewer": "institutional-reviewer-id",
  "decision": "ACCEPT_WITHIN_SCOPE | RETURN_FOR_MORE_EVIDENCE | EXCLUDE_OUT_OF_SCOPE",
  "reason": "required reviewer rationale",
  "timestamp": "RFC3339 UTC",
  "independent_review": true
}
```

This workflow complements Case Management and Audit Trail; P5-A does not connect it to real institutional identity systems or legally binding signatures.
