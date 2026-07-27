# P3-C operations manual

## Start-of-shift checks

1. Confirm the internal gateway is not exposed to a public network and only approved operators can reach it.
2. Run the private health checks. They return only booleans:

   ```json
   {"service": true, "storage": true, "database": true, "audit_integrity": true, "ready": true}
   ```

3. If `audit_integrity` is false, stop report issuance and open an internal integrity incident. Preserve logs and storage; do not rewrite events.
4. Confirm that operational, error, and audit logging have separate handlers and no sensitive file payloads are being logged.

## Incident actions

| Signal | Immediate action | Do not do |
| --- | --- | --- |
| Storage unavailable | Pause new analysis; preserve request metadata and retry only through the normal case workflow | Substitute a personal/local storage location |
| Database unavailable | Stop lifecycle transitions and report signing; restore only through the recovery procedure | Manually alter Case records |
| Audit chain broken | Stop issuance, isolate the affected event range, begin review | Regenerate or delete audit events |
| Key-provider failure | Stop signing; use a distinct unsigned-review state | Fall back silently to a test key |
| Input rejected | Record reason class and input hash only | Log image bytes or treat rejection as AI evidence |

## Change and release control

Deployment changes need a recorded operator, approved configuration version, container image digest, dependency review, and rollback plan. Changes to authentication logic, evidence fusion, model calibration, access policy, KMS integration, or retention require separate review; none are authorized by this P3-C reference implementation.

## Health implementation boundary

`PrivateDeploymentHealth` is a pure internal probe aggregator. The deployer supplies storage, database, and audit verification callables. It intentionally has no outbound telemetry and returns no image content, case detail, secret, or report payload.
