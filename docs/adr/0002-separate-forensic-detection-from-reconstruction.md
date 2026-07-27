# ADR 0002: Separate forensic detection from prompt reconstruction

## Status

Accepted, 2026-07-27.

## Context

The existing API returns editable reconstruction suggestions from observable visual features. A future forensic detector must report uncertainty, evaluation scope, evidence levels and possible provenance observations. Combining the two into one result would make creative suggestions look like evidence and make forensic findings look like source-model reconstruction.

## Decision

Forensic detection will use a new, versioned `/v2/detections` contract and a separate `DetectionResult` schema. The current `/v1/analyze` and `/analyze` behaviour remains prompt reconstruction. Detection results will not contain prompt candidates, and reconstruction results will not contain AI-generation or source-model probabilities.

## Consequences

- Clients choose a capability explicitly and can migrate independently.
- Detection-specific retention, calibration, audit and human-review requirements can evolve without reinterpreting v1 output.
- Any future shared upload plumbing must preserve the two result types and their distinct evidence semantics.
