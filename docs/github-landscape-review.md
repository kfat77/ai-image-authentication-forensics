# GitHub landscape review — 2026-07-26

This review informs architecture; it does not copy code or claim the quality, licences, or benchmarks of other projects.

| Project | Useful lesson | Decision here |
| --- | --- | --- |
| [CLIP Interrogator](https://github.com/pharmapsychotic/clip-interrogator) | Combines BLIP image description and CLIP ranking to produce prompts; supports configurable local models and vocabulary ranking. | Keep prompt reconstruction separate from provenance. Support an approved internal visual-analysis endpoint now; consider a locally packaged BLIP/CLIP engine only after a licensed model/evaluation bundle is approved. |
| [AIDE](https://github.com/shilinyan99/AIDE) | Research result stresses that detectors can fail on real-world, carefully edited AI images; its dataset is academic-only. | Do not return a source-model verdict or calibrated “AI probability” without local, lawful evaluation evidence. Do not import its dataset or weights into an official workflow. |
| [AI-GenBench](https://github.com/MI-BioLab/AI-GenBench) | Temporal benchmark evaluates whether detectors generalise to generator families released after their training data. | Add a release gate requiring time-split, out-of-generator evaluation and calibration before enabling any detector-based decision support. |
| [FakeTrace](https://github.com/mwp-create-wonders/FakeTrace) | A multi-model system benefits from clear model loading, runtime configuration and separate CLI/API/UI paths, but needs carefully managed model weights and dependencies. | Keep this service narrow and adapter-based. An institution may connect approved internal detectors/vision services; third-party checkpoints are not silently downloaded. |
| [c2pa-rs](https://github.com/contentauth/c2pa-rs) | C2PA is a cryptographic provenance standard with explicit validation and supported-format boundaries. The SDK advises using released versions rather than its unstable main branch. | Add an internal C2PA-verifier adapter and a distinct provenance output; no custom EXIF/C2PA parser or provenance inference from visual features. |

## Integration priorities

1. Operate an internal C2PA verifier using released, approved upstream tooling and a governed trust policy.
2. Build an institution-owned evaluation corpus and run temporal/out-of-distribution tests before introducing a detector score.
3. If adding a local image-to-prompt engine, pin model artefacts, licences, checksums, hardware requirements, version and evaluation report as deployable evidence.
4. Keep raw images inside the approved data boundary, and retain only authorised audit metadata.
