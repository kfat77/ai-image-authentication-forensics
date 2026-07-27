"""Separated operational, error, and audit logger configuration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path


@dataclass(frozen=True)
class PrivateLoggers:
    operations: logging.Logger
    errors: logging.Logger
    audit: logging.Logger


def configure_private_loggers(log_directory: str | Path, level: str) -> PrivateLoggers:
    """Create separate file channels without logging image bytes or secrets."""
    directory = Path(log_directory)
    directory.mkdir(parents=True, exist_ok=True)
    numeric_level = logging._nameToLevel[level.upper()]
    channels = []
    for name, filename in (
        ("institution.operations", "operations.log"),
        ("institution.errors", "errors.log"),
        ("institution.audit", "audit.log"),
    ):
        logger = logging.getLogger(name)
        logger.setLevel(numeric_level)
        logger.propagate = False
        for previous_handler in logger.handlers:
            previous_handler.close()
            logger.removeHandler(previous_handler)
        handler = logging.FileHandler(directory / filename, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
        channels.append(logger)
    return PrivateLoggers(*channels)
