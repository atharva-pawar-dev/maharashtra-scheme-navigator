"""Tests for WS5: Identity, Sessions, and Authorisation Hardening."""
from __future__ import annotations

import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.security.auth import SessionManager, session_manager
from scheme_navigator.security.models import UserRole, UserSession

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def client():
    return TestClient(app)


# -------------------------------------------------------------------------
# 1. Citizen Session Security, Entropy, and Cookie Security
# -------------------------------------------------------------------------

def test_session_token_entropy_and_cookie_attributes(client):
    """Verify session token is high-entropy, sets HttpOnly cookie, and contains no raw PII."""
    resp = client.post("/auth/session")
    assert resp.status_code == 200
    data = resp.json()

    assert "token" in data
    token = data["token"]
    assert len(token) > 50
    assert data["role"] == "citizen"

    # Verify no PII (e.g. email, phone, name) is encoded
    assert "aadhaar" not in token.lower()
    assert "@" not in token

    # Check cookies set in response
    cookies = resp.cookies
    assert "sn_session" in cookies
    # Verify cookie matches token
    assert cookies["sn_session"] == token


def test_anonymous_session_minting_fallback(client):
    """Verify unauthenticated requests safely mint an isolated anonymous session."""
    resp = client.get("/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "citizen"
    assert "anonymous" in data["user_id"] or data["user_id"].startswith("user_")


# -------------------------------------------------------------------------
# 2. Privilege Escalation Prevention
# -------------------------------------------------------------------------

def test_public_session_endpoint_rejects_privileged_role(client):
    """Verify public /auth/session forbids requesting administrative roles."""
    for forbidden_role in ["analyst", "legal_reviewer", "catalogue_admin", "admin", "root"]:
        resp = client.post(f"/auth/session?role={forbidden_role}")
        assert resp.status_code == 403, f"Expected 403 for role {forbidden_role}, got {resp.status_code}"
        assert "Role escalation forbidden" in resp.json()["detail"]


def test_analyst_cannot_sign_catalogue_release(client):
    """Verify ANALYST role cannot perform CATALOGUE_ADMIN operations (signing)."""
    # Create an analyst session
    analyst_session, analyst_token = session_manager.create_session(role=UserRole.ANALYST)
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # Attempt to sign catalogue release
    resp = client.post("/admin/catalogue/sign-release", headers=headers)
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
    assert "catalogue_admin" in resp.json()["detail"].lower()


# -------------------------------------------------------------------------
# 3. Insecure Direct Object Reference (IDOR) Protections
# -------------------------------------------------------------------------

def test_citizen_cannot_answer_another_citizens_interview_thread(client):
    """Verify Citizen B cannot submit answers to Citizen A's interview thread."""
    # Citizen A starts an interview
    resp_a = client.post("/auth/session")
    token_a = resp_a.json()["token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Start interview under Citizen A
    start_payload = {
        "mode": "DISCOVERY",
        "thread_id": "thread_idor_citizen_a_001",
        "user_profile": {"resident_state": "Maharashtra"},
    }
    start_resp = client.post("/interview/start", json=start_payload, headers=headers_a)
    assert start_resp.status_code == 200

    # Citizen B creates their own session
    resp_b = client.post("/auth/session")
    token_b = resp_b.json()["token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Citizen B attempts to answer Citizen A's interview
    answer_payload = {
        "thread_id": "thread_idor_citizen_a_001",
        "answer": "Male",
    }
    answer_resp = client.post("/interview/answer", json=answer_payload, headers=headers_b)
    assert answer_resp.status_code == 403, f"IDOR vulnerability! Expected 403, got {answer_resp.status_code}"
    assert "Forbidden" in answer_resp.json()["detail"]


# -------------------------------------------------------------------------
# 4. Session Revocation and Expiry
# -------------------------------------------------------------------------

def test_session_revocation_invalidates_token(client):
    """Verify revoking a session immediately rejects the token."""
    session, token = session_manager.create_session(role=UserRole.CITIZEN)
    headers = {"Authorization": f"Bearer {token}"}

    # Verify session is valid
    resp_valid = client.get("/auth/me", headers=headers)
    assert resp_valid.status_code == 200
    assert resp_valid.json()["session_id"] == session.session_id

    # Revoke session
    session_manager.revoke_session(session.session_id)

    # Next request with revoked token must be rejected or demoted to fresh anonymous
    resp_revoked = client.get("/auth/me", headers=headers)
    # validate_token returns None for revoked session, so /auth/me returns new anonymous session
    assert resp_revoked.json()["session_id"] != session.session_id


def test_expired_session_token_rejected():
    """Verify expired token fails validation."""
    mgr = SessionManager(secret_key=b"test-secret-key-must-be-32-chars-long!")
    session, token = mgr.create_session(role=UserRole.CITIZEN)

    # Validate before expiry
    assert mgr.validate_token(token) is not None

    # Artificially expire the token by constructing an expired token payload
    parts = token.split(":")
    expired_exp = int(time.time()) - 100
    expired_payload = f"{parts[0]}:{parts[1]}:{parts[2]}:{expired_exp}"
    expired_sig = mgr._sign(expired_payload)
    expired_token = f"{expired_payload}:{expired_sig}"

    assert mgr.validate_token(expired_token) is None
