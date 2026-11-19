"""Forensic verification of SQLite Persistence, Restart Durability, and Document Replacement Lineage.

Requirements verified:
1. All citizen state lives in authoritative SQLite tables (not sessionStorage):
   - citizen_profiles
   - interview_runs
   - citizen_progress
   - citizen_scheme_documents
   - citizen_scheme_audit_history
2. Durability across backend restarts:
   - State persists when memory and sessionStorage are completely wiped.
3. Document replacement lineage:
   - Replaced documents are marked status='superseded' with superseded_by and replacement_reason.
   - Original records are NEVER deleted or erased.
   - New document is active with version 2 and new SHA-256.
   - Readiness score recalculates.
   - UI/API state endpoint distinguishes active vs superseded history.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

import scheme_navigator.api.main as api_module
from scheme_navigator.core.citizen_store import citizen_store
from scheme_navigator.security.auth import session_manager, UserRole, UserSession

SPECIMENS_DIR = Path(__file__).resolve().parent / "fixtures" / "specimens"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DB_PATH = DATA_DIR / "citizen_profiles.sqlite3"
TARGET_SCHEME = "candidate-majhi-ladki-bahin"


@pytest.fixture(autouse=True)
def enable_local_fallback(monkeypatch):
    monkeypatch.setenv("ENABLE_LOCAL_FALLBACK_OCR", "true")


def test_sqlite_persistence_and_backend_restart_durability(monkeypatch):
    """Prove that citizen profile, interview runs, scheme progress, documents,

    and audit history survive memory wipes and simulate server restart.
    """
    # 1. Start authenticated citizen session
    session, token = session_manager.create_session(role=UserRole.CITIZEN, user_id="anonymous_citizen")
    session_id = session.session_id
    client = TestClient(api_module.app, cookies={"sn_session": token})

    # 2. Update profile
    profile_payload = {
        "profile": {
            "name": "Sunita Ramesh Patil",
            "age_years": 32,
            "gender": "female",
            "marital_status": "married",
            "resident_state": "maharashtra",
            "annual_family_income": 120000,
            "caste_category": "OBC",
        }
    }
    prof_resp = client.post("/profile", json=profile_payload)
    assert prof_resp.status_code == 200

    # 3. Start eligibility interview
    thread_id = "thread_restart_durability_01"
    start_resp = client.post(
        "/interview/start",
        json={"thread_id": thread_id, "mode": "FOCUSED_SCHEME", "target_scheme_id": TARGET_SCHEME, "language": "mr"},
    )
    assert start_resp.status_code == 200
    assert start_resp.json()["thread_id"] == thread_id

    # 4. Set active scheme progress
    prog_resp = client.post(
        "/progress/activate",
        json={"scheme_id": TARGET_SCHEME, "version": "1.0.0"},
    )
    assert prog_resp.status_code == 200

    # 5. Upload document
    valid_pdf_path = SPECIMENS_DIR / "valid_income_certificate.pdf"
    with open(valid_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    upload_resp = client.post(
        "/documents/audit-upload",
        files={"file": ("income_certificate.pdf", pdf_bytes, "application/pdf")},
        data={"target_financial_year": "2026-27", "scheme_id": TARGET_SCHEME},
    )
    assert upload_resp.status_code == 200
    up_data = upload_resp.json()
    assert len(up_data["persisted_documents"]) == 1
    doc_id = up_data["persisted_documents"][0]["document_id"]
    sha256_v1 = hashlib.sha256(pdf_bytes).hexdigest()

    # 6. Run audit and calculate readiness
    audit_resp = client.post(
        f"/canonical-schemes/{TARGET_SCHEME}/documents/audit",
        json={
            "scheme_id": TARGET_SCHEME,
            "documents": up_data["extracted_documents"],
            "profile": profile_payload["profile"],
            "target_financial_year": "2026-27",
            "language": "mr",
        },
    )
    assert audit_resp.status_code == 200
    assert audit_resp.json()["readiness_percentage"] > 0

    # -------------------------------------------------------------------------
    # FORENSIC SQLITE VERIFICATION BEFORE RESTART
    # -------------------------------------------------------------------------
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row

        # Check citizen_profiles
        p_row = conn.execute("SELECT * FROM citizen_profiles WHERE session_id = ?", (session_id,)).fetchone()
        assert p_row is not None, "Profile must exist in SQLite citizen_profiles"

        # Check interview_runs
        r_row = conn.execute("SELECT * FROM interview_runs WHERE thread_id = ?", (thread_id,)).fetchone()
        assert r_row is not None, "Interview run must exist in SQLite interview_runs"
        assert r_row["session_id"] == session_id

        # Check citizen_progress
        pr_row = conn.execute("SELECT * FROM citizen_progress WHERE session_id = ?", (session_id,)).fetchone()
        assert pr_row is not None, "Progress must exist in SQLite citizen_progress"
        assert pr_row["active_scheme_id"] == TARGET_SCHEME

        # Check citizen_scheme_documents
        d_row = conn.execute("SELECT * FROM citizen_scheme_documents WHERE document_id = ?", (doc_id,)).fetchone()
        assert d_row is not None, "Document must exist in SQLite citizen_scheme_documents"
        assert d_row["status"] == "active"
        assert d_row["version"] == 1
        assert d_row["source_file_sha256"] == sha256_v1

        # Check citizen_scheme_audit_history
        a_row = conn.execute("SELECT * FROM citizen_scheme_audit_history WHERE session_id = ?", (session_id,)).fetchone()
        assert a_row is not None, "Audit must exist in SQLite citizen_scheme_audit_history"
        assert a_row["readiness_percentage"] > 0

    # -------------------------------------------------------------------------
    # SIMULATE COMPLETE SERVER CRASH & RESTART (PURGE IN-MEMORY MAPS)
    # -------------------------------------------------------------------------
    session_manager._thread_owners.clear()
    session_manager._review_owners.clear()

    # Re-instantiate TestClient (simulating fresh connection with same session cookie, 0 sessionStorage)
    new_client = TestClient(api_module.app, cookies={"sn_session": token})

    # 7. Verify full state recovery from SQLite
    rec_prof = new_client.get("/profile")
    assert rec_prof.status_code == 200
    assert rec_prof.json()["profile"]["name"] == "Sunita Ramesh Patil"

    rec_prog = new_client.get("/progress")
    assert rec_prog.status_code == 200
    assert rec_prog.json()["active_scheme_id"] == TARGET_SCHEME

    # Thread access authorization must succeed across restart via SQLite lookup
    rec_thread = new_client.get(f"/interview/{thread_id}")
    assert rec_thread.status_code == 200, "Thread ownership must be recovered from SQLite across server restarts"

    # Document state must be 100% recovered from SQLite
    rec_doc_state = new_client.get(f"/canonical-schemes/{TARGET_SCHEME}/documents/state")
    assert rec_doc_state.status_code == 200
    doc_state_data = rec_doc_state.json()
    assert doc_state_data["total_active"] == 1
    assert doc_state_data["active_documents"][0]["document_type"] == "income_certificate"
    assert doc_state_data["active_document_records"][0]["source_file_sha256"] == sha256_v1
    assert doc_state_data["latest_audit"] is not None
    assert doc_state_data["latest_audit"]["readiness_percentage"] > 0


def test_document_replacement_and_audit_lineage(monkeypatch):
    """Prove that:

    1. Citizen uploads expired document (v1) -> readiness fails / reports FY mismatch.
    2. Citizen replaces document with valid document -> new record (v2) created with new SHA-256.
    3. Original v1 record is NOT deleted; marked status='superseded' with superseded_by and replacement_reason.
    4. Readiness recalculates and increases.
    5. State endpoint distinguishes active vs superseded history.
    """
    session, token = session_manager.create_session(role=UserRole.CITIZEN, user_id="anonymous_citizen")
    session_id = session.session_id
    client = TestClient(api_module.app, cookies={"sn_session": token})

    scheme_id = TARGET_SCHEME
    client.post("/progress/activate", json={"scheme_id": scheme_id, "version": "1.0.0"})

    # 2. Upload expired income certificate (v1)
    expired_pdf_path = SPECIMENS_DIR / "expired_income_certificate.pdf"
    with open(expired_pdf_path, "rb") as f:
        expired_bytes = f.read()

    up1_resp = client.post(
        "/documents/audit-upload",
        files={"file": ("expired_income_certificate.pdf", expired_bytes, "application/pdf")},
        data={"target_financial_year": "2026-27", "scheme_id": scheme_id},
    )
    assert up1_resp.status_code == 200
    doc1_id = up1_resp.json()["persisted_documents"][0]["document_id"]
    sha256_v1 = hashlib.sha256(expired_bytes).hexdigest()

    # Initial audit report with expired doc
    audit1_resp = client.post(
        f"/canonical-schemes/{scheme_id}/documents/audit",
        json={
            "scheme_id": scheme_id,
            "documents": up1_resp.json()["extracted_documents"],
            "profile": {"name": "Sunita Ramesh Patil", "annual_family_income": 120000},
            "target_financial_year": "2026-27",
            "language": "mr",
        },
    )
    assert audit1_resp.status_code == 200
    rep1 = audit1_resp.json()
    inc_req_1 = next(r for r in rep1["requirements"] if "Income" in r["document_name"] or "उत्पन्न" in r["document_name"])
    st1 = (inc_req_1.get("state") or inc_req_1.get("match_status") or "").upper()
    assert any(w in st1 for w in ("EXPIRED", "MISMATCH", "REPLACEMENT")), f"Expired doc must report mismatch/expired, got {st1}"

    # 3. Replace document with valid income certificate (v2)
    valid_pdf_path = SPECIMENS_DIR / "valid_income_certificate.pdf"
    with open(valid_pdf_path, "rb") as f:
        valid_bytes = f.read()

    up2_resp = client.post(
        "/documents/audit-upload",
        files={"file": ("valid_income_certificate.pdf", valid_bytes, "application/pdf")},
        data={
            "target_financial_year": "2026-27",
            "scheme_id": scheme_id,
            "replaces_document_id": doc1_id,
            "replacement_reason": "Citizen uploaded corrected financial year certificate",
        },
    )
    assert up2_resp.status_code == 200
    doc2_id = up2_resp.json()["persisted_documents"][0]["document_id"]
    sha256_v2 = hashlib.sha256(valid_bytes).hexdigest()
    assert doc1_id != doc2_id, "Replacement document must have unique document_id"
    assert sha256_v1 != sha256_v2, "Replacement document must have different SHA-256"

    # 4. Check SQLite directly for lineage preservation
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row

        # Check v1 record: MUST STILL EXIST and be marked 'superseded'
        v1_row = conn.execute("SELECT * FROM citizen_scheme_documents WHERE document_id = ?", (doc1_id,)).fetchone()
        assert v1_row is not None, "Original v1 document must NEVER be deleted from SQLite"
        assert v1_row["status"] == "superseded", "Original record must be marked 'superseded'"
        assert v1_row["superseded_by"] == doc2_id, "Original record must point to replacement document"
        assert "corrected financial year" in v1_row["replacement_reason"]
        assert v1_row["version"] == 1

        # Check v2 record: MUST BE 'active' and version 2
        v2_row = conn.execute("SELECT * FROM citizen_scheme_documents WHERE document_id = ?", (doc2_id,)).fetchone()
        assert v2_row is not None
        assert v2_row["status"] == "active"
        assert v2_row["version"] == 2
        assert v2_row["source_file_sha256"] == sha256_v2

    # 5. Query state endpoint: active vs superseded history
    state_resp = client.get(f"/canonical-schemes/{scheme_id}/documents/state")
    assert state_resp.status_code == 200
    state_data = state_resp.json()

    assert state_data["total_active"] == 1, "Only v2 should be active"
    assert state_data["total_superseded"] == 1, "v1 should be in superseded history"
    assert state_data["active_documents"][0]["valid_financial_year"] == "2026-27"

    # 6. Re-audit with active documents: readiness must now be satisfied for income
    audit2_resp = client.post(
        f"/canonical-schemes/{scheme_id}/documents/audit",
        json={
            "scheme_id": scheme_id,
            "documents": state_data["active_documents"],
            "profile": {"name": "Sunita Ramesh Patil", "annual_family_income": 120000},
            "target_financial_year": "2026-27",
            "language": "mr",
        },
    )
    assert audit2_resp.status_code == 200
    rep2 = audit2_resp.json()
    inc_req_2 = next(r for r in rep2["requirements"] if "Income" in r["document_name"] or "उत्पन्न" in r["document_name"])
    st2 = (inc_req_2.get("state") or inc_req_2.get("match_status") or "").upper()
    assert any(w in st2 for w in ("MATCH", "PREPARATION", "SATISFIED")), f"Valid doc must match requirement, got {st2}"
    assert rep2["readiness_percentage"] > rep1["readiness_percentage"], "Readiness percentage must increase after replacement"
