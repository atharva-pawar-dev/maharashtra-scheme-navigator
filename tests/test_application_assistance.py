from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.domain.models import (
    ApplicantAssessmentRequest,
    CitizenProfile,
    ExtractedDocument,
    Language,
    RuleNode,
    Scheme,
    SourceReference,
)
from scheme_navigator.services.assessment import build_applicant_assessment
from scheme_navigator.services.document_prep import (
    DocumentMatchStatus,
    prepare_intelligent_document_audit,
)
from scheme_navigator.services.portal_assistance import (
    FieldFillSource,
    PortalTarget,
    build_portal_application_package,
)


def _make_sample_scheme() -> Scheme:
    excerpt = "Beneficiaries must submit domicile and income proof under Government of Maharashtra guidelines."
    ex_hash = sha256(excerpt.encode("utf-8")).hexdigest()
    return Scheme(
        scheme_id="test-scholarship-scheme",
        name="Post-Matric Scholarship Scheme for Testing",
        department="Social Justice and Special Assistance Department",
        summary="A test post-matric scholarship scheme for testing intelligent preparation.",
        benefits=["Tuition fee waiver", "Maintenance allowance of Rs. 1000/month"],
        required_documents=[
            "Income Certificate",
            "Domicile Certificate",
            "Caste Certificate",
        ],
        eligibility_rule=RuleNode(
            op="all",
            children=[
                RuleNode(op="eq", field="resident_state", value="maharashtra", condition_id="c1"),
                RuleNode(op="lte", field="annual_family_income", value=250000, condition_id="c2"),
            ],
        ),
        sources=[
            SourceReference(
                source_name="GR No. SCH-2024/CR-101/Edu-2",
                source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/20240701.pdf",
                source_kind="government_resolution",
                retrieved_at=datetime(2024, 7, 1, tzinfo=timezone.utc),
                evidence_excerpt=excerpt,
                evidence_sha256=ex_hash,
                page_or_section="Para 4",
            )
        ],
        rule_version="1.0.0",
        rule_status="draft",
        publication_authorized=False,
    )


def test_document_preparation_alternatives_and_matching():
    scheme = _make_sample_scheme()

    # 1. Provide an alternative document for Domicile (15-year Ration Card)
    # and valid income certificate for FY 2026-27
    doc_income = ExtractedDocument(
        document_id="doc-inc-01",
        document_type="income_certificate",
        person_name="Sunita Patil",
        annual_family_income=120000,
        valid_financial_year="2026-27",
        confidence=0.92,
        source_file_sha256="1" * 64,
    )

    doc_domicile_alt = ExtractedDocument(
        document_id="doc-ration-01",
        document_type="other",
        field_evidence={"document_title": "15-year Ration Card"},
        extraction_notes=["Alternative: 15-year Ration Card"],
        person_name="Sunita Patil",
        confidence=0.88,
        source_file_sha256="2" * 64,
    )

    report = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=[doc_income, doc_domicile_alt],
        target_financial_year="2026-27",
        language=Language.EN,
        today=date(2026, 8, 1),
    )

    assert report.scheme_id == scheme.scheme_id
    assert report.all_mandatory_satisfied is False  # Caste certificate is still missing

    # Income certificate directly matched
    req_income = next(r for r in report.requirements if "income" in r.requirement_id)
    assert req_income.match_status == DocumentMatchStatus.MATCHED
    assert req_income.matched_document_id == "doc-inc-01"
    assert "Tehsildar" in req_income.issuing_authority

    # Domicile matched via alternative
    req_dom = next(r for r in report.requirements if "domicile" in r.requirement_id)
    assert req_dom.match_status == DocumentMatchStatus.ALTERNATIVE_MATCHED
    assert req_dom.alternative_used == "15-year Ration Card"

    # Caste certificate is missing
    req_caste = next(r for r in report.requirements if "caste" in r.requirement_id)
    assert req_caste.match_status == DocumentMatchStatus.MISSING
    assert req_caste.rts_notified_days == 21
    assert "Sub-Divisional Officer" in req_caste.issuing_authority


def test_document_preparation_expiry_and_fy_mismatch():
    scheme = _make_sample_scheme()

    # Expired document
    doc_expired = ExtractedDocument(
        document_id="doc-exp-01",
        document_type="income_certificate",
        valid_until=date(2025, 3, 31),
        valid_financial_year="2024-25",
        confidence=0.90,
        source_file_sha256="3" * 64,
    )

    report = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=[doc_expired],
        target_financial_year="2026-27",
        today=date(2026, 8, 1),
    )

    req_income = next(r for r in report.requirements if "income" in r.requirement_id)
    assert req_income.match_status == DocumentMatchStatus.EXPIRED
    assert "expired on 2025-03-31" in req_income.explanation


def test_document_preparation_duplicate_detection():
    scheme = _make_sample_scheme()

    same_hash = "f" * 64
    doc1 = ExtractedDocument(
        document_id="doc-dup-01",
        document_type="income_certificate",
        source_file_sha256=same_hash,
    )
    doc2 = ExtractedDocument(
        document_id="doc-dup-02",
        document_type="income_certificate",
        source_file_sha256=same_hash,
    )

    report = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=[doc1, doc2],
    )

    assert len(report.duplicates_detected) >= 1
    assert any(f.code == "DUPLICATE_DOCUMENT_UPLOAD" for f in report.conflicts_detected)


def test_safe_portal_assistance_invariants():
    scheme = _make_sample_scheme()
    profile = CitizenProfile(
        name="Sunita Patil",
        gender="female",
        resident_state="maharashtra",
        annual_family_income=150000,
    )

    pkg = build_portal_application_package(
        scheme=scheme,
        profile=profile,
        extracted_documents=[],
        language=Language.MR,
    )

    # Invariants
    assert pkg.target_portal == PortalTarget.MAHADBT
    assert pkg.requires_explicit_citizen_confirmation is True
    assert pkg.application_submission_status == "not_submitted_guidance_only"
    assert "सुरक्षित पोर्टल सहाय्यता हमी" in pkg.security_disclaimer

    # Restricted security field for Aadhaar OTP
    otp_field = next(f for f in pkg.field_mappings if f.portal_field_id == "aadhaar_authentication")
    assert otp_field.source == FieldFillSource.RESTRICTED_SECURITY_FIELD
    assert otp_field.is_sensitive is True
    assert "DO NOT ENTER" in (otp_field.suggested_value or "")

    # Name mapping
    name_field = next(f for f in pkg.field_mappings if f.portal_field_id == "applicant_full_name")
    assert name_field.suggested_value == "Sunita Patil"
    assert name_field.source == FieldFillSource.PROFILE_REPORTED


def test_applicant_assessment_integration_with_phase5():
    scheme = _make_sample_scheme()
    profile = CitizenProfile(
        name="Sunita Patil",
        gender="female",
        resident_state="maharashtra",
        annual_family_income=120000,
    )

    doc_inc = ExtractedDocument(
        document_id="doc-eval-01",
        document_type="income_certificate",
        person_name="Sunita Patil",
        annual_family_income=120000,
        valid_financial_year="2026-27",
        confidence=0.95,
        source_file_sha256="4" * 64,
    )

    req = ApplicantAssessmentRequest(
        profile=profile,
        documents=[doc_inc],
        target_financial_year="2026-27",
    )

    resp = build_applicant_assessment(scheme=scheme, payload=req)

    assert resp.scheme_id == scheme.scheme_id
    assert resp.document_prep_report is not None
    assert resp.portal_guidance is not None
    assert resp.portal_guidance.requires_explicit_citizen_confirmation is True
    assert resp.portal_guidance.application_submission_status == "not_submitted_guidance_only"


def test_assistance_api_routes():
    client = TestClient(app)

    # Test audit-and-prepare route
    payload_doc = {
        "scheme_id": "candidate-majhi-ladki-bahin",
        "documents": [
            {
                "document_id": "test-doc-api-01",
                "document_type": "income_certificate",
                "person_name": "Kavita Shinde",
                "annual_family_income": 180000,
                "valid_financial_year": "2026-27",
                "confidence": 0.90,
                "source_file_sha256": "5" * 64,
            }
        ],
        "target_financial_year": "2026-27",
        "language": "en",
    }
    # Using candidate or active scheme in catalog
    catalog_schemes = client.get("/schemes").json()
    if catalog_schemes:
        sid = catalog_schemes[0]["scheme_id"]
        res_doc = client.post(
            "/assistance/documents/audit-and-prepare",
            json={
                "scheme_id": sid,
                "documents": payload_doc["documents"],
                "target_financial_year": "2026-27",
                "language": "en",
            },
        )
        assert res_doc.status_code == 200
        data = res_doc.json()
        assert "requirements" in data
        assert "all_mandatory_satisfied" in data

        # Test portal guidance route
        res_portal = client.post(
            "/assistance/portal/guidance",
            json={
                "scheme_id": sid,
                "profile": {
                    "name": "Kavita Shinde",
                    "annual_family_income": 180000,
                    "resident_state": "maharashtra",
                },
                "documents": payload_doc["documents"],
                "language": "en",
            },
        )
        assert res_portal.status_code == 200
        pdata = res_portal.json()
        assert pdata["requires_explicit_citizen_confirmation"] is True
        assert pdata["application_submission_status"] == "not_submitted_guidance_only"
        assert len(pdata["preparation_steps"]) >= 4
