"""Manifest-backed research data admission and leakage checks."""

from .manifest import DatasetManifest, ManifestError, load_manifest, manifest_hash
from .splits import DatasetRecord, SplitValidationError, load_records, validate_admitted_dataset, validate_records_for_experiment
from .admission import load_approved_manifests

__all__ = ["DatasetManifest", "DatasetRecord", "ManifestError", "SplitValidationError", "load_approved_manifests", "load_manifest", "load_records", "manifest_hash", "validate_admitted_dataset", "validate_records_for_experiment"]
