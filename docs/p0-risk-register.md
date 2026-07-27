# P0 AI-image forensics risk register

## Status

This register governs future research and release decisions. It does not describe an implemented detector, and no P0 artifact is approved for operational use.

| ID | Risk | Why it matters | P0 control | Release gate / owner |
| --- | --- | --- | --- | --- |
| R1 | False positive | A real, edited, compressed, stylized or metadata-stripped image can resemble learned or forensic artifacts; a false accusation can cause reputational, legal and procedural harm. | Contract requires limitations, human review, abstention and no current probability. | Predeclared FPR slices, appeal/remediation, independent review; product and legal owners. |
| R2 | False negative | New generators, prompt editing, post-processing, screenshots and adversarial transforms can evade detection. | Generator/time-held-out and transformation tests are mandatory in the benchmark protocol. | OOD/temporal performance, drift monitoring and documented scope; research owner. |
| R3 | Data bias and leakage | Dataset sources can overrepresent content, demographics, languages, cameras or web platforms; duplicate prompts/batches can inflate results. | Licence register, source manifests, clustered splits and slice reporting. | Data approval plus leakage/bias review; data steward. |
| R4 | Model attribution is not provable | A model-family classifier may confuse variants, editing pipelines, tool wrappers and unseen generators. Closed-set output can force a false label. | `unknown` is mandatory; contract calls attribution a hypothesis, not provenance. | Open-set results and per-family calibration; research and governance owners. |
| R5 | Metadata/provenance misinterpretation | EXIF is easily absent/altered; a C2PA result has format and trust-policy limits. | Separate evidence levels and provenance fields; absence cannot raise AI probability. | Trust policy, verifier review and reviewer training; security/provenance owner. |
| R6 | Explainability overclaim | Saliency maps, spectra and region overlays can look authoritative without validating their causal/semantic meaning. | Every visualization includes source and limitation; P1 has no semantic claim. | Qualitative/quantitative validation and UI review; research owner. |
| R7 | Dataset and weight licensing | Code licence, data licence, checkpoint terms and generated-output terms differ; academic-only sources can bar deployment. | No P0 download; mandatory intake register. | Legal/data-owner approval before acquisition and redistribution; legal owner. |
| R8 | Privacy and sensitive uploads | Images can contain faces, documents, location, minors or regulated data. | Existing no-persistence posture remains; future retention design is explicitly unresolved. | DPIA/PIA, access/retention policy, deletion test and incident process; privacy owner. |
| R9 | Commercial and government deployment limits | Public-sector use can require procurement, accessibility, records retention, security assurance, auditability and jurisdiction-specific legality. | Documentation states no endorsement or certification claim. | Independent assessment and accountable official acceptance; institution owner. |
| R10 | Supply-chain compromise | Model packages, checkpoints and image parsers can introduce vulnerable or malicious artifacts. | P0 adds no dependencies or weights. | Signed manifests, SBOM, scanning, provenance and rollback; security owner. |
| R11 | Automation bias / consequential use | Reviewers may treat a score as a definitive verdict in enforcement, benefits, employment or other high-impact settings. | Model-governance boundary and mandatory human review continue to apply. | Use-policy approval, training, logging and appeal; policy owner. |
| R12 | Benchmark gaming and model drift | Optimizing to known datasets or transforms can hide poor field performance, while generator evolution invalidates scores. | Locked test protocol, time split and immutable experiment record. | Periodic independent reevaluation and release expiry; research owner. |

## Escalation rule

Any evidence of material false positives, label/permission defects, unexplained subgroup disparity, model artifact integrity failure, or use outside the approved scope pauses release and requires a documented corrective decision. A green unit-test run is not a substitute for this gate.
