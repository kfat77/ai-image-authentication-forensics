# P2-B1 dataset and split schema

Every external dataset requires a canonical-hash-verified manifest before it can be admitted. An approved manifest also binds the byte-level SHA-256 of its `index.jsonl`. Each index record then contains a content SHA-256, labels, and a grouped split assignment; all image bytes are re-hashed before feature extraction.

| Field | Allowed values / requirement |
| --- | --- |
| `image_origin` | `REAL`, `AI_GENERATED`, `UNKNOWN` |
| `generator` | `NONE`, `SD`, `SDXL`, `MIDJOURNEY`, `DALL-E`, `FLUX`, `IMAGEN`, `OTHER` |
| `edit_status` | `ORIGINAL`, `COMPRESSED`, `RESIZED`, `CROPPED`, `AI_EDITED` |
| `split` | Exactly `train`, `validation`, or `test`; all three must exist in an admitted experiment. |
| `generator_split` | Non-empty declared generator-distribution stratum. |
| `temporal_split` | Non-empty declared generation/collection-time stratum. |
| `transformation_split` | Non-empty declared edit/transformation stratum. |
| `parent_id` | All variants of one parent image must remain in one split. |
| `source_group` | Records from one source/provenance group must remain in one split. |

`REAL` records must have generator `NONE`; `AI_GENERATED` records must name a generator or `OTHER`. No random split function exists. The validator rejects duplicate sample IDs, missing partitions, content/parent/source-group leakage, invalid labels, manifests absent from the trusted approval index, index/file hash mismatch, sample-count mismatches, and malformed content hashes.
