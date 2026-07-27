from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256


class CaseState(StrEnum):
    CREATED = "CREATED"; EVIDENCE_COLLECTED = "EVIDENCE_COLLECTED"; ANALYZING = "ANALYZING"; UNDER_REVIEW = "UNDER_REVIEW"; REPORT_GENERATED = "REPORT_GENERATED"; ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class Case:
    case_id: str; original_file_hash: str; evidence_bundle_hash: str | None; report_hash: str | None; created_time: str; operator: str; state: CaseState; reviewer: str | None = None


class CaseRepository:
    def __init__(self) -> None: self._cases: dict[str, Case] = {}

    def create(self, original_file_hash: str, operator: str) -> Case:
        case_id = sha256(f"{original_file_hash}:{operator}:{len(self._cases)}".encode()).hexdigest()[:20]
        case = Case(case_id, original_file_hash, None, None, datetime.now(timezone.utc).isoformat(), operator, CaseState.CREATED)
        self._cases[case_id] = case; return case

    def get(self, case_id: str) -> Case: return self._cases[case_id]

    def advance(self, case_id: str, state: CaseState, *, evidence_bundle_hash: str | None = None, report_hash: str | None = None, reviewer: str | None = None) -> Case:
        case = self.get(case_id)
        if list(CaseState).index(state) < list(CaseState).index(case.state): raise ValueError("Case lifecycle cannot move backwards.")
        if state == CaseState.REPORT_GENERATED and (not reviewer or reviewer == case.operator or not report_hash): raise ValueError("A different reviewer and report hash are required.")
        updated = replace(case, state=state, evidence_bundle_hash=evidence_bundle_hash or case.evidence_bundle_hash, report_hash=report_hash or case.report_hash, reviewer=reviewer or case.reviewer)
        self._cases[case_id] = updated; return updated
