# P6-C Validation Dataset Admission

The P6-C Validation Dataset Registry is the only allowed entry point for the next P6-B benchmark. Each record must include `sample_id`, `file_hash`, `source`, `license`, `scenario`, `label`, `collection_metadata`, and `split`; the schema rejects a missing or malformed hash.

Admission flow:

```text
Candidate file and source record
        ↓
Licence / consent and source review
        ↓
SHA-256 verification and immutable sample record
        ↓
Scenario and transformation label review
        ↓
Parent-group split contamination check
        ↓
Admitted Validation Dataset Registry record
```

The registry starts empty. The existing P2-B2-A fixture remains outside it because its raw source files and per-file hashes are unavailable in this workspace. Dataset-level hash claims do not satisfy this per-file gate.

See [registry schema](../../validation-datasets/sample-schema.json) and [coverage matrix](../../validation-datasets/coverage-matrix.md).
