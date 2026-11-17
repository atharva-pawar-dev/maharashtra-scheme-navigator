"""
Tests for WS9: Containers, Infrastructure-as-Code & Deployment Verification.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.verify_deployment import verify_in_process


def test_dockerfile_hardening():
    """Verify Dockerfile meets multi-stage and non-root security standards."""
    dockerfile_path = REPO_ROOT / "Dockerfile"
    assert dockerfile_path.exists(), "Dockerfile must exist"
    content = dockerfile_path.read_text(encoding="utf-8")

    # Multi-stage build check
    assert "FROM python:3.11-slim AS builder" in content
    assert "FROM python:3.11-slim AS runner" in content

    # Non-root user check (UID 10001)
    assert "groupadd -g 10001 msnuser" in content or "useradd" in content
    assert "USER 10001:10001" in content or "USER msnuser" in content

    # Healthcheck check
    assert "HEALTHCHECK" in content
    assert "/healthz" in content

    # Environment variables
    assert "PYTHONDONTWRITEBYTECODE=1" in content
    assert "PYTHONUNBUFFERED=1" in content


def test_dockerignore_coverage():
    """Verify .dockerignore excludes sensitive and heavy build directories."""
    dockerignore_path = REPO_ROOT / ".dockerignore"
    assert dockerignore_path.exists(), ".dockerignore must exist"
    content = dockerignore_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]

    assert ".git" in lines
    assert ".venv" in lines
    assert "_backups" in lines or "_backups/" in lines
    assert any("*.pyc" in line or "__pycache__" in line for line in lines)
    assert any("*.db" in line or "*.sqlite" in line for line in lines)


def test_docker_compose_stack_spec():
    """Verify docker-compose.yml defines app, postgres, minio with healthchecks."""
    compose_path = REPO_ROOT / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist"
    content = compose_path.read_text(encoding="utf-8")

    assert "postgres:16-alpine" in content
    assert "minio/minio" in content
    assert "healthcheck:" in content
    assert "postgres_data:" in content
    assert "minio_data:" in content


def test_in_process_deployment_verification():
    """Verify that verify_deployment in-process execution completes with all_passed=True."""
    results = verify_in_process()
    assert results["all_passed"] is True, f"Verification failed: {results}"
    assert results["checks"]["healthz"]["passed"] is True
    assert results["checks"]["readyz"]["passed"] is True
    assert results["checks"]["schemes"]["passed"] is True
    assert results["checks"]["security_headers"]["passed"] is True
    assert results["checks"]["anonymous_session"]["passed"] is True
