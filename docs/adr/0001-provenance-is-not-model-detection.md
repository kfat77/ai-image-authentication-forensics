# ADR 0001: Treat C2PA verification as provenance evidence, not model detection

## Status

Accepted, 2026-07-26.

## Context

The service reconstructs editable image-generation prompts and can call an approved vision service. Neither a visual similarity score nor an AI-image detector can establish who created an asset, which model generated it, or whether its history is authentic. Institutions need a separate, reviewable evidence channel for source and editing history.

## Decision

The API exposes a separate `provenance` record. When configured, an internal HTTPS verifier receives the uploaded bytes and returns a bounded C2PA verification result: `valid`, `invalid`, `not_present`, or `unsupported`, plus limited verifier metadata. When no verifier is configured, the API returns `not_checked`.

The verifier must be operated within the institution's approved data boundary and use an approved trust configuration. The intended implementation is based on a released version of the Content Authenticity Initiative's C2PA SDK/tooling, not a bespoke metadata parser.

## Consequences

- A `valid` result is only the verifier's report under its configured trust policy; a human still evaluates its relevance.
- AI-generated-image detection and prompt reconstruction remain separate, non-provenance outputs.
- Institutions must provide the verifier, trust-list governance, certificate policy, retention policy and audit evidence.
- The API fails closed with 503 if a configured verifier cannot be reached or returns an invalid contract.
