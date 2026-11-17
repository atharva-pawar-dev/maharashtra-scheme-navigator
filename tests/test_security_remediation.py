from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from scheme_navigator.agents.interview_store import InterviewSessionStore
from scheme_navigator.api.main import app
from scheme_navigator.core.config import Settings
from scheme_navigator.documents.review_store import DocumentReviewStore
from scheme_navigator.domain.models import Language
from scheme_navigator.security.auth import session_manager
from scheme_navigator.security.models import UserRole
from scheme_navigator.security.rate_limiter import rate_limiter
from scheme_navigator.security.retention import purge_expired_data
from scheme_navigator.security.ssrf import validate_safe_url
from scheme_navigator.security.upload import validate_uploaded_audio_security


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. AUTHENTICATION & ROLE ESCALATION
# ==============================================================================

def test_public_session_creation_rejects_privileged_roles(client: TestClient):
    """Public /auth/session endpoint must strictly reject client-supplied administrative roles."""
    # Attempt role escalation to catalogue_admin
    res_admin = client.post("/auth/session?role=catalogue_admin")
    assert res_admin.status_code == 403
    assert "Role escalation forbidden" in res_admin.json()["detail"]

    # Attempt role escalation to analyst
    res_analyst = client.post("/auth/session?role=analyst")
    assert res_analyst.status_code == 403
    assert "Role escalation forbidden" in res_analyst.json()["detail"]

    # Ordinary session creation defaults to CITIZEN
    res_citizen = client.post("/auth/session")
    assert res_citizen.status_code == 200
    data = res_citizen.json()
    assert data["role"] == "citizen"
    assert "token" in data
    assert data["session_id"]


def test_admin_auth_provisioning_requires_valid_bootstrap_key(client: TestClient, monkeypatch):
    """Privileged sessions can ONLY be provisioned via /admin/auth/provision with ADMIN_BOOTSTRAP_KEY."""
    bootstrap_secret = "super-secret-bootstrap-key-with-over-32-characters-entropy"
    monkeypatch.setenv("ADMIN_BOOTSTRAP_KEY", bootstrap_secret)

    # 1. Missing bootstrap key header -> 403
    res_no_key = client.post(
        "/admin/auth/provision",
        json={"role": "catalogue_admin", "user_id": "admin_ops_1"},
    )
    assert res_no_key.status_code == 403

    # 2. Invalid bootstrap key -> 403
    res_wrong_key = client.post(
        "/admin/auth/provision",
        headers={"X-Admin-Bootstrap-Key": "incorrect-secret-key-attempt"},
        json={"role": "catalogue_admin", "user_id": "admin_ops_1"},
    )
    assert res_wrong_key.status_code == 403

    # 3. Valid bootstrap key -> 200 with provisioned role
    res_valid = client.post(
        "/admin/auth/provision",
        headers={"X-Admin-Bootstrap-Key": bootstrap_secret},
        json={"role": "catalogue_admin", "user_id": "admin_ops_1"},
    )
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert data["role"] == "catalogue_admin"
    assert data["user_id"] == "admin_ops_1"
    assert "token" in data


def test_admin_auth_provisioning_fails_closed_when_unconfigured(client: TestClient, monkeypatch):
    """If ADMIN_BOOTSTRAP_KEY is missing or weak, provisioning fails closed with 503."""
    monkeypatch.delenv("ADMIN_BOOTSTRAP_KEY", raising=False)
    monkeypatch.setattr("scheme_navigator.core.config.settings.admin_bootstrap_key", None)

    res = client.post(
        "/admin/auth/provision",
        headers={"X-Admin-Bootstrap-Key": "some-key"},
        json={"role": "analyst"},
    )
    assert res.status_code == 503
    assert "Administrative provisioning is disabled" in res.json()["detail"]


# ==============================================================================
# 2. INTERVIEW THREAD OWNERSHIP & CROSS-SESSION ACCESS
# ==============================================================================

def test_interview_thread_ownership_isolation(client: TestClient):
    """Citizen A's interview thread cannot be answered or read by Citizen B or unauthenticated callers."""
    rate_limiter.reset()
    # Create Citizen A session
    res_a = client.post("/auth/session?role=citizen")
    assert res_a.status_code == 200
    token_a = res_a.json()["token"]

    # Create Citizen B session
    res_b = client.post("/auth/session?role=citizen")
    assert res_b.status_code == 200
    token_b = res_b.json()["token"]

    thread_alice = "thread-alice-isolated-001"

    # Citizen A starts interview
    start_res = client.post(
        "/interview/start",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "thread_id": thread_alice,
            "language": "en",
            "profile": {"resident_state": "Maharashtra"},
        },
    )
    assert start_res.status_code == 200
    assert start_res.json()["thread_id"] == thread_alice

    # 1. Citizen B attempts to answer Citizen A's thread -> 403 Forbidden
    b_ans = client.post(
        "/interview/answer",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"thread_id": thread_alice, "answer": "25", "language": "en"},
    )
    assert b_ans.status_code == 403
    assert "Forbidden" in b_ans.json()["detail"]

    # 2. Unauthenticated caller attempts to answer Citizen A's thread -> 403 Forbidden
    anon_ans = client.post(
        "/interview/answer",
        json={"thread_id": thread_alice, "answer": "25", "language": "en"},
    )
    assert anon_ans.status_code == 403

    # 3. Unauthenticated caller attempts to read Citizen A's thread state -> 403 Forbidden
    anon_read = client.get(f"/interview/{thread_alice}")
    assert anon_read.status_code == 403

    # 4. Citizen B attempts to read Citizen A's thread state -> 403 Forbidden
    b_read = client.get(
        f"/interview/{thread_alice}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_read.status_code == 403

    # 5. Citizen A successfully reads and answers their own thread -> 200 OK
    a_read = client.get(
        f"/interview/{thread_alice}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert a_read.status_code == 200

    a_ans = client.post(
        "/interview/answer",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"thread_id": thread_alice, "answer": "25", "language": "en"},
    )
    assert a_ans.status_code == 200


# ==============================================================================
# 3. REVIEWER DASHBOARD ACCESS AND RBAC
# ==============================================================================

def test_reviewer_dashboard_and_review_endpoints_rbac(client: TestClient, monkeypatch):
    """Citizens cannot access reviewer endpoints. In production, unauthenticated requests are rejected."""
    # Create citizen session
    res_cit = client.post("/auth/session?role=citizen")
    token_cit = res_cit.json()["token"]

    # 1. Citizen trying to access /reviewer -> 403
    res_dash = client.get(
        "/reviewer",
        headers={"Authorization": f"Bearer {token_cit}"},
    )
    assert res_dash.status_code == 403
    assert "citizen accounts are not authorized" in res_dash.json()["detail"].lower()

    # 2. Citizen trying to inspect a document review -> 403
    res_rev = client.get(
        "/documents/reviews/rev-123",
        headers={"Authorization": f"Bearer {token_cit}"},
    )
    assert res_rev.status_code == 403
    assert "citizen accounts are not authorized" in res_rev.json()["detail"].lower()

    # 3. Citizen trying to delete a review -> 403
    res_del = client.delete(
        "/documents/reviews/rev-123",
        headers={"Authorization": f"Bearer {token_cit}"},
    )
    assert res_del.status_code == 403

    # 4. In production, unauthenticated /reviewer -> 403
    monkeypatch.setattr("scheme_navigator.core.config.settings.app_env", "production")
    res_prod_anon = client.get("/reviewer")
    assert res_prod_anon.status_code == 403


# ==============================================================================
# 4. RATE LIMITING ENFORCEMENT
# ==============================================================================

def test_rate_limiting_enforcement(client: TestClient):
    """Rapid successive calls to rate-limited endpoints trigger HTTP 429 with Retry-After header."""
    # Endpoint: /auth/session limit is 20 requests per 60 seconds
    responses = [client.post("/auth/session") for _ in range(25)]
    status_codes = [r.status_code for r in responses]

    # At least some requests after 20 must return 429
    assert 429 in status_codes
    rate_limited_res = next(r for r in responses if r.status_code == 429)
    assert "Retry-After" in rate_limited_res.headers
    assert "Rate limit exceeded" in rate_limited_res.json()["detail"]


# ==============================================================================
# 5. DATA RETENTION & SQLITE PURGE
# ==============================================================================

def test_retention_purge_cleans_sqlite_stores(tmp_path: Path):
    """purge_expired_data removes expired records from InterviewSessionStore and DocumentReviewStore."""
    interview_db = tmp_path / "test_interviews.sqlite3"
    review_db = tmp_path / "test_reviews.sqlite3"

    # Initialize interview store and add expired row
    int_store = InterviewSessionStore(db_path=interview_db, retention_hours=1)
    int_store.create_session("active_thread")
    with int_store._metadata_connection:
        int_store._metadata_connection.execute(
            "INSERT INTO interview_sessions (thread_id, created_at, last_activity_at, expires_at) "
            "VALUES ('expired_thread_1', '2020-01-01T00:00:00Z', '2020-01-01T00:00:00Z', '2020-01-01T01:00:00Z')"
        )
    int_store.close()

    # Initialize review store and add expired row
    rev_store = DocumentReviewStore(db_path=review_db, retention_hours=1)
    rev_store.create_review(
        is_pdf=False,
        source_file_sha256="fake_sha",
        target_financial_year="2026-27",
        extracted_documents=[],
        page_extractions=[],
        document_groups=[],
        audit={"findings": []},
    )
    with rev_store._connect() as conn:
        conn.execute(
            "INSERT INTO document_reviews (review_id, status, created_at, updated_at, expires_at, "
            "is_pdf, source_file_sha256, target_financial_year, original_documents_json, "
            "current_documents_json, original_page_extractions_json, current_page_extractions_json, "
            "original_document_groups_json, current_document_groups_json, original_audit_json, current_audit_json) "
            "VALUES ('expired_rev_1', 'pending_review', '2020-01-01T00:00:00Z', '2020-01-01T00:00:00Z', "
            "'2020-01-01T01:00:00Z', 0, 'sha', '2026-27', '[]', '[]', '[]', '[]', '[]', '[]', '{}', '{}')"
        )

    # Execute purge
    result = purge_expired_data(
        retention_hours=1,
        interview_db_path=interview_db,
        review_db_path=review_db,
    )

    assert result["purged_interviews"] >= 1
    assert result["purged_reviews"] >= 1

    with sqlite3.connect(interview_db) as conn:
        rows = conn.execute("SELECT thread_id FROM interview_sessions").fetchall()
        t_ids = [r[0] for r in rows]
        assert "expired_thread_1" not in t_ids
        assert "active_thread" in t_ids

    with sqlite3.connect(review_db) as conn:
        rows = conn.execute("SELECT review_id FROM document_reviews").fetchall()
        r_ids = [r[0] for r in rows]
        assert "expired_rev_1" not in r_ids


# ==============================================================================
# 6. SSRF AND DNS REBINDING PROTECTION
# ==============================================================================

def test_ssrf_and_dns_rebinding_protection():
    """validate_safe_url rejects private IPs, loopback, link-local, non-allowlisted domains, and non-HTTPS."""
    # 1. Plain HTTP rejected
    with pytest.raises(ValueError, match="Only secure HTTPS URLs are permitted"):
        validate_safe_url("http://gr.maharashtra.gov.in/test.pdf")

    # 2. Localhost & loopback rejected
    with pytest.raises(ValueError, match="blocked"):
        validate_safe_url("https://127.0.0.1/admin")

    with pytest.raises(ValueError, match="blocked"):
        validate_safe_url("https://localhost/admin")

    # 3. AWS / cloud metadata link-local rejected
    with pytest.raises(ValueError, match="blocked"):
        validate_safe_url("https://169.254.169.254/latest/meta-data")

    # 4. Private network IP ranges rejected
    with pytest.raises(ValueError, match="blocked"):
        validate_safe_url("https://10.0.0.5/secret")

    with pytest.raises(ValueError, match="blocked"):
        validate_safe_url("https://192.168.1.100/router")

    # 5. Non-allowlisted external domain rejected
    with pytest.raises(ValueError, match="not in the official government allowlist"):
        validate_safe_url("https://evil-phishing-site.com/exploit", enforce_allowlist=True)


# ==============================================================================
# 7. AUDIO MAGIC-BYTE VALIDATION
# ==============================================================================

def test_audio_magic_byte_validation(client: TestClient):
    """Audio upload endpoint rejects spoofed files and validates genuine audio container headers."""
    rate_limiter.reset()
    # 1. Spoofed executable pretending to be audio
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 50
    res_spoofed = client.post(
        "/voice/transcribe?provider=whisper&language=en",
        files={"file": ("recording.wav", fake_exe, "audio/wav")},
    )
    assert res_spoofed.status_code == 400
    assert "Upload security check failed" in res_spoofed.json()["detail"]

    # 2. Plain text disguised as WebM audio
    res_txt = client.post(
        "/voice/transcribe?provider=whisper&language=en",
        files={"file": ("speech.webm", b"Hello I am text", "audio/webm")},
    )
    assert res_txt.status_code == 400
    assert "Upload security check failed" in res_txt.json()["detail"]

    # 3. Genuine WAV header passes validation
    valid_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
    safe_name, fmt = validate_uploaded_audio_security(valid_wav, "sample.wav", "audio/wav")
    assert fmt == "audio/wav"

    # 4. Genuine WebM header passes validation
    valid_webm = b"\x1a\x45\xdf\xa3" + b"matroska-data"
    safe_name, fmt = validate_uploaded_audio_security(valid_webm, "sample.webm", "audio/webm")
    assert fmt == "audio/webm"


# ==============================================================================
# 8. SECRET MANAGEMENT AND PRODUCTION FAIL-CLOSED
# ==============================================================================

def test_production_secrets_validation_fails_closed():
    """Missing, short, or identical secrets in production fail startup immediately."""
    # Missing secrets
    weak_settings = Settings(
        app_env="production",
        scheme_navigator_auth_secret=None,
        scheme_navigator_release_key=None,
    )
    with pytest.raises(RuntimeError, match="SCHEME_NAVIGATOR_AUTH_SECRET must be set"):
        weak_settings.validate_production_secrets()

    # Weak secret (< 32 chars)
    short_settings = Settings(
        app_env="production",
        scheme_navigator_auth_secret="too-short",
        scheme_navigator_release_key="also-short",
    )
    with pytest.raises(RuntimeError, match="minimum 32 characters"):
        short_settings.validate_production_secrets()

    # Identical keys (key reuse forbidden)
    reused_key = "a-very-long-secret-key-that-has-over-thirty-two-characters"
    reused_settings = Settings(
        app_env="production",
        scheme_navigator_auth_secret=reused_key,
        scheme_navigator_release_key=reused_key,
    )
    with pytest.raises(RuntimeError, match="must be distinct"):
        reused_settings.validate_production_secrets()


# ==============================================================================
# 9. SGNAY POLICY DATA ACCURACY
# ==============================================================================

def test_sgnay_policy_disability_tier_distinction():
    """SGNAY candidate record distinguishes 40% disability eligibility from 80% severe disability enhanced benefit."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sgnay_file = os.path.join(project_root, "data", "candidates", "sanjay-gandhi-niradhar-anudan.json")
    candidate_catalog_file = os.path.join(project_root, "data", "candidates", "candidate_schemes.json")

    with open(sgnay_file, "r", encoding="utf-8") as f:
        sgnay_data = json.load(f)

    # 1. Must remain draft and not publication authorized
    assert sgnay_data.get("rule_status") == "draft"
    assert sgnay_data.get("publication_authorized") is False

    # 2. Summary must distinguish >= 80% severe disability from baseline >= 40% eligibility
    summary = sgnay_data["summary"]
    assert "80%" in summary
    assert "40%" in summary

    # 3. Benefits must differentiate Rs. 1,500 from Rs. 2,500 severe disability tier
    benefits = sgnay_data["benefits"]
    assert any("1,500" in b and "40% to 79%" in b for b in benefits)
    assert any("2,500" in b and "80%" in b for b in benefits)

    # 4. Check candidate_schemes.json has synchronized benefits
    with open(candidate_catalog_file, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    catalog_sgnay = next(s for s in catalog if s["scheme_id"] == "candidate-sanjay-gandhi-niradhar")
    assert catalog_sgnay.get("publication_authorized") is False
    assert any("80%" in b for b in catalog_sgnay["benefits"])

    # 5. Verify AST predicates for 40% eligibility vs 80% severe disability
    from scheme_navigator.domain.models import CitizenProfile, Scheme
    from scheme_navigator.services.rule_engine import evaluate_node

    scheme_sgnay = Scheme.model_validate(sgnay_data)

    # 5a. Beneficiary with 85% disability and 40k income -> satisfies severe disability branch
    prof_severe = CitizenProfile(
        resident_state="maharashtra",
        age_years=35,
        receiving_other_pension=False,
        has_disability=True,
        disability_percentage=85,
        annual_family_income=40000,
    )
    eval_severe = evaluate_node(scheme_sgnay.eligibility_rule, prof_severe)
    assert eval_severe.value is True

    # 5b. Beneficiary with 45% disability and 40k income -> satisfies baseline disability branch
    prof_standard = CitizenProfile(
        resident_state="maharashtra",
        age_years=35,
        receiving_other_pension=False,
        has_disability=True,
        disability_percentage=45,
        annual_family_income=40000,
    )
    eval_standard = evaluate_node(scheme_sgnay.eligibility_rule, prof_standard)
    assert eval_standard.value is True

    # 5c. Beneficiary with 30% disability and 40k income -> fails (under 40% and income > 21k)
    prof_below_40 = CitizenProfile(
        resident_state="maharashtra",
        age_years=35,
        receiving_other_pension=False,
        has_disability=True,
        disability_percentage=30,
        annual_family_income=40000,
    )
    eval_below_40 = evaluate_node(scheme_sgnay.eligibility_rule, prof_below_40)
    assert eval_below_40.value is False

    # 5d. General destitute without disability (income 18k <= 21k) -> satisfies general branch
    prof_general = CitizenProfile(
        resident_state="maharashtra",
        age_years=35,
        receiving_other_pension=False,
        has_disability=False,
        annual_family_income=18000,
    )
    eval_general = evaluate_node(scheme_sgnay.eligibility_rule, prof_general)
    assert eval_general.value is True
    assert len(eval_general.missing_fields) == 0


def test_sgnay_disability_boundary_and_missing_information():
    """Verify SGNAY boundary values (39%, 40%, 79%, 80%) and missing-information semantics."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sgnay_file = os.path.join(project_root, "data", "candidates", "sanjay-gandhi-niradhar-anudan.json")

    with open(sgnay_file, "r", encoding="utf-8") as f:
        sgnay_data = json.load(f)

    from scheme_navigator.domain.models import CitizenProfile, Scheme
    from scheme_navigator.services.explanation import generate_scheme_explanation
    from scheme_navigator.services.rule_engine import evaluate_node

    scheme = Scheme.model_validate(sgnay_data)

    # 1. Explicitly declared non-disabled MUST NOT create an unnecessary UNKNOWN condition
    # 1a. Income <= 21k -> Evaluates to True, 0 missing fields
    p_non_disabled_eligible = CitizenProfile(
        resident_state="maharashtra",
        age_years=35,
        receiving_other_pension=False,
        has_disability=False,
        annual_family_income=18000,
    )
    e_nd_elig = evaluate_node(scheme.eligibility_rule, p_non_disabled_eligible)
    assert e_nd_elig.value is True
    assert len(e_nd_elig.missing_fields) == 0
    exp_nd_elig = generate_scheme_explanation(scheme, p_non_disabled_eligible, language="en")
    assert len(exp_nd_elig.missing_information) == 0

    # 1b. Income > 21k -> Evaluates to False (ineligible), 0 missing fields (not UNKNOWN)
    p_non_disabled_ineligible = CitizenProfile(
        resident_state="maharashtra",
        age_years=35,
        receiving_other_pension=False,
        has_disability=False,
        annual_family_income=35000,
    )
    e_nd_inelig = evaluate_node(scheme.eligibility_rule, p_non_disabled_ineligible)
    assert e_nd_inelig.value is False
    assert len(e_nd_inelig.missing_fields) == 0

    # 2. Missing disability information MUST remain UNKNOWN
    # 2a. Disability completely unstated (has_disability=None, disability_percentage=None) with income between 21k and 50k
    p_missing_disability = CitizenProfile(
        resident_state="maharashtra",
        age_years=35,
        receiving_other_pension=False,
        annual_family_income=35000,
    )
    e_missing = evaluate_node(scheme.eligibility_rule, p_missing_disability)
    assert e_missing.value is None  # UNKNOWN
    assert "disability_percentage" in e_missing.missing_fields

    exp_missing = generate_scheme_explanation(scheme, p_missing_disability, language="en")
    assert any(m.field == "disability_percentage" for m in exp_missing.missing_information)

    # 2b. has_disability=True but disability_percentage is missing -> must remain UNKNOWN
    p_has_disability_missing_pct = CitizenProfile(
        resident_state="maharashtra",
        age_years=35,
        receiving_other_pension=False,
        has_disability=True,
        disability_percentage=None,
        annual_family_income=35000,
    )
    e_missing_pct = evaluate_node(scheme.eligibility_rule, p_has_disability_missing_pct)
    assert e_missing_pct.value is None  # UNKNOWN
    assert "disability_percentage" in e_missing_pct.missing_fields

    # 3. Exact Boundary Testing: 39%, 40%, 79%, 80% (with income 35k <= 50k)
    # Boundary 39%: Below 40% statutory threshold -> Ineligible (False)
    p_39 = CitizenProfile(
        resident_state="maharashtra",
        age_years=35,
        receiving_other_pension=False,
        has_disability=True,
        disability_percentage=39,
        annual_family_income=35000,
    )
    e_39 = evaluate_node(scheme.eligibility_rule, p_39)
    assert e_39.value is False
    assert len(e_39.missing_fields) == 0

    # Boundary 40%: Baseline disability eligibility met -> Eligible (True)
    p_40 = CitizenProfile(
        resident_state="maharashtra",
        age_years=35,
        receiving_other_pension=False,
        has_disability=True,
        disability_percentage=40,
        annual_family_income=35000,
    )
    e_40 = evaluate_node(scheme.eligibility_rule, p_40)
    assert e_40.value is True
    assert len(e_40.missing_fields) == 0
    exp_40 = generate_scheme_explanation(scheme, p_40, language="en")
    pos_40_ids = {c.condition_id for c in exp_40.positive_conditions}
    assert "c_sgnay_disability_min_40" in pos_40_ids
    assert "c_sgnay_severe_disability_80" not in pos_40_ids

    # Boundary 79%: Meets 40% baseline but NOT 80% severe tier
    p_79 = CitizenProfile(
        resident_state="maharashtra",
        age_years=35,
        receiving_other_pension=False,
        has_disability=True,
        disability_percentage=79,
        annual_family_income=35000,
    )
    e_79 = evaluate_node(scheme.eligibility_rule, p_79)
    assert e_79.value is True
    exp_79 = generate_scheme_explanation(scheme, p_79, language="en")
    pos_79_ids = {c.condition_id for c in exp_79.positive_conditions}
    assert "c_sgnay_disability_min_40" in pos_79_ids
    assert "c_sgnay_severe_disability_80" not in pos_79_ids

    # Boundary 80%: Meets severe disability tier -> qualifies for enhanced Rs. 2,500/month
    p_80 = CitizenProfile(
        resident_state="maharashtra",
        age_years=35,
        receiving_other_pension=False,
        has_disability=True,
        disability_percentage=80,
        annual_family_income=35000,
    )
    e_80 = evaluate_node(scheme.eligibility_rule, p_80)
    assert e_80.value is True
    exp_80 = generate_scheme_explanation(scheme, p_80, language="en")
    pos_80_ids = {c.condition_id for c in exp_80.positive_conditions}
    assert "c_sgnay_severe_disability_80" in pos_80_ids

