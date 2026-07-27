# P4-A Fusion Integration

`AuthenticationReportEngine.create()` accepts an optional `ProviderRegistry` and provider tuple. It first creates the existing P1 Evidence Bundle, then collects provider evidence with the same input hash and analysis timestamp. The registry returns either:

- approved `DetectionEvidence`, which is passed to `assess()` and written to the JSON/PDF report; or
- a recorded exclusion for a provider that is not approved.

Fusion receives provider evidence as auxiliary review material. P4-A adds an evidence-summary statement and trace IDs only. It does not add a rule that maps provider scores, observations, C2PA marker presence, absent metadata, or an external response directly to `likely_real` or `likely_ai_generated`.

This preserves existing conservative behavior: with no separately admitted calibrated model evidence, the assessment remains `uncertain`. The report captures provider ID/version, provenance, scope, and limitations so a reviewer can see what was considered and what was excluded.

## P4-B route

P4-B may admit one ML Detector Provider only after: a licensed data and weight record; Model Registry and Calibration Registry linkage; a fixed validation scope and excluded conditions; reproducible evaluation; approved registry status; unknown/out-of-scope behavior; and human-review controls. It must still treat model output as auxiliary evidence rather than a unilateral authenticity conclusion.
