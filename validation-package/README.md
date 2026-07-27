# Signed Validation Package

A signed Validation Package is an independently reviewable artifact created by `backend/validation_package`. It can be issued only when the Registry of Record verifies an approved Provider Admission and the caller supplies a fixed dataset manifest hash, configuration, report hashes, metrics-schema hash, and limitations.

The package signature covers both content and signature metadata. It does not promote a model, change Registry status, or authorize a formal report by itself.

`p6c-readiness-preflight.json` is intentionally **not signed**: it documents why the current experimental candidate cannot receive a package. No valid signed package exists for that candidate at this stage.
