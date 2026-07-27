"""Explicit configuration contract for an internal-only deployment."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
from typing import Mapping


class ConfigurationError(ValueError):
    """Raised when a required private-deployment setting is absent or unsafe."""


_REQUIRED = ("DATABASE_URL", "STORAGE_PATH", "SIGNING_KEY_PROVIDER", "AUDIT_CONFIG", "LOG_LEVEL")
_LOG_LEVELS = frozenset({"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"})
_KEY_PROVIDERS = frozenset({"local_test", "external_kms"})


@dataclass(frozen=True)
class PrivateDeploymentConfig:
    database_url: str
    storage_path: str
    signing_key_provider: str
    audit_config: str
    log_level: str

    @classmethod
    def from_env(cls, values: Mapping[str, str] | None = None) -> "PrivateDeploymentConfig":
        values = environ if values is None else values
        missing = [name for name in _REQUIRED if not values.get(name, "").strip()]
        if missing:
            raise ConfigurationError(f"Missing required private-deployment configuration: {', '.join(missing)}")

        provider = values["SIGNING_KEY_PROVIDER"].strip().lower()
        if provider not in _KEY_PROVIDERS:
            raise ConfigurationError("SIGNING_KEY_PROVIDER must be local_test or external_kms.")
        log_level = values["LOG_LEVEL"].strip().upper()
        if log_level not in _LOG_LEVELS:
            raise ConfigurationError("LOG_LEVEL is not a supported Python logging level.")
        if not values["DATABASE_URL"].strip().startswith(("sqlite:", "postgresql:", "postgres:")):
            raise ConfigurationError("DATABASE_URL must identify an approved database scheme.")
        if not values["STORAGE_PATH"].strip():
            raise ConfigurationError("STORAGE_PATH must not be empty.")
        if not values["AUDIT_CONFIG"].strip():
            raise ConfigurationError("AUDIT_CONFIG must name a configured audit policy.")
        return cls(
            database_url=values["DATABASE_URL"].strip(),
            storage_path=values["STORAGE_PATH"].strip(),
            signing_key_provider=provider,
            audit_config=values["AUDIT_CONFIG"].strip(),
            log_level=log_level,
        )
