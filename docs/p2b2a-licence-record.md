# P2-B2-A data and weight licence record

Status date: 2026-07-27. This is a research-governance record, not legal advice or a general licence clearance.

## Approved data input

| Field | Recorded value |
| --- | --- |
| Dataset | DiTFake mini (`p2b2a-ditfake-mini`) |
| Official source | [Jouesmak/DiTFake dataset revision `ca9ea06`](https://huggingface.co/datasets/Jouesmak/DiTFake/tree/ca9ea06c8f926c3a11ca4b657074cc7cbb99e5c7) |
| Dataset-card licence | Apache-2.0, as declared by the dataset card |
| Locked version | `ca9ea06c8f926c3a11ca4b657074cc7cbb99e5c7` |
| Manifest | [`/manifests/p2b2a-ditfake-mini.json`](../manifests/p2b2a-ditfake-mini.json), SHA-256 `81505c1f7713257a2dcf0344c57fc9916b1d01ab2375afd279102434f0ce3a3b` |
| Index hash | SHA-256 `01babc8cc2b2650beba96c1969cba0bd95f5029279839240394d9378d9c7cf06` |
| Contents | 12 real images from the `0_real` branch and 12 FLUX images from `1_fake`; all marked `ORIGINAL` |
| Approved use | Frozen EfficientNet feature extraction plus small linear research baselines only |
| Not approved | Commercial use, production deployment, redistribution, benchmark publication, or broader DiTFake access |

The dataset-card declaration does not settle any rights inherited from the real-image source collection. The P2-B2-A intake therefore remains a small, non-commercial research fixture. Before expansion, a designated reviewer must verify upstream-image terms, attribution requirements, privacy considerations, and the desired use.

The machine-readable approval record is [`/registry/approved-manifests.json`](../registry/approved-manifests.json). It is a separately versioned governance input: [`/experiments/prepare_p2b2a_data.py`](../experiments/prepare_p2b2a_data.py) can only materialise and verify it; it cannot create or amend an approval. The raw files and feature vectors are intentionally excluded from Git; their index and content hashes are checked by the experiment before feature extraction.

## Encoder checkpoint record

| Field | Recorded value |
| --- | --- |
| Encoder | Torchvision EfficientNet-B0, `IMAGENET1K_V1` preprocessing contract |
| Official project | [pytorch/vision](https://github.com/pytorch/vision) |
| Official checkpoint URL | [efficientnet_b0_rwightman-3dd342df.pth](https://download.pytorch.org/models/efficientnet_b0_rwightman-3dd342df.pth) |
| Code licence | BSD-3-Clause |
| Architecture | EfficientNet-B0; frozen `features` + `avgpool`; 1,280-dimensional vector |
| Preprocessing | RGB; resize short side to 256 (bicubic); centre crop 224; ImageNet normalization |
| Observed checkpoint SHA-256 | `7f5810bc96def8f7552d5b7e68d53c4786f81167d28291b21c0d90e1fca14934` |

Torchvision 0.16.0 embeds the short token `3dd342df` in the filename metadata, while the full SHA-256 observed from the recorded official URL begins `7f5810bc`. The experiment requires the complete recorded SHA-256 before loading it with `weights_only=True`, then verifies that it strictly matches the EfficientNet-B0 state-dict architecture. The differing filename token is retained for independent maintainer review before any reuse beyond this experiment.

[`/experiments/fetch_p2b2a_checkpoint.py`](../experiments/fetch_p2b2a_checkpoint.py) retrieves only the recorded official URL and rejects a different full hash before writing it. The optional, isolated dependency list is [`/experiments/requirements-p2b2a.txt`](../experiments/requirements-p2b2a.txt). It is deliberately not part of the production service requirements.
