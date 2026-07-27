# P2-B2-A first real-image baseline report

Status: completed 2026-07-27. This report validates a research pipeline; it does not establish an AI-image detection capability.

## Question and fixed pipeline

The experiment exercised the locked sequence:

`approved images → frozen EfficientNet-B0 → 1,280-D features → linear classifier → validation-only temperature scaling → held-out metrics`.

The reproducibility entry point is [`/experiments/run_p2b2a_real.py`](../experiments/run_p2b2a_real.py). It rejects absent approval, a changed index, or any changed image before extracting features. The exact input and checkpoint records are in the [licence record](p2b2a-licence-record.md).

## Dataset and split

The approved DiTFake mini fixture contains 24 original images at one fixed dataset revision: 12 real-reference images and 12 FLUX-generated images. It uses a deterministic non-random 12/6/6 split (6/3/3 examples per class for train/validation/test). Each source image, content hash, and parent group is unique across splits. This is a plumbing fixture, not an independent benchmark: it has only one generated source and uses a curated test branch.

## Result

The full machine-readable output is [`/experiments/results/p2b2a-ditfake-efficientnet-b0-linear-baseline-v1/result.json`](../experiments/results/p2b2a-ditfake-efficientnet-b0-linear-baseline-v1/result.json). The intentionally small baseline is logistic regression, which is a linear classifier:

| Classifier | Test images | Accuracy | F1 | AUROC | ECE | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Linear logistic regression | 6 | 1.000 | 1.000 | 1.000 | 0.408 | 0.170 |

The test grouping was real (`n=3`), AI-generated/FLUX (`n=3`), and original transformation (`n=6`). Accuracy was 1.000 for each available group. AUROC is undefined for the single-label real/FLUX groups; the aggregate AUROC above has only six examples. The high ECE shows that this tiny run is not well calibrated despite perfect thresholded labels. These figures are not publishable benchmark results and must not be used as a production threshold or an AI-probability claim.

## Error analysis

There were no threshold errors in this six-image test split. This does not demonstrate low false-positive or false-negative risk. Unknown-generator analysis was not possible because only FLUX is present. The required error-analysis record is [`/error-analysis/p2b2a-ditfake-efficientnet-b0-linear-baseline-v1.md`](../error-analysis/p2b2a-ditfake-efficientnet-b0-linear-baseline-v1.md).

## Limits

- The input is very small, source-constrained, and uses only original files; it does not test compression, resize, crop, screenshots, or AI edits.
- No held-out generator is available, so unknown-class rejection is unmeasured.
- The model was frozen; no deep detector was trained.
- The checkpoint metadata discrepancy is recorded as unresolved in the licence record.
- There is no production API, end-user prediction, provenance attribution, or commercial performance claim.
