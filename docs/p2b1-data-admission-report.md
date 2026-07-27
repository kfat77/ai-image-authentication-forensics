# P2-B1 data admission report

Date: 2026-07-27. Decision: **no external dataset is admitted for experimentation in P2-B1**.

| Dataset | Manifest | Registry status | Admission decision | Reason |
| --- | --- | --- | --- | --- |
| ImageNet ILSVRC 2012 | `imagenet-ilsvrc-2012.json` | pending review | not admitted | Terms constrain use and underlying rights require review. |
| COCO 2017 | `coco-2017.json` | pending review | not admitted | Subset-specific source-image rights and permitted use are unresolved. |
| Open Images V7 | `open-images-v7.json` | pending review | not admitted | Per-image licence and attribution review is outstanding. |
| GenImage | `genimage.json` | blocked | not admitted | Dataset licence is not verified. |
| CIFAKE | `cifake.json` | blocked | not admitted | Authoritative source/version and licence are not verified. |
| DiffusionDB | `diffusiondb.json` | pending review | not admitted | CC0 card is recorded, but privacy/provenance governance has not cleared use. |

All six candidate manifests are canonical-hash verified. `registry/approved-manifests.json` is intentionally empty. The only P2-A approved fixture remains a numeric, repository-owned plumbing fixture and is not an image dataset.

## Admission requirements before P2-B2

1. Freeze the authoritative dataset version and record source retrieval evidence.
2. Resolve licence, attribution, training, commercial-use, privacy, and content-risk review for the intended task.
3. Add a named approval entry with manifest hash and scope to the registry.
4. Materialise a hash-verified `index.jsonl` without crossing parent or source groups between splits.
5. Re-run data validation before feature extraction.
