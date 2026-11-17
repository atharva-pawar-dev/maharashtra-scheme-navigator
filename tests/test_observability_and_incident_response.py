"""Tests for WS8: Observability, Health Probes, and Incident Response Redaction Canaries."""
from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.security.audit_logger import audit_logger
from scheme_navigator.security.models import AuditEventType

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def client():
    return TestClient(app)


# -------------------------------------------------------------------------
# 1. Health and Readiness Probes
# -------------------------------------------------------------------------

def test_liveness_probe_healthz(client):
    """Verify /healthz returns 200 OK with environment status."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "environment" in data


def test_readiness_probe_readyz(client):
    """Verify /readyz returns 200 with catalogue and storage readiness."""
    resp = client.get("/readyz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["schemes_loaded"] > 0
    assert data["storage_ready"] is True
    assert "environment" in data


# -------------------------------------------------------------------------
# 2. Redaction Canaries & Structured Logging
# -------------------------------------------------------------------------

def test_audit_logger_redaction_canaries():
    """Verify PII (Aadhaar numbers), passwords, and security tokens are redacted in audit logs."""
    canary_details = {
        "user_aadhaar_number": "9876-5432-1098",
        "auth_password": "TopSecretProductionPassword!123",
        "api_secret_key": "sec_prod_key_must_not_leak_9999",
        "normal_field": "Scholarship eligibility check",
        "raw_identity_number": "1234 5678 9012",
    }
    event = audit_logger.log_event(
        event_type=AuditEventType.SECURITY_VIOLATION,
        actor_id="test_canary_actor",
        actor_role="citizen",
        action="canary_redaction_test",
        resource="test_resource",
        details=canary_details,
    )

    details = event.details
    # Key-based redactions
    assert details["user_aadhaar_number"] == "[REDACTED]"
    assert details["auth_password"] == "[REDACTED]"
    assert details["api_secret_key"] == "[REDACTED]"

    # Pattern-based value redaction for 12-digit Aadhaar pattern
    assert details["raw_identity_number"] == "[REDACTED_AADHAAR]"

    # Safe public fields must NOT be redacted
    assert details["normal_field"] == "Scholarship eligibility check"
