# P5-A Scenario Test Matrix

This is the required register format for controlled validation samples. A row without a reviewed source, explicit licence/use authorization, SHA-256 hash, curated label, or limitation is **not admitted**. P5-A ships no real image data and no pre-filled sample hashes.

| Scenario | Required source / licence review | Curated label | Minimum record fields | Typical limitations |
|---|---|---|---|---|
| Ordinary photography | Documented photographer, archive, or approved benchmark; licence must cover validation | `REAL`, `ORIGINAL` | source ID, licence, SHA-256, capture/source notes | post-processing may be unknown; missing metadata is neutral |
| Mobile-camera image | Device-owner consent or approved corpus with stated terms | `REAL`, `ORIGINAL` | plus device class if lawfully available | computational photography/HDR can resemble synthetic artifacts |
| Social-platform recompression | Original plus permitted platform-derived copy, or documented corpus | `REAL` or documented origin, `COMPRESSED` | parent/group ID, platform transform notes | codec and resize artifacts reduce provenance and model scope |
| Screenshot | Permitted source and screenshot procedure | origin label only if verified, `RESIZED`/derived | capture procedure, parent reference when available | commonly outside calibrated photo scope; absence of provenance is neutral |
| News image | Licensed newsroom/archive source with edit-history terms | `REAL` or documented origin | editorial context and known modifications | editorial crops, colour correction, syndication compression |
| AI-generated image | Generator/source documentation with permitted validation use | `AI_GENERATED`, generator if documented | generation provenance/time when available | generator label may be incomplete or closed-set only |
| AI-edited image | Original and documented edit source/permission where possible | documented origin, `AI_EDITED` | parent/group ID and edit description | mixed evidence; no required single-origin conclusion |
| Mixed-processing image | Documented multi-step permitted derivation | documented origin, derived edit status | complete transformation chain where available | may be out of model scope and require `uncertain` |

## Required sample-record template

```yaml
sample_id: institution-assigned-stable-id
validation_batch_id: pending-until-freeze
scenario: ordinary_photography | mobile_camera | social_recompression | screenshot | news | ai_generated | ai_edited | mixed_processing
source: reviewed-source-description
license: SPDX-or-verbatim-licence-reference
permitted_use: controlled_institutional_validation
license_reviewed_by: reviewer-id
license_reviewed_at: RFC3339-UTC
sha256: lowercase-64-character-digest
image_origin: REAL | AI_GENERATED | UNKNOWN
generator: NONE | SD | SDXL | MIDJOURNEY | DALL-E | FLUX | IMAGEN | OTHER
edit_status: ORIGINAL | COMPRESSED | RESIZED | CROPPED | AI_EDITED
parent_group_id: optional-non-identifying-source-group
limitations:
  - documented limitation
admission_status: CANDIDATE | ADMITTED | REJECTED
```

The `image_origin`, generator, and edit labels are curated protocol labels. They must not be written back as runtime findings or used to erase an adverse result.
