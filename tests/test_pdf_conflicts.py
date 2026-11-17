from __future__ import annotations

import hashlib
from datetime import date

from scheme_navigator.documents.audit import (
    add_pdf_page_conflict_findings,
    audit_extracted_documents,
)
from scheme_navigator.documents.grouping import find_pdf_page_field_conflicts, group_pdf_page_extractions
from scheme_navigator.domain.models import ExtractedDocument


SOURCE_HASH = hashlib.sha256(b"synthetic-conflicting-pdf").hexdigest()


def document(
    document_id: str,
    *,
    kind: str = "income_certificate",
    name: str | None = "Demo Citizen",
    dob: str | None = "2000-01-01",
    fy: str | None = "2025-26",
    income: int | None = 180000,
    income_currency: str | None = "INR",
    issue_date: str | None = None,
    valid_until: str | None = None,
    certificate_number: str | None = None,
    evidence: dict[str, str] | None = None,
) -> ExtractedDocument:
    return ExtractedDocument(
        document_id=document_id,
        document_type=kind,
        person_name=name,
        date_of_birth=dob,
        valid_financial_year=fy,
        annual_family_income=income,
        income_currency=income_currency,
        issue_date=issue_date,
        valid_until=valid_until,
        certificate_number_masked=certificate_number,
        confidence=0.96,
        source_file_sha256=SOURCE_HASH,
        field_evidence=evidence or {},
        extraction_notes=[],
    )


def codes(findings):
    return [finding.code for finding in findings]


def test_conflicting_income_is_reported_with_page_evidence_and_pages_stay_separate():
    pages = [
        (1, document("page-1", income=180000, evidence={"annual_family_income": "Annual income: INR 180000"})),
        (2, document("page-2", income=280000, evidence={"annual_family_income": "Annual income: INR 280000"})),
    ]

    conflicts = find_pdf_page_field_conflicts(pages)
    groups = group_pdf_page_extractions(pages, SOURCE_HASH)

    assert len(groups) == 2
    assert len(conflicts) == 1
    assert conflicts[0].field_name == "annual_family_income"
    finding = conflicts[0].finding
    assert finding.code == "DOCUMENT_FIELD_CONFLICT"
    assert finding.severity == "warning"
    assert "Page 1" in finding.message
    assert "Page 2" in finding.message
    assert "180000" in finding.message
    assert "280000" in finding.message
    assert finding.document_ids == ["page-1", "page-2"]


def test_conflicting_financial_year_is_reported():
    pages = [
        (1, document("page-1", fy="2024-25")),
        (2, document("page-2", fy="2025-26")),
    ]

    conflicts = find_pdf_page_field_conflicts(pages)

    assert "valid_financial_year" in [item.field_name for item in conflicts]
    finding = next(item.finding for item in conflicts if item.field_name == "valid_financial_year")
    assert finding.code == "DOCUMENT_FIELD_CONFLICT"
    assert "Page 1" in finding.message and "Page 2" in finding.message
    assert "2024-25" in finding.message and "2025-26" in finding.message


def test_conflicting_name_and_dob_are_reported_as_identity_conflicts():
    pages = [
        (1, document("page-1", name="Demo Citizen", dob="2000-01-01")),
        (2, document("page-2", name="Different Citizen", dob="2001-02-02")),
    ]

    conflicts = find_pdf_page_field_conflicts(pages)

    assert {item.field_name for item in conflicts} >= {"person_name", "date_of_birth"}
    name_conflict = next(item.finding for item in conflicts if item.field_name == "person_name")
    dob_conflict = next(item.finding for item in conflicts if item.field_name == "date_of_birth")
    assert name_conflict.severity == "error"
    assert dob_conflict.severity == "error"
    assert "Page 1" in name_conflict.message and "Page 2" in name_conflict.message


def test_conflicting_masked_certificate_numbers_are_reported_without_echoing_identifier():
    pages = [
        (1, document("page-1", certificate_number="XXXX-1234", evidence={"certificate_number_masked": "Certificate No: XXXX-1234"})),
        (2, document("page-2", certificate_number="YYYY-5678", evidence={"certificate_number_masked": "Certificate No: YYYY-5678"})),
    ]

    conflicts = find_pdf_page_field_conflicts(pages)
    finding = next(item.finding for item in conflicts if item.field_name == "certificate_number_masked")

    assert finding.code == "DOCUMENT_FIELD_CONFLICT"
    assert "Page 1" in finding.message and "Page 2" in finding.message
    assert "XXXX-1234" not in finding.message
    assert "YYYY-5678" not in finding.message


def test_full_twelve_digit_id_is_redacted_from_page_evidence():
    pages = [
        (1, document("page-1", evidence={"annual_family_income": "Income: INR 180000; ID 1234 5678 9012"})),
        (2, document("page-2", income=280000, evidence={"annual_family_income": "Income: INR 280000; ID 1234 5678 9012"})),
    ]

    conflicts = find_pdf_page_field_conflicts(pages)
    finding = next(item.finding for item in conflicts if item.field_name == "annual_family_income")

    assert "1234 5678 9012" not in finding.message
    assert "REDACTED 12-DIGIT ID" in finding.message


def test_fields_are_not_compared_across_different_document_types_unless_identity_fields():
    pages = [
        (1, document("income", kind="income_certificate", income=180000, fy="2025-26")),
        (2, document("domicile", kind="domicile_certificate", income=280000, fy="2026-27")),
    ]

    conflicts = find_pdf_page_field_conflicts(pages)

    assert not any(item.field_name in {"annual_family_income", "valid_financial_year"} for item in conflicts)
    # Name and DOB agree, so there are no identity conflicts either.
    assert conflicts == []


def test_matching_page_extractions_do_not_create_conflict_findings():
    pages = [
        (1, document("page-1")),
        (2, document("page-2", evidence={"annual_family_income": "Annual income INR 180000"})),
    ]

    assert find_pdf_page_field_conflicts(pages) == []


def test_page_conflicts_are_added_to_audit_and_duplicate_identity_findings_are_replaced():
    pages = [
        (1, document("page-1", name="Asha Patil", dob="2000-01-01", income=180000)),
        (2, document("page-2", name="Riya Deshmukh", dob="2001-02-02", income=280000)),
    ]
    logical_documents = [document("logical-1", name="Asha Patil", dob="2000-01-01", income=180000),
                         document("logical-2", name="Riya Deshmukh", dob="2001-02-02", income=280000)]
    original_audit = audit_extracted_documents(logical_documents, today=date(2026, 10, 27))

    updated = add_pdf_page_conflict_findings(original_audit, pages)

    field_conflicts = [finding for finding in updated.findings if finding.code == "DOCUMENT_FIELD_CONFLICT"]
    assert {"person_name", "date_of_birth", "annual_family_income"} <= {
        item.field_name for item in find_pdf_page_field_conflicts(pages)
    }
    assert len(field_conflicts) == 3
    assert "NAME_MISMATCH" not in codes(updated.findings)
    assert "DOB_MISMATCH" not in codes(updated.findings)
    assert updated.status == "issues_found"
    assert updated.cross_document_name_match is not None
    assert updated.cross_document_dob_match is False


def test_empty_page_list_does_not_change_existing_audit():
    original = audit_extracted_documents([document("only")], today=date(2026, 10, 27))
    assert add_pdf_page_conflict_findings(original, []) == original
