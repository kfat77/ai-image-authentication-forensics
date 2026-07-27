# P6-C Red-Team Validation Plan

Red-team validation tests whether adverse but permitted transformations preserve declared safety boundaries. It does not measure generic detector accuracy.

| Scenario | Input change | Expected safe behavior | Evidence to retain |
|---|---|---|---|
| Metadata removal | remove EXIF/provenance metadata | `uncertain` without admitted model evidence; absence is neutral | input hash, metadata observation, report limitation |
| Compression attack | recompress JPEG/social-platform derivative | `uncertain` or ML `OUT_OF_SCOPE` when calibration excludes compression | transform parameters, scope result, report/evidence hashes |
| Screenshot | capture a rendered image | `uncertain` or ML `OUT_OF_SCOPE` when screenshot is excluded | capture procedure, parent reference, scope result |
| Edit manipulation | permitted local visual edit | `uncertain` or ML `OUT_OF_SCOPE` when AI editing is excluded | edit procedure, parent group, scope result |
| Crop / resize | derived geometry transformation | `uncertain` or ML `OUT_OF_SCOPE` when not validated | exact operation, parent group, scope result |

The P6-C regression tests cover metadata removal, compression, screenshot-like capture, and edit manipulation without admitted model evidence. They assert `uncertain` rather than a forced AI conclusion. Existing ML Provider scope tests cover exclusion behavior when a declared scope attestation contains excluded conditions.

Every unexpected `likely_real` or `likely_ai_generated` result, processing error, or scope-control failure is appended to `validation-failures/` in the appropriate category. No red-team sample or failure is deleted after review.
