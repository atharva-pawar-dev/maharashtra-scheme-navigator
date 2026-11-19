from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from scheme_navigator.core.citizen_store import CitizenProfileStore
from scheme_navigator.domain.models import ExtractedDocument, Language, RuleNode, Scheme, SourceReference
from scheme_navigator.services.document_prep import (
    DocumentMatchStatus,
    get_scheme_document_requirements,
    prepare_intelligent_document_audit,
)


def _make_dummy_scheme(scheme_id: str, name: str, department: str, req_docs: list[str]) -> Scheme:
    import hashlib
    excerpt = "Official statutory guidelines for Maharashtra state scheme administration."
    h = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
    return Scheme(
        scheme_id=scheme_id,
        name=name,
        department=department,
        summary="Official statutory scheme summary",
        required_documents=req_docs,
        eligibility_rule=RuleNode(
            op="all",
            children=[RuleNode(op="gte", field="age", value=18, condition_id="c_age_dummy")],
        ),
        sources=[
            SourceReference(
                source_name="Maharashtra Government Gazette",
                source_url="https://maharashtra.gov.in/gazette",
                source_kind="official_scheme_page",
                retrieved_at=datetime.now(timezone.utc),
                evidence_excerpt=excerpt,
                evidence_sha256=h,
            )
        ],
    )


def test_retention_purge_invalidates_readiness_and_prevents_stale_green_state(tmp_path):
    """Verify 24-hr retention ceiling purge reactively drops readiness from 100% to blocked."""
    db_file = tmp_path / "retention_test.sqlite3"
    store = CitizenProfileStore(db_path=db_file)
    session_id = "sess_retention_001"
    scheme_id = "MHA-S-0001"
    canon_id = "candidate-sanjay-gandhi-niradhar-anudan"

    req_data = get_scheme_document_requirements(scheme_id)
    scheme_obj = _make_dummy_scheme(
        scheme_id=canon_id,
        name="Sanjay Gandhi Niradhar Anudan Yojana",
        department="Social Justice and Special Assistance",
        req_docs=[r["document_name"] for r in req_data.get("requirements", [])],
    )

    # 1. Citizen uploads required documents: Domicile, Income, and Age
    doc_domicile = ExtractedDocument(
        document_id="doc_domicile_100",
        document_type="domicile_certificate",
        person_name="Sunita Ramesh Patil",
        confidence=0.96,
        source_file_sha256="1" * 64,
        field_evidence={"document_title": "Maharashtra Domicile Certificate"},
    )
    doc_income = ExtractedDocument(
        document_id="doc_income_100",
        document_type="income_certificate",
        person_name="Sunita Ramesh Patil",
        annual_family_income=20000,
        valid_financial_year="2026-27",
        confidence=0.96,
        source_file_sha256="2" * 64,
        field_evidence={"document_title": "Tahsil Income Certificate"},
    )
    doc_age = ExtractedDocument(
        document_id="doc_age_100",
        document_type="aadhaar_card",
        person_name="Sunita Ramesh Patil",
        confidence=0.96,
        source_file_sha256="3" * 64,
        field_evidence={"document_title": "Aadhaar Card / Age Proof"},
    )

    # Initial assessment: All supplied -> 100% readiness
    report_initial = prepare_intelligent_document_audit(
        scheme=scheme_obj,
        extracted_documents=[doc_domicile, doc_income, doc_age],
        scheme_id=scheme_id,
    )
    assert report_initial.readiness_percentage == 100
    assert report_initial.all_mandatory_satisfied

    # Persist documents into SQLite
    store.save_scheme_document(session_id, scheme_id, doc_domicile.model_dump(), "domicile.pdf", "1" * 64)
    store.save_scheme_document(session_id, scheme_id, doc_income.model_dump(), "income.pdf", "2" * 64)
    store.save_scheme_document(session_id, scheme_id, doc_age.model_dump(), "age.pdf", "3" * 64)

    # 2. Simulate passage of 25 hours (past the 24-hr statutory ceiling)
    twenty_five_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    conn = sqlite3.connect(str(db_file))
    conn.execute(
        "UPDATE citizen_scheme_documents SET updated_at = ? WHERE document_type = 'income_certificate'",
        (twenty_five_hours_ago,),
    )
    conn.commit()
    conn.close()

    # 3. Execute retention purge
    purge_stats = store.purge_expired_records(retention_hours=24)
    assert purge_stats["documents_purged"] >= 1

    # Retrieve documents from store after purge
    stored_docs = store.get_scheme_documents(session_id, scheme_id, include_superseded=True)
    income_stored = next(d for d in stored_docs if d["document_type"] == "income_certificate")
    assert income_stored["status"] == "purged_expired"

    # 4. Reactive readiness re-evaluation
    # Construct doc list representing current stored state
    purged_income_doc = ExtractedDocument(
        document_id=income_stored["document_id"],
        document_type="income_certificate",
        person_name="Sunita Ramesh Patil",
        confidence=0.96,
        source_file_sha256="2" * 64,
        extraction_notes=["purged_expired: Statutory 24-hour privacy retention ceiling expired"],
    )

    report_post_purge = prepare_intelligent_document_audit(
        scheme=scheme_obj,
        extracted_documents=[doc_domicile, purged_income_doc, doc_age],
        scheme_id=scheme_id,
        language=Language.EN,
    )

    # Readiness MUST drop and cannot remain stale green 100%
    assert not report_post_purge.all_mandatory_satisfied
    assert report_post_purge.readiness_percentage < 100

    # Requirement status must transition to REPLACEMENT_REQUIRED
    income_req = next(r for r in report_post_purge.requirements if "income" in r.document_name.lower())
    assert income_req.state == DocumentMatchStatus.REPLACEMENT_REQUIRED

    # RETENTION_PERIOD_EXPIRED finding must be raised
    retention_findings = [f for f in report_post_purge.conflicts_detected if f.code == "RETENTION_PERIOD_EXPIRED"]
    assert len(retention_findings) == 1
    assert retention_findings[0].severity == "error"
    assert "24-hour" in retention_findings[0].message


def test_localized_reupload_notices_trilingual():
    """Verify localized re-upload notices in EN, MR, and HI for purged evidence."""
    scheme_obj = _make_dummy_scheme(
        scheme_id="candidate-sanjay-gandhi-niradhar-anudan",
        name="SGNAY",
        department="Social Justice",
        req_docs=["Income Certificate (Tahsildar)"],
    )

    purged_doc = ExtractedDocument(
        document_id="purged_doc_01",
        document_type="income_certificate",
        person_name="Sunita Patil",
        confidence=0.90,
        source_file_sha256="4" * 64,
        extraction_notes=["purged_expired"],
    )

    # English
    rep_en = prepare_intelligent_document_audit(
        scheme=scheme_obj,
        extracted_documents=[purged_doc],
        scheme_id="MHA-S-0001",
        language=Language.EN,
    )
    assert any("24-hour" in f.message for f in rep_en.conflicts_detected)

    # Marathi
    rep_mr = prepare_intelligent_document_audit(
        scheme=scheme_obj,
        extracted_documents=[purged_doc],
        scheme_id="MHA-S-0001",
        language=Language.MR,
    )
    assert any("२४ तासांच्या" in f.message for f in rep_mr.conflicts_detected)

    # Hindi
    rep_hi = prepare_intelligent_document_audit(
        scheme=scheme_obj,
        extracted_documents=[purged_doc],
        scheme_id="MHA-S-0001",
        language=Language.HI,
    )
    assert any("२४ घंटे" in f.message for f in rep_hi.conflicts_detected)
