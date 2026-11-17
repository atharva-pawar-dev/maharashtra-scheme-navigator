from __future__ import annotations

import hashlib
from datetime import date

from scheme_navigator.documents.audit import audit_extracted_documents
from scheme_navigator.domain.models import ExtractedDocument


def document(doc_id: str, *, kind: str = "income_certificate", name: str | None = "Asha Patil", dob: str | None = "2000-01-01", fy: str | None = "2026-27", until: str | None = None, confidence: float = .96) -> ExtractedDocument:
    return ExtractedDocument(
        document_id=doc_id,
        document_type=kind,
        person_name=name,
        date_of_birth=dob,
        valid_until=until,
        valid_financial_year=fy,
        annual_family_income=180000,
        income_currency="INR",
        confidence=confidence,
        source_file_sha256=hashlib.sha256(doc_id.encode()).hexdigest(),
    )


def test_financial_year_mismatch_is_warning_for_explicit_fy():
    result = audit_extracted_documents([document("one", fy="2025-26")], today=date(2026, 10, 27))
    assert any(item.code == "FINANCIAL_YEAR_MISMATCH" for item in result.findings)
    assert result.status == "review_required"


def test_dob_mismatch_is_error():
    docs = [document("one"), document("two", kind="domicile_certificate", dob="2001-01-01", fy=None)]
    result = audit_extracted_documents(docs, today=date(2026, 10, 27))
    assert any(item.code == "DOB_MISMATCH" for item in result.findings)
    assert result.status == "issues_found"
    assert result.cross_document_dob_match is False


def test_domicile_is_not_expired_just_because_fy_absent():
    result = audit_extracted_documents([document("one", kind="domicile_certificate", fy=None)], today=date(2026, 10, 27))
    assert not any(item.code in {"INCOME_FY_NOT_EXTRACTED", "FINANCIAL_YEAR_MISMATCH"} for item in result.findings)


def test_expired_certificate_flagged():
    result = audit_extracted_documents([document("one", until="2026-01-01")], today=date(2026, 10, 27))
    assert any(item.code == "CERTIFICATE_EXPIRED" for item in result.findings)


def test_cross_script_names_require_review_not_automatic_mismatch():
    docs = [
        document("latin", name="Asha Patil"),
        document("devanagari", kind="domicile_certificate", name="आशा पाटील", fy=None),
    ]
    result = audit_extracted_documents(docs, today=date(2026, 10, 27))
    assert any(item.code == "CROSS_SCRIPT_NAME_REVIEW" for item in result.findings)
    assert not any(item.code == "NAME_MISMATCH" for item in result.findings)



def test_matching_names_and_dates_of_birth_pass_cross_document_checks():
    docs = [
        document("income", name="Asha Patil", dob="2000-01-01", fy="2026-27"),
        document(
            "domicile",
            kind="domicile_certificate",
            name="Asha Patil",
            dob="2000-01-01",
            fy=None,
        ),
    ]

    result = audit_extracted_documents(docs, today=date(2026, 10, 27))

    assert result.status == "pass"
    assert result.cross_document_name_match == 1.0
    assert result.cross_document_dob_match is True
    assert not any(
        item.code in {"NAME_MISMATCH", "DOB_MISMATCH"}
        for item in result.findings
    )


def test_name_and_dob_mismatches_are_flagged_for_manual_review():
    docs = [
        document("income", name="Asha Patil", dob="2000-01-01"),
        document(
            "domicile",
            kind="domicile_certificate",
            name="Riya Deshmukh",
            dob="2001-02-02",
            fy=None,
        ),
    ]

    result = audit_extracted_documents(docs, today=date(2026, 10, 27))
    codes = {item.code for item in result.findings}

    assert "NAME_MISMATCH" in codes
    assert "DOB_MISMATCH" in codes
    assert result.status == "issues_found"
    assert result.cross_document_dob_match is False
    assert result.cross_document_name_match is not None
    assert result.cross_document_name_match < 0.88


def test_missing_income_fields_are_not_invented_and_require_review():
    incomplete = document(
        "incomplete-income",
        kind="income_certificate",
        name=None,
        dob=None,
        fy=None,
        confidence=0.40,
    ).model_copy(update={"annual_family_income": None})

    result = audit_extracted_documents(
        [incomplete],
        target_financial_year="2026-27",
        today=date(2026, 10, 27),
    )
    codes = {item.code for item in result.findings}

    assert incomplete.person_name is None
    assert incomplete.date_of_birth is None
    assert incomplete.annual_family_income is None
    assert "LOW_EXTRACTION_CONFIDENCE" in codes
    assert "INCOME_FY_NOT_EXTRACTED" in codes
    assert "INCOME_AMOUNT_NOT_EXTRACTED" in codes
    assert result.status == "review_required"
