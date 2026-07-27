# P3-C security baseline

## Baseline controls

| Boundary | P3-C control | Limitation / deployment action |
| --- | --- | --- |
| Network | Compose internal network; only backend maps to `127.0.0.1:8080` | Institution must place an approved internal gateway and firewall in front of any shared service |
| Input | JPEG, PNG, and WebP magic-byte allowlist; byte-size limit; SHA-256 verification | This is file admission, not malware scanning or origin determination |
| Access | Existing institutional roles remain `ADMIN`, `ANALYST`, `REVIEWER`, `AUDITOR`; reviewers cannot approve their own reports | Production identity lifecycle and MFA remain institution responsibilities |
| Custody | Original, evidence-bundle, and report hashes are preserved without replacement | Physical/media chain of custody is outside software-only control |
| Signing | `KeyProvider` supports injected test and external-KMS operations | Test HMAC keys must never be used operationally; no cloud KMS is integrated |
| Logging | Distinct `institution.operations`, `institution.errors`, and `institution.audit` channels | Deployment handlers must redact image bytes, prompts, credentials, and access tokens |
| Dependency / host | Non-root backend container and pinned Python dependencies | Vulnerability scanning, patch SLAs, and host hardening are required before institution operation |

## Input admission contract

`validate_input_file` rejects empty, over-limit, unknown-type, and hash-mismatched input before a worker receives it. The admission service must take its size limit from reviewed configuration and must store only the content hash in logs. It must never infer AI generation from an absent metadata field, a failed upload, or a rejected file.

## Authentication and authorization

P3-C keeps P3-B RBAC as the authorization domain. API authentication must be terminated at an institution-controlled internal gateway or identity-aware service. The gateway must bind an authenticated actor to the existing role decision; client-controlled role headers are not authoritative.

This reference does not connect to a real identity provider, government system, certificate authority, HSM, or KMS and therefore makes no compliance or certification assertion.
