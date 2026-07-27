# P6-A Model Validation Program

## Objective and status boundary

P6-A defines how an experimental AI Detector is evaluated as a **validated detector candidate** in a controlled benchmark. It does not implement or claim a validated detector, authorize institutional deployment, establish judicial suitability, or permit public performance claims.

`validated detector candidate` is a validation-program outcome. It is not equivalent to the P4-C Registry `APPROVED` state. A candidate cannot contribute to a formal Authentication Report until the separate Model Registry, Calibration Registry, and Provider Admission controls have been satisfied and verified at report time.

## Candidate lifecycle

```text
Experimental candidate
        ↓  (frozen benchmark, reproducible run)
Validation
        ↓  (independent technical/governance review)
Review
        ↓  (all acceptance criteria and failure register retained)
Validated detector candidate
        ↓  (separate Registry-of-Record approval workflow; not part of P6-A)
Potential formal Provider admission
```

At each stage, a failed gate may return the candidate to experimental work, narrow the declared scope, or halt it. A candidate may never be relabelled “validated” merely because a single aggregate metric is high.

## Data and benchmark admission

Every validation sample must have a documented source, unambiguous permission for controlled validation, stable SHA-256, complete scenario labels, and a repeatable access path under the approved retention/access terms. The Benchmark Manifest is frozen before model scoring.

The benchmark must include, with separately reported coverage:

- real images: ordinary photography, mobile-camera images, and licensed news images;
- AI-generated images: more than one documented generation method and quality level where licences permit;
- edited/derived images: compression, screenshots, and secondary processing.

Missing coverage is a coverage gap, not a reason to infer performance. Samples with unavailable permissions, unknown provenance, mutable hashes, or incomplete labels are excluded before the run and reported in the admission log.

## Required run procedure

1. Freeze the Benchmark Manifest, code/build identifier, pre-processing configuration, candidate weight hash, and evaluation plan.
2. Record Model Registry and Calibration Registry references. For any report-like ML evidence path, record the Provider Admission reference and verify the entire signed chain. Experimental candidates without a formal admission may be benchmarked only outside formal Authentication Report fusion.
3. Run scoring once per frozen sample under declared hardware/software conditions. Record scope exclusion and processing errors separately from predicted labels.
4. Compute the defined metrics overall and by scenario, source, generator/quality where documented, and transformation.
5. Append every false positive, false negative, out-of-scope, uncertain, and processing failure to `validation-failures/` with no deletion path.
6. Have independent technical and governance reviewers verify data admission, reproducibility selection, Registry references, metrics, and all failure records.
7. Issue a P6-A validation report recommending one of: `remain experimental`, `validated candidate within stated scope`, `narrow scope and repeat`, or `halt`. None authorizes formal use.

## Candidate acceptance gate

The validation report may recommend `validated candidate within stated scope` only when:

- all included samples are manifest-complete and permission-reviewed;
- the benchmark, code, weights, configuration, and Registry references are immutable and reproducible;
- required metrics are calculated with explicit denominators, exclusions, and scope conditions;
- calibration metrics are reported only for inputs within the declared calibration population;
- all required failure categories are retained and independently reviewed;
- the report states supported conditions, coverage gaps, limitations, and non-authorized uses;
- an independent reviewer approves the *validation report*, not the model for formal service.

Thresholds and minimum sample sizes must be pre-registered by the sponsoring institution before scoring. P6-A intentionally supplies no universal threshold or “pass” number.
