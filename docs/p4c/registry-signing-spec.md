# Registry signing specification

Each record is serialized with deterministic JSON (sorted keys and compact separators). `record_hash` is SHA-256 over `{record_type, record_content}`. The signed canonical payload is deliberately broader:

```json
{
  "record_content": "...",
  "record_hash": "...",
  "signer_id": "...",
  "signing_algorithm": "...",
  "signing_time": "RFC3339 UTC",
  "key_provider_id": "..."
}
```

Verification recomputes the record hash, looks up the declared key provider, checks its declared algorithm, recreates this entire payload, and verifies the signature. Therefore changing a record field, signer identity, algorithm, signing time, or key-provider ID fails verification. P4-C uses injected test keys only; institutional keys and signer authorization are deferred.
