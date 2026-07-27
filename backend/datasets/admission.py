"""Trusted approval-index parsing for manifest-backed experiment admission."""
from __future__ import annotations

import json
from pathlib import Path

from .manifest import ManifestError


ApprovedManifest = tuple[str, str, str]


def load_approved_manifests(path: str | Path) -> frozenset[ApprovedManifest]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = raw.get("approved_manifests") if isinstance(raw, dict) else None
    if not isinstance(entries, list):
        raise ManifestError("Approval index must contain an approved_manifests list.")
    approved: set[ApprovedManifest] = set()
    for entry in entries:
        required_text = ("name", "version", "hash", "reviewer", "approval_date", "approval_scope")
        if not isinstance(entry, dict) or not all(isinstance(entry.get(key), str) and entry[key] for key in required_text):
            raise ManifestError("Each approval entry must contain non-empty name, version, hash, reviewer, approval_date, and approval_scope.")
        if not isinstance(entry.get("training_permitted"), bool) or not isinstance(entry.get("commercial_use_permitted"), bool):
            raise ManifestError("Each approval entry must declare training_permitted and commercial_use_permitted booleans.")
        approved.add((entry["name"], entry["version"], entry["hash"]))
    return frozenset(approved)
