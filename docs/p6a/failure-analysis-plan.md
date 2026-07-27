# P6-A Validation Failure Analysis Plan

`validation-failures/` is the append-only library for P6-A benchmark failures. It is separate from P5-B Shadow Pilot failures: P6-A concerns candidate validation against a frozen benchmark; P5-B concerns a non-consequential institutional parallel workflow.

## Required categories

| Category | Definition | Metric treatment | Review question |
|---|---|---|---|
| `false_positive` | a comparable, in-scope curated real sample receives the detector’s positive outcome under the pre-registered decision rule | remains in FPR and precision denominators | is the pattern linked to camera processing, news editing, compression, or a dataset source? |
| `false_negative` | a comparable, in-scope curated AI-generated sample does not receive the positive outcome under the pre-registered rule | remains in FNR and recall denominators | is the pattern linked to method, quality, transformation, or unrepresented generator family? |
| `out_of_scope` | a sample or score fails declared calibration/model/benchmark conditions | excluded only under the pre-registered rule; count and reason reported | should the candidate scope remain narrow or should a separate validation population be defined? |
| `uncertain` | the detector or report legitimately cannot produce a bounded positive/negative comparison | reported separately; never silently coerced into a binary class | does uncertainty protect against unsupported inference, or reveal an evidence/pipeline limitation? |

## Investigation procedure

1. Append the failure record with sample hash, manifest ID, candidate/model hash, analysis version, Registry references, category, and factual observed output.
2. Confirm manifest integrity, label/permission state, scope state, and reproducibility of the processing result before interpreting the failure.
3. Slice the register by source, scenario, generator/method, quality, transformation, metadata/provenance availability, and parent group.
4. Record a bounded hypothesis and one of: retain limitation, narrow scope, correct an operational defect, propose a separate calibration/model experiment, or halt candidate progression.
5. Independent reviewers verify that the register includes every expected failure and that no sample was deleted, relabelled, or moved across splits after scoring.

No failure analysis may update a model, threshold, benchmark label, or Registry status in place. Any such proposed change begins a new versioned validation run.
