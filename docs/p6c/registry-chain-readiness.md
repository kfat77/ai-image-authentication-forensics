# P6-C Registry Chain Readiness

The next P6-B run needs two separate conditions:

1. **Research validation eligibility:** every dataset sample is admitted and hash-verifiable, with contamination-safe splits and declared coverage.
2. **Formal validation-package eligibility:** a signed Registry of Record chain exists for the selected Provider:

```text
ModelRecord (signed, APPROVED)
        ↓
CalibrationRecord (signed, APPROVED, model/scope-consistent)
        ↓
ProviderAdmissionRecord (signed, verified binding)
        ↓
Signed Validation Package
```

The P4-C `APPROVED` workflow remains independent from P6 candidate-validation outcomes. P6-C does not alter the current candidate's `experimental` state and does not create a placeholder approval. If the Registry chain is unavailable, a run may record research observations only; it cannot issue a formal validation package or influence an Authentication Report.

Before a future chain is proposed, reviewers must resolve model-weight rights, calibration population and scope, validation data permissions, evaluation references, and provider/version binding. The required approval workflow remains append-only with separated roles.
