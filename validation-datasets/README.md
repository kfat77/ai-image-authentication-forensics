# Validation Dataset Registry

This directory is the admission boundary for P6 validation data. It currently contains schemas and an empty registry only; it does not admit the P2-B2-A fixture, because the workspace lacks its per-file records and hashes.

Every admitted record must validate against `sample-schema.json`, have a lower-case SHA-256 file hash, and include source, licence, scenario, label, collection metadata, and split. The registry rejects records that do not meet these conditions before a validation run begins.

No image bytes, personal information, secrets, or unreviewed samples belong in this repository directory.
