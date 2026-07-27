# P6-A Benchmark Definition

## Benchmark unit and manifest

One benchmark unit is an immutable file plus its curated validation metadata. A frozen Benchmark Manifest specifies every unit and its split. The same file hash may not appear in more than one split; parent/group identifiers prevent transformed variants from crossing splits.

```yaml
benchmark_id: institution-defined-versioned-id
manifest_hash: sha256-of-canonical-manifest
sample_id: stable-id
file_hash: lowercase-sha256
repeatable_access_reference: controlled-repository-or-archive-reference
source: reviewed-source
license: explicit-license-or-permission-reference
license_reviewed_by: reviewer-id
license_reviewed_at: RFC3339-UTC
scenario: photography | mobile | news | ai_generated | compressed | screenshot | secondary_processed
image_origin: REAL | AI_GENERATED | UNKNOWN
generator_or_method: documented-value-or-OTHER
quality_band: documented-high | documented-medium | documented-low | unknown
edit_status: ORIGINAL | COMPRESSED | RESIZED | CROPPED | AI_EDITED
parent_group_id: source-family-id
split: validation | holdout
limitations:
  - required
```

`UNKNOWN` labels and non-comparable samples are retained as coverage observations but are excluded from binary error denominators with an explicit count and reason.

## Required coverage matrix

| Population | Required benchmark conditions | Reporting slices |
|---|---|---|
| Real | photography, mobile-camera, and licensed news images | image type, source, known post-processing, metadata/provenance availability |
| AI generated | multiple documented generation methods and quality bands where legally available | method/generator, quality, known source, holdout method if any |
| Edited / derived | JPEG/social compression, screenshots, and secondary processing | transformation type/severity and parent group |

The protocol does not invent a label where documentation is absent. It reports coverage gaps such as unavailable generators, unavailable news licences, or unrepresented low-quality images.

## Reproducibility package

Each run stores the manifest hash, sample-hash verification result, code/build hash, model/checkpoint hash, pre-processing configuration hash, hardware/runtime description, scoring output hash, metric artifact hash, and Registry references. Repeatable access means an authorized reviewer can retrieve or verify the frozen content under the documented permission terms; it does not require public publication.

## Pre-scoring controls

- Verify each file hash against the frozen manifest.
- Reject absent/changed files and record them as admission failures.
- Validate label vocabulary and scenario completeness.
- Detect duplicate and parent-group split contamination.
- Freeze the metric definitions, calibration method, and scope/exclusion rules before reading outcomes.
