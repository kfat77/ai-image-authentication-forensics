# P4-B governed model baseline

## Candidate and admission result

P4-B selects the existing research candidate “Torchvision EfficientNet-B0 frozen features plus a linear logistic-regression baseline” only to test the governance chain. Torchvision documents the `IMAGENET1K_V1` EfficientNet-B0 architecture, official weight URL, and preprocessing contract; Torchvision code is BSD-3-Clause. [Torchvision EfficientNet-B0 documentation](https://docs.pytorch.org/vision/main/models/generated/torchvision.models.efficientnet_b0.html) [Torchvision license](https://github.com/pytorch/vision/blob/main/LICENSE)

The candidate record is `models/registry/p4b-efficientnet-b0-linear-baseline.json`; its calibration record is `calibration/p4b-efficientnet-b0-temperature-v1.json`. Its status is deliberately **experimental**, not approved. The pre-existing P2-B2-A licence record permits only frozen-feature research, and it records an unresolved full-checksum/filename-token discrepancy. No checkpoint is downloaded or loaded in this stage.

## Recorded experiment result

`experiments/p4b/efficientnet-b0-governance-baseline.json` carries forward the P2-B2-A six-image held-out fixture values: accuracy 1.0, F1 1.0, AUROC 1.0, ECE 0.408368, Brier 0.169729, false positives 0, and false negatives 0. These are plumbing records, not a claim of detection quality, generalization, or real-world error rate.

## Provider admission rules

`MLDetectorProvider` checks, in order:

1. supplied image bytes match the Provider Context SHA-256;
2. model status is `approved`;
3. model and calibration references match exactly and satisfy the P3-A registry invariant;
4. loaded reader weight hash equals the registered weight hash;
5. bundle-derived properties plus a hash-bound attestation signed by a configured trusted key satisfy calibration scope.

An unregistered Provider is rejected by the P4-A Provider Registry. The ML Provider resolves its model and calibration only from the file-backed registry. An unapproved or uncalibrated model is rejected before inference. A model with `SCREENSHOT`, `AI_EDITED`, `LOW_RESOLUTION`, an undeclared condition, an absent/invalid/untrusted signed attestation, or other excluded/missing conditions produces `OUT_OF_SCOPE` with no score. A valid raw score is transformed by the registry-recorded temperature calibration and becomes auxiliary model evidence; it cannot directly set an authenticity assessment.

## P4-C route

P4-C may consider an institution-reviewed candidate only after independent licence review of data and weights, a materialized checksum-verified checkpoint, source-disjoint evaluation with meaningful coverage, approved calibration, registry approval workflow, persistent audit binding, scope-intake controls, and human-review operating procedures. It must not promote this P4-B experimental record automatically.
