from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest

from scheme_navigator.core.citizen_store import CitizenProfileStore


def test_document_replacement_lineage_and_immutability(tmp_path):
    """Verify v1 -> v2 document replacement preserves v1 fields, hashes, and findings."""
    db_file = tmp_path / "immutable_test.sqlite3"
    store = CitizenProfileStore(db_path=db_file)
    session_id = "sess_immutable_001"
    scheme_id = "MHA-S-0001"

    # 1. Upload initial version (v1) of Income Certificate
    v1_extracted = {
        "document_type": "income_certificate",
        "person_name": "Sunita Patil",
        "annual_family_income": 120000,
        "valid_financial_year": "2026-27",
        "findings": [{"code": "INITIAL_AUDIT_PASS", "severity": "info"}],
    }
    v1_hash = "1" * 64
    v1_saved = store.save_scheme_document(
        session_id=session_id,
        scheme_id=scheme_id,
        doc_dict=v1_extracted,
        filename="income_v1.pdf",
        source_file_sha256=v1_hash,
    )

    assert v1_saved["version"] == 1
    assert v1_saved["status"] == "active"
    assert v1_saved["source_file_sha256"] == v1_hash

    # 2. Upload replacement version (v2) of Income Certificate
    v2_extracted = {
        "document_type": "income_certificate",
        "person_name": "Sunita Ramesh Patil",
        "annual_family_income": 115000,
        "valid_financial_year": "2026-27",
        "findings": [{"code": "REPLACEMENT_AUDIT_PASS", "severity": "info"}],
    }
    v2_hash = "2" * 64
    v2_saved = store.save_scheme_document(
        session_id=session_id,
        scheme_id=scheme_id,
        doc_dict=v2_extracted,
        filename="income_v2.pdf",
        source_file_sha256=v2_hash,
        replaces_doc_id=v1_saved["document_id"],
        replacement_reason="Name spelling updated per Gazette notice",
    )

    assert v2_saved["version"] == 2
    assert v2_saved["status"] == "active"
    assert v2_saved["source_file_sha256"] == v2_hash
    assert v2_saved["supersedes"] == v1_saved["document_id"]

    # 3. Verify history preserves all original v1 data
    history = store.get_scheme_document_history(session_id, scheme_id)
    assert len(history) == 2

    hist_v1 = next(d for d in history if d["version"] == 1)
    hist_v2 = next(d for d in history if d["version"] == 2)

    # v1 must be marked superseded and linked to v2
    assert hist_v1["status"] == "superseded"
    assert hist_v1["superseded_by"] == hist_v2["document_id"]
    assert hist_v1["replacement_reason"] == "Name spelling updated per Gazette notice"
    # Content and hash of v1 MUST be preserved exactly
    assert hist_v1["source_file_sha256"] == v1_hash
    assert hist_v1["filename"] == "income_v1.pdf"
    assert hist_v1["extracted"]["annual_family_income"] == 120000

    # 4. Invariant verification function
    verif = store.verify_audit_history_immutability(session_id, scheme_id)
    assert verif["is_immutable_and_valid"]
    assert len(verif["integrity_issues"]) == 0


def test_sqlite_trigger_blocks_unauthorized_content_tampering(tmp_path):
    """Verify SQLite triggers prevent modification of document hashes, content, or version."""
    db_file = tmp_path / "tamper_test.sqlite3"
    store = CitizenProfileStore(db_path=db_file)
    session_id = "sess_tamper_001"
    scheme_id = "MHA-S-0001"

    doc = {
        "document_type": "caste_certificate",
        "person_name": "Sunita Patil",
        "caste_category": "SC",
    }
    saved = store.save_scheme_document(
        session_id=session_id,
        scheme_id=scheme_id,
        doc_dict=doc,
        filename="caste.pdf",
        source_file_sha256="a" * 64,
    )
    doc_id = saved["document_id"]

    # Connect directly via raw sqlite3 to simulate malicious or accidental tampering
    conn = sqlite3.connect(str(db_file))

    # A) Attempt to tamper with source_file_sha256
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        conn.execute(
            "UPDATE citizen_scheme_documents SET source_file_sha256 = ? WHERE document_id = ?",
            ("b" * 64, doc_id),
        )

    # B) Attempt to tamper with extracted_json
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        conn.execute(
            "UPDATE citizen_scheme_documents SET extracted_json = '{\"tampered\": true}' WHERE document_id = ?",
            (doc_id,),
        )

    # C) Attempt to tamper with version
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        conn.execute(
            "UPDATE citizen_scheme_documents SET version = 99 WHERE document_id = ?",
            (doc_id,),
        )

    # D) Permitted update: status transition to 'superseded' with replacement reason
    conn.execute(
        "UPDATE citizen_scheme_documents SET status = 'superseded', superseded_by = 'doc_replacement_99' WHERE document_id = ?",
        (doc_id,),
    )
    conn.commit()

    # E) Attempt to reactivate a superseded document
    with pytest.raises(sqlite3.IntegrityError, match="cannot be reactivated"):
        conn.execute(
            "UPDATE citizen_scheme_documents SET status = 'active' WHERE document_id = ?",
            (doc_id,),
        )

    conn.close()


def test_audit_history_records_are_strictly_append_only(tmp_path):
    """Verify citizen_scheme_audit_history records cannot be modified via UPDATE."""
    db_file = tmp_path / "audit_append_only.sqlite3"
    store = CitizenProfileStore(db_path=db_file)
    session_id = "sess_audit_001"
    scheme_id = "MHA-S-0001"

    audit_id = store.save_scheme_audit_report(
        session_id=session_id,
        scheme_id=scheme_id,
        report_data={"readiness_percentage": 100, "audit_summary": "All mandatory documents verified"},
    )

    conn = sqlite3.connect(str(db_file))

    # Attempt to tamper with readiness_percentage in audit history
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        conn.execute(
            "UPDATE citizen_scheme_audit_history SET readiness_percentage = 0 WHERE audit_id = ?",
            (audit_id,),
        )

    conn.close()
