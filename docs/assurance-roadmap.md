# Institutional assurance roadmap

This checklist defines evidence needed before an institution can decide the service is suitable for an official environment. It is intentionally not a self-attestation.

| Gate | Required evidence | Current repository state |
| --- | --- | --- |
| Data governance | Approved classification, DPIA/PIA, retention schedule, processor agreements | Deployment responsibility; documented boundary only |
| Identity and access | Organisation SSO/service identity, secret rotation, revocation and least privilege | API-key roles and OIDC JWT/role mapping are implemented; identity-team integration evidence still required |
| Auditability | Central immutable audit sink, access review and retrieval test | Structured stdout events; external sink required |
| Operational resilience | HA design, recovery objective, monitoring, on-call and disaster exercise | Kubernetes baseline provides 3 replicas, HPA, PDB, resource limits and probes; target-environment exercise remains required |
| Security assurance | Threat model, independent penetration test, SBOM, signed builds and vulnerability remediation | Container/CI/Kubernetes restricted-runtime baseline; remaining evidence required |
| Model assurance | Evaluation report, use-policy approval, reviewer training and change control | Governance boundary and human-review contract included |
| Accessibility and procurement | Accessibility assessment, localisation, records/publication obligations, legal/procurement approval | Not implemented |

An accountable official, not this repository, must accept each gate with jurisdiction-specific evidence before production use.
