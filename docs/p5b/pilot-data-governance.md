# P5-B Pilot Data Governance

## Admission protocol

Only a permitted copy of a source-reviewed image may enter the Shadow Pilot. The normal-workflow original remains governed by the institution's existing process. A sample with missing source, consent/licence, file hash, scenario type, case reference, or analysis version is rejected before analysis.

```yaml
pilot_record_id: institution-assigned-stable-id
case_id: pseudonymous-or-internal-case-reference
source: reviewed-source-description
consent_or_license: recorded-authority-for-shadow-pilot-use
reviewed_by: data-governance-reviewer-id
reviewed_at: RFC3339-UTC
file_hash: lowercase-sha256
scenario_type: ordinary_photography | mobile_camera | social_recompression | screenshot | news | ai_generated | ai_edited | mixed_processing
analysis_version: immutable-system-build-or-release-id
registry_references: optional-approved-ML-chain-hashes
retention_class: institution-defined-pilot-policy
admission_status: CANDIDATE | ADMITTED | REJECTED | WITHDRAWN
limitations:
  - required documented limitation
```

## Isolation and minimization

- Store pilot copies and derived Evidence Bundles in a pilot-only storage boundary. Do not commingle them with general research or institution production data.
- Use the least data required for the declared scenario. Exclude unnecessary personal information from pilot metadata and reviewer feedback.
- Preserve input, Evidence Bundle, report, and audit hashes for reproducibility. Do not overwrite an admitted record or replace its source file after hashing.
- A consent withdrawal or licence restriction changes the record to `WITHDRAWN`; retain only the minimum audit reference required by the pilot charter and prevent further analysis.
- No record with unknown source may be converted to an admitted pilot record merely because it is technically analyzable.

## Retention, access, and disposal

The pilot charter must state retention duration, authorized roles, backup treatment, legal/organisational hold handling, and disposal verification. At closeout, the data custodian documents deletion or archival under the charter while preserving non-content audit evidence as authorized. P5-B does not prescribe an institution's retention period.
