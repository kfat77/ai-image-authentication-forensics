"""Persistence ports for case records and immutable forensic custody objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import json
from pathlib import Path
import sqlite3
from typing import Any, Protocol
from uuid import uuid4


class CaseRepositoryPort(Protocol):
    def save_case(self, case_id: str, record: Any) -> None: ...
    def get_case(self, case_id: str) -> Any: ...


class EvidenceRepositoryPort(Protocol):
    def preserve_evidence(self, case_id: str, record: Any) -> None: ...
    def evidence_for(self, case_id: str) -> tuple[Any, ...]: ...


class AuditRepositoryPort(Protocol):
    def append_audit_event(self, record: Any) -> None: ...
    def audit_events(self) -> tuple[Any, ...]: ...


class ReportRepositoryPort(Protocol):
    def preserve_report(self, case_id: str, report_hash: str, record: Any) -> None: ...
    def report_for(self, case_id: str) -> Any: ...


@dataclass(frozen=True)
class StoredReport:
    report_hash: str
    record: Any


class MemoryInstitutionRepository:
    """In-memory persistence adapter for deterministic tests and recovery drills."""

    def __init__(self) -> None:
        self._cases: dict[str, Any] = {}
        self._evidence: dict[str, list[Any]] = {}
        self._audit: list[Any] = []
        self._reports: dict[str, StoredReport] = {}

    def save_case(self, case_id: str, record: Any) -> None:
        self._cases[case_id] = record

    def get_case(self, case_id: str) -> Any:
        return self._cases[case_id]

    def preserve_evidence(self, case_id: str, record: Any) -> None:
        records = self._evidence.setdefault(case_id, [])
        if record in records:
            return
        records.append(record)

    def evidence_for(self, case_id: str) -> tuple[Any, ...]:
        return tuple(self._evidence.get(case_id, []))

    def append_audit_event(self, record: Any) -> None:
        self._audit.append(record)

    def audit_events(self) -> tuple[Any, ...]:
        return tuple(self._audit)

    def preserve_report(self, case_id: str, report_hash: str, record: Any) -> None:
        existing = self._reports.get(case_id)
        if existing:
            raise ValueError("A preserved report cannot be overwritten for a case.")
        self._reports[case_id] = StoredReport(report_hash, record)

    def report_for(self, case_id: str) -> StoredReport:
        return self._reports[case_id]


class SqliteInstitutionRepository:
    """Small durable DB-API adapter for local institutional acceptance testing.

    Production PostgreSQL adapters must implement the same ports after the
    institution selects its database driver, migration procedure, and backup
    controls.  This class is not a PostgreSQL substitute.
    """

    def __init__(self, database_path: str | Path) -> None:
        self._connection = sqlite3.connect(str(database_path))
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS institution_records (kind TEXT, record_key TEXT, value TEXT, PRIMARY KEY(kind, record_key))"
        )

    @staticmethod
    def _serialize(record: Any) -> str:
        return json.dumps(asdict(record) if is_dataclass(record) else record, sort_keys=True, default=str)

    def save_case(self, case_id: str, record: Any) -> None:
        self._write("case", case_id, record, overwrite=True)

    def get_case(self, case_id: str) -> dict[str, Any]:
        return self._read("case", case_id)

    def preserve_evidence(self, case_id: str, record: Any) -> None:
        key = f"{case_id}:{uuid4().hex}"
        self._write("evidence", key, record, overwrite=False)

    def evidence_for(self, case_id: str) -> tuple[dict[str, Any], ...]:
        cursor = self._connection.execute(
            "SELECT value FROM institution_records WHERE kind = 'evidence' AND record_key LIKE ? ORDER BY rowid", (f"{case_id}:%",)
        )
        return tuple(json.loads(row[0]) for row in cursor.fetchall())

    def append_audit_event(self, record: Any) -> None:
        self._write("audit", uuid4().hex, record, overwrite=False)

    def audit_events(self) -> tuple[dict[str, Any], ...]:
        cursor = self._connection.execute("SELECT value FROM institution_records WHERE kind = 'audit' ORDER BY rowid")
        return tuple(json.loads(row[0]) for row in cursor.fetchall())

    def preserve_report(self, case_id: str, report_hash: str, record: Any) -> None:
        existing = self._connection.execute("SELECT value FROM institution_records WHERE kind = 'report' AND record_key = ?", (case_id,)).fetchone()
        if existing:
            raise ValueError("A preserved report cannot be overwritten for a case.")
        self._write("report", case_id, {"report_hash": report_hash, "record": record}, overwrite=False)

    def report_for(self, case_id: str) -> dict[str, Any]:
        return self._read("report", case_id)

    def close(self) -> None:
        self._connection.close()

    def _write(self, kind: str, record_key: str, record: Any, *, overwrite: bool) -> None:
        statement = "INSERT OR REPLACE" if overwrite else "INSERT"
        try:
            self._connection.execute(f"{statement} INTO institution_records(kind, record_key, value) VALUES (?, ?, ?)", (kind, record_key, self._serialize(record)))
            self._connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Immutable {kind} record already exists: {record_key}") from exc

    def _read(self, kind: str, record_key: str) -> dict[str, Any]:
        row = self._connection.execute("SELECT value FROM institution_records WHERE kind = ? AND record_key = ?", (kind, record_key)).fetchone()
        if row is None:
            raise KeyError(record_key)
        return json.loads(row[0])
