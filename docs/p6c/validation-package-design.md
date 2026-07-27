# P6-C Signed Validation Package Design

The Validation Package is an independently reviewable, canonical JSON artifact. It binds:

- verified `model_record_hash`, `calibration_record_hash`, and `provider_record_hash` from Registry of Record;
- frozen `dataset_manifest_hash`;
- run configuration and red-team scope policy;
- report hashes and metrics-schema hash;
- explicit limitations; and
- signer identity, signing algorithm, time, key-provider identity, package hash, and signature.

The implementation at `backend/validation_package` uses the same canonical-signing envelope principles as Registry of Record. Verification recomputes the package hash and signature payload, so changes to content or signature metadata fail verification.

Package issuance calls `resolve_provider_for_report()` before signing. Therefore a missing, unverified, deprecated, or inconsistent Provider Admission cannot be converted into a signed package. A package signature attests to the frozen validation material; it is not model approval, a production authorization, or an authenticity conclusion.

The current readiness preflight is intentionally unsigned and blocked: [p6c-readiness-preflight.json](../../validation-package/p6c-readiness-preflight.json).
