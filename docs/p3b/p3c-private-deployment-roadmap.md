# P3-C private deployment roadmap

1. Replace in-memory repositories with an institution-approved private datastore and object store using write-once evidence retention.
2. Integrate SSO, role provisioning, reviewer separation and audited administrator actions.
3. Use managed institutional signing keys, signature verification and immutable audit retention; retire the test HMAC signer.
4. Place the documented Cases, Audit and Report APIs behind a private network gateway, rate controls, backup/restore exercises and security review. Do not expose public endpoints.
5. Pilot with synthetic or formally approved non-government test cases, then conduct legal, privacy, accessibility, records and incident-response review before any operational use.
