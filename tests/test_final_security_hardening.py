from __future__ import annotations

import io
import os
import socket
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
import httpcore
import httpx

from scheme_navigator.api.main import app
from scheme_navigator.core.config import settings
from scheme_navigator.documents.review_store import DocumentReviewStore
from scheme_navigator.agents.interview_store import InterviewSessionStore
from scheme_navigator.ingestion.pipeline import ingest_public_source
from scheme_navigator.security.auth import SessionManager, session_manager
from scheme_navigator.security.models import UserRole, UserSession
from scheme_navigator.security.rate_limiter import InMemoryRateLimiter, rate_limiter
from scheme_navigator.security.retention import purge_expired_data
from scheme_navigator.security.ssrf import (
    SSRFSafeSyncBackend,
    SSRFSafeTransport,
    is_private_or_loopback_ip,
    validate_safe_url,
)


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. ADMIN BOOTSTRAP, SHORT PRIVILEGED TTL, REVOCATION & SECRET ROTATION
# ==============================================================================


def test_admin_bootstrap_one_time_only(client, monkeypatch):
    """Initial admin bootstrap can only be executed once; subsequent calls return 403."""
    bootstrap_secret = "super-secret-bootstrap-key-with-over-32-characters-entropy"
    monkeypatch.setenv("ADMIN_BOOTSTRAP_KEY", bootstrap_secret)
    monkeypatch.setattr(settings, "admin_bootstrap_key", bootstrap_secret)
    session_manager.reset_bootstrap()

    # 1. Initial bootstrap succeeds
    res1 = client.post(
        "/admin/auth/provision",
        headers={"X-Admin-Bootstrap-Key": bootstrap_secret},
        json={"role": "catalogue_admin", "user_id": "root_admin_1"},
    )
    assert res1.status_code == 200, res1.text
    data1 = res1.json()
    assert data1["role"] == "catalogue_admin"
    assert data1["user_id"] == "root_admin_1"
    token1 = data1["token"]

    # Verify session has short privileged TTL (default 1 hour)
    expires_at = datetime.fromisoformat(data1["expires_at"])
    now = datetime.now(timezone.utc)
    delta_hours = (expires_at - now).total_seconds() / 3600
    assert 0.8 <= delta_hours <= 1.2

    # 2. Second bootstrap attempt is strictly blocked (even with valid key)
    res2 = client.post(
        "/admin/auth/provision",
        headers={"X-Admin-Bootstrap-Key": bootstrap_secret},
        json={"role": "catalogue_admin", "user_id": "second_admin_attempt"},
    )
    assert res2.status_code == 403
    assert "Bootstrap disabled" in res2.json()["detail"]

    # 3. Invalid bootstrap key is blocked
    session_manager.reset_bootstrap()
    res3 = client.post(
        "/admin/auth/provision",
        headers={"X-Admin-Bootstrap-Key": "wrong-secret-key-attempt"},
        json={"role": "catalogue_admin", "user_id": "attacker"},
    )
    assert res3.status_code == 403
    assert "Invalid administrative bootstrap key" in res3.json()["detail"]


def test_admin_provision_user_and_revocation(client, monkeypatch):
    """Active catalogue admin can provision users and revoke sessions; revoked tokens fail."""
    bootstrap_secret = "super-secret-bootstrap-key-with-over-32-characters-entropy"
    monkeypatch.setenv("ADMIN_BOOTSTRAP_KEY", bootstrap_secret)
    monkeypatch.setattr(settings, "admin_bootstrap_key", bootstrap_secret)
    session_manager.reset_bootstrap()

    # Bootstrap initial admin
    res_boot = client.post(
        "/admin/auth/provision",
        headers={"X-Admin-Bootstrap-Key": bootstrap_secret},
        json={"role": "catalogue_admin", "user_id": "superadmin"},
    )
    assert res_boot.status_code == 200, res_boot.text
    admin_token = res_boot.json()["token"]

    # 1. Active admin provisions a legal reviewer
    res_prov = client.post(
        "/admin/auth/provision-user",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "legal_reviewer", "user_id": "advocate_shinde"},
    )
    assert res_prov.status_code == 200, res_prov.text
    rev_data = res_prov.json()
    assert rev_data["role"] == "legal_reviewer"
    rev_token = rev_data["token"]
    rev_session_id = rev_data["session_id"]

    # Verify reviewer token works on /auth/me
    res_me = client.get("/auth/me", headers={"Authorization": f"Bearer {rev_token}"})
    assert res_me.status_code == 200
    assert res_me.json()["user_id"] == "advocate_shinde"

    # 2. Citizen cannot provision users
    citizen_session, citizen_token = session_manager.create_session(role=UserRole.CITIZEN, user_id="cit_1")
    res_unauth_prov = client.post(
        "/admin/auth/provision-user",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={"role": "analyst", "user_id": "rogue_analyst"},
    )
    assert res_unauth_prov.status_code == 403

    # 3. Admin revokes the legal reviewer's session
    res_revoke = client.post(
        "/admin/auth/revoke",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"session_id": rev_session_id},
    )
    assert res_revoke.status_code == 200
    assert res_revoke.json()["status"] == "revoked"

    # 4. Revoked token is immediately rejected
    assert session_manager.validate_token(rev_token) is None
    res_me_revoked = client.get("/auth/me", headers={"Authorization": f"Bearer {rev_token}"})
    # Since anonymous session fallback triggers on invalid token, role must be citizen, not legal_reviewer
    assert res_me_revoked.json()["role"] == "citizen"


def test_secret_rotation_invalidates_all_prior_tokens():
    """Rotating HMAC secret key invalidates previously signed tokens."""
    sm = SessionManager(secret_key=b"initial-secret-key-32-bytes-length!")
    session, token = sm.create_session(role=UserRole.CITIZEN, user_id="user_pre_rotation")
    assert sm.validate_token(token) is not None

    # Rotate secret
    sm.rotate_secret(b"brand-new-rotated-secret-key-32bytes!")

    # Old token fails HMAC verification
    assert sm.validate_token(token) is None


# ==============================================================================
# 2. SSRF DNS REBINDING & CONNECTION PINNING
# ==============================================================================


def test_ssrf_sync_backend_blocks_dns_rebinding_to_loopback_and_private():
    """SSRFSafeSyncBackend checks every resolved address at connection time."""
    backend = SSRFSafeSyncBackend()

    # Case A: DNS returns loopback IPv4
    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 443))
        ]
        with pytest.raises(httpcore.ConnectError, match="SSRF violation.*forbidden private/internal IP"):
            backend.connect_tcp("gr.maharashtra.gov.in", 443)

    # Case B: DNS returns private IPv4 (10.0.0.1)
    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("10.0.0.1", 443))
        ]
        with pytest.raises(httpcore.ConnectError, match="SSRF violation.*forbidden private/internal IP"):
            backend.connect_tcp("gr.maharashtra.gov.in", 443)

    # Case C: DNS returns IPv6 loopback (::1)
    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [
            (socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("::1", 443, 0, 0))
        ]
        with pytest.raises(httpcore.ConnectError, match="SSRF violation.*forbidden private/internal IP"):
            backend.connect_tcp("gr.maharashtra.gov.in", 443)

    # Case D: DNS returns mixed addresses where one is internal
    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("192.168.1.1", 443)),
        ]
        with pytest.raises(httpcore.ConnectError, match="SSRF violation.*forbidden private/internal IP"):
            backend.connect_tcp("gr.maharashtra.gov.in", 443)


def test_ssrf_transport_integration_with_httpx():
    """HTTPX client using SSRFSafeTransport prevents connection to rebinded hosts."""
    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 443))
        ]
        client = httpx.Client(transport=SSRFSafeTransport(), timeout=5)
        with pytest.raises(httpx.ConnectError, match="SSRF violation"):
            client.get("https://gr.maharashtra.gov.in/test.pdf")


# ==============================================================================
# 3. RETENTION VERIFICATION & SQLITE WAL/SHM PROTECTION
# ==============================================================================


def test_retention_purge_protects_sqlite_wal_and_shm_files(tmp_path: Path):
    """Temporary file purge removes expired temp files but NEVER deletes SQLite databases, WAL, or SHM files."""
    temp_dir = tmp_path / "temp_uploads"
    temp_dir.mkdir()

    # Create dummy files
    normal_temp = temp_dir / "uploaded_doc_old.pdf"
    normal_temp.write_bytes(b"%PDF-1.4 test")

    sqlite_db = temp_dir / "interviews.sqlite3"
    sqlite_db.write_bytes(b"SQLite format 3\x00")

    sqlite_wal = temp_dir / "interviews.sqlite3-wal"
    sqlite_wal.write_bytes(b"wal-bytes")

    sqlite_shm = temp_dir / "interviews.sqlite3-shm"
    sqlite_shm.write_bytes(b"shm-bytes")

    other_wal = temp_dir / "custom.wal"
    other_wal.write_bytes(b"wal-bytes-2")

    # Age files past retention cutoff (48 hours ago)
    old_time = time.time() - (48 * 3600)
    for p in (normal_temp, sqlite_db, sqlite_wal, sqlite_shm, other_wal):
        os.utime(str(p), (old_time, old_time))

    # Run purge with 24 hour retention
    result = purge_expired_data(retention_hours=24, temp_dir=temp_dir)

    # Normal temp PDF is purged
    assert not normal_temp.exists()
    assert result["purged_files"] == 1

    # SQLite files, WAL, and SHM files are strictly preserved
    assert sqlite_db.exists()
    assert sqlite_wal.exists()
    assert sqlite_shm.exists()
    assert other_wal.exists()


def test_document_review_cascading_purge_and_retrieval(tmp_path: Path):
    """Expired review records and all their associated audit events cascade-delete."""
    db_path = tmp_path / "test_reviews.sqlite3"
    store = DocumentReviewStore(db_path=db_path, retention_hours=1)

    record = store.create_review(
        is_pdf=False,
        source_file_sha256="abc" * 20,
        target_financial_year="2026-27",
        extracted_documents=[{"document_id": "d1", "person_name": "Applicant"}],
        page_extractions=[],
        document_groups=[],
        audit={"status": "ok", "findings": []},
    )
    review_id = record["review_id"]

    # Append an audit event directly in the SQLite database
    now_iso = datetime.now(timezone.utc).isoformat()
    with store._connect() as conn:
        conn.execute(
            """
            INSERT INTO document_review_events (
                review_id, action, reviewer_id, document_id, field_name,
                original_value_json, previous_value_json, new_value_json,
                note, page_numbers_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id, "field_corrected", "reviewer_1", "d1", "person_name",
                '"Applicant"', '"Applicant"', '"Corrected Applicant"',
                "Fixed name", "[]", now_iso,
            ),
        )

    # Verify review and event exist
    with store._connect() as conn:
        rev_count = conn.execute("SELECT COUNT(*) FROM document_reviews").fetchone()[0]
        evt_count = conn.execute("SELECT COUNT(*) FROM document_review_events").fetchone()[0]
        assert rev_count == 1
        assert evt_count == 1

    # Age record past expiry
    past_iso = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    with store._connect() as conn:
        conn.execute("UPDATE document_reviews SET expires_at = ?", (past_iso,))

    # Purge expired
    purged_count = store.purge_expired()
    assert purged_count == 1

    # Verify record and cascading events are gone
    assert store.get_review(review_id) is None
    with store._connect() as conn:
        rev_count = conn.execute("SELECT COUNT(*) FROM document_reviews").fetchone()[0]
        evt_count = conn.execute("SELECT COUNT(*) FROM document_review_events").fetchone()[0]
        assert rev_count == 0
        assert evt_count == 0


def test_interview_store_purge_on_restart(tmp_path: Path):
    """Interview store purges expired sessions on startup/restart."""
    db_path = tmp_path / "test_interviews.sqlite3"
    store1 = InterviewSessionStore(db_path=db_path, retention_hours=1)
    store1.create_session("thread_alpha")
    assert store1.is_active("thread_alpha")

    # Age session past expiry
    past_iso = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    with store1._metadata_connection:
        store1._metadata_connection.execute(
            "UPDATE interview_sessions SET expires_at = ? WHERE thread_id = ?",
            (past_iso, "thread_alpha"),
        )
    store1.close()

    # Simulate restart by instantiating new store on same database
    store2 = InterviewSessionStore(db_path=db_path, retention_hours=1)
    assert store2.last_purge_count >= 1
    assert not store2.is_active("thread_alpha")
    store2.close()


# ==============================================================================
# 4. REVIEWER & ADMIN ACCESS CONTROL
# ==============================================================================


def test_citizen_cannot_access_reviewer_endpoints(client):
    """Citizens cannot access /reviewer dashboard or document review CRUD endpoints."""
    citizen_session, citizen_token = session_manager.create_session(role=UserRole.CITIZEN, user_id="citizen_xyz")
    auth_header = {"Authorization": f"Bearer {citizen_token}"}

    # 1. GET /reviewer dashboard returns 403
    res_dash = client.get("/reviewer", headers=auth_header)
    assert res_dash.status_code == 403
    assert "citizen accounts are not authorized" in res_dash.json()["detail"]

    # 2. GET /documents/reviews/{id} returns 403
    res_get = client.get("/documents/reviews/rev_sample_123", headers=auth_header)
    assert res_get.status_code == 403
    assert "citizen accounts are not authorized" in res_get.json()["detail"]

    # 3. PATCH /documents/reviews/{id}/documents/{doc_id} returns 403
    res_patch = client.patch(
        "/documents/reviews/rev_sample_123/documents/doc_1",
        headers=auth_header,
        json={
            "reviewer_id": "attacker",
            "note": "fraudulent attempt",
            "corrections": {"annual_family_income": 100000},
        },
    )
    assert res_patch.status_code == 403
    assert "citizen accounts are not authorized" in res_patch.json()["detail"]

    # 4. DELETE /documents/reviews/{id} returns 403
    res_del = client.delete("/documents/reviews/rev_sample_123", headers=auth_header)
    assert res_del.status_code == 403
    assert "citizen accounts are not authorized" in res_del.json()["detail"]


def test_production_unauthenticated_reviewer_access_rejected(client, monkeypatch):
    """In production mode, unauthenticated access to reviewer UI and API is rejected with 403."""
    auth_secret = "super-secret-auth-key-32-characters-minimum!"
    monkeypatch.setenv("SCHEME_NAVIGATOR_AUTH_SECRET", auth_secret)
    monkeypatch.setattr(settings, "scheme_navigator_auth_secret", auth_secret)
    monkeypatch.setattr(settings, "app_env", "production")

    # Unauthenticated /reviewer
    res_ui = client.get("/reviewer")
    assert res_ui.status_code == 403
    assert "requires authenticated reviewer access" in res_ui.json()["detail"]

    # Unauthenticated /documents/reviews/{id}
    res_api = client.get("/documents/reviews/rev_sample_123")
    assert res_api.status_code == 403
    assert "requires authenticated reviewer access" in res_api.json()["detail"]


# ==============================================================================
# 5. RATE LIMITING ACROSS SENSITIVE ROUTES
# ==============================================================================


def test_rate_limiter_sensitive_routes_trigger_429(client):
    """Exceeding request limits triggers HTTP 429 with Retry-After header."""
    rate_limiter.reset()

    # Route: POST /auth/session limit is 20/min
    for _ in range(20):
        res = client.post("/auth/session")
        assert res.status_code == 200

    # 21st request triggers 429
    res_throttled = client.post("/auth/session")
    assert res_throttled.status_code == 429
    assert "Retry-After" in res_throttled.headers
    assert int(res_throttled.headers["Retry-After"]) >= 1
    assert "Rate limit exceeded" in res_throttled.json()["detail"]
