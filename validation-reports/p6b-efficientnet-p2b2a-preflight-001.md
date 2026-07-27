# P6-B Validation Report: EfficientNet-B0 Candidate Preflight 001

> **Result: REJECTED.** This controlled preflight is not a production admission, Registry `APPROVED` decision, public performance result, or claim that the candidate detects AI-generated images.

## Run identity and environment

| Field | Value |
|---|---|
| Validation Run | `p6b-efficientnet-p2b2a-preflight-001` |
| Timestamp | `2026-07-27T10:16:55.9724588Z` |
| Code version | `a3279e7d794267c47c4e7b42be99d53f37d621b9` |
| Candidate | `efficientnet_b0_linear_logistic_p2b2a` / `p4b-candidate-1` |
| Candidate status | `experimental` |
| Candidate weight hash | `7f5810bc96def8f7552d5b7e68d53c4786f81167d28291b21c0d90e1fca14934` |
| Model / Calibration / Provider record hashes | unavailable / unavailable / unavailable |
| Formal evidence path | blocked before scoring |

The candidate has local research registry files, but no signed P4-C ModelRecord, CalibrationRecord, or approved Provider Admission. Therefore it cannot enter formal Authentication Report fusion.

## Data scope and admission result

The proposed input was the approved-for-research 24-image `p2b2a-ditfake-mini` fixture (declared identity hash `81505c1f7713257a2dcf0344c57fc9916b1d01ab2375afd279102434f0ce3a3b`; frozen manifest file hash `e501036e84584dd48c8e854fcb0ff0de5943c7c0283d761484fc108c9ad63a45`). It documents 12 COCO-referenced real images and 12 FLUX-generated images with a grouped 12/6/6 train/validation/test plan.

Admission was rejected before scoring: raw source files and per-file hashes are intentionally absent from the workspace, so P6-A sample-level hash verification and repeatable access cannot be shown. Required P6-A slices are also absent: photography, mobile, news, screenshot, secondary processing, multiple AI methods, and multiple quality bands.

## Metrics

| Metric family | P6-B result | Reason |
|---|---:|---|
| Accuracy / Precision / Recall / F1 | not evaluated | no admitted P6-B scored test set |
| FPR / FNR | not evaluated | no comparable P6-B scored test set |
| ECE / Brier | not evaluated | no admissible P6-B calibration population |
| Evidence completeness | not evaluated | no formal reports permitted |
| Report reproducibility | not evaluated | no formal reports generated |

Historical artifact only: the separately recorded six-image P2-B2-A test fixture observed accuracy/precision/recall/F1 of `1.0`, zero counted errors, ECE `0.408368`, and Brier `0.169729`. These values are not P6-B metrics, are not risk estimates, and are not published performance.

## Failure analysis

- [`p6b-001-out-of-scope-unverifiable-fixture`](../validation-failures/p6b-001-out-of-scope-unverifiable-fixture.json): per-file hash/repeatable-access evidence is unavailable.
- [`p6b-002-uncertain-coverage-and-admission-gap`](../validation-failures/p6b-002-uncertain-coverage-and-admission-gap.json): single-generator, narrow-fixture coverage cannot support the required validation slices.

No P6-B false-positive or false-negative records exist because scoring did not begin. The historical fixture's zero counts are retained only in the run artifact and do not substitute for P6-B failures.

## Admission recommendation

**REJECTED.** The candidate remains `experimental` and cannot be promoted to `VALIDATED_CANDIDATE`, Registry `APPROVED`, or a formal Provider.

Before a new P6-B run, obtain licence-reviewed, sample-hash-verifiable, repeatably accessible real photography/mobile/news, multi-method AI-generated, and transformed/edit samples; lock a contamination-checked benchmark split; establish a signed ModelRecord, CalibrationRecord, and Provider Admission; then score under the P6-A protocol with all failure records retained.

## P6-C route

P6-C should be a **remediation and re-validation preparation** stage, not an approval stage: complete data admission, resolve checkpoint/weight rights review, create signed Registry records through the separate workflow, produce a governed candidate Provider, and run a new independently reviewed benchmark. It must not rely on this rejected preflight as evidence of detector capability.
