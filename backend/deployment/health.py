"""Non-sensitive readiness checks for an isolated institution deployment."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class HealthStatus:
    service: bool
    storage: bool
    database: bool
    audit_integrity: bool

    @property
    def ready(self) -> bool:
        return all(asdict(self).values())

    def as_dict(self) -> dict[str, bool]:
        return {**asdict(self), "ready": self.ready}


class PrivateDeploymentHealth:
    def __init__(self, *, storage_check: Callable[[], bool], database_check: Callable[[], bool], audit_check: Callable[[], bool]) -> None:
        self._storage_check = storage_check
        self._database_check = database_check
        self._audit_check = audit_check

    def check(self) -> HealthStatus:
        return HealthStatus(
            service=True,
            storage=self._safe(self._storage_check),
            database=self._safe(self._database_check),
            audit_integrity=self._safe(self._audit_check),
        )

    @staticmethod
    def _safe(check: Callable[[], bool]) -> bool:
        try:
            return bool(check())
        except Exception:
            return False
