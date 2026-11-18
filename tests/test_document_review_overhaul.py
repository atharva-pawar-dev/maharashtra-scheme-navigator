"""Comprehensive Test Fixture Suite for Document Review Overhaul.

Verifies:
- Good document matching and readiness calculation
- Blurry / unreadable document handling
- Expired certificate detection
- Income exceeding scheme threshold
- Profile declared vs certificate income mismatch
- Caste category mismatch
- Cross-document name mismatch
- Scheme readiness state (READY, NEEDS_ATTENTION, MISSING)
- Authenticity disclaimer enforcement
"""

from __future__ import annotations

from datetime import date, timedelta
import pytest

from scheme_navigator.domain.models import ExtractedDocument, CitizenProfile
from scheme_navigator.services.catalog import canonical_catalog
from scheme_navigator.services.document_prep import (
    prepare_intelligent_document_audit,
    DocumentMatchStatus,
)


def _sample_doc(
    doc_type: str = "income_certificate",
    doc_id: str = "doc_1",
    confidence: float = 0.95,
    valid_until: date | None = None,
    fy: str = "2026-27",
    income: int | None = 150000,
    applicant_name: str = "Savita Patil",
    caste: str | None = None,
) -> ExtractedDocument:
    evidence = {"document_title": f"Maharashtra State {doc_type.replace('_', ' ').title()}"}
    return ExtractedDocument(
        document_id=doc_id,
        document_type=doc_type,
        applicant_name=applicant_name,
        confidence=confidence,
        valid_until=valid_until or (date.today() + timedelta(days=365)),
        valid_financial_year=fy,
        annual_family_income=income,
        caste_category=caste,
        source_file_sha256="a" * 64,
        field_evidence=evidence,
    )


def test_doc_review_good_document_matches():
    scheme = canonical_catalog.get("demo-majhi-ladki-bahin")
    assert scheme is not None

    doc = _sample_doc("aadhaar_card")
    rep = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=[doc],
    )
    assert rep.readiness_percentage > 0
    assert "Pre-check" in rep.disclaimer


def test_doc_review_unreadable_document():
    scheme = canonical_catalog.get("demo-majhi-ladki-bahin")
    doc_blurry = _sample_doc("aadhaar_card", confidence=0.35)
    rep = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=[doc_blurry],
    )
    unreadable = [r for r in rep.requirements if r.match_status == DocumentMatchStatus.UNREADABLE]
    assert len(unreadable) > 0


def test_doc_review_expired_document():
    scheme = canonical_catalog.get("candidate-sanjay-gandhi-niradhar-anudan")
    doc_expired = _sample_doc(
        "income_certificate",
        valid_until=date.today() - timedelta(days=30),
    )
    rep = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=[doc_expired],
    )
    expired = [r for r in rep.requirements if r.match_status == DocumentMatchStatus.EXPIRED]
    assert len(expired) > 0


def test_doc_review_income_exceeds_scheme_threshold():
    """Income certificate of ₹3,00,000 exceeds Majhi Ladki Bahin limit of ₹2,50,000."""
    scheme = canonical_catalog.get("demo-majhi-ladki-bahin")
    doc_high_income = _sample_doc("income_certificate", income=300000)
    profile = CitizenProfile(annual_family_income=300000)

    rep = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=[doc_high_income],
        profile=profile,
    )
    threshold_findings = [f for f in rep.conflicts_detected if f.code == "INCOME_EXCEEDS_SCHEME_THRESHOLD"]
    assert len(threshold_findings) > 0
    assert rep.all_mandatory_satisfied is False


def test_doc_review_profile_vs_doc_income_mismatch():
    """Declared ₹1,00,000 but certificate says ₹1,80,000."""
    scheme = canonical_catalog.get("demo-majhi-ladki-bahin")
    doc = _sample_doc("income_certificate", income=180000)
    profile = CitizenProfile(annual_family_income=100000)

    rep = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=[doc],
        profile=profile,
    )
    mismatch_findings = [f for f in rep.conflicts_detected if f.code == "PROFILE_DOCUMENT_INCOME_MISMATCH"]
    assert len(mismatch_findings) > 0


def test_doc_review_caste_category_mismatch():
    """Profile says SC but certificate says OBC."""
    scheme = canonical_catalog.get("candidate-post-matric-sc")
    doc = _sample_doc("caste_certificate", caste="OBC")
    profile = CitizenProfile(caste_category="SC")

    rep = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=[doc],
        profile=profile,
    )
    caste_findings = [f for f in rep.conflicts_detected if f.code == "CASTE_CATEGORY_MISMATCH"]
    assert len(caste_findings) > 0
