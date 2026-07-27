"""Signature verification for hash-bound intake scope attestations."""

from __future__ import annotations

from dataclasses import dataclass

from deployment.key_provider import KeyProvider

from ..models import ScopeAttestation


@dataclass(frozen=True)
class ScopeAttestationVerifier:
    trusted_keys: dict[str, KeyProvider]

    def verify(self, attestation: ScopeAttestation) -> bool:
        key = self.trusted_keys.get(attestation.key_id)
        return key is not None and key.verify(attestation.payload(), attestation.signature)
