# P2-B2-B plan: broaden the research evaluation safely

P2-B2-B must remain a research phase. It may begin only after each new corpus and each encoder checkpoint passes the same licence, version-lock, manifest, hash, and approval gate used in P2-B2-A.

1. Add independently sourced real-image and generated-image corpora with documented upstream rights, source-disjoint splits, and larger fixed test sets.
2. Add at least two held-out generators and a true `UNKNOWN` evaluation partition; report rejection coverage and failure cases rather than forcing attribution.
3. Materialize controlled JPEG, resize, crop, screenshot, and AI-edit transformations with parent-group leakage checks.
4. Re-acquire or independently verify the EfficientNet checkpoint from an official source, resolving the filename-token versus full-SHA discrepancy before reuse; admit additional official encoders only with equivalent records.
5. Repeat frozen-feature baselines and report confidence intervals, calibration plots, per-dataset/per-generator/per-transformation metrics, and qualitative false-positive/false-negative reviews.
6. Subject every experiment report and model card to governance review before any claim outside research. Do not expose a production API or a consumer-facing AI probability in P2-B2-B.
