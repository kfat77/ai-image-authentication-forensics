"""Append-only, signed Registry of Record contracts (test/in-memory implementation)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any, Literal
from uuid import uuid4

from deployment.key_provider import KeyProvider


class ApprovalStatus(StrEnum):
    DRAFT = "DRAFT"; SUBMITTED = "SUBMITTED"; VALIDATED = "VALIDATED"; REVIEWED = "REVIEWED"; APPROVED = "APPROVED"; DEPRECATED = "DEPRECATED"


@dataclass(frozen=True)
class RegistrySignature:
    signer_id: str
    signing_algorithm: str
    signing_time: str
    key_provider_id: str
    signature: str

    # Compatibility aliases for the key-provider contract.
    @property
    def key_id(self) -> str: return self.key_provider_id
    @property
    def algorithm(self) -> str: return self.signing_algorithm


@dataclass(frozen=True)
class RegistryRecord:
    record_id: str
    record_type: Literal["model", "calibration"]
    payload: dict[str, Any]
    record_hash: str
    signature: RegistrySignature


@dataclass(frozen=True)
class ApprovalEvent:
    event_id: str
    record_id: str
    previous_state: ApprovalStatus | None
    new_state: ApprovalStatus
    actor: str
    timestamp: str
    reason: str
    event_hash: str
    previous_event_hash: str | None


@dataclass(frozen=True)
class ProviderAdmissionRecord:
    provider_id: str
    provider_version: str
    model_record_hash: str
    calibration_record_hash: str
    scope_hash: str
    approval_record_hash: str
    record_hash: str
    signature: RegistrySignature


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def canonical_record_hash(record_type: str, payload: dict[str, Any]) -> str:
    return sha256(_canonical({"record_type": record_type, "record_content": payload})).hexdigest()


def canonical_signing_payload(record_content: dict[str, Any], record_hash: str, signature: RegistrySignature) -> bytes:
    """Everything describing a signature is covered by its signature."""
    return _canonical({"record_content": record_content, "record_hash": record_hash,
                       "signer_id": signature.signer_id, "signing_algorithm": signature.signing_algorithm,
                       "signing_time": signature.signing_time, "key_provider_id": signature.key_provider_id})


def _provider_content(record: ProviderAdmissionRecord) -> dict[str, Any]:
    return {"provider_id": record.provider_id, "provider_version": record.provider_version,
            "model_record_hash": record.model_record_hash, "calibration_record_hash": record.calibration_record_hash,
            "scope_hash": record.scope_hash, "approval_record_hash": record.approval_record_hash}


def verify_registry_record(record: RegistryRecord | ProviderAdmissionRecord, keys: dict[str, KeyProvider]) -> bool:
    content = record.payload if isinstance(record, RegistryRecord) else _provider_content(record)
    record_type = record.record_type if isinstance(record, RegistryRecord) else "provider_admission"
    key = keys.get(record.signature.key_provider_id)
    return bool(key and key.key_id == record.signature.key_provider_id and key.algorithm == record.signature.signing_algorithm
                and canonical_record_hash(record_type, content) == record.record_hash
                and key.verify(canonical_signing_payload(content, record.record_hash, record.signature), record.signature.signature))


class InstitutionalRegistry:
    """In-memory reference implementation. Records and approval events are never deleted or overwritten."""
    def __init__(self, signer: KeyProvider) -> None:
        self._signer = signer
        self._records: dict[str, RegistryRecord] = {}
        self._current: dict[str, str] = {}
        self._events: dict[str, list[ApprovalEvent]] = {}
        self._providers: dict[tuple[str, str], ProviderAdmissionRecord] = {}
        self._known_providers: set[tuple[str, str]] = set()

    def register_provider(self, provider_id: str, provider_version: str) -> None:
        if not provider_id or not provider_version: raise ValueError("Provider identity is required.")
        self._known_providers.add((provider_id, provider_version))

    def create_model(self, payload: dict[str, Any], actor: str) -> RegistryRecord:
        required = {"model_id", "version", "architecture", "weight_hash", "source", "license", "training_data_reference", "evaluation_reference", "calibration_id", "provider_id"}
        if required - set(payload): raise ValueError("Model record is missing required fields.")
        return self._create("model", payload, actor)

    def create_calibration(self, payload: dict[str, Any], actor: str) -> RegistryRecord:
        required = {"calibration_id", "model_id", "dataset_reference", "method", "metrics", "threshold", "scope", "limitations"}
        if required - set(payload): raise ValueError("Calibration record is missing required fields.")
        return self._create("calibration", payload, actor)

    def transition(self, record_hash: str, status: ApprovalStatus, actor: str, reason: str) -> RegistryRecord:
        record = self._records[record_hash]
        if self._current.get(record.record_id) != record_hash: raise ValueError("Only the current record revision may transition.")
        current = ApprovalStatus(record.payload["approval_status"])
        allowed = {ApprovalStatus.DRAFT: ApprovalStatus.SUBMITTED, ApprovalStatus.SUBMITTED: ApprovalStatus.VALIDATED,
                   ApprovalStatus.VALIDATED: ApprovalStatus.REVIEWED, ApprovalStatus.REVIEWED: ApprovalStatus.APPROVED,
                   ApprovalStatus.APPROVED: ApprovalStatus.DEPRECATED}
        if allowed.get(current) != status: raise ValueError("Invalid approval workflow transition.")
        if status == ApprovalStatus.APPROVED and actor == record.payload["submitted_by"]:
            raise PermissionError("Submitter cannot approve the same record.")
        payload = {**record.payload, "approval_status": status, "approved_by": actor if status == ApprovalStatus.APPROVED else record.payload["approved_by"], "approval_reason": reason, "updated_at": _now()}
        updated = self._append_revision(record.record_id, record.record_type, payload, actor)
        self._append_event(record.record_id, current, status, actor, reason)
        return updated

    def approval_history(self, record_id: str) -> tuple[ApprovalEvent, ...]: return tuple(self._events[record_id])

    def verify_approval_history(self, record_id: str, events: tuple[ApprovalEvent, ...] | list[ApprovalEvent] | None = None) -> bool:
        chain = tuple(events) if events is not None else self.approval_history(record_id)
        expected = {None: ApprovalStatus.DRAFT, ApprovalStatus.DRAFT: ApprovalStatus.SUBMITTED, ApprovalStatus.SUBMITTED: ApprovalStatus.VALIDATED,
                    ApprovalStatus.VALIDATED: ApprovalStatus.REVIEWED, ApprovalStatus.REVIEWED: ApprovalStatus.APPROVED,
                    ApprovalStatus.APPROVED: ApprovalStatus.DEPRECATED}
        previous_hash: str | None = None; previous_state: ApprovalStatus | None = None
        for event in chain:
            body = {"event_id": event.event_id, "record_id": event.record_id, "previous_state": event.previous_state,
                    "new_state": event.new_state, "actor": event.actor, "timestamp": event.timestamp, "reason": event.reason,
                    "previous_event_hash": event.previous_event_hash}
            if (event.record_id != record_id or event.previous_event_hash != previous_hash or event.previous_state != previous_state
                    or expected.get(previous_state) != event.new_state or sha256(_canonical(body)).hexdigest() != event.event_hash): return False
            previous_hash, previous_state = event.event_hash, event.new_state
        return bool(chain) and previous_state == ApprovalStatus(self._records[self._current[record_id]].payload["approval_status"])

    def admit_provider(self, provider_id: str, provider_version: str, model_hash: str, calibration_hash: str, scope: tuple[str, ...], actor: str = "registry-administrator") -> ProviderAdmissionRecord:
        if (provider_id, provider_version) not in self._known_providers: raise ValueError("Provider is not registered for admission.")
        model = self.get_model_record(model_hash); calibration = self.get_calibration_record(calibration_hash)
        if not self.verify_record(model_hash) or not self.verify_record(calibration_hash): raise ValueError("Registry record signature verification failed.")
        if model.payload["approval_status"] != ApprovalStatus.APPROVED or calibration.payload["approval_status"] != ApprovalStatus.APPROVED: raise PermissionError("Provider admission requires approved model and calibration records.")
        if model.payload["calibration_id"] != calibration.payload["calibration_id"] or calibration.payload["model_id"] != model.payload["model_id"] or model.payload["provider_id"] != provider_id: raise ValueError("Provider, model, and calibration binding is inconsistent.")
        scope_hash = sha256(_canonical(list(scope))).hexdigest()
        if scope_hash != sha256(_canonical(calibration.payload["scope"])).hexdigest(): raise ValueError("Provider scope must equal the approved calibration scope.")
        approval_hash = sha256(_canonical({"model_approval_event_hash": self.approval_history(model.record_id)[-1].event_hash, "calibration_approval_event_hash": self.approval_history(calibration.record_id)[-1].event_hash})).hexdigest()
        content = {"provider_id": provider_id, "provider_version": provider_version, "model_record_hash": model_hash,
                   "calibration_record_hash": calibration_hash, "scope_hash": scope_hash, "approval_record_hash": approval_hash}
        digest = canonical_record_hash("provider_admission", content)
        result = ProviderAdmissionRecord(**content, record_hash=digest, signature=self._signature(content, digest, actor))
        self._providers[(provider_id, provider_version)] = result
        return result

    def resolve_provider_for_report(self, provider_id: str, provider_version: str) -> dict[str, str]:
        admission = self.get_provider_admission(provider_id, provider_version)
        if not self.verify_provider_admission(admission): raise PermissionError("Provider admission is absent, invalid, or no longer consistent with Registry of Record.")
        return {"provider_record_hash": admission.record_hash, "model_record_hash": admission.model_record_hash,
                "calibration_record_hash": admission.calibration_record_hash, "registry_verified": "true",
                "verified_record_hash": admission.record_hash}

    def verify_provider_admission(self, admission: ProviderAdmissionRecord) -> bool:
        if (admission.provider_id, admission.provider_version) not in self._known_providers or not verify_registry_record(admission, {self._signer.key_id: self._signer}): return False
        try:
            model = self.get_model_record(admission.model_record_hash); calibration = self.get_calibration_record(admission.calibration_record_hash)
        except KeyError: return False
        if not self.verify_record(model.record_hash) or not self.verify_record(calibration.record_hash): return False
        if model.payload["approval_status"] != ApprovalStatus.APPROVED or calibration.payload["approval_status"] != ApprovalStatus.APPROVED: return False
        if calibration.payload["model_id"] != model.payload["model_id"] or model.payload["calibration_id"] != calibration.payload["calibration_id"] or model.payload["provider_id"] != admission.provider_id: return False
        scope_hash = sha256(_canonical(calibration.payload["scope"])).hexdigest()
        approval_hash = sha256(_canonical({"model_approval_event_hash": self.approval_history(model.record_id)[-1].event_hash, "calibration_approval_event_hash": self.approval_history(calibration.record_id)[-1].event_hash})).hexdigest()
        return scope_hash == admission.scope_hash and approval_hash == admission.approval_record_hash

    def get_model_record(self, record_hash: str) -> RegistryRecord:
        record = self._records[record_hash]
        if record.record_type != "model": raise KeyError(record_hash)
        return record
    def get_calibration_record(self, record_hash: str) -> RegistryRecord:
        record = self._records[record_hash]
        if record.record_type != "calibration": raise KeyError(record_hash)
        return record
    def get_provider_admission(self, provider_id: str, version: str) -> ProviderAdmissionRecord: return self._providers[(provider_id, version)]
    def verify_record(self, record_hash: str) -> bool: return verify_registry_record(self._records[record_hash], {self._signer.key_id: self._signer})

    def _create(self, record_type: Literal["model", "calibration"], payload: dict[str, Any], actor: str) -> RegistryRecord:
        record_id = str(uuid4())
        content = {**payload, "approval_status": ApprovalStatus.DRAFT, "created_at": _now(), "submitted_by": actor, "approved_by": None, "approval_reason": "created"}
        record = self._append_revision(record_id, record_type, content, actor)
        self._events[record_id] = []
        self._append_event(record_id, None, ApprovalStatus.DRAFT, actor, "created")
        return record
    def _append_revision(self, record_id: str, record_type: Literal["model", "calibration"], payload: dict[str, Any], actor: str) -> RegistryRecord:
        content = {**payload, "record_id": record_id}
        digest = canonical_record_hash(record_type, content)
        record = RegistryRecord(record_id, record_type, content, digest, self._signature(content, digest, actor))
        self._records[digest] = record; self._current[record_id] = digest
        return record
    def _append_event(self, record_id: str, previous: ApprovalStatus | None, new: ApprovalStatus, actor: str, reason: str) -> ApprovalEvent:
        preceding = self._events[record_id][-1].event_hash if self._events[record_id] else None
        body = {"event_id": str(uuid4()), "record_id": record_id, "previous_state": previous, "new_state": new, "actor": actor, "timestamp": _now(), "reason": reason, "previous_event_hash": preceding}
        event = ApprovalEvent(**body, event_hash=sha256(_canonical(body)).hexdigest())
        self._events[record_id].append(event); return event
    def _signature(self, content: dict[str, Any], digest: str, signer_id: str) -> RegistrySignature:
        unsigned = RegistrySignature(signer_id, self._signer.algorithm, _now(), self._signer.key_id, "")
        return RegistrySignature(**{**asdict(unsigned), "signature": self._signer.sign(canonical_signing_payload(content, digest, unsigned))})


def _now() -> str: return datetime.now(timezone.utc).isoformat()
