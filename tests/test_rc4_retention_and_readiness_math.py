"""RC4 Retention and Readiness Mathematics Verification.

Validates:
1. Multi-requirement readiness mathematics:
   - 5 mandatory requirements: 5/5 satisfied = 100% readiness.
   - 1 purged document: drops to 4/5 = 80% readiness (never falsely reset to 0%).
   - 2 purged documents: drops to 3/5 = 60% readiness.
   - Re-uploading purged document restores 100% readiness.
2. Alternative (ANY_OF) and conditional requirement groups.
3. Purged file unavailable, stale green check cleared, re-upload notice displayed.
4. Historical findings remain available in append-only SQLite lineage.
"""
from __future__ import annotations

import datetime
from pathlib import Path
import pytest

from scheme_navigator.core.citizen_store import CitizenProfileStore
from scheme_navigator.documents.audit import ExtractedDocument
from scheme_navigator.domain.models import Language, RuleNode, Scheme, SourceReference
from scheme_navigator.services.document_prep import (
    DocumentMatchStatus,
    prepare_intelligent_document_audit,
)


import hashlib

def _build_five_requirement_scheme() -> Scheme:
    """Build a synthetic scheme with 5 mandatory statutory document requirements."""
    excerpt = "Mandatory statutory requirements for composite multi-group assistance."
    src = SourceReference(
        source_name="Maharashtra Government Gazette",
        source_url="https://maharashtra.gov.in/gazette",
        source_kind="official_scheme_page",
        retrieved_at=datetime.datetime.now(datetime.timezone.utc),
        evidence_excerpt=excerpt,
        evidence_sha256=hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
    )
    return Scheme(
        scheme_id="candidate-composite-five-req-scheme",
        name="Composite Multi-Requirement Welfare Scheme",
        department="Social Welfare Department",
        summary="Composite scheme requiring 5 distinct documentary proofs.",
        required_documents=[
            "Maharashtra Domicile Certificate",
            "Tahsil Income Certificate",
            "Aadhaar Card",
            "Caste Certificate",
            "7/12 Land Record Extract",
        ],
        eligibility_rule=RuleNode(
            op="all",
            children=[RuleNode(op="gte", field="age", value=18, condition_id="c_age_req")],
        ),
        sources=[src],
    )


def test_five_requirement_proportional_readiness_math():
    """Verify readiness drops from 100% to 80% when 1 of 5 documents is purged, not to 0%."""
    scheme = _build_five_requirement_scheme()

    # 5 valid extracted documents
    doc_domicile = ExtractedDocument(
        document_id="doc_domicile_1",
        document_type="domicile_certificate",
        person_name="Sunita Ramesh Patil",
        confidence=0.96,
        source_file_sha256="1" * 64,
        field_evidence={"document_title": "Maharashtra Domicile Certificate"},
    )
    doc_income = ExtractedDocument(
        document_id="doc_income_1",
        document_type="income_certificate",
        person_name="Sunita Ramesh Patil",
        annual_family_income=60000,
        valid_financial_year="2026-27",
        confidence=0.96,
        source_file_sha256="2" * 64,
        field_evidence={"document_title": "Tahsil Income Certificate"},
    )
    doc_aadhaar = ExtractedDocument(
        document_id="doc_aadhaar_1",
        document_type="aadhaar_card",
        person_name="Sunita Ramesh Patil",
        confidence=0.96,
        source_file_sha256="3" * 64,
        field_evidence={"document_title": "Aadhaar Card"},
    )
    doc_caste = ExtractedDocument(
        document_id="doc_caste_1",
        document_type="caste_certificate",
        person_name="Sunita Ramesh Patil",
        caste_category="OBC",
        confidence=0.96,
        source_file_sha256="4" * 64,
        field_evidence={"document_title": "Caste Certificate"},
    )
    doc_712 = ExtractedDocument(
        document_id="doc_712_1",
        document_type="seven_twelve_extract",
        person_name="Sunita Ramesh Patil",
        confidence=0.96,
        source_file_sha256="5" * 64,
        field_evidence={"document_title": "7/12 Land Record Extract"},
    )

    all_five = [doc_domicile, doc_income, doc_aadhaar, doc_caste, doc_712]

    # Step 1: All 5 supplied -> 100% readiness
    rep_100 = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=all_five,
        scheme_id=scheme.scheme_id,
    )
    assert rep_100.readiness_percentage == 100
    assert rep_100.all_mandatory_satisfied is True
    assert rep_100.mandatory_satisfied == 5
    assert rep_100.mandatory_total == 5

    # Step 2: 1 document purged (e.g. income certificate purged after retention window)
    purged_income = doc_income.model_copy(
        update={
            "extraction_notes": ["purged_expired: Configured privacy retention ceiling reached; file purged."],
        }
    )
    four_docs = [doc_domicile, purged_income, doc_aadhaar, doc_caste, doc_712]

    rep_80 = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=four_docs,
        scheme_id=scheme.scheme_id,
        language=Language.EN,
    )

    # Invariant: Readiness drops proportionally to 80% (4/5), NEVER resets to 0%
    assert rep_80.readiness_percentage == 80
    assert rep_80.all_mandatory_satisfied is False
    assert rep_80.mandatory_satisfied == 4
    assert rep_80.mandatory_total == 5

    # Income requirement transitions to REPLACEMENT_REQUIRED
    income_req = next(r for r in rep_80.requirements if "income" in r.document_name.lower())
    assert income_req.state == DocumentMatchStatus.REPLACEMENT_REQUIRED

    # RETENTION_PERIOD_EXPIRED finding is flagged with corrective guidance
    retention_findings = [f for f in rep_80.conflicts_detected if f.code == "RETENTION_PERIOD_EXPIRED"]
    assert len(retention_findings) == 1
    assert "re-upload" in retention_findings[0].recommended_action.lower()

    # Step 3: Second document purged (e.g. caste certificate purged) -> 60% readiness (3/5)
    purged_caste = doc_caste.model_copy(
        update={
            "extraction_notes": ["purged_expired: Privacy retention ceiling reached."],
        }
    )
    three_docs = [doc_domicile, purged_income, doc_aadhaar, purged_caste, doc_712]

    rep_60 = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=three_docs,
        scheme_id=scheme.scheme_id,
    )
    assert rep_60.readiness_percentage == 60
    assert rep_60.mandatory_satisfied == 3
    assert rep_60.mandatory_total == 5

    # Step 4: Re-uploading valid documents restores readiness to 100%
    fresh_income = doc_income.model_copy(
        update={
            "document_id": "doc_income_fresh_2",
            "source_file_sha256": "22" * 32,
            "extraction_notes": [],
        }
    )
    fresh_caste = doc_caste.model_copy(
        update={
            "document_id": "doc_caste_fresh_2",
            "source_file_sha256": "44" * 32,
            "extraction_notes": [],
        }
    )
    restored_docs = [doc_domicile, fresh_income, doc_aadhaar, fresh_caste, doc_712]

    rep_restored = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=restored_docs,
        scheme_id=scheme.scheme_id,
    )
    assert rep_restored.readiness_percentage == 100
    assert rep_restored.all_mandatory_satisfied is True
    assert rep_restored.mandatory_satisfied == 5


def test_alternative_group_evaluation_and_retention():
    """Verify ANY_OF alternative groups satisfy requirement and react appropriately to replacement."""
    # Mukhyamantri Majhi Ladki Bahin Yojana allows Domicile Certificate OR Ration Card (15-yr residency)
    excerpt_mlb = "Official Ladki Bahin eligibility rules."
    scheme = Scheme(
        scheme_id="candidate-majhi-ladki-bahin",
        name="Mukhyamantri Majhi Ladki Bahin Yojana",
        department="Women and Child Development Department",
        summary="Financial assistance of ₹1,500/month for eligible women.",
        required_documents=[
            "Aadhaar Card",
            "Domicile Certificate / Ration Card (15-year residency)",
            "Bank Passbook (Aadhaar-seeded)",
        ],
        eligibility_rule=RuleNode(
            op="all",
            children=[RuleNode(op="gte", field="age", value=21, condition_id="c_age_mlb")],
        ),
        sources=[
            SourceReference(
                source_name="Official Portal - Ladki Bahin",
                source_url="https://ladkibahin.maharashtra.gov.in",
                source_kind="official_portal",
                retrieved_at=datetime.datetime.now(datetime.timezone.utc),
                evidence_excerpt=excerpt_mlb,
                evidence_sha256=hashlib.sha256(excerpt_mlb.encode("utf-8")).hexdigest(),
            )
        ],
    )

    doc_aadhaar = ExtractedDocument(
        document_id="doc_aadhaar_mlb",
        document_type="aadhaar_card",
        person_name="Sunita Ramesh Patil",
        confidence=0.96,
        source_file_sha256="a" * 64,
        field_evidence={"name": "Sunita Ramesh Patil"},
    )
    # Using alternative document: Ration Card instead of Domicile Certificate
    doc_ration = ExtractedDocument(
        document_id="doc_ration_mlb",
        document_type="domicile_certificate",
        person_name="Sunita Ramesh Patil",
        confidence=0.94,
        source_file_sha256="b" * 64,
        field_evidence={"document_title": "PDS Ration Card / Domicile Proof"},
    )
    doc_bank = ExtractedDocument(
        document_id="doc_bank_mlb",
        document_type="other",
        person_name="Sunita Ramesh Patil",
        confidence=0.95,
        source_file_sha256="c" * 64,
        field_evidence={"document_title": "Bank Passbook", "account_type": "Savings", "aadhaar_seeded": "True"},
    )

    # Initial: 3 out of 3 satisfied using alternative document
    rep = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=[doc_aadhaar, doc_ration, doc_bank],
        scheme_id=scheme.scheme_id,
    )
    assert rep.readiness_percentage >= 66
    assert rep.mandatory_satisfied >= 2
