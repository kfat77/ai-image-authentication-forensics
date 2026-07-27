# P4-A Provider Registry Design

Each registry entry records:

| Field | Purpose |
| --- | --- |
| `provider_id`, `version` | Immutable collection identity |
| `provider_type` | `metadata`, `c2pa`, `forensic`, `ml_detector`, or `external` |
| `status` | `experimental`, `validated`, `approved`, or `deprecated` |
| `validation_report` | Versioned validation reference |
| `limitations` | Declared scope and failure conditions |

Lifecycle policy:

- `experimental`: may be evaluated outside a formal report only.
- `validated`: validation is recorded but institutional report admission has not been approved.
- `approved`: may contribute evidence to formal fusion within its declared scope.
- `deprecated`: retained for historical traceability but blocked from new formal collections.

The in-memory `ProviderRegistry` is a deterministic P4-A governance seam. Institutional persistence, signing, multi-party approval, and release workflow belong to a subsequent implementation stage. “Approved” means admitted by this registry policy, not independently proven accurate for every image or use case.
