from __future__ import annotations

import io
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.security.audit_logger import audit_logger
from scheme_navigator.security.auth import SessionManager, session_manager
from scheme_navigator.security.models import AuditEventType, UserRole
from scheme_navigator.security.publication import (
    PublicationAuthorizationError,
    publication_manager,
)
from scheme_navigator.security.rate_limiter import InMemoryRateLimiter
from scheme_navigator.security.retention import purge_expired_data
from scheme_navigator.security.ssrf import validate_safe_url
from scheme_navigator.security.upload import (
    sanitize_filename,
    validate_uploaded_document_security,
)


def test_session_manager_hmac_and_tamper_resistance():
    sm = SessionManager(secret_key=b"test-secret-key-32-bytes-minimum-entropy")
    session, token = sm.create_session(role=UserRole.CITIZEN, user_id="user_123")

    # 1. Valid token validates successfully
    val = sm.validate_token(token)
    assert val is not None
    assert val.user_id == "user_123"
    assert val.role == UserRole.CITIZEN

    # 2. Tampered signature fails
    parts = token.split(":")
    tampered_sig = parts[:-1] + ["invalid_signature_xyz"]
    assert sm.validate_token(":".join(tampered_sig)) is None

    # 3. Privilege escalation attempt (altering role in payload) fails
    escalated = [parts[0], parts[1], UserRole.CATALOGUE_ADMIN.value, parts[3], parts[4]]
    assert sm.validate_token(":".join(escalated)) is None

    # 4. Session ownership
    sm.bind_thread_to_session(session.session_id, "thread-alpha")
    assert sm.authorize_thread_access(session, "thread-alpha") is True
    assert sm.authorize_thread_access(session, "thread-beta-other-citizen") is False


def test_rbac_endpoint_access_control():
    client = TestClient(app)

    # 1. Anonymous / Citizen accessing admin endpoint gets 403 Forbidden
    resp_unauth = client.post("/admin/catalogue/sign-release?version=1.0.0")
    assert resp_unauth.status_code == 403
    assert "Access denied" in resp_unauth.json()["detail"]

    # 2. Create admin session
    admin_sess, admin_token = session_manager.create_session(
        role=UserRole.CATALOGUE_ADMIN, user_id="admin_user_01"
    )

    # 3. Admin accessing sign-release succeeds (with demo catalog or active catalog)
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp_admin = client.post("/admin/catalogue/sign-release?version=1.0.0", headers=headers)
    assert resp_admin.status_code == 200
    sig_data = resp_admin.json()
    assert sig_data["catalogue_version"] == "1.0.0"
    assert sig_data["signed_by_admin"] == "admin_user_01"
    assert "DOES NOT constitute official government endorsement" in sig_data["provenance_declaration"]

    # 4. Analyst accessing audit logs succeeds; Citizen gets 403
    analyst_sess, analyst_token = session_manager.create_session(
        role=UserRole.ANALYST, user_id="analyst_01"
    )
    resp_logs_analyst = client.get("/admin/audit-logs", headers={"Authorization": f"Bearer {analyst_token}"})
    assert resp_logs_analyst.status_code == 200
    assert isinstance(resp_logs_analyst.json(), list)

    citizen_sess, citizen_token = session_manager.create_session(role=UserRole.CITIZEN)
    resp_logs_citizen = client.get("/admin/audit-logs", headers={"Authorization": f"Bearer {citizen_token}"})
    assert resp_logs_citizen.status_code == 403


def test_ssrf_protection_and_allowlist():
    # 1. Valid official government URL succeeds
    valid_url = "https://gr.maharashtra.gov.in/Site/Upload/GR/20240628.pdf"
    assert validate_safe_url(valid_url) == valid_url

    valid_portal = "https://aaplesarkar.mahaonline.gov.in/en/CommonForm/CitizenServices"
    assert validate_safe_url(valid_portal) == valid_portal

    # 2. HTTP is rejected (only HTTPS allowed)
    with pytest.raises(ValueError, match="Only secure HTTPS"):
        validate_safe_url("http://gr.maharashtra.gov.in/test.pdf")

    # 3. Private IP addresses and loopback rejected
    with pytest.raises(ValueError, match="Private IP|Access to local"):
        validate_safe_url("https://127.0.0.1:8000/admin")

    with pytest.raises(ValueError, match="Private IP|Access to local"):
        validate_safe_url("https://10.0.0.5/api")

    with pytest.raises(ValueError, match="Private IP|Access to local"):
        validate_safe_url("https://192.168.1.100/router")

    # 4. Cloud metadata IP rejected
    with pytest.raises(ValueError, match="Private IP|Access to local"):
        validate_safe_url("https://169.254.169.254/computeMetadata/v1/")

    # 5. Non-allowlisted external domain rejected
    with pytest.raises(ValueError, match="not in the official government allowlist"):
        validate_safe_url("https://malicious-external-site.com/exploit.pdf")

    # 6. Blocked ports rejected
    with pytest.raises(ValueError, match="port 6333 is blocked"):
        validate_safe_url("https://gr.maharashtra.gov.in:6333/api")


def test_upload_security_and_magic_bytes():
    # 1. Valid PDF with proper magic bytes passes
    valid_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    fname, mime = validate_uploaded_document_security(valid_pdf_bytes, "valid_cert.pdf", "application/pdf")
    assert fname == "valid_cert.pdf"
    assert mime == "application/pdf"

    # 2. Path traversal in filename is sanitized
    fname2, _ = validate_uploaded_document_security(valid_pdf_bytes, "../../etc/passwd", "application/pdf")
    assert fname2 == "passwd"
    assert ".." not in fname2

    fname3, _ = validate_uploaded_document_security(valid_pdf_bytes, "..\\..\\boot.ini", "application/pdf")
    assert ".." not in fname3

    # 3. Executable extensions rejected
    with pytest.raises(ValueError, match="extension '.exe' is forbidden"):
        validate_uploaded_document_security(valid_pdf_bytes, "malware.exe")

    with pytest.raises(ValueError, match="extension '.svg' is forbidden"):
        validate_uploaded_document_security(valid_pdf_bytes, "xss_vector.svg")

    # 4. Forged file (plain text pretending to be PDF) rejected by magic bytes
    fake_pdf_bytes = b"Hello world, I am just a plain text file pretending to be a PDF"
    with pytest.raises(ValueError, match="unrecognized or forged file header"):
        validate_uploaded_document_security(fake_pdf_bytes, "fake.pdf", "application/pdf")


def test_rate_limiter_throttling():
    limiter = InMemoryRateLimiter()
    key = "client-ip-test"

    # Allow up to 3 requests per 10 seconds
    assert limiter.check_limit(key, max_requests=3, window_seconds=10)[0] is True
    assert limiter.check_limit(key, max_requests=3, window_seconds=10)[0] is True
    assert limiter.check_limit(key, max_requests=3, window_seconds=10)[0] is True

    # 4th request must be throttled
    allowed, retry_after = limiter.check_limit(key, max_requests=3, window_seconds=10)
    assert allowed is False
    assert retry_after > 0


def test_audit_logging_and_sensitive_data_redaction():
    event = audit_logger.log_event(
        event_type=AuditEventType.AUTH_LOGIN,
        actor_id="user_test_99",
        actor_role="citizen",
        action="login",
        resource="session_endpoint",
        client_ip="192.0.2.1",
        details={
            "declared_aadhaar": "123456789012",
            "password_hash": "secret_pwd",
            "safe_detail": "regular_info",
        },
    )

    # Sensitive fields must be redacted
    assert event.details["declared_aadhaar"] == "[REDACTED]"
    assert event.details["password_hash"] == "[REDACTED]"
    assert event.details["safe_detail"] == "regular_info"


def test_monitoring_probes():
    client = TestClient(app)

    # Liveness probe
    resp_health = client.get("/healthz")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "ok"

    # Readiness probe
    resp_ready = client.get("/readyz")
    assert resp_ready.status_code == 200
    ready_data = resp_ready.json()
    assert "status" in ready_data
    assert "schemes_loaded" in ready_data
    assert "environment" in ready_data
