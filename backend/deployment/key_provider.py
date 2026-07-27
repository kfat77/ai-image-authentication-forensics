"""Signing-key seam; cloud KMS products are intentionally not bound here."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import hmac
from typing import Protocol


class KeyProvider(Protocol):
    key_id: str
    algorithm: str

    def sign(self, data: bytes) -> str: ...

    def verify(self, data: bytes, signature: str) -> bool: ...


@dataclass
class LocalTestKeyProvider:
    """Injected test-only HMAC key provider.  No key value is embedded in code."""

    key: bytes
    key_id: str = "local-test-key"
    algorithm: str = "HMAC-SHA256-TEST-ONLY"

    def sign(self, data: bytes) -> str:
        return hmac.new(self.key, data, hashlib.sha256).hexdigest()

    def verify(self, data: bytes, signature: str) -> bool:
        return hmac.compare_digest(self.sign(data), signature)


@dataclass
class ExternalKmsKeyProvider:
    """Adapter contract for an institution-owned KMS integration supplied at runtime."""

    key_id: str
    algorithm: str
    sign_operation: Callable[[bytes], str]
    verify_operation: Callable[[bytes, str], bool]

    def sign(self, data: bytes) -> str:
        return self.sign_operation(data)

    def verify(self, data: bytes, signature: str) -> bool:
        return self.verify_operation(data, signature)
