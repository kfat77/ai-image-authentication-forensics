# P6-B Re-run Entry Criteria

The rejected P6-B preflight remains the historical result. A new P6-B run can begin only as a new run ID after all of these conditions are evidenced:

1. `validation-datasets/registry.json` contains licence-reviewed sample records with valid per-file SHA-256 values, source, scenario, label, collection metadata, and split.
2. The frozen dataset manifest records real camera, smartphone, news, and online-distributed images; multiple documented AI methods and resolution/quality slices; JPEG, screenshot, crop, resize, and editing transformations. Any remaining gap is explicitly reported.
3. Parent/source groups are split-contamination checked, and raw files are repeatably accessible to authorized reviewers under documented permissions.
4. The selected model has a source/licence/weight-hash review, and its calibration has an independently documented population, scope, exclusions, ECE, and Brier record.
5. A ModelRecord, CalibrationRecord, and ProviderAdmissionRecord are signed, internally consistent, and verified through the separate Registry workflow. This must not be inferred from a P6 candidate label.
6. A signed Validation Package is generated from the verified chain, frozen dataset manifest, run configuration, report hashes, metrics schema, and limitations.
7. Red-team transformations complete with retained `uncertain`/`OUT_OF_SCOPE` behavior where applicable, and all failures are preserved.
8. Independent technical and governance reviewers approve the **start of the new validation run**. This does not approve the detector for production or public use.

Failure of any item blocks the new run or restricts it to explicitly labeled experimental observation. It never changes the prior P6-B status.
