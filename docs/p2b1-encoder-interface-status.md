# P2-B1 encoder interface status

All six adapters implement the common future contract `encode(image: bytes) -> feature vector`. They are deliberately non-executable in P2-B1.

| Adapter | Version | Feature dimension | State | Reason |
| --- | --- | ---: | --- | --- |
| CLIP | unselected | — | blocked | Package, checkpoint provenance, model licence, and approval are absent. |
| DINOv2 | unselected | — | blocked | Package, checkpoint provenance, model licence, and approval are absent. |
| SigLIP | unselected | — | blocked | Package, checkpoint provenance, model licence, and approval are absent. |
| ConvNeXt | unselected | — | blocked | Package, checkpoint provenance, model licence, and approval are absent. |
| EfficientNet | unselected | — | blocked | Package, checkpoint provenance, model licence, and approval are absent. |
| ViT | unselected | — | blocked | Package, checkpoint provenance, model licence, and approval are absent. |

No adapter silently falls back to another encoder. Calling a blocked adapter raises an error rather than loading or downloading a weight.
