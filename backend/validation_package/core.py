"""Signed, independently reviewable validation-package contracts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

from deployment.key_provider import KeyProvider
from institutional_registry import InstitutionalRegistry, RegistrySignature, canonical_signing_payload


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _hash(value: object) -> str:
    return sha256(_canonical(value)).hexdigest()


def _sha256(value: str, field: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest.")


@dataclass(frozen=True)
class SignedValidationPackage:
    content: dict[str, Any]
    package_hash: str
    signature: RegistrySignature

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


class ValidationPackageBuilder:
    """Issues a package only after Registry of Record verifies the Provider chain."""
    def __init__(self, registry: InstitutionalRegistry, signer: KeyProvider) -> None:
        self._registry = registry
        self._signer = signer

    def create(self, *, provider_id: str, provider_version: str, dataset_manifest_hash: str,
               config: dict[str, Any], report_hashes: tuple[str, ...], metrics_schema_hash: str,
               limitations: tuple[str, ...], signer_id: str) -> SignedValidationPackage:
        _sha256(dataset_manifest_hash, "dataset_manifest_hash")
        _sha256(metrics_schema_hash, "metrics_schema_hash")
        if not config or not report_hashes or not limitations or not signer_id:
            raise ValueError("Validation package requires config, report hashes, limitations, and signer ID.")
        for report_hash in report_hashes:
            _sha256(report_hash, "report_hash")
        references = self._registry.resolve_provider_for_report(provider_id, provider_version)
        content = {
            "package_version": "p6c.validation-package.1",
            "issued_at": _now(),
            "provider": {"provider_id": provider_id, "provider_version": provider_version,
                         "provider_record_hash": references["provider_record_hash"]},
            "registry": {"model_record_hash": references["model_record_hash"],
                         "calibration_record_hash": references["calibration_record_hash"],
                         "registry_verified": references["registry_verified"]},
            "dataset_manifest_hash": dataset_manifest_hash,
            "config": config,
            "report_hashes": list(report_hashes),
            "metrics_schema_hash": metrics_schema_hash,
            "limitations": list(limitations),
        }
        package_hash = _hash(content)
        unsigned = RegistrySignature(signer_id, self._signer.algorithm, _now(), self._signer.key_id, "")
        signature = RegistrySignature(**{**asdict(unsigned), "signature": self._signer.sign(canonical_signing_payload(content, package_hash, unsigned))})
        return SignedValidationPackage(content, package_hash, signature)


def verify_validation_package(package: SignedValidationPackage, keys: dict[str, KeyProvider]) -> bool:
    signature = package.signature
    key = keys.get(signature.key_provider_id)
    return bool(key and key.key_id == signature.key_provider_id and key.algorithm == signature.signing_algorithm
                and _hash(package.content) == package.package_hash
                and key.verify(canonical_signing_payload(package.content, package.package_hash, signature), signature.signature))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
