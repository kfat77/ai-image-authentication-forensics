# Kubernetes deployment baseline

`k8s/base` is an institution-adaptable baseline rather than a one-command production deployment. It assumes a restricted Pod Security admission policy, a metrics server, an ingress gateway labelled as shown, an egress gateway, and external secret delivery.

## Required organisation changes

1. Replace the `image` placeholder with a signed, approved image from the institution's registry.
2. Create `ai-photo-reconstructor-config` from reviewed values; do not apply `config.example.yaml` unchanged.
3. Populate the `ai-photo-reconstructor-runtime` Secret through the approved secret manager/CSI driver. It may contain `APP_API_KEYS` and, when `APP_VISION_PROVIDER_URL` is enabled, `APP_VISION_PROVIDER_TOKEN`. It may be omitted only when OIDC is fully configured and vision enrichment is disabled. Do not commit a Secret manifest or use `kubectl create secret` in shell history.
4. Adapt the ingress and egress namespace/pod labels in `network-policy.yaml` to the cluster. The egress gateway must allow only the configured identity-provider JWKS endpoint and approved audit/telemetry destinations.
5. Verify PDB/HPA support, namespace policies, probes, gateway access logs, central audit shipping and a rollback procedure in the target cluster.

Render the baseline after providing the external ConfigMap and secret mechanism:

```bash
kubectl kustomize k8s/base
```

The deployment mounts a memory-backed ephemeral `/tmp` volume to support multipart uploads while retaining a read-only root filesystem. It does not persist images.
