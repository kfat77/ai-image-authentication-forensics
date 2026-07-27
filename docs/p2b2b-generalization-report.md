# P2-B2-B generalization report

Status: restricted robustness run completed on 2026-07-27. This is not a cross-generator or cross-dataset generalization result, and it does not establish an AI-image detection capability.

## 1. Dataset coverage

The only runnable corpus remains the 24-image DiTFake mini manifest from P2-B2-A: 12 COCO-referenced real images and 12 FLUX images. The source revision, manifest hash, and byte-verified index are recorded in the [P2-B2-A licence record](p2b2a-licence-record.md). Train/validation/test remain 12/6/6 and all transformation variants derive only from frozen test parents.

| Required coverage | P2-B2-B state | Reason |
| --- | --- | --- |
| Multiple real-photo sources | gap | A second source with per-file, research-use rights has not passed admission. |
| FLUX | covered | DiTFake mini. |
| SD / SDXL | gap | No approved corpus. |
| Midjourney | gap | GenImage was reviewed but its repository licence is `NOASSERTION`; it was not admitted. |
| DALL-E | gap | No approved corpus. |
| Imagen | gap | No approved corpus. |

No unreviewed source was downloaded or used to fill these gaps. Consequently, generator holdout, dataset holdout, and unknown-generator rejection are explicitly **uncovered**, rather than assigned an accuracy value.

## 2. Encoder comparison

| Encoder | State | Feature-quality conclusion |
| --- | --- | --- |
| EfficientNet-B0 | run; frozen 1,280-D ImageNet feature | Only available measured reference; no comparative conclusion. |
| DINOv2 | not run | The official project declares Apache-2.0 for code and weights, but no independently hash-pinned checkpoint was materialised. |
| CLIP | not run | Official code is MIT; checkpoint-specific licence/hash admission is incomplete. |

The required two additional encoder experiments are therefore a P2-C prerequisite, not silently substituted with simulated features.

## 3. Cross-generator and cross-dataset results

No valid cross-generator or dataset-holdout measurement exists: fitting and testing would otherwise reuse the same generator and dataset context. The experiment result file records these slices as `uncovered` with their reasons, preserving the unknown mechanism rather than forcing a generator label.

## 4. Robustness results

The runnable experiment evaluates test-parent variants only: JPEG quality 75 (no chroma subsampling), 75% Lanczos resize, 80% centred crop, and brightness ×1.15. Screenshot and AI-edit variants are uncovered because no repeatable capture environment or approved edit provenance was available.

| Classifier | Original accuracy / ECE before calibration | JPEG accuracy / ECE before calibration | Crop accuracy / ECE before calibration |
| --- | --- | --- | --- |
| Linear logistic regression | 1.000 / 0.145 | 1.000 / 0.155 | 1.000 / 0.115 |
| Linear SVM | 1.000 / 0.318 | 1.000 / 0.324 | 1.000 / 0.303 |
| Tiny MLP | 0.667 / 0.325 | 0.667 / 0.350 | 0.667 / 0.315 |

Every cell has only six test images. These values are implementation observations, not robustness claims. The detailed, machine-readable per-transformation and per-generator slices are in [`/experiments/results/p2b2b-permitted-robustness-efficientnet-v1/result.json`](../experiments/results/p2b2b-permitted-robustness-efficientnet-v1/result.json).

## 5. Calibration results

Calibration was fitted on the separate six-image validation split only. On linear logistic regression, raw scores had lower ECE (0.115–0.159) than temperature scaling (0.404–0.413) and Platt scaling (0.270–0.301) on the test variants. Isotonic regression reports ECE 0.000 here only by collapsing the tiny validation support; it also reduces threshold accuracy to 0.500. This is direct evidence of severe small-sample calibration instability, not an improvement.

The MLP’s raw ECE is 0.315–0.461; calibration changes it inconsistently by transformation. P2-C must use substantially larger, source-disjoint calibration data and reliability diagrams before selecting any mapping.

## 6. Failure analysis

- **False positives:** none for the linear models in this six-image fixture. This says nothing about HDR, phone computational photography, or heavy post-processing because those categories were not labelled or covered.
- **False negatives:** the Tiny MLP misses generated examples on the tiny fixture; it is therefore a feature-pipeline comparison point, not a candidate detector.
- **Unknown:** no unknown-generator sample was admitted. The result is `uncovered`, not a rejection-rate claim.

## 7. Limitations and P2-C entry criteria

The run has one dataset, one generated source, six test parents, and unresolved upstream source-rights/checkpoint governance notes. It omits dataset holdout, generator holdout, screenshot, AI editing, and feature-quality comparison across DINOv2/CLIP. P2-C may start only after: (1) per-file real-image rights and at least two source-disjoint real corpora are approved; (2) SD/SDXL, Midjourney, DALL-E, and Imagen coverage is admitted or formally documented as unavailable; and (3) two additional official encoder checkpoints have licence, full hash, preprocessing, and model-card records.
