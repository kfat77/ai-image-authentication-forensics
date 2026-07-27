# P5-B Shadow Pilot Design

## Purpose and non-consequential boundary

The Shadow Pilot is a private, parallel validation exercise. It observes how the existing AI Image Authentication platform behaves beside an institution's ordinary human workflow. It is not a deployment, judicial use, commercial service, public endpoint, or a source of operational decisions.

The pilot output must not approve, reject, delay, prioritize, route, or alter any institution process. The normal human process remains authoritative and proceeds without waiting for system analysis.

## Parallel Review Workflow

```text
Permitted image enters normal institution workflow
        ├── Normal human workflow continues unchanged ──→ human-process disposition
        │
        └── Isolated pilot copy → Authentication analysis → hash-bound report
                                                        ↓
                                      Reviewer feedback comparison (non-consequential)
                                                        ↓
                                     Aggregate metrics and failure register
```

The system assessment is one of `likely_real`, `likely_ai_generated`, or `uncertain`, with scope and evidence limitations. The human-process disposition is recorded as an institution-defined pilot comparison value, not as judicial ground truth. Comparison is `AGREE`, `DISAGREE`, or `UNDETERMINED`; `UNDETERMINED` is required whenever the two outputs are not semantically comparable or either side lacks a conclusion.

## Pilot Environment

The pilot runs only within a separately identified private environment:

- private network boundary; no internet-facing API, public UI, or public report download;
- distinct pilot data store/object-storage prefix and isolated credentials from normal operations;
- minimum necessary RBAC: analysts submit permitted copies, reviewers view reports/feedback, auditors inspect audit records, and administrators manage pilot configuration;
- audit trail, evidence preservation, Registry-of-Record verification, health checks, and backup/restore procedures enabled before the first sample;
- logs contain identifiers/hashes and operational metadata only; no image content is exported to external telemetry;
- test-only keys are acceptable only for a non-consequential technical rehearsal and must be explicitly marked. A pilot with institution-supplied keys still remains non-production.

## Entry and exit gates

Entry requires a completed P5-A Validation Report, an approved private pilot charter, source/licence-reviewed pilot records, verified approved model/calibration/provider chains for any ML evidence, successful audit-chain verification, and a recovery drill.

Exit requires an internal closeout report, frozen pilot metrics/failure records, audit verification, retention/disposal action under the charter, revoked temporary access, and a documented decision to halt, repeat with narrower scope, or seek separate approval for a later phase. Exit never automatically authorizes a public or operational rollout.
