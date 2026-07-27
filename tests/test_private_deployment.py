from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from deployment import (
    ConfigurationError,
    InputSecurityError,
    LocalTestKeyProvider,
    MemoryInstitutionRepository,
    PrivateDeploymentConfig,
    PrivateDeploymentHealth,
    SqliteInstitutionRepository,
    validate_input_file,
)
from deployment.logging import configure_private_loggers
from institutional import Role, require_role


def private_env(**overrides: str) -> dict[str, str]:
    values = {
        "DATABASE_URL": "sqlite:///private-test.db",
        "STORAGE_PATH": "/var/lib/evidence",
        "SIGNING_KEY_PROVIDER": "local_test",
        "AUDIT_CONFIG": "hash_chain_v1",
        "LOG_LEVEL": "INFO",
    }
    values.update(overrides)
    return values


def test_configuration_requires_all_values_and_rejects_unknown_provider():
    with pytest.raises(ConfigurationError, match="DATABASE_URL"):
        PrivateDeploymentConfig.from_env(private_env(DATABASE_URL=""))
    with pytest.raises(ConfigurationError, match="SIGNING_KEY_PROVIDER"):
        PrivateDeploymentConfig.from_env(private_env(SIGNING_KEY_PROVIDER="unreviewed"))
    assert PrivateDeploymentConfig.from_env(private_env()).log_level == "INFO"


def test_input_security_admits_bounded_png_and_checks_hash():
    data = b"\x89PNG\r\n\x1a\nprivate-test"
    validated = validate_input_file(data, max_bytes=1024, expected_hash=sha256(data).hexdigest())
    assert validated.media_type == "image/png"
    with pytest.raises(InputSecurityError, match="exceeds"):
        validate_input_file(data, max_bytes=4)
    with pytest.raises(InputSecurityError, match="hash"):
        validate_input_file(data, max_bytes=1024, expected_hash="a" * 64)
    with pytest.raises(InputSecurityError, match="admitted"):
        validate_input_file(b"not an image", max_bytes=1024)


def test_key_provider_and_rbac_keep_test_signing_and_roles_separate():
    provider = LocalTestKeyProvider(b"injected-only-test-key")
    signature = provider.sign(b"report-hash")
    assert provider.verify(b"report-hash", signature)
    assert not provider.verify(b"other", signature)
    with pytest.raises(PermissionError):
        require_role({Role.ANALYST}, Role.REVIEWER)


def test_memory_repository_preserves_report_and_audit_for_recovery():
    repository = MemoryInstitutionRepository()
    repository.save_case("case-1", {"original_file_hash": "a" * 64})
    repository.preserve_evidence("case-1", {"evidence_bundle_hash": "b" * 64})
    repository.append_audit_event({"event_id": "1"})
    repository.preserve_report("case-1", "c" * 64, {"report": "frozen"})
    assert repository.get_case("case-1")["original_file_hash"] == "a" * 64
    assert repository.evidence_for("case-1") == ({"evidence_bundle_hash": "b" * 64},)
    assert repository.audit_events() == ({"event_id": "1"},)
    with pytest.raises(ValueError, match="cannot be overwritten"):
        repository.preserve_report("case-1", "c" * 64, {"report": "replacement"})


def test_sqlite_repository_persists_a_recovery_snapshot(tmp_path: Path):
    database = tmp_path / "institution.db"
    repository = SqliteInstitutionRepository(database)
    repository.save_case("case-1", {"original_file_hash": "a" * 64})
    repository.preserve_evidence("case-1", {"evidence_bundle_hash": "b" * 64})
    repository.append_audit_event({"event_id": "1"})
    repository.preserve_report("case-1", "c" * 64, {"state": "frozen"})
    repository.close()
    restored = SqliteInstitutionRepository(database)
    assert restored.get_case("case-1")["original_file_hash"] == "a" * 64
    assert restored.evidence_for("case-1")[0]["evidence_bundle_hash"] == "b" * 64
    assert restored.audit_events()[0]["event_id"] == "1"
    assert restored.report_for("case-1")["report_hash"] == "c" * 64
    with pytest.raises(ValueError, match="cannot be overwritten"):
        restored.preserve_report("case-1", "c" * 64, {"state": "replacement"})
    restored.close()


def test_health_reports_storage_failure_without_sensitive_detail():
    health = PrivateDeploymentHealth(storage_check=lambda: (_ for _ in ()).throw(OSError("storage unavailable")), database_check=lambda: True, audit_check=lambda: True)
    assert health.check().as_dict() == {"service": True, "storage": False, "database": True, "audit_integrity": True, "ready": False}


def test_log_channels_have_separate_local_files(tmp_path: Path):
    loggers = configure_private_loggers(tmp_path, "INFO")
    loggers.operations.info("operation")
    loggers.errors.error("failure")
    loggers.audit.info("audit")
    for logger in (loggers.operations, loggers.errors, loggers.audit):
        for handler in logger.handlers:
            handler.flush()
    assert (tmp_path / "operations.log").read_text(encoding="utf-8").endswith("operation\n")
    assert (tmp_path / "errors.log").read_text(encoding="utf-8").endswith("failure\n")
    assert (tmp_path / "audit.log").read_text(encoding="utf-8").endswith("audit\n")


def test_compose_is_internal_and_backend_is_loopback_only():
    compose = (Path(__file__).parents[1] / "docker-compose.yml").read_text(encoding="utf-8")
    assert '"127.0.0.1:8080:8000"' in compose
    assert "internal: true" in compose
    assert "database:\n    image" in compose and "storage:\n    image" in compose
    assert "9000:" not in compose and "5432:" not in compose
