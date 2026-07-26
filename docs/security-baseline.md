# Security baseline

This document defines the implemented minimum baseline, not a certification claim. An institution must perform its own legal, privacy, security and procurement review before deployment.

## Implemented controls

- **No image persistence:** the API handles image bytes in memory only. It does not save uploads, prompts or generated candidates.
- **Controlled vision enrichment:** optional AI recognition is disabled by default. When enabled, bytes are sent only to the configured HTTPS internal vision service with a dedicated token; its response is length-bounded and treated as untrusted text.
- **Cryptographic provenance boundary:** optional C2PA verification is delegated to an approved HTTPS internal verifier. Only its bounded validation result is returned; visual analysis is never presented as provenance.
- **Authenticated production API:** `APP_ENV=production` refuses to start without API keys or a complete OIDC configuration. Keys and OIDC role claims map to explicit `analyst` and `operator` roles.
- **Abuse limits:** uploads have byte and pixel limits; a process-local per-client rate guard limits analysis requests. Deploy a shared gateway limiter for multiple replicas.
- **Privacy-preserving audit events:** successful/rejected analysis and readiness operations emit structured metadata (client ID, request ID, route, outcome, MIME type and byte count). Image bytes, prompt text and secrets are excluded.
- **Browser/API hardening:** an allowlisted CORS policy, `no-store`, `nosniff`, `no-referrer`, correlation IDs and disabled API documentation in production are enabled.
- **Deployment posture:** the supplied image runs as a non-root user and exposes a separate unauthenticated `/health` endpoint for orchestration.

## Required deployment controls

The repository deliberately does not attempt to replace institutional controls. Before handling non-public data, deploy behind a managed API gateway/WAF and configure:

1. TLS termination, an organisational identity provider or managed secret store, rotation and immediate revocation for API credentials. OIDC integration accepts only RS256 JWTs from the configured issuer/audience/JWKS endpoint; validate its claim and group mapping with the identity team.
2. Central, append-only audit collection with access restrictions and a retention schedule approved by the data owner.
3. Network segmentation, vulnerability scanning, container image signing, patch SLAs, backups for configuration, and incident response ownership.
4. A jurisdiction-specific privacy impact assessment, data classification decision, accessibility review and model-risk assessment.
5. Independent penetration testing and an approved change-management/release process.

## Data-flow boundary

```text
Authorised client -> TLS/API gateway -> stateless analyzer -> response
                       |                    |
                       v                    v
                central audit sink      in-memory image bytes
```

No model attribution claim is made. Reconstruction output must be reviewed by a human before it informs an official decision or communication.
