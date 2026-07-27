"""In-memory Registry of Record contracts, signed with injected test or institutional keys."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any, Literal

from deployment.key_provider import KeyProvider


class ApprovalStatus(StrEnum):
    DRAFT="DRAFT"; SUBMITTED="SUBMITTED"; VALIDATED="VALIDATED"; REVIEWED="REVIEWED"; APPROVED="APPROVED"; DEPRECATED="DEPRECATED"


@dataclass(frozen=True)
class RegistrySignature:
    key_id: str; algorithm: str; signature: str


@dataclass(frozen=True)
class RegistryRecord:
    record_type: Literal["model", "calibration"]
    payload: dict[str, Any]
    record_hash: str
    signature: RegistrySignature


@dataclass(frozen=True)
class ProviderAdmissionRecord:
    provider_id: str; provider_version: str; model_record_hash: str; calibration_record_hash: str; scope: tuple[str, ...]; record_hash: str; signature: RegistrySignature


def canonical_record_hash(record_type: str, payload: dict[str, Any]) -> str:
    return sha256(json.dumps({"record_type": record_type, "payload": payload}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify_registry_record(record: RegistryRecord | ProviderAdmissionRecord, keys: dict[str, KeyProvider]) -> bool:
    if isinstance(record, RegistryRecord):
        expected = canonical_record_hash(record.record_type, record.payload)
    else:
        payload = {key: value for key, value in asdict(record).items() if key not in {"record_hash", "signature"}}
        expected = canonical_record_hash("provider_admission", payload)
    key = keys.get(record.signature.key_id)
    return expected == record.record_hash and key is not None and key.verify(record.record_hash.encode(), record.signature.signature)


class InstitutionalRegistry:
    def __init__(self, signer: KeyProvider) -> None:
        self._signer = signer; self._records: dict[str, RegistryRecord] = {}; self._providers: dict[tuple[str, str], ProviderAdmissionRecord] = {}

    def create_model(self, payload: dict[str, Any], actor: str) -> RegistryRecord:
        required={"model_id","version","architecture","weight_hash","source","license","training_data_reference","evaluation_reference","calibration_id","provider_id"}
        if required-set(payload): raise ValueError("Model record is missing required fields.")
        return self._create("model", {**payload,"approval_status":ApprovalStatus.DRAFT,"created_at":_now(),"submitted_by":actor,"approved_by":None,"approval_reason":None})

    def create_calibration(self, payload: dict[str, Any], actor: str) -> RegistryRecord:
        required={"calibration_id","model_id","dataset_reference","method","metrics","threshold","scope","limitations"}
        if required-set(payload): raise ValueError("Calibration record is missing required fields.")
        return self._create("calibration", {**payload,"approval_status":ApprovalStatus.DRAFT,"created_at":_now(),"submitted_by":actor,"approved_by":None,"approval_reason":None})

    def transition(self, record_hash: str, status: ApprovalStatus, actor: str, reason: str) -> RegistryRecord:
        record=self._records[record_hash]; current=ApprovalStatus(record.payload["approval_status"])
        allowed={ApprovalStatus.DRAFT:ApprovalStatus.SUBMITTED,ApprovalStatus.SUBMITTED:ApprovalStatus.VALIDATED,ApprovalStatus.VALIDATED:ApprovalStatus.REVIEWED,ApprovalStatus.REVIEWED:ApprovalStatus.APPROVED,ApprovalStatus.APPROVED:ApprovalStatus.DEPRECATED}
        if allowed.get(current)!=status: raise ValueError("Invalid approval workflow transition.")
        if status==ApprovalStatus.APPROVED and actor==record.payload["submitted_by"]: raise PermissionError("Submitter cannot approve the same record.")
        payload={**record.payload,"approval_status":status,"approved_by":actor if status==ApprovalStatus.APPROVED else record.payload["approved_by"],"approval_reason":reason,"updated_at":_now()}
        del self._records[record_hash]; updated=self._create(record.record_type,payload); return updated

    def admit_provider(self, provider_id: str, provider_version: str, model_hash: str, calibration_hash: str, scope: tuple[str, ...]) -> ProviderAdmissionRecord:
        model=self.get_model_record(model_hash); calibration=self.get_calibration_record(calibration_hash)
        if model.payload["approval_status"]!=ApprovalStatus.APPROVED or calibration.payload["approval_status"]!=ApprovalStatus.APPROVED: raise PermissionError("Provider admission requires approved model and calibration records.")
        if model.payload["calibration_id"]!=calibration.payload["calibration_id"] or model.payload["provider_id"]!=provider_id: raise ValueError("Provider admission binding is inconsistent.")
        payload={"provider_id":provider_id,"provider_version":provider_version,"model_record_hash":model_hash,"calibration_record_hash":calibration_hash,"scope":scope}
        digest=canonical_record_hash("provider_admission",payload); result=ProviderAdmissionRecord(**payload,record_hash=digest,signature=self._signature(digest)); self._providers[(provider_id,provider_version)]=result; return result

    def get_model_record(self, record_hash: str) -> RegistryRecord:
        record=self._records[record_hash]
        if record.record_type!="model": raise KeyError(record_hash)
        return record
    def get_calibration_record(self, record_hash: str) -> RegistryRecord:
        record=self._records[record_hash]
        if record.record_type!="calibration": raise KeyError(record_hash)
        return record
    def get_provider_admission(self, provider_id: str, version: str) -> ProviderAdmissionRecord: return self._providers[(provider_id,version)]
    def verify_record(self, record_hash: str) -> bool: return verify_registry_record(self._records[record_hash],{self._signer.key_id:self._signer})
    def _create(self, record_type: Literal["model","calibration"], payload: dict[str, Any]) -> RegistryRecord:
        digest=canonical_record_hash(record_type,payload); record=RegistryRecord(record_type,payload,digest,self._signature(digest)); self._records[digest]=record; return record
    def _signature(self, digest: str) -> RegistrySignature: return RegistrySignature(self._signer.key_id,self._signer.algorithm,self._signer.sign(digest.encode()))

def _now() -> str: return datetime.now(timezone.utc).isoformat()
