"""Dataset-manifest gate: unreviewed sources cannot enter baseline training."""
from __future__ import annotations

from dataclasses import dataclass


_TRUSTED_APPROVED_MANIFESTS = {
    ("synthetic-feature-fixture-v1", "1"): "9752fec9d00fbb13dd2abd88ffcc47e7d848f788cde322a6fddfcd43d2f3a44b",
}


@dataclass(frozen=True)
class DatasetManifest:
    dataset_id: str
    version: str
    approval_status: str
    training_permitted: bool
    commercial_use_permitted: bool
    manifest_hash: str


class DatasetApprovalError(PermissionError):
    pass


def require_training_approval(manifest: DatasetManifest) -> None:
    trusted_hash = _TRUSTED_APPROVED_MANIFESTS.get((manifest.dataset_id, manifest.version))
    if (
        manifest.approval_status != "approved"
        or not manifest.training_permitted
        or trusted_hash is None
        or manifest.manifest_hash != trusted_hash
    ):
        raise DatasetApprovalError(f"Dataset {manifest.dataset_id}@{manifest.version} is not approved for training.")
