# P0 forensics architecture and P1 implementation plan

## Status

This is an architecture and interface design. The packages, detectors, ensemble, encoders and trained classifiers described here do not exist in P0. It introduces no model dependency, checkpoint download or production configuration change.

## Design goals

- Keep a **small external interface**: a detection coordinator consumes an image plus a profile and produces a bounded `DetectionResult` draft.
- Keep provenance, observable signals, learned scores and reviewer explanations separable until final result assembly.
- Treat every detector as an adapter behind one seam. Detectors may be unavailable without fabricating a score.
- Preserve feature provenance: every numeric value must identify its method, version, input normalisation and limitation.
- Support offline research execution before any API integration.

## Planned package map

```text
backend/
  detectors/
    metadata_detector.py     # EXIF/container observations and C2PA adapter result mapping
    frequency_detector.py    # spectrum and high-frequency residual observations
    noise_detector.py        # noise/residual consistency observations
    artifact_detector.py     # approved artifact/localization adapter (not a generic claim engine)
    semantic_detector.py     # approved semantic-consistency adapter (optional)
    base.py                  # common Detector interface and result types
  models/
    vision_encoder.py        # approved, pinned encoder adapter: CLIP/DINOv2/SigLIP/CNN/ViT candidates
    classifier.py            # binary and source-family classifier adapters
    ensemble.py              # calibration-aware late-fusion implementation
  forensics/
    coordinator.py           # invokes enabled detectors and assembles a contract result
    registry.py              # approved detector/model manifest lookup
    visualizations.py        # spectrum/noise/overlay rendering from explicit artifacts
```

The current `backend/app/analyzer.py` remains a reconstruction-only observable-feature extractor. P1 should add the new modules rather than turn it into a detector, preserving the seam recorded in ADR 0002.

## Detector interface draft

The following is a design-level Python interface, not a file to be imported in P0:

```python
class Detector(Protocol):
    descriptor: DetectorDescriptor  # id, version, evidence_capabilities, availability

    def analyze(self, image: ForensicImage, context: DetectionContext) -> DetectorObservation:
        """Return bounded observations, artifacts, limitations and availability; never a final verdict."""

@dataclass(frozen=True)
class DetectorObservation:
    detector_id: str
    detector_version: str
    status: Literal["available", "unavailable", "unsupported", "failed"]
    evidence: tuple[EvidenceItem, ...]
    artifacts: tuple[VisualizationArtifact, ...]
    limitations: tuple[str, ...]
```

### Interface invariants

- `analyze` receives immutable normalized image bytes plus metadata about declared profile and allowed resource budget; it must not write image bytes to logs or select an outcome requested by the caller.
- A detector returns `unavailable`/`unsupported`/`failed` with an `E0` item rather than silently returning zero.
- Only the coordinator can create `ai_probability`, `confidence`, `suspected_model` and `forensic_summary`.
- Detectors never set their own evidence level above their approved descriptor capability.
- `VisualizationArtifact` must name its transform, color mapping, coordinate system and source evidence ID. A heatmap is not an explanation unless a validation report defines what it measures.
- External C2PA, vision or future detector services use adapters that validate a bounded response contract and carry an approval/manifest identity.

## Detector responsibilities and P1 boundaries

| Detector | P1 responsibility | Evidence ceiling in P1 | Explicit non-goal |
| --- | --- | --- | --- |
| Metadata | Parse bounded EXIF/container observations; map existing provenance adapter results | `E1` or `E4` only for verifier output | Treat missing metadata as AI evidence |
| Frequency | Compute reproducible spectrum and residual summaries | `E2` | Assert diffusion sampling from a frequency peak |
| Noise | Compute reproducible residual/noise consistency observations | `E2` | Claim a generator fingerprint without validated training |
| Artifact | Interface plus unavailable adapter state; later use approved localization model | `E0` in P1 unless independently validated | Diagnose hands, text, geometry or objects from generic heuristics |
| Semantic | Interface plus unavailable adapter state; later use approved visual model | `E0` in P1 unless independently validated | Assert lighting or semantic inconsistency as a generation verdict |

## Ensemble architecture

The ensemble is a deep module with one interface: `assemble(observations, approved_model_outputs, policy) -> DetectionAssessment`. It hides feature normalisation, missing-signal handling, calibration, abstention and evidence traceability from callers.

```text
immutable image
      │
      ├── metadata / C2PA ────────────────┐
      ├── frequency / JPEG ───────────────┤
      ├── noise residual ─────────────────┤  raw observations + artifact references
      ├── approved CNN / ViT encoders ────┤
      └── approved semantic adapter ──────┘
                                             │
                                  feature provenance validator
                                             │
                       calibrated late fusion + unknown/abstain policy
                                             │
                           DetectionResult evidence and review summary
```

The planned final score is **not** a fixed sum. `metadata + frequency + CNN + ViT + semantic` is a research hypothesis that risks double-counting correlated signals and mixing qualitatively different evidence. P2 must compare late fusion, calibrated stacking and abstention with held-out data. C2PA/provenance remains a parallel evidence channel, not a weight in an “AI score.”

## Encoder and classifier research matrix

| Candidate | Intended research role | Admission condition |
| --- | --- | --- |
| CLIP / SigLIP | Vision-language baseline and semantic feature comparison | Pin code/weight licence, preprocessing, artifact hash and evaluation report. |
| DINOv2 | Self-supervised visual feature baseline | Same manifest, time-held-out and transformation evaluation. |
| ConvNeXt / EfficientNet | CNN baseline with high-frequency sensitivity comparison | Same manifest and calibration gate. |
| Vision Transformer | ViT baseline and patch-feature/localization research | Same manifest and localization-scope validation. |

No candidate is labelled “state of the art” or enabled just because it is popular. The benchmark protocol selects the release candidate; all weights remain excluded in P0.

## P1 implementation plan

1. Add the package structure and pure-Python shared types, without adding large ML libraries or downloading weights.
2. Implement metadata, frequency and noise detectors as deterministic, bounded `E1`/`E2` research observations with visualization artifacts; artifact and semantic detectors return explicit `E0` unavailable states.
3. Add offline fixtures with lawful provenance, detector unit tests and a contract test that validates a P1 result has no `ai_probability` and no source attribution probability.
4. Add a local-only coordinator and JSON Schema serialization test. Do not expose `/v2/detections` until retention, authorization, audit and asynchronous-processing design are reviewed.
5. Produce a P1 report describing feature definitions, known confounders and transformation results. A P2 gate decides whether to add any encoder/classifier or probability.

## P1 acceptance criteria

- Existing reconstruction routes and deployment files are byte-for-byte unchanged by the P1 forensic module work unless separately approved.
- Every detector outcome is deterministic for a fixed input and version, or declares its seed/non-determinism.
- Every visualization maps to a named `EvidenceItem` and contains its limitation in the result metadata.
- No P1 user-facing response states or implies that an image is AI-generated, model-attributed, manipulated, or authentic.
- The P0 test plan and a new detector-specific test report pass before any P2 model integration proposal.
