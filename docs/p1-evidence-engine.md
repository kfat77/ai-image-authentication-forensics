# P1 Evidence Extraction Engine

## Scope

P1 implements a local, deterministic evidence-extraction module. It accepts image bytes and an explicitly supplied artifact directory, writes reproducible reviewer artifacts, and returns an `EvidenceBundle`. It is not attached to the existing web UI or FastAPI routes; therefore P1 makes **no API change**.

The public Python interface is:

```python
from evidence import extract_evidence

bundle = extract_evidence(image_bytes, "analysis-artifacts/case-001")
```

The artifact directory contains:

- `original.png` — bounded reviewer rendering of the source pixels;
- `frequency-spectrum.png` — centered log-magnitude FFT visualization;
- `noise-map.png` — amplified Gaussian-residual reviewer rendering;
- `anomaly-overlay.png` — localized visual-detail outliers from the artifact detector;
- `evidence-bundle.json` — deterministic manifest with parameters, detector status/evidence ceilings, observation IDs/levels/scopes, relative artifact paths, SHA-256 hashes, transforms, colour mappings, coordinate systems and source-observation references.

Artifacts are reproducible for the same input bytes, processing version, Pillow version and parameters. They are not immutable evidence storage; callers must choose a per-analysis directory and retain it under their approved data policy.

Before the manifest is written, the engine validates detector status, evidence levels and ceilings, unique observation IDs, visualization source-observation references and region references. A failed validation prevents manifest persistence.

## Implemented observations

| Detector | Output | P1 limitation |
| --- | --- | --- |
| Metadata | Container format, EXIF tags, software field, ICC presence and an unverified C2PA-marker reader | Missing/altered metadata is not an AI or provenance signal; marker reading is not C2PA validation. |
| Frequency | 2D FFT high-frequency energy, 8×8 DCT energy and spectrum image | Frequency measurements are not diffusion fingerprints. |
| Noise | Gaussian residual, tile variance and residual consistency, plus noise map | Values change with content, denoising, resizing and compression. |
| Artifact | JPEG container/quantization observation, block-boundary difference, gradient alternation and optional grid regions | Regions are visual anomalies only, not findings of AI generation or manipulation. |

`EvidenceBundle` intentionally has no `ai_probability`, `confidence` as a verdict, `suspected_model`, classifier output, or C2PA validation outcome. P1 must not be wired into a consequential workflow.

## Limits and safety

- The function rejects empty, unreadable and decompression-bomb inputs, and enforces its explicit pixel limit.
- Renderings are bounded to 1024 pixels per side; detector analysis images are bounded to 128 or 512 pixels depending on detector.
- No model dependency, checkpoint, network call, training code or image upload persistence is introduced.
- The C2PA reader only observes embedded byte markers through an injectable interface. Use the existing approved verifier adapter for actual trust-policy validation in a separately approved integration.
