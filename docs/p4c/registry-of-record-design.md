# Registry of Record

The in-memory P4-C reference implementation maintains an append-only set of signed model/calibration revisions indexed by content hash, a current-revision pointer by stable record ID, append-only approval history, and signed provider-admission records. Record content is recursively immutable after signing; an attempted in-memory change raises an error and independently supplied altered content fails hash/signature verification. It is a governance seam, not a production approval service.

An approved ML Provider is usable in an institutional report only through this chain:

`Provider → Registry lookup and signature/binding verification → evidence marked registry_verified → fusion → hash-bound report`.

Evidence from a provider without a valid formal ML admission is rejected before collection. P1 metadata, C2PA, and deterministic forensic providers retain their P4-A Provider Registry governance and are not represented as calibrated ML models.

P4-C adds an in-memory, signed Registry of Record seam for model, calibration, and Provider-admission records. Each record is canonical JSON hashed, then signed through an injected Key Provider. This stage uses test keys only and does not approve a real model.
