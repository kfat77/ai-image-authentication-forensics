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

## Audit collection

Application audit events are emitted to standard output. Ship stdout to the organisation's central audit platform. Restrict access, make the sink append-only, and configure retention under the approved records schedule.

## Incident handling

Revoke a suspected key in the secret store, redeploy with the revised `APP_API_KEYS` set, identify impacted request IDs in the central audit system, and follow the organisation's incident-response process.
