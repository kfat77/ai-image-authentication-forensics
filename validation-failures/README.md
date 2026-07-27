# P6-A Validation Failure Records

This directory is reserved for append-only, versioned P6-A validation-failure manifests. It contains no validation images, personal data, secrets, or unapproved institution material.

Each failure record follows this minimum structure:

```yaml
failure_id: immutable-id
benchmark_id: frozen-benchmark-id
sample_id: manifest-sample-id
sample_hash: sha256
category: false_positive | false_negative | out_of_scope | uncertain
candidate_id: candidate-version-id
model_hash: checkpoint-hash
analysis_version: immutable-build-id
registry_references: model-calibration-provider-chain-or-experimental-status
observed_output: bounded-factual-description
scope_state: IN_SCOPE | OUT_OF_SCOPE | UNKNOWN
limitation: required
created_at: RFC3339-UTC
supersedes: optional-prior-record
```

Records are never deleted. Corrections and later analysis append a linked superseding record while retaining the original failure observation.
