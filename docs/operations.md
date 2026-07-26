# Operations guide

## Run in production

Set secrets in the deployment platform; do not place them in a command history or source file.

```bash
docker build -t ai-photo-reconstructor:0.2.0 .
docker run --rm -p 8000:8000 \
  -e APP_ENV=production \
  -e APP_API_KEYS='agency-analyst:long-random-secret:analyst,agency-operator:another-long-random-secret:operator' \
  -e APP_ALLOWED_ORIGINS='https://reconstructor.example.gov' \
  ai-photo-reconstructor:0.2.0
```

Use `GET /health` for liveness. Use `GET /ready` with an `operator` API key for authenticated readiness. Use `POST /analyze` with an `analyst` API key.

## Organisational SSO

For bearer-token integration, set `APP_OIDC_ISSUER`, `APP_OIDC_AUDIENCE`, and `APP_OIDC_JWKS_URL` together. The service validates RS256 tokens and requires `exp`, `iat`, `sub`, and a configurable roles claim (`APP_OIDC_ROLE_CLAIM`, default `roles`). Only the values `analyst` and `operator` grant access. Validate the issuer's exact token format and claim-mapping contract before enabling it.

## Internal vision recognition

To enable AI-based visual context, configure `APP_VISION_PROVIDER_URL` and `APP_VISION_PROVIDER_TOKEN` together. The URL must be HTTPS and should resolve only through the approved institutional egress path. The endpoint accepts multipart field `image` and returns JSON in the form `{"description": "...", "tags": ["..."]}`. Its response is used only to enrich editable prompts; it is not provenance evidence or an automated decision.

## Audit collection

Application audit events are emitted to standard output. Ship stdout to the organisation's central audit platform. Restrict access, make the sink append-only, and configure retention under the approved records schedule.

## Incident handling

Revoke a suspected key in the secret store, redeploy with the revised `APP_API_KEYS` set, identify impacted request IDs in the central audit system, and follow the organisation's incident-response process.
