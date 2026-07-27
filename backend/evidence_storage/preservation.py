from dataclasses import dataclass

@dataclass(frozen=True)
class PreservedEvidence: case_id: str; original_file_hash: str; evidence_bundle_hash: str; report_hash: str | None
class EvidencePreservationStore:
    def __init__(self) -> None: self._records: list[PreservedEvidence] = []
    def preserve(self, record: PreservedEvidence) -> None:
        if any(item.case_id == record.case_id and item.original_file_hash != record.original_file_hash for item in self._records): raise ValueError("Original evidence cannot be replaced.")
        self._records.append(record)
    def records(self, case_id: str) -> tuple[PreservedEvidence, ...]: return tuple(item for item in self._records if item.case_id == case_id)
