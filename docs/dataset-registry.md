# P2-A dataset registry

Status date: 2026-07-27. This registry is a research governance control, not a download list. A source cannot enter training until its row is marked **approved**, a versioned manifest is recorded, and its terms have been reviewed for the exact proposed use.

P2-B1 candidate manifests are stored in [`/manifests`](../manifests), while the externally approved index is deliberately empty at [`/registry/approved-manifests.json`](../registry/approved-manifests.json). See the [P2-B1 admission report](p2b1-data-admission-report.md) for the current decisions.

| Dataset | Authoritative source | Candidate sample count | Image type | Generator / collection time | Licence or terms recorded | Training allowed | Commercial use allowed | Registry status |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| ImageNet ILSVRC 2012 | [ImageNet download](https://www.image-net.org/download.php) | 1,281,167 train; 50,000 validation; 100,000 test | Natural images | Not generated; 2012 challenge release | ImageNet terms; image copyrights remain with rightsholders | Terms-constrained, not yet cleared | No: non-commercial research/education terms | pending review |
| COCO 2017 | [COCO](https://cocodataset.org/) | 118,287 train; 5,000 validation; 40,670 test-dev | Natural images with captions/annotations | Not generated; 2017 split | COCO terms plus underlying image-source rights must be reviewed | Unknown pending subset review | Unknown pending subset review | pending review |
| Open Images V7 | [Open Images](https://storage.googleapis.com/openimages/web/index.html) | 9,011,219 train; 41,620 validation; 125,436 test | Natural images and annotations | Not generated; V7 release | Images are listed as CC BY 2.0; annotations CC BY 4.0; each selected image needs licence/attribution verification | Unknown until per-image review | Unknown until per-image review | pending review |
| GenImage | [GenImage project](https://github.com/GenImage-Dataset/GenImage) | Over 1 million real/generated pairs (project claim) | Generated/natural paired images | Midjourney, SD, ADM, GLIDE, Wukong, VQDM, BigGAN; project release | No verified dataset SPDX licence in the source repository | Not cleared | Not cleared | blocked: licence review required |
| CIFAKE | [CIFAKE source repository](https://github.com/jordan-bird/CIFAKE-Real-and-AI-Generated-Synthetic-Images) | Not accepted until authoritative release and exact version are verified | CIFAR-like real/synthetic images | Generator/version requires per-release confirmation | No verified authoritative dataset licence recorded | Not cleared | Not cleared | blocked: source and licence verification required |
| DiffusionDB | [DiffusionDB data card](https://huggingface.co/datasets/poloclub/diffusiondb/blob/main/README.md) | 2M subset; 14M large subset | Stable Diffusion images, prompts and generation parameters | Stable Diffusion; collection published 2022 | Dataset card: CC0 1.0 data; MIT code | Terms appear permissive, but not yet cleared for this programme | Terms appear permissive, but privacy/provenance review is pending | pending privacy and governance review |

## Required registration fields

Each approved version must add a machine-readable manifest with: source URL and retrieval date; licence text/version; sample count and content types; real/generated/generator labels; generation or collection time; split definitions; whether training and commercial use are permitted; required attribution; privacy/content-risk review; reviewer; approval date; and SHA-256 of the manifest or index.

## Training gate

`backend/models/datasets.py` exposes `require_training_approval`. It rejects every manifest unless `approval_status` is exactly `approved`, `training_permitted` is true, and its versioned SHA-256 is present in the trusted P2-A approval allow-list. The only approved P2-A input is the repository-owned synthetic **feature** fixture used to test plumbing; it contains no downloaded images and is not a benchmark dataset.

## Intake procedure

1. Identify an authoritative source and freeze an exact version or index.
2. Record the required fields above and retain the applicable terms.
3. Check attribution, privacy, personal-data, and downstream commercial restrictions.
4. Obtain named research-governance approval for the specified task and use.
5. Generate the manifest hash, freeze splits, then change the status to `approved`.

Until step 5 is complete, experiments may not fit on the source. The registry deliberately does not infer permission from a GitHub repository, a mirror, or a paper citation.
