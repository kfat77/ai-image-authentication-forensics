# P5-A Validation Program

## Purpose and boundary

This program prepares a controlled institutional validation of the existing AI Image Authentication platform. It tests whether the system's evidence, governance controls, and human-review process operate reproducibly within a declared image population. It does **not** establish a judicial qualification, a commercial service, or a claim of universal or 100% AI-image detection.

No real institution data, external production integration, public endpoint, or public performance claim is authorized under P5-A.

## Validation objectives

1. Confirm that submitted inputs produce hash-bound Evidence Bundles and Authentication Reports.
2. Confirm that approved ML evidence is tied to a valid Model Record, Calibration Record, and Provider Admission Record at report time.
3. Measure error, uncertainty, evidence completeness, reproducibility, and reviewer-agreement metrics by declared scenario.
4. Identify failure cases and restrict the recommended usage scope rather than masking them with aggregate metrics.

## Scope

The validation population is limited to licence-reviewed samples recorded in the P5-A scenario matrix. Each batch must declare image type, transformation state, acquisition/source constraints, available metadata/provenance, and any applicable ML validation scope.

Samples or conditions outside the matrix, including undisclosed AI edits, unverified screenshots, low-resolution derivatives, or new generators not represented in the admitted corpus, are recorded as coverage gaps or handled as `OUT_OF_SCOPE`/`uncertain`; they must not be forced into a conclusion.

## Admission and execution procedure

1. Register each candidate in the scenario matrix with source, licence, hash, curated label, and limitations.
2. Reject records with an incomplete licence review, absent content hash, invalid label, or unapproved use purpose.
3. Freeze the admitted list as a versioned Validation batch. Preserve source files and their hashes separately from derived artifacts.
4. Verify the system version; for each ML Provider, verify the signed Model Registry, Calibration Registry, and Provider Admission records. Experimental or unapproved models may be evaluated only in a separately labeled research run and cannot contribute to formal validation evidence.
5. Run deterministic evidence extraction and Authentication Report generation. Record input/output hashes, provider exclusions, scope outcomes, and errors.
6. Send reports to independent human reviewers using the P5-A review workflow. Reviewers see evidence and limitations, not a hidden “correct answer.”
7. Calculate metrics by scenario and record all failed, excluded, and uncertain cases. Do not remove difficult cases after execution.
8. Produce the Institution Validation Report using the P5-A template. Its recommendations may narrow scope or halt further validation; they cannot authorize public deployment.

## Acceptance criteria

The program is accepted only when all of the following are evidenced in the validation report:

- 100% of included samples have a reviewed source, licence/use authorization, SHA-256 hash, scenario, curated label, and limitation record.
- 100% of formal ML evidence records reference a verified, approved Model/Calibration/Provider chain. Unverified or out-of-scope evidence is excluded or marked accordingly.
- 100% of reports selected for reproducibility re-run have matching input hashes, versioned methods, registry references, evidence-manifest hashes, and verifiable output hashes. Content-identical output is not required when analysis timestamps differ.
- Every false positive, false negative, uncertain, failed, and excluded case remains in the final report with a disposition.
- At least two appropriately separated reviewers complete the agreement sample; disagreement and abstention are reported rather than resolved silently.
- The report states a bounded recommended-use scope and exclusions. It makes no judicial, public-service, or 100% performance claim.

Metric targets, sample sizes, and acceptance thresholds are deliberately institution-specific and must be approved before a batch begins. P5-A defines the measurement and governance mechanism, not a pre-approved performance bar.
