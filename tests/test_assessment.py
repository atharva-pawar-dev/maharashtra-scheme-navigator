
from __future__ import annotations

import hashlib

from scheme_navigator.domain.models import (
    ApplicantAssessmentRequest,
    CitizenProfile,
    ExtractedDocument,
)
from scheme_navigator.services.assessment import build_applicant_assessment
from scheme_navigator.services.catalog import SchemeCatalog
from datetime import date


def make_income_document(
    income: int,
    currency: str = "INR",
    date_of_birth: date | None = None,
) -> ExtractedDocument:
    return ExtractedDocument(
        document_id="synthetic-income-001",
        document_type="income_certificate",
        person_name="Demo Citizen",
        date_of_birth=date_of_birth,
        annual_family_income=income,
        income_currency=currency,
        valid_financial_year="2026-27",
        confidence=0.95,
        source_file_sha256=hashlib.sha256(
            b"synthetic-income-document"
        ).hexdigest(),
        field_evidence={
            "annual_family_income": "Synthetic annual income evidence"
        },
    )


def get_demo_scheme():
    return next(
        scheme
        for scheme in SchemeCatalog.from_json().all()
        if scheme.scheme_id == "demo-majhi-ladki-bahin"
    )


def test_assessment_flags_profile_document_income_mismatch():
    profile = CitizenProfile(
        age_years=24,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=200000,
        aadhaar_linked_bank_account=True,
        documents_available=["income certificate"],
    )

    document = make_income_document(180000)

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[document],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(
        get_demo_scheme(),
        payload,
    )

    finding = next(
        item
        for item in result.document_audit.findings
        if item.code == "PROFILE_DOCUMENT_INCOME_MISMATCH"
    )

    assert finding.severity == "warning"
    assert finding.category == "document_consistency"
    assert finding.recommended_action
    assert "synthetic-income-001" in finding.document_ids

    # Neither source should be overwritten.
    assert profile.annual_family_income == 200000
    assert document.annual_family_income == 180000

    assert result.eligibility.status.value == "needs_review"


def test_assessment_does_not_flag_matching_income_values():
    profile = CitizenProfile(
        annual_family_income=180000,
    )

    document = make_income_document(180000)

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[document],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(
        get_demo_scheme(),
        payload,
    )

    assert not any(
        item.code == "PROFILE_DOCUMENT_INCOME_MISMATCH"
        for item in result.document_audit.findings
    )


def test_assessment_uses_pending_human_review_record():
    from scheme_navigator.documents.audit import audit_extracted_documents

    document = make_income_document(180000)
    audit = audit_extracted_documents(
        [document],
        target_financial_year="2026-27",
    )

    review_record = {
        "review_id": "synthetic-review-pending-001",
        "status": "pending_review",
        "extracted_documents": [document.model_dump(mode="json")],
        "audit": audit.model_dump(mode="json"),
    }

    payload = ApplicantAssessmentRequest(
        profile=CitizenProfile(annual_family_income=200000),
        documents=[],
    )

    result = build_applicant_assessment(
        get_demo_scheme(),
        payload,
        review_record=review_record,
    )

    assert result.human_review_status == "pending_review"
    assert result.human_review_id == "synthetic-review-pending-001"
    assert result.document_authenticity_status == "not_verified"

    assert any(
        item.code == "PROFILE_DOCUMENT_INCOME_MISMATCH"
        for item in result.document_audit.findings
    )


def test_assessment_uses_completed_human_review_record():
    from scheme_navigator.documents.audit import audit_extracted_documents

    document = make_income_document(180000)
    audit = audit_extracted_documents(
        [document],
        target_financial_year="2026-27",
    )

    review_record = {
        "review_id": "synthetic-review-completed-001",
        "status": "review_completed",
        "extracted_documents": [document.model_dump(mode="json")],
        "audit": audit.model_dump(mode="json"),
    }

    payload = ApplicantAssessmentRequest(
        profile=CitizenProfile(annual_family_income=200000),
        documents=[],
    )

    result = build_applicant_assessment(
        get_demo_scheme(),
        payload,
        review_record=review_record,
    )

    assert result.human_review_status == "review_completed"
    assert result.human_review_id == "synthetic-review-completed-001"
    assert result.document_authenticity_status == "not_verified"
    assert any(
        item.code == "human-review:completed"
        for item in result.next_actions
    )

def test_assessment_does_not_flag_matching_dob():
    dob = date(2000, 1, 1)

    profile = CitizenProfile(
        date_of_birth=dob,
    )

    document = make_income_document(
        income=180000,
        date_of_birth=dob,
    )

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[document],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(
        get_demo_scheme(),
        payload,
    )

    assert not any(
        item.code == "PROFILE_DOCUMENT_DOB_MISMATCH"
        for item in result.document_audit.findings
    )


def test_assessment_flags_different_dob():
    profile_dob = date(2000, 1, 1)
    document_dob = date(2000, 2, 1)

    profile = CitizenProfile(
        date_of_birth=profile_dob,
    )

    document = make_income_document(
        income=180000,
        date_of_birth=document_dob,
    )

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[document],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(
        get_demo_scheme(),
        payload,
    )

    finding = next(
        item
        for item in result.document_audit.findings
        if item.code == "PROFILE_DOCUMENT_DOB_MISMATCH"
    )

    assert finding.severity == "warning"
    assert finding.category == "document_consistency"
    assert finding.recommended_action
    assert "synthetic-income-001" in finding.document_ids

    # Neither value should be automatically overwritten.
    assert profile.date_of_birth == profile_dob
    assert document.date_of_birth == document_dob


def test_assessment_flags_age_dob_mismatch():
    today = date.today()

    document_dob = date(
        today.year - 30,
        1,
        1,
    )

    profile = CitizenProfile(
        age_years=24,
    )

    document = make_income_document(
        income=180000,
        date_of_birth=document_dob,
    )

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[document],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(
        get_demo_scheme(),
        payload,
    )

    finding = next(
        item
        for item in result.document_audit.findings
        if item.code == "PROFILE_DOCUMENT_AGE_MISMATCH"
    )

    assert finding.severity == "warning"
    assert finding.category == "document_consistency"
    assert "synthetic-income-001" in finding.document_ids

    # Original applicant age and extracted DOB remain unchanged.
    assert profile.age_years == 24
    assert document.date_of_birth == document_dob


def test_assessment_does_not_flag_missing_dob():
    profile = CitizenProfile(
        age_years=24,
    )

    document = make_income_document(
        income=180000,
        date_of_birth=None,
    )

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[document],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(
        get_demo_scheme(),
        payload,
    )

    assert not any(
        item.code in {
            "PROFILE_DOCUMENT_DOB_MISMATCH",
            "PROFILE_DOCUMENT_AGE_MISMATCH",
        }
        for item in result.document_audit.findings
    )

def test_assessment_does_not_flag_matching_profile_document_name():
    profile = CitizenProfile(
        name="  DEMO   CITIZEN ",
    )

    document = make_income_document(180000)

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[document],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(get_demo_scheme(), payload)

    assert not any(
        item.code in {
            "PROFILE_DOCUMENT_NAME_MISMATCH",
            "PROFILE_DOCUMENT_NAME_REVIEW",
        }
        for item in result.document_audit.findings
    )


def test_assessment_flags_profile_document_name_mismatch():
    profile_name = "Atharva Pawar"

    profile = CitizenProfile(name=profile_name)
    document = make_income_document(180000)

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[document],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(get_demo_scheme(), payload)

    finding = next(
        item for item in result.document_audit.findings
        if item.code == "PROFILE_DOCUMENT_NAME_MISMATCH"
    )

    assert finding.severity == "warning"
    assert finding.category == "document_consistency"
    assert finding.recommended_action
    assert document.document_id in finding.document_ids

    assert profile.name == profile_name
    assert document.person_name == "Demo Citizen"


def test_assessment_flags_profile_document_cross_script_name():
    profile = CitizenProfile(name="अथर्व पवार")
    document = make_income_document(180000)

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[document],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(get_demo_scheme(), payload)

    finding = next(
        item for item in result.document_audit.findings
        if item.code == "PROFILE_DOCUMENT_NAME_REVIEW"
    )

    assert finding.severity == "warning"
    assert finding.document_ids == [document.document_id]


def test_assessment_does_not_flag_missing_profile_or_document_name():
    profile = CitizenProfile()

    document = make_income_document(180000).model_copy(
        update={"person_name": None}
    )

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[document],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(get_demo_scheme(), payload)

    assert not any(
        item.code in {
            "PROFILE_DOCUMENT_NAME_MISMATCH",
            "PROFILE_DOCUMENT_NAME_REVIEW",
        }
        for item in result.document_audit.findings
    )

def test_uploaded_income_certificate_in_review_record_is_counted_for_planning():
    from scheme_navigator.documents.audit import audit_extracted_documents

    document = make_income_document(180000).model_copy(
        update={"valid_financial_year": "2025-26"}
    )

    audit = audit_extracted_documents(
        [document],
        target_financial_year="2026-27",
    )

    review_record = {
        "review_id": "synthetic-review-planner-001",
        "status": "pending_review",
        "extracted_documents": [document.model_dump(mode="json")],
        "audit": audit.model_dump(mode="json"),
    }

    profile = CitizenProfile(
        age_years=24,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=180000,
        aadhaar_linked_bank_account=True,
        documents_available=[],
    )

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(
        get_demo_scheme(),
        payload,
        review_record=review_record,
    )

    plan_text = str(result.application_plan)

    # Uploaded document should not be requested again.
    assert "Obtain Income Certificate" not in plan_text

    # The document must still be subject to review.
    assert result.human_review_status == "pending_review"
    assert result.document_authenticity_status == "not_verified"

    # The financial-year mismatch must not be hidden.
    assert any(
        item.code == "FINANCIAL_YEAR_MISMATCH"
        for item in result.document_audit.findings
    )


def test_uploaded_income_certificate_is_counted_as_available_for_planning():
    profile = CitizenProfile(
        age_years=24,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=180000,
        aadhaar_linked_bank_account=True,
        documents_available=[],
    )

    document = make_income_document(180000)

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[document],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(
        get_demo_scheme(),
        payload,
    )

    plan_text = str(result.application_plan)

    assert "Obtain Income Certificate" not in plan_text


def test_unknown_document_type_does_not_satisfy_income_certificate_requirement():
    profile = CitizenProfile(
        age_years=24,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=180000,
        aadhaar_linked_bank_account=True,
        documents_available=[],
    )

    document = make_income_document(180000).model_copy(
        update={"document_type": "unknown"}
    )

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[document],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(
        get_demo_scheme(),
        payload,
    )

    plan_text = str(result.application_plan)

    assert "Obtain Income Certificate" in plan_text


def test_applicant_declared_income_certificate_remains_available_for_planning():
    profile = CitizenProfile(
        age_years=24,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=180000,
        aadhaar_linked_bank_account=True,
        documents_available=["income certificate"],
    )

    payload = ApplicantAssessmentRequest(
        profile=profile,
        documents=[],
        target_financial_year="2026-27",
    )

    result = build_applicant_assessment(
        get_demo_scheme(),
        payload,
    )

    plan_text = str(result.application_plan)

    assert "Obtain Income Certificate" not in plan_text
