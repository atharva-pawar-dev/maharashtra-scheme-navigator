from __future__ import annotations

import hashlib

from scheme_navigator.documents.audit import (
    add_pdf_page_conflict_findings,
    audit_extracted_documents,
)
from scheme_navigator.documents.grouping import (
    find_pdf_page_field_conflicts,
    group_pdf_page_extractions,
)
from scheme_navigator.domain.models import ExtractedDocument


SOURCE_HASH = hashlib.sha256(b"actionable-report-synthetic-pdf").hexdigest()


def make_document(
    document_id: str,
    *,
    name: str | None = "Demo Citizen",
    dob: str | None = "2000-01-01",
    financial_year: str | None = "2025-26",
    income: int | None = 180000,
    valid_until: str | None = None,
    evidence: dict[str, str] | None = None,
    document_type: str = "income_certificate",
    confidence: float = 0.96,
) -> ExtractedDocument:
    return ExtractedDocument(
        document_id=document_id,
        document_type=document_type,
        person_name=name,
        date_of_birth=dob,
        valid_financial_year=financial_year,
        annual_family_income=income,
        income_currency="INR" if income is not None else None,
        valid_until=valid_until,
        confidence=confidence,
        source_file_sha256=hashlib.sha256(document_id.encode()).hexdigest(),
        field_evidence=evidence or {},
        extraction_notes=[],
    )


def test_duplicate_financial_year_findings_merge_document_and_page_references():
    documents = [
        make_document(
            "logical-page-1",
            evidence={"valid_financial_year": "Page 1: Financial Year: 2025-26"},
        ),
        make_document(
            "logical-page-2",
            evidence={"valid_financial_year": "Page 2: Financial Year: 2025-26"},
        ),
    ]

    result = audit_extracted_documents(documents, target_financial_year="2026-27")
    fy_findings = [item for item in result.findings if item.code == "FINANCIAL_YEAR_MISMATCH"]

    assert len(fy_findings) == 1
    finding = fy_findings[0]
    assert finding.category == "document_validity"
    assert finding.recommended_action
    assert set(finding.document_ids) == {"logical-page-1", "logical-page-2"}
    assert finding.page_numbers == [1, 2]
    assert any("Page 1" in item for item in finding.evidence)
    assert any("Page 2" in item for item in finding.evidence)


def test_missing_income_is_classified_as_extraction_quality_with_action():
    document = make_document(
        "income-missing",
        financial_year="2026-27",
        income=None,
    )

    result = audit_extracted_documents([document], target_financial_year="2026-27")
    finding = next(item for item in result.findings if item.code == "INCOME_AMOUNT_NOT_EXTRACTED")

    assert finding.category == "document_extraction"
    assert finding.recommended_action
    assert "original" in finding.recommended_action.casefold()


def test_identity_conflict_is_classified_as_document_consistency():
    documents = [
        make_document("identity-one", name="Demo Citizen"),
        make_document("identity-two", name="Different Citizen"),
    ]

    result = audit_extracted_documents(documents)
    finding = next(item for item in result.findings if item.code == "NAME_MISMATCH")

    assert finding.category == "document_consistency"
    assert finding.recommended_action


def test_expiry_finding_is_classified_as_document_validity():
    document = make_document("expired", valid_until="2025-01-01")
    result = audit_extracted_documents([document])
    finding = next(item for item in result.findings if item.code == "CERTIFICATE_EXPIRED")

    assert finding.category == "document_validity"
    assert finding.recommended_action


def test_document_report_explicitly_does_not_determine_scheme_eligibility():
    result = audit_extracted_documents([make_document("scope-check", financial_year="2026-27")])

    assert result.scheme_eligibility_evaluated is False
    assert "does not determine eligibility" in result.scope_note.casefold()
    assert all(item.category != "scheme_eligibility" for item in result.findings)


def test_pdf_income_conflict_contains_page_references_and_recommended_action():
    page_documents = [
        (
            1,
            make_document(
                "page-1",
                income=180000,
                evidence={"annual_family_income": "Annual Family Income: INR 180000"},
            ),
        ),
        (
            2,
            make_document(
                "page-2",
                income=280000,
                evidence={"annual_family_income": "Annual Family Income: INR 280000"},
            ),
        ),
    ]

    conflict = next(
        item for item in find_pdf_page_field_conflicts(page_documents)
        if item.field_name == "annual_family_income"
    )
    finding = conflict.finding

    assert finding.category == "document_consistency"
    assert finding.recommended_action
    assert finding.page_numbers == [1, 2]
    assert len(finding.evidence) == 2
    assert "Page 1" in finding.evidence[0]
    assert "Page 2" in finding.evidence[1]


def test_page_conflict_and_duplicate_financial_year_warning_are_reported_once():
    page_documents = [
        (
            1,
            make_document(
                "page-1",
                income=180000,
                evidence={
                    "annual_family_income": "Annual Family Income: INR 180000",
                    "valid_financial_year": "Financial Year: 2025-26",
                },
            ),
        ),
        (
            2,
            make_document(
                "page-2",
                income=280000,
                evidence={
                    "annual_family_income": "Annual Family Income: INR 280000",
                    "valid_financial_year": "Financial Year: 2025-26",
                },
            ),
        ),
    ]

    groups = group_pdf_page_extractions(page_documents, SOURCE_HASH)
    logical_documents = [group.document for group in groups]
    base_audit = audit_extracted_documents(
        logical_documents,
        target_financial_year="2026-27",
    )
    result = add_pdf_page_conflict_findings(base_audit, page_documents)

    fy_findings = [item for item in result.findings if item.code == "FINANCIAL_YEAR_MISMATCH"]
    conflict_findings = [item for item in result.findings if item.code == "DOCUMENT_FIELD_CONFLICT"]

    assert len(fy_findings) == 1
    assert len(fy_findings[0].document_ids) == 2
    assert fy_findings[0].page_numbers == [1, 2]
    assert len(conflict_findings) == 1
    assert conflict_findings[0].page_numbers == [1, 2]
    assert result.scheme_eligibility_evaluated is False
    assert result.status == "review_required"
