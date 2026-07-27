# P3-C configuration reference

All values are provided at runtime. `config/private.env.example` is a non-secret template and must not be used unchanged.

| Variable | Required | Example form | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | `postgresql://user:password@database:5432/ai_auth` | Institution-selected database endpoint; keep its password synchronized with the local Compose bootstrap value |
| `STORAGE_PATH` | Yes | `/var/lib/ai-authentication/evidence` | Mounted evidence working path; production object-storage adapter is separately governed |
| `SIGNING_KEY_PROVIDER` | Yes | `local_test` or `external_kms` | Selects the key-provider mode, never a secret value |
| `AUDIT_CONFIG` | Yes | `hash_chain_v1` | Names the reviewed audit policy |
| `LOG_LEVEL` | Yes | `INFO` | Operations/error logging threshold |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Compose only | deployment-local values | Database container bootstrap; protect the password outside source control |
| `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` | Compose only | deployment-local values | Storage container bootstrap; protect outside source control |

`PrivateDeploymentConfig.from_env()` fails closed when any required variable is missing, when the provider is unknown, or when the database scheme is not `sqlite`, `postgres`, or `postgresql`. It deliberately reads no signing-key material: a local test key is injected by the local operator only, and an external KMS adapter receives its operations from the institution runtime.

`configure_private_loggers(log_directory, level)` writes three independent local streams: `operations.log`, `errors.log`, and `audit.log`. The deployment must mount that directory with an institution-approved retention and access policy; log handlers must never be passed image bytes, prompts, secrets, or access tokens.

## Configuration handling rules

- Keep secret values in the institution's approved secret store or protected local file, never in source, containers, reports, audit records, or tickets.
- Do not log `DATABASE_URL` because it can contain credentials.
- Rotate database and storage bootstrap credentials before any environment is shared.
- Treat `local_test` as acceptance-test-only. A deployment requesting `external_kms` must provide a reviewed adapter and key reference.
- Version and approve every configuration change alongside its deployment and recovery record.
