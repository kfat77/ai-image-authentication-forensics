# Model approval workflow

`DRAFT → SUBMITTED → VALIDATED → REVIEWED → APPROVED → DEPRECATED`.

The current Registry revision changes with each transition, but no prior revision is removed. A distinct append-only `ApprovalEvent` chain is retained per stable `record_id`:

```json
{
  "event_id": "...",
  "record_id": "...",
  "previous_state": "...",
  "new_state": "...",
  "actor": "...",
  "timestamp": "RFC3339 UTC",
  "reason": "...",
  "event_hash": "...",
  "previous_event_hash": "..."
}
```

`verify_approval_history()` checks the mandatory initial DRAFT event, permitted state sequence, event contents, and each previous-event hash. Missing, modified, reordered, or disconnected events fail verification. The submitting actor cannot approve their own model or calibration record.

The Registry consumes the P3-B role model at its boundary: `ANALYST` creates and submits, `REVIEWER` validates and reviews, and `ADMIN` approves or deprecates. A missing required role or a submitter attempting approval is rejected.
