"""Opt-in container startup verification; never requires a public endpoint."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
from urllib.request import urlopen

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DOCKER_STARTUP_TEST") != "1",
    reason="Set RUN_DOCKER_STARTUP_TEST=1 on an isolated Docker-capable host.",
)


def test_private_compose_starts_on_loopback(tmp_path: Path):
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI is unavailable.")
    project = "ai-auth-p3c-startup-test"
    environment_file = tmp_path / "private.env"
    environment_file.write_text(
        "\n".join(
            (
                "DATABASE_URL=postgresql://ai_auth:local-test-password@database:5432/ai_auth",
                "STORAGE_PATH=/var/lib/ai-authentication/evidence",
                "SIGNING_KEY_PROVIDER=local_test",
                "AUDIT_CONFIG=hash_chain_v1",
                "LOG_LEVEL=INFO",
                "POSTGRES_DB=ai_auth",
                "POSTGRES_USER=ai_auth",
                "POSTGRES_PASSWORD=local-test-password",
                "MINIO_ROOT_USER=local-test-user",
                "MINIO_ROOT_PASSWORD=local-test-secret",
            )
        ),
        encoding="utf-8",
    )
    command = ["docker", "compose", "-p", project, "--env-file", str(environment_file)]
    try:
        result = subprocess.run(command + ["up", "--build", "--wait", "--wait-timeout", "120"], capture_output=True, text=True, timeout=180)
        assert result.returncode == 0, result.stderr
        with urlopen("http://127.0.0.1:8080/health", timeout=10) as response:
            assert response.status == 200
    finally:
        subprocess.run(command + ["down", "--volumes", "--remove-orphans"], capture_output=True, text=True, timeout=60)
