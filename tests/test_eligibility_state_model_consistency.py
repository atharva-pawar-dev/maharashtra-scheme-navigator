from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
from pathlib import Path
import pytest

from scheme_navigator.domain.evidence import (
    OfficialSourceType,
    RuleEvidence,
    RuleVerificationStatus,
)
from scheme_navigator.domain.models import (
    CitizenProfile,
    EligibilityResult,
    EligibilityStatus,
    Language,
    RuleNode,
    Scheme,
    SourceReference,
)
from scheme_navigator.services.rule_engine import (
    check_production_eligibility_gate,
    evaluate_scheme,
    has_non_demo_approval_metadata,
)


def _make_verified_scheme(scheme_id: str = "scheme-verified-01") -> Scheme:
    excerpt = "Official statutory approved rule criteria for state scheme."
    h = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
    doc_hash = hashlib.sha256(b"official_gazette_pdf_bytes_checksum").hexdigest()
    
    ev_age = RuleEvidence(
        condition_id="c_age_verified",
        source_title="Maharashtra Government Gazette Vol 45",
        official_reference="GR-SJ-2026-CONFIRMED-8899",
        official_source_url="https://maharashtra.gov.in/gazette/verified",
        source_type=OfficialSourceType.GAZETTE_NOTIFICATION,
        publication_date=date(2026, 1, 1),
        effective_from=date(2026, 1, 1),
        verbatim_excerpt="Age must be at least 18 years for verified eligibility.",
        excerpt_language=Language.MR,
        source_document_sha256=doc_hash,
        verification_status=RuleVerificationStatus.LEGAL_APPROVED,
        verified_by="Adv. Ramesh Deshmukh, Legal Remembrancer",
        verification_timestamp=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
    )
    ev_income = RuleEvidence(
        condition_id="c_income_verified",
        source_title="Maharashtra Government Gazette Vol 45",
        official_reference="GR-SJ-2026-CONFIRMED-8899",
        official_source_url="https://maharashtra.gov.in/gazette/verified",
        source_type=OfficialSourceType.GAZETTE_NOTIFICATION,
        publication_date=date(2026, 1, 1),
        effective_from=date(2026, 1, 1),
        verbatim_excerpt="Annual family income must not exceed Rs 150000.",
        excerpt_language=Language.MR,
        source_document_sha256=doc_hash,
        verification_status=RuleVerificationStatus.LEGAL_APPROVED,
        verified_by="Adv. Ramesh Deshmukh, Legal Remembrancer",
        verification_timestamp=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
    )

    return Scheme(
        scheme_id=scheme_id,
        name="Verified Maharashtra Scheme",
        department="Social Justice and Special Assistance",
        summary="Statutory welfare benefit",
        required_documents=["Aadhaar Card"],
        rule_status="active",
        approved_by="Principal Secretary, Social Justice Department",
        approval_reference="GR-SJ-2026-CONFIRMED-8899",
        last_verified_at=date(2026, 11, 1),
        publication_authorized=True,
        eligibility_rule=RuleNode(
            op="all",
            children=[
                RuleNode(op="gte", field="age", value=18, condition_id="c_age_verified"),
                RuleNode(op="lte", field="annual_family_income", value=150000, condition_id="c_income_verified"),
            ],
        ),
        sources=[
            SourceReference(
                source_name="Maharashtra Government Gazette",
                source_url="https://maharashtra.gov.in/gazette/verified",
                source_kind="official_scheme_page",
                retrieved_at=datetime.now(timezone.utc),
                evidence_excerpt=excerpt,
                evidence_sha256=h,
            )
        ],
        evidence=[ev_age, ev_income],
    )


def test_meets_verified_criteria_enum_consistency():
    """Verify MEETS_VERIFIED_CRITERIA is recognized as confirmed eligibility status."""
    assert EligibilityStatus.MEETS_VERIFIED_CRITERIA == "meets_verified_criteria"
    # Backward compatibility alias
    assert EligibilityStatus.ELIGIBLE == "eligible"


def test_production_gate_and_confirmed_eligibility():
    """Verify that a compliant scheme evaluated with satisfying profile yields confirmed eligibility."""
    scheme = _make_verified_scheme()
    profile = CitizenProfile(
        age_years=25,
        annual_family_income=120000,
        resident_state="Maharashtra",
    )

    is_gate_ok, gate_msg = check_production_eligibility_gate(scheme)
    assert is_gate_ok, f"Gate failed unexpectedly: {gate_msg}"

    res = evaluate_scheme(scheme, profile)
    # The evaluation must reflect verified satisfaction
    assert res.status in (EligibilityStatus.MEETS_VERIFIED_CRITERIA, EligibilityStatus.ELIGIBLE)
    assert not res.is_partial
    assert "Preliminary match" in res.reason or "all evaluated requirements satisfied" in res.reason


def test_unapproved_or_demo_fixture_cannot_trigger_confirmed_eligibility():
    """Verify fail-closed invariant: demo fixtures and unapproved rules CANNOT produce confirmed eligibility."""
    excerpt = "Demo fixture guidelines."
    h = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()

    demo_scheme = Scheme(
        scheme_id="demo-unapproved-fixture",
        name="Demo Unapproved Scheme",
        department="Women and Child Development Department",
        summary="Demo test fixture",
        required_documents=["Aadhaar Card"],
        rule_status="active",
        approved_by="local_demo_fixture_only",
        approval_reference="not_for_production_demo",
        last_verified_at=date(2026, 11, 1),
        publication_authorized=False,
        eligibility_rule=RuleNode(
            op="all",
            children=[RuleNode(op="gte", field="age", value=18, condition_id="c_age_demo")],
        ),
        sources=[
            SourceReference(
                source_name="Demo Portal",
                source_url="https://maharashtra.gov.in/demo",
                source_kind="official_scheme_page",
                retrieved_at=datetime.now(timezone.utc),
                evidence_excerpt=excerpt,
                evidence_sha256=h,
            )
        ],
    )

    profile = CitizenProfile(age_years=25)
    assert not has_non_demo_approval_metadata(demo_scheme)

    res = evaluate_scheme(demo_scheme, profile)
    # MUST fail closed to NEEDS_REVIEW (Caseworker Review), never confirmed eligibility
    assert res.status == EligibilityStatus.NEEDS_REVIEW
    assert "demo fixture or lacks non-demo approval metadata" in res.reason


def test_ui_localized_terms_for_meets_verified_criteria():
    """Verify frontend UI strings file contains distinct localized terms for Meets Verified Criteria."""
    static_html_path = Path(__file__).resolve().parents[1] / "static" / "index.html"
    assert static_html_path.exists()
    content = static_html_path.read_text(encoding="utf-8")

    # English
    assert "Meets Verified Criteria" in content
    # Marathi
    assert "पडताळणी निकष पूर्ण" in content
    # Hindi
    assert "सत्यापित मानदंड पूर्ण" in content
    # Scoreboard condition check
    assert "st === 'meets_verified_criteria'" in content
