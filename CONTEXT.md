# Ubiquitous language

## Terms

- **Analysis request**: a one-time request to extract observable visual features and produce reconstruction suggestions from an uploaded image.
- **Reconstruction suggestion**: an editable prompt and parameter set inferred from observable features. It is not source-model attribution or a recovered model configuration.
- **Client**: an organisation or service integration identified by an API key.
- **Role**: the access level assigned to a Client. The MVP supports `analyst` to submit analyses and `operator` to inspect service readiness.
- **Audit event**: a structured record of a security-relevant operation. It contains no image bytes, prompts, or API secrets.
- **Provenance evidence**: a cryptographically validated statement about an asset's origin or edit history, such as a valid C2PA manifest. It is distinct from visual-model detection or a reconstruction suggestion.
- **Provenance status**: the result of asking an approved verifier to check an uploaded asset. `valid`, `invalid`, `not_present`, and `unsupported` are evidence states; `not_checked` means no verifier was configured.
