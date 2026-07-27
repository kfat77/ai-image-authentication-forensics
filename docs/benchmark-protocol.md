# P2-A benchmark protocol

This protocol defines research measurements only. No P2-A score is an assertion about an individual image's origin, and no result may be exposed through a production API.

## Preconditions

Only a versioned, manifest-hashed, approved dataset may be used. Splits must be frozen before fitting, with provenance groups and near-duplicates kept within a single split. Calibration data must be distinct from classifier-training and final-test data.

## Tasks

| Task | Input and label | Required output | Boundary |
| --- | --- | --- | --- |
| A — Binary detection | Approved real versus generated image samples | Research score and calibrated evaluation metrics | A score is population-scoped, not a default AI probability or proof of origin. |
| B — Generator attribution | Approved generated samples labelled SD, SDXL, Midjourney, DALL-E, FLUX, or Imagen | `prediction`, `confidence`, `unknown_score` | The known labels form a closed set. The system must return `unknown` when support is insufficient; it must not force attribution. |
| C — Robust detection | A and B samples with declared transformations | Per-transformation metrics and error slices | Test JPEG compression, resize, crop, screenshot, and AI edit separately; never pool them into an unexplained robustness claim. |

## Evaluation rules

Report Accuracy, Precision, Recall, F1, AUROC, PR-AUC, Expected Calibration Error (ECE), and Brier score. Report each metric overall and sliced by dataset, generator, and transformation. Mark AUROC and PR-AUC as undefined when a slice contains only one class. Preserve threshold, positive-label convention, calibration method, confidence interval method (when applicable), and sample count with every report.

For Task B, report the confusion matrix over known labels plus `unknown`, known-class coverage, unknown recall, and false-known attribution rate. Unknown examples must include generators, workflows, and edits excluded from the training label set.

## Robustness protocol

Transformations are generated from the frozen test images only and retain a parent-image identifier. Record exact JPEG quality/subsampling, resize algorithm and scale, crop coordinates, screenshot environment, and AI-edit method/version. Do not use transformed variants of a parent image in training or calibration if a sibling is in test.

## Reproducibility record

Each run writes an experiment record containing dataset manifest hash/version, code/model version, encoder identifier, feature settings, classifier hyperparameters, random seeds, hardware and software versions, calibration procedure, metric outputs, error cases, and SHA-256 checkpoint hash. Raw restricted images and prompts are not written to public result artifacts.

## P2-A fixture exception

`p2a-synthetic-feature-pipeline-smoke-v1` exercises the interfaces with deterministic synthetic numeric features. It has no images, no pretrained encoder, and no scientific benchmark status. Its results validate only data-gate, fitting, calibration, metric, grouping, and record-writing mechanics.
