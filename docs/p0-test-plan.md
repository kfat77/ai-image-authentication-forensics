# P0 test and verification plan

## Scope

P0 ships documentation and a standalone JSON Schema draft only. It must not alter the current prompt-reconstruction route, add model dependencies, download weights, change deployment manifests, or claim a detector exists. The P0 verification target is therefore contract integrity and non-regression, not detection accuracy.

## P0 checks

| Check | Evidence | Acceptance condition |
| --- | --- | --- |
| JSON Schema parses | Automated JSON parse in CI/local check | `contracts/detection-result.v2.schema.json` is valid JSON. |
| Schema examples validate | Future contract test with a draft validator | A score is allowed only with `calibration_status: approved`; all other statuses require `ai_probability: null`. |
| Closed fields | Contract test | Unknown top-level and nested fields are rejected where `additionalProperties: false` is declared. |
| Evidence semantics | Documentation review | Each evidence item requires level, source and limitation; summary requires human review and a limitation. |
| v1 non-regression | Existing test suite | Existing `/v1/analyze` OpenAPI and response tests remain green without any route behaviour change. |
| Dependency/deployment non-regression | Diff and dependency review | No large-model dependency, weight artifact, Dockerfile, Kubernetes, production setting or workflow behaviour change is introduced by P0. |
| Governance completeness | Document review | Dataset register, benchmark protocol, experiment record, model card, detector interface, ensemble plan and risk register exist and cross-reference one another. |

## P1 test matrix (planned)

| Layer | Unit tests | Integration tests | Evaluation gate |
| --- | --- | --- | --- |
| Metadata/C2PA adapter | unsupported files, malformed EXIF, bounded extraction, verifier mapping | authorized upload through result assembly | no provenance inference from absence/presence alone |
| Frequency/JPEG/noise detectors | deterministic fixtures, dimensions, normalization, invalid images | detector registry with fixed image corpus | robustness matrix, false-positive slices |
| Artifact/semantic adapters | declared unavailable/no-model behaviour and output limits | only approved adapters can load | labelled localization/semantic evaluation before evidence claim |
| Vision encoders/classifiers | artifact hash, preprocessing, logits, abstention | offline inference fixture | held-out, time-held-out and calibration reports |
| Ensemble | missing-signal handling, feature provenance, deterministic fusion | complete DetectionResult assembly | no probability until approved calibration |
| API/UI | schema compatibility, authorization, audit fields, response size | upload-to-result lifecycle and human-review display | security/privacy/accessibility review |

## Test-data rules

- Fixtures must be synthetic, public-domain, or otherwise explicitly approved; do not commit user uploads, restricted datasets, real credentials, or model weights.
- Test manifests carry source, licence, hash, intended use and deletion/retention policy.
- A transformation test saves parameters and seed, never just its output file.
- Unit tests never use a real score as an oracle. Performance conclusions belong to versioned benchmark reports.

## P1 readiness condition

P1 may begin only after this P0 contract is approved, at least one lawful fixture set is registered, the detector interface is accepted, and the release owners agree that early features will be labeled `E0`–`E2` rather than presented as detection probabilities.
