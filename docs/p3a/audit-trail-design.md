# Audit Trail Design

Institutional `AuditEvent` has `event_id`, timestamp, actor, action, case ID, input/output hashes, previous event hash and optional institutional signature. Event hashes form a sequential tamper-evident chain; this is not a blockchain. The signature must cover the canonical event hash (which intentionally excludes the signature field itself); P3-B must verify it using the institution key policy.

P3-B must implement durable immutable storage, access control, signature/key lifecycle, retention, export and chain-verification procedures. The current P2-C JSONL log is expressly not this audit system.
