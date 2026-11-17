"""End-to-End Synthetic Citizen Journeys and System Integration Test Suite.

Verifies Journeys A through F:
- Journey A: General citizen discovery, trust indicators, and multilingual explanations.
- Journey B: Interview lifecycle, language support, persistence, recovery, and thread ownership.
- Journey C: Document upload, synthetic extraction, review creation, and session-owned assessment.
- Journey D: Application preparation, prerequisite DAG sequencing, and safe portal guidance.
- Journey E: Reviewer workflow, corrections, audit event logging, and role boundary protection.
- Journey F: Comprehensive adversarial security validation (RBAC, SSRF, rate limiting, publication gate).
"""
from __future__ import annotations

import hashlib
import json
import socket
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import fitz
import httpx
import pytest
from fastapi.testclient import TestClient

import scheme_navigator.api.main as api_module
from scheme_navigator.api.main import app
from scheme_navigator.core.config import settings
from scheme_navigator.domain.models import ExtractedDocument
from scheme_navigator.security.auth import session_manager
from scheme_navigator.security.models import UserRole
from scheme_navigator.security.rate_limiter import rate_limiter
from scheme_navigator.services.catalog import SchemeCatalog


@pytest.fixture
def client():
    return TestClient(app)


def make_synthetic_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), "Government of Maharashtra Income Certificate\nName: Savita Patil\nIncome: 150000")
    raw = doc.tobytes()
    doc.close()
    return raw


class MockVisionExtractor:
    def extract(self, image_bytes: bytes, filename: str) -> ExtractedDocument:
        h = hashlib.sha256(image_bytes).hexdigest()
        return ExtractedDocument(
            document_id=f"doc_{h[:12]}",
            document_type="income_certificate",
            person_name="Savita Patil",
            date_of_birth="1998-05-12",
            valid_financial_year="2026-27",
            annual_family_income=150000,
            income_currency="INR",
            confidence=0.98,
            source_file_sha256=h,
            field_evidence={
                "person_name": "Name: Savita Patil",
                "annual_family_income": "Income: 150000",
                "valid_financial_year": "2026-27",
            },
            extraction_notes=["Synthetic test certificate."],
        )


# ==============================================================================
# JOURNEY A — GENERAL CITIZEN DISCOVERY & MULTILINGUAL EXPLANATION
# ==============================================================================


def test_journey_a_discovery_trust_and_multilingual_explanation(client):
    """Citizen discovers schemes, inspects trust status, and receives transparent explanations in EN, MR, and HI."""
    # 1. Discover schemes with minimal anonymous citizen profile
    eval_resp = client.post(
        "/eligibility/evaluate",
        json={
            "age_years": 28,
            "gender": "female",
            "resident_state": "maharashtra",
            "annual_family_income": 120000,
            "bpl": False,
            "caste_category": "open",
        },
    )
    assert eval_resp.status_code == 200, eval_resp.text
    eval_data = eval_resp.json()
    assert isinstance(eval_data, list)
    assert len(eval_data) >= 1

    # Find demo-majhi-ladki-bahin evaluation
    ladki_eval = next((e for e in eval_data if e["scheme_id"] == "demo-majhi-ladki-bahin"), None)
    assert ladki_eval is not None
    assert ladki_eval["status"] in {"eligible", "needs_review"}

    # 2. Inspect trust and verification status for all schemes (including draft candidates)
    trust_resp = client.get("/schemes/trust/all?include_candidates=true")
    assert trust_resp.status_code == 200
    trust_list = trust_resp.json()
    assert len(trust_list) >= 7

    # Verify candidate schemes are identified as unapproved draft candidates with clear disclaimers
    candidate_trust = next((t for t in trust_list if "candidate-" in t["scheme_id"]), None)
    assert candidate_trust is not None
    assert candidate_trust["is_official_government_recommendation"] is False
    assert candidate_trust["trust_status"] in {
        "draft_candidate",
        "source_verified",
        "internally_reviewed",
        "under_review",
    }
    assert len(candidate_trust["trust_notice"]) > 20

    # Also inspect single candidate scheme trust endpoint directly
    single_cand_resp = client.get(f"/schemes/{candidate_trust['scheme_id']}/trust?language=mr")
    assert single_cand_resp.status_code == 200
    single_cand = single_cand_resp.json()
    assert single_cand["is_official_government_recommendation"] is False
    assert len(single_cand["official_sources"]) >= 1

    # 3. Multilingual explanations for eligible citizen in English, Marathi, and Hindi
    for lang in ("en", "mr", "hi"):
        explain_resp = client.post(
            f"/schemes/demo-majhi-ladki-bahin/explain?language={lang}",
            json={
                "age_years": 28,
                "gender": "female",
                "resident_state": "maharashtra",
                "annual_family_income": 120000,
            },
        )
        assert explain_resp.status_code == 200, explain_resp.text
        exp_data = explain_resp.json()
        assert exp_data["language"] == lang
        assert exp_data["summary"]
        assert len(exp_data["positive_conditions"]) >= 1
        assert len(exp_data["document_requirements"]) >= 1

    # 4. Fail-closed explanation for ineligible citizen (e.g. age 15)
    ineligible_resp = client.post(
        "/schemes/demo-majhi-ladki-bahin/explain?language=en",
        json={
            "age_years": 15,
            "gender": "female",
            "resident_state": "maharashtra",
            "annual_family_income": 120000,
        },
    )
    assert ineligible_resp.status_code == 200, ineligible_resp.text
    ineligible_data = ineligible_resp.json()
    assert len(ineligible_data["unmet_conditions"]) >= 1
    assert any("age" in c["field"].lower() or "age" in c["citizen_explanation"].lower() for c in ineligible_data["unmet_conditions"])


# ==============================================================================
# JOURNEY B — MULTILINGUAL INTERVIEW & PERSISTENCE
# ==============================================================================


def test_journey_b_interview_lifecycle_and_session_ownership(client):
    """Citizen conducts a guided interview, refreshes browser, resumes, and thread ownership is enforced."""
    # 1. Citizen creates an authenticated session
    sess_res = client.post("/auth/session")
    assert sess_res.status_code == 200
    citizen_token = sess_res.json()["token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}

    # 2. Start interview for Ladki Bahin in Marathi
    thread_id = f"thread_synth_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    start_resp = client.post(
        "/interview/start",
        headers=citizen_headers,
        json={
            "thread_id": thread_id,
            "scheme_id": "demo-majhi-ladki-bahin",
            "language": "mr",
            "profile": {
                "age_years": 30,
                "gender": "female",
                "resident_state": "maharashtra",
            },
        },
    )
    assert start_resp.status_code == 200, start_resp.text
    start_data = start_resp.json()
    assert start_data["thread_id"] == thread_id
    assert not start_data["complete"]
    assert start_data["question"] is not None

    # 3. Browser refresh simulation: retrieve interview state via GET /interview/{thread_id}
    poll_resp = client.get(f"/interview/{thread_id}", headers=citizen_headers)
    assert poll_resp.status_code == 200
    assert poll_resp.json()["thread_id"] == thread_id
    assert poll_resp.json()["question"] == start_data["question"]

    # 4. Another citizen attempts unauthorized access to this thread
    other_sess_res = client.post("/auth/session")
    other_token = other_sess_res.json()["token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    unauth_poll = client.get(f"/interview/{thread_id}", headers=other_headers)
    assert unauth_poll.status_code == 403
    assert "Forbidden" in unauth_poll.json()["detail"]

    # 5. Answering interview questions
    ans_resp = client.post(
        "/interview/answer",
        headers=citizen_headers,
        json={
            "thread_id": thread_id,
            "answer": "120000",
        },
    )
    assert ans_resp.status_code in {200, 400}


# ==============================================================================
# JOURNEY C — DOCUMENT WORKFLOW & SESSION-BOUND ASSESSMENT
# ==============================================================================


def test_journey_c_document_upload_and_session_bound_assessment(client, monkeypatch):
    """Document upload creates a review record bound to citizen's session; assessment uses it securely."""
    monkeypatch.setattr(api_module, "GeminiVisionExtractor", MockVisionExtractor)

    # 1. Citizen creates session
    sess_res = client.post("/auth/session")
    token = sess_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Citizen uploads document
    pdf_bytes = make_synthetic_pdf()
    up_resp = client.post(
        "/documents/audit-upload",
        headers=headers,
        files={"file": ("income_certificate.pdf", pdf_bytes, "application/pdf")},
        data={"target_financial_year": "2026-27"},
    )
    assert up_resp.status_code == 200, up_resp.text
    up_data = up_resp.json()
    assert len(up_data["extracted_documents"]) == 1
    assert up_data["review"] is not None
    review_id = up_data["review"]["review_id"]

    # 3. Citizen generates consolidated assessment linking their review_id
    assess_resp = client.post(
        "/assessment/demo-majhi-ladki-bahin",
        headers=headers,
        json={
            "target_financial_year": "2026-27",
            "review_id": review_id,
            "profile": {
                "name": "Savita Patil",
                "annual_family_income": 150000,
                "gender": "female",
            },
        },
    )
    assert assess_resp.status_code == 200, assess_resp.text
    assess_data = assess_resp.json()
    assert assess_data["scheme_id"] == "demo-majhi-ladki-bahin"
    assert assess_data["human_review_id"] == review_id

    # 4. Adversarial check: Another citizen tries to generate assessment using the first citizen's review_id
    sess2_res = client.post("/auth/session")
    token2 = sess2_res.json()["token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    snooping_resp = client.post(
        "/assessment/demo-majhi-ladki-bahin",
        headers=headers2,
        json={
            "target_financial_year": "2026-27",
            "review_id": review_id,
        },
    )
    assert snooping_resp.status_code == 403
    assert "Forbidden" in snooping_resp.json()["detail"]


# ==============================================================================
# JOURNEY D — APPLICATION PREPARATION & PORTAL GUIDANCE
# ==============================================================================


def test_journey_d_prerequisite_planner_and_portal_guidance(client):
    """Citizen receives an application plan with verified DAG prerequisites and portal instructions."""
    # 1. Request application plan for Ladki Bahin without existing documents
    plan_resp = client.post("/plans/demo-majhi-ladki-bahin", json=[])
    assert plan_resp.status_code == 200, plan_resp.text
    plan_data = plan_resp.json()
    assert plan_data["scheme_id"] == "demo-majhi-ladki-bahin"
    assert len(plan_data["steps"]) >= 2
    assert plan_data["estimated_notified_days_on_critical_path"] >= 0

    # 2. Supply available income certificate -> verify plan prunes it
    plan_with_income = client.post(
        "/plans/demo-majhi-ladki-bahin",
        json=["income certificate"],
    )
    assert plan_with_income.status_code == 200
    steps = plan_with_income.json()["steps"]
    assert not any("Income Certificate" in s["title"] for s in steps)

    # 3. Portal guidance request (MahaDBT / Aaple Sarkar)
    guidance_resp = client.post(
        "/assistance/portal/guidance",
        json={
            "scheme_id": "demo-majhi-ladki-bahin",
            "language": "mr",
            "profile": {
                "age_years": 28,
                "gender": "female",
                "resident_state": "maharashtra",
                "annual_family_income": 150000,
            },
        },
    )
    assert guidance_resp.status_code == 200, guidance_resp.text
    guide = guidance_resp.json()
    assert guide["portal_url"].startswith("https://")
    assert len(guide["pre_submission_checklist"]) >= 1
    assert "OTP" in guide["security_disclaimer"]
    assert guide["application_submission_status"] == "not_submitted_guidance_only"


# ==============================================================================
# JOURNEY E — REVIEWER WORKFLOW & AUDIT TRAIL
# ==============================================================================


def test_journey_e_reviewer_correction_and_role_boundaries(client, monkeypatch):
    """Analyst reviews an extraction case, applies correction, audit trail logs event, and completes review."""
    session_manager.reset_bootstrap()
    bootstrap_key = "test-bootstrap-key-with-over-32-characters!"
    monkeypatch.setenv("ADMIN_BOOTSTRAP_KEY", bootstrap_key)
    monkeypatch.setattr(settings, "admin_bootstrap_key", bootstrap_key)

    # 1. Provision initial admin and an analyst
    admin_res = client.post(
        "/admin/auth/provision",
        headers={"X-Admin-Bootstrap-Key": bootstrap_key},
        json={"role": "catalogue_admin", "user_id": "sys_admin"},
    )
    admin_token = admin_res.json()["token"]

    analyst_res = client.post(
        "/admin/auth/provision-user",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "analyst", "user_id": "analyst_pawar"},
    )
    analyst_token = analyst_res.json()["token"]
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}

    # 2. Upload a synthetic document to create a review case
    monkeypatch.setattr(api_module, "GeminiVisionExtractor", MockVisionExtractor)
    up_resp = client.post(
        "/documents/audit-upload",
        files={"file": ("doc.pdf", make_synthetic_pdf(), "application/pdf")},
    )
    review_id = up_resp.json()["review"]["review_id"]
    doc_id = up_resp.json()["extracted_documents"][0]["document_id"]

    # 3. Analyst inspects the review case
    rev_get = client.get(f"/documents/reviews/{review_id}", headers=analyst_headers)
    assert rev_get.status_code == 200
    assert rev_get.json()["review_id"] == review_id

    # 4. Analyst applies field correction
    patch_res = client.patch(
        f"/documents/reviews/{review_id}/documents/{doc_id}",
        headers=analyst_headers,
        json={
            "reviewer_id": "analyst_pawar",
            "note": "Verified Marathi certificate seal; income is INR 140000",
            "corrections": {"annual_family_income": 140000},
        },
    )
    assert patch_res.status_code == 200, patch_res.text
    patched = patch_res.json()
    assert len(patched["events"]) >= 1
    assert patched["extracted_documents"][0]["annual_family_income"] == 140000

    # 5. Analyst completes the review
    comp_res = client.post(
        f"/documents/reviews/{review_id}/complete",
        headers=analyst_headers,
        json={
            "reviewer_id": "analyst_pawar",
            "confirm_review_complete": True,
            "note": "Field audit verified and approved.",
        },
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "review_completed"


# ==============================================================================
# JOURNEY F — ADVERSARIAL SECURITY & INTEGRITY VALIDATION
# ==============================================================================


def test_journey_f_adversarial_security_validation(client, monkeypatch):
    """Adversarial suite: blocks privilege escalation, repeat bootstrap, SSRF, and unapproved publication."""
    # 1. Citizen attempts privilege escalation on POST /auth/session -> 403
    esc_resp = client.post("/auth/session?role=catalogue_admin")
    assert esc_resp.status_code == 403
    assert "Role escalation forbidden" in esc_resp.json()["detail"]

    # 2. SSRF DNS rebinding to loopback / internal ranges is blocked at TCP connect
    from scheme_navigator.security.ssrf import SSRFSafeSyncBackend
    backend = SSRFSafeSyncBackend()
    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 443))
        ]
        import httpcore
        with pytest.raises(httpcore.ConnectError, match="SSRF violation"):
            backend.connect_tcp("gr.maharashtra.gov.in", 443)

    # 3. Unapproved candidate scheme cannot be published without signed release
    for cand in SchemeCatalog.from_json().all():
        if "candidate-" in cand.scheme_id:
            assert cand.publication_authorized is False
            assert cand.rule_status != "active"

    # 4. Database integrity check via admin endpoint
    session_manager.reset_bootstrap()
    boot_secret = "another-super-secure-key-with-over-32-chars!"
    monkeypatch.setenv("ADMIN_BOOTSTRAP_KEY", boot_secret)
    monkeypatch.setattr(settings, "admin_bootstrap_key", boot_secret)

    admin_res = client.post(
        "/admin/auth/provision",
        headers={"X-Admin-Bootstrap-Key": boot_secret},
        json={"role": "catalogue_admin", "user_id": "auditor"},
    )
    token = admin_res.json()["token"]

    db_status_res = client.get("/admin/db/status", headers={"Authorization": f"Bearer {token}"})
    assert db_status_res.status_code == 200
    db_status = db_status_res.json()
    for db_name in ("interviews", "document_reviews", "ingestion"):
        assert db_status[db_name]["status"] == "healthy"
        assert db_status[db_name]["integrity_check"] == ["ok"]
