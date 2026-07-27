# P0 research governance

## Purpose

This document defines the minimum evidence required before data, model weights, benchmarks, or a probability claim can enter the future forensic system. It is a research-control document, not a declaration that detection is implemented or approved for deployment.

## Dataset intake and licence register

Use [dataset-license-register.template.csv](templates/dataset-license-register.template.csv) for every source, including a subset extracted from a larger dataset. A row is incomplete until an accountable reviewer records the source terms and intended-use approval.

Required gates:

1. Record the immutable source URL, version/date, acquisition method, content origin, labels and sample hashes or manifest reference.
2. Separate the **code licence**, **dataset licence**, **model-output terms**, and **derivative/distribution terms**. A permissive repository licence does not license its data or weights.
3. Record whether commercial use, redistribution, model training, derivative labels, biometric/person data, and cross-border storage are permitted.
4. Inspect labels for generator version, prompt/edit history, duplication, leakage, and real-image provenance. Unknown labels remain unknown; they cannot be inferred from filenames or missing metadata.
5. Obtain legal/privacy/data-owner approval before download or use. P0 intentionally downloads no datasets and no checkpoints.
6. Preserve a versioned manifest and data split assignment. Never split near-duplicates, prompt variants, or one generation batch across train and test.

Initial source posture (not approval):

| Candidate | P0 posture | Reason |
| --- | --- | --- |
| GenImage | Evaluation candidate only | The upstream repository does not expose a standard SPDX licence for the dataset; underlying ImageNet and generated-output terms need review. |
| CIFAKE | Do not adopt until original source and terms are identified | Mirrors and tutorial repositories are not an authoritative licence grant. |
| DiffusionDB | Metadata/prompt research candidate only | Image and prompt provenance, user content, and downstream terms must be reviewed separately. |
| LAION AI-related subsets | Do not adopt by name alone | Each subset needs its own construction, opt-out, privacy and licence assessment. |
| ImageNet real images | Controlled evaluation candidate | Access and use terms must be approved; it is not a blanket real-world reference population. |
| AIDE Chameleon | Excluded from commercial/deployment training | Its upstream README states academic research only. |

## Benchmark protocol

### Research questions

Every experiment must declare which question it answers:

- Binary discrimination: within a defined population, distinguish `real` from `generated`.
- Open-set detection: retain performance on generator families or versions withheld from training.
- Source-family hypothesis: rank a finite, documented family set while allowing `unknown`.
- Localization support: identify regions useful for reviewer attention, not ground-truth provenance unless pixel labels exist.

### Required splits

| Split | Purpose | Constraints |
| --- | --- | --- |
| Development | Model choice and debugging | Never used for final claims. |
| Validation | Threshold, calibration and ensemble fitting | Kept distinct by source, generator job and near-duplicate cluster. |
| In-domain test | Fixed holdout from declared population | Locked before final training. |
| Generator-held-out test | New generator family/version | No samples or derivatives in training/validation. |
| Time-held-out test | Generators released or collected after the training cutoff | Documents temporal generalisation. |
| Transformation test | Post-generation edits and delivery transformations | Uses the locked test images, transform parameters and seeds. |
| Field test | Institution-approved, independently curated material | Used only after privacy and lawful-use approval. |

### Metrics and reporting

Report with confidence intervals and counts for each split, generator family, content category and transformation:

- Accuracy, balanced accuracy, AUROC, PR-AUC, precision, recall and F1.
- False-positive and false-negative rates at predeclared operating points; never choose a threshold after inspecting the test results.
- Calibration metrics: expected calibration error, Brier score, reliability diagram and calibration-set description.
- Open-set coverage: unknown-selection rate, forced-attribution rate, and source-family confusion matrix.
- Localization metrics only where legitimate region labels exist; otherwise label overlays as qualitative review aids.
- Latency, peak memory, hardware, image-resolution and failure-rate measurements.

No aggregate score may hide a material subgroup failure. A probability is not eligible for the API until the relevant calibration and transformation results are approved.

### Transformation matrix

The benchmark must include original images and controlled derivatives: JPEG quality bands, resizing, crop/pad, screenshot/re-encode, color adjustment, blur/sharpen, metadata strip/preserve, compositing/Photoshop-style edits where lawfully created, and AI redraw/inpainting where the source image permits it. Each transformation records tool/version, parameters, random seed, order, and whether it changes the correct label or only the expected robustness condition.

## Reproducible experiment record

Create one immutable record per run, based on this template:

```text
experiment_id:
date_utc:
question_and_hypothesis:
repository_commit:
container_digest_and_sbom:
dataset_manifest_ids_and_hashes:
split_manifest_hash:
label_policy_version:
preprocessing_and_transform_versions:
model_architecture_and_weight_hashes:
training_configuration_and_random_seeds:
hardware_and_runtime:
calibration_method_and_data:
predeclared_thresholds:
metrics_with_intervals:
per_slice_results:
known_failures_and_out_of_scope_populations:
reviewer_and_approval_reference:
```

Reruns must either reproduce the registered output within documented numeric tolerance or be marked as a new experiment. Do not overwrite a failed run or replace an artifact at the same digest/path.

## Model card template

Every model, detector adapter, ensemble, and released checkpoint must publish:

```text
model_id / version / artifact hash:
purpose and non-goals:
task and label definitions:
architecture and dependencies:
training data manifests and licences:
evaluation data, time cutoff, transformations and metrics:
calibration method / operating points / abstention policy:
known failure modes and subgroup limitations:
intended users, prohibited uses and human-review requirement:
privacy, retention and data-flow notes:
security / supply-chain provenance / rollback plan:
owner, approver, release date and next review date:
```

## Review and release gate

A model cannot move from research to any externally visible probability or source-family hypothesis unless data governance, independent evaluation, calibration, model card, security review, monitoring, rollback and human-review workflow are approved by accountable owners. This repository cannot grant a government endorsement or substitute for a jurisdiction-specific assessment.
