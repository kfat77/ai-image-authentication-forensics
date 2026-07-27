# Container boundary

The root `Dockerfile` builds the backend as a non-root user.  The root
`docker-compose.yml` binds the backend only to `127.0.0.1` for a local,
institution-operated acceptance environment.  Database and object-storage
services have no host port mapping.

Use the guarded configuration procedure in `docs/p3c/private-deployment-guide.md`.
