# Ubiquitous language

This project contains two separate product capabilities: creative reconstruction and forensic detection. They may inspect the same uploaded image but never share a conclusion or evidence meaning.

## Reconstruction

- **Analysis request**: a one-time request to extract observable visual features and produce reconstruction suggestions from an uploaded image.
- **Reconstruction suggestion**: an editable prompt and parameter set inferred from observable features. It is not source-model attribution or a recovered model configuration.

## Forensics

- **Detection request**: a request for a versioned forensic assessment of an uploaded image. It is distinct from an Analysis request and produces no prompt reconstruction output.
- **Detection result**: a versioned record containing a detection score, uncertainty, evidence items, provenance observations and stated limitations. A draft contract is not an implemented detector.
- **AI-generation probability**: a calibrated estimate for a precisely documented population and transformation scope. It is not a fact about origin, and must be omitted when no approved calibrated model exists.
- **Suspected model**: a ranked hypothesis from a closed, versioned set of generator families plus `unknown`. It is not proof that a particular proprietary model generated an image.
- **Evidence item**: one bounded observation from a detector or verifier, labeled with its evidence level, method version, scope and limitations.
- **Observation**: a deterministic file or pixel measurement with a source, confidence description and limitation. It is not a finding about image origin.
- **Evidence bundle**: the versioned, hash-bound collection of P1 detector observations, artifact files, processing parameters and limitations for one input image.
- **Artifact file**: a derived display or manifest file listed in an Evidence bundle with a relative path and content hash.
- **Suspicious region**: an image area highlighted by a localization method as relevant to a detector score. It is a review aid, not proof of manipulation or generation in that area.
- **Evidence level**: the strength and kind of support attached to an Evidence item. Levels describe evidence semantics, not a universal ordering of truth.
- **Forensic summary**: a human-readable synthesis of a Detection result that preserves its uncertainty, scope and review requirement.

## Governance and operations

- **Client**: an organisation or service integration identified by an API key.
- **Role**: the access level assigned to a Client. The MVP supports `analyst` to submit analyses and `operator` to inspect service readiness.
- **Audit event**: a structured record of a security-relevant operation. It contains no image bytes, prompts, or API secrets.
- **Provenance evidence**: a cryptographically validated statement about an asset's origin or edit history, such as a valid C2PA manifest. It is distinct from visual-model detection or a reconstruction suggestion.
- **Provenance status**: the result of asking an approved verifier to check an uploaded asset. `valid`, `invalid`, `not_present`, and `unsupported` are evidence states; `not_checked` means no verifier was configured.
