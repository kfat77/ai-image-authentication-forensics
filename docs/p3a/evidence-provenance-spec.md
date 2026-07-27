# Evidence Provenance Specification

Every evidence item conforms to `EvidenceProvenance`:

```json
{"evidence_id":"...","source_type":"c2pa|exif|metadata|frequency|noise|artifact|model|external","detector_version":"...","timestamp":"RFC3339 UTC","input_hash":"SHA-256","reliability":"declared method reliability","observation":{},"limitation":"..."}
```

Evidence is traceable to one input hash and detector version. A missing source observation remains an absence of evidence. Model evidence additionally requires a registry admission and calibration reference before it can enter fusion.
