# P3-C backup and recovery

## Backup set

Each backup set must contain the same declared recovery point:

1. Database backup of Case, Evidence Preservation, Audit Event, and Report records.
2. Immutable copy of evidence objects and derived report files, retaining original content hashes.
3. An audit-chain verification result and the event range included in the backup.
4. A manifest listing backup timestamp, tool/deployment version, database backup hash, object inventory hash, and audit verification result.

Encrypt backup media with institution-controlled keys. Store at least one copy in a separately administered recovery location. Do not place source image bytes in external telemetry or unapproved cloud storage.

## Restore drill

1. Create an isolated recovery environment, with no access to a production-like service endpoint.
2. Restore the database snapshot and evidence/report objects to a new storage location.
3. Verify every restored object hash against the backup manifest.
4. Run `verify_audit_chain()` over the restored audit event sequence; fail the drill if it returns `invalid` or `broken_event`.
5. Check each report's original-file, evidence-bundle, report, and signature hashes against its Case record.
6. Record the drill operator, time, tool version, manifest hash, pass/fail result, and any exception in an audit event.

A restore is successful only when the integrity checks pass. The SQLite persistence acceptance test demonstrates close/reopen recovery of Case, Evidence, Audit Event, and Report records; the Docker acceptance test is intentionally opt-in. A successful drill does not validate a forensic conclusion and does not repair a broken audit chain; it preserves the failure for investigation.

## Recovery objectives to set institutionally

P3-C intentionally does not prescribe an RPO or RTO. The deploying institution must set them based on case retention obligations, storage volume, legal process, and incident-response policy, then test them at least at the required internal cadence.
