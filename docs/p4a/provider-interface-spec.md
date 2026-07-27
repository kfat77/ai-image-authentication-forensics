# P4-A Provider Interface Specification

```python
class DetectionProvider(Protocol):
    provider_id: str
    provider_version: str

    def detect(self, image: bytes, context: ProviderContext) -> tuple[DetectionEvidence, ...]: ...
```

`ProviderContext` contains the input SHA-256, UTC collection time, and optionally the existing P1 Evidence Bundle. Providers receive the image bytes and context but must not mutate the bundle, case, audit trail, report, or assessment.

`DetectionEvidence` contains:

```json
{
  "provider_id": "...",
  "provider_version": "...",
  "observation": {},
  "score": null,
  "confidence": "declared method confidence",
  "validation_scope": "declared population and conditions",
  "limitations": ["..."],
  "evidence_provenance": {
    "evidence_id": "...",
    "source_type": "metadata|c2pa|frequency|noise|artifact|model|external",
    "detector_version": "provider version",
    "timestamp": "RFC3339 UTC",
    "input_hash": "SHA-256",
    "reliability": "declared method reliability",
    "observation": {},
    "limitation": "..."
  }
}
```

`score` is optional and has no default semantic. A score is not an AI probability or a verdict. An ML provider can emit a score only after separate model, calibration, validation-scope, and registry governance; P4-A does not implement that bridge.

Provider families are `metadata`, `c2pa`, `forensic`, `ml_detector`, and `external`. ML and external families are contracts only in P4-A: no weights, model calls, or external institutional services are configured.
