# P2-A baseline model cards

These cards document experimental interfaces, not released detection models. No encoder weights are downloaded, loaded, or evaluated in P2-A.

## Encoder registry

| Identifier | Family | P2-A availability | Intended role | Limitation |
| --- | --- | --- | --- | --- |
| `clip` | CLIP | unavailable | Candidate feature encoder | No package, checkpoint, or licence approval is present. |
| `dinov2` | DINOv2 | unavailable | Candidate feature encoder | No package, checkpoint, or licence approval is present. |
| `siglip` | SigLIP | unavailable | Candidate feature encoder | No package, checkpoint, or licence approval is present. |
| `convnext` | ConvNeXt | unavailable | Candidate feature encoder | No package, checkpoint, or licence approval is present. |
| `efficientnet` | EfficientNet | unavailable | Candidate feature encoder | No package, checkpoint, or licence approval is present. |
| `vit` | Vision Transformer | unavailable | Candidate feature encoder | No package, checkpoint, or licence approval is present. |

All families implement the same `FeatureEncoder` protocol. An unavailable entry raises an explicit error instead of silently substituting another model. Selecting an encoder requires P2-B licensing, provenance, reproducibility, and benchmark review.

## Classifier baselines

| Identifier | Input | Output | P2-A use | Limitation |
| --- | --- | --- | --- | --- |
| `logistic_regression` | Fixed feature vector | Binary score | Synthetic plumbing fixture | Not trained on images; no detection claim. |
| `linear_layer` | Fixed feature vector | Binary score | Synthetic plumbing fixture | Equivalent low-capacity reference; not an encoder head release. |
| `tiny_mlp` | Fixed feature vector | Binary score | Synthetic plumbing fixture | Random initialisation and synthetic data only; not comparable to external work. |
| `softmax_linear` | Fixed feature vector | Label scores including `unknown` | Interface/unit tests only | No attribution dataset or trained checkpoint exists. |

## Calibration and unknown handling

Temperature scaling is fit only on held-out validation scores. `choose_attribution` returns `prediction`, `confidence`, and `unknown_score`; it selects `unknown` whenever known-label support is below the declared threshold or an explicit unknown score is stronger. It does not manufacture a generator label.

Attribution inputs are finite values in `[0, 1]`. If an explicit `unknown` value is supplied, all class values must sum to one; without it, any unallocated mass is treated as unknown support. Invalid or over-allocated score sets are rejected rather than returned as a misleading result.
