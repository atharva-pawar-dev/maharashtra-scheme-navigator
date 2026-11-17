from __future__ import annotations

import hashlib

from scheme_navigator.documents.grouping import group_pdf_page_extractions
from scheme_navigator.domain.models import ExtractedDocument


SOURCE_HASH = hashlib.sha256(b"synthetic-pdf").hexdigest()


def document(
    document_id: str,
    *,
    kind: str = "income_certificate",
    name: str | None = "Demo Citizen",
    dob: str | None = "2000-01-01",
    fy: str | None = "2025-26",
    income: int | None = 180000,
) -> ExtractedDocument:
    return ExtractedDocument(
        document_id=document_id,
        document_type=kind,
        person_name=name,
        date_of_birth=dob,
        valid_financial_year=fy,
        annual_family_income=income,
        income_currency="INR" if income is not None else None,
        confidence=0.95,
        source_file_sha256=SOURCE_HASH,
        field_evidence={"person_name": f"Applicant Name: {name}"} if name else {},
        extraction_notes=[],
    )


def test_matching_consecutive_pages_group_into_one_logical_document():
    groups = group_pdf_page_extractions(
        [(1, document("page-1")), (2, document("page-2"))],
        SOURCE_HASH,
    )

    assert len(groups) == 1
    assert groups[0].page_numbers == (1, 2)
    assert groups[0].document.document_type == "income_certificate"
    assert groups[0].document.annual_family_income == 180000
    assert "Page 1:" in groups[0].document.field_evidence["person_name"]
    assert "Page 2:" in groups[0].document.field_evidence["person_name"]
    assert any("grouped" in note.casefold() for note in groups[0].document.extraction_notes)


def test_fields_split_across_matching_pages_are_combined():
    page_one = document("page-1", fy=None, income=None)
    page_two = document("page-2", name="Demo Citizen", dob="2000-01-01", fy="2025-26", income=180000)

    groups = group_pdf_page_extractions(
        [(1, page_one), (2, page_two)],
        SOURCE_HASH,
    )

    assert len(groups) == 1
    assert groups[0].document.valid_financial_year == "2025-26"
    assert groups[0].document.annual_family_income == 180000


def test_conflicting_financial_years_remain_separate_documents():
    groups = group_pdf_page_extractions(
        [
            (1, document("page-1", fy="2024-25")),
            (2, document("page-2", fy="2025-26")),
        ],
        SOURCE_HASH,
    )

    assert len(groups) == 2
    assert [group.page_numbers for group in groups] == [(1,), (2,)]


def test_conflicting_identity_fields_remain_separate_documents():
    groups = group_pdf_page_extractions(
        [
            (1, document("page-1", name="Demo Citizen", dob="2000-01-01")),
            (2, document("page-2", name="Different Citizen", dob="2000-01-01")),
        ],
        SOURCE_HASH,
    )

    assert len(groups) == 2


def test_different_document_types_remain_separate_documents():
    groups = group_pdf_page_extractions(
        [
            (1, document("page-1", kind="income_certificate")),
            (2, document("page-2", kind="domicile_certificate", fy=None, income=None)),
        ],
        SOURCE_HASH,
    )

    assert len(groups) == 2


def test_pages_without_a_shared_identity_anchor_remain_separate():
    groups = group_pdf_page_extractions(
        [
            (1, document("page-1", name="Demo Citizen", dob=None)),
            (2, document("page-2", name=None, dob="2000-01-01")),
        ],
        SOURCE_HASH,
    )

    assert len(groups) == 2


def test_nonconsecutive_pages_are_not_grouped():
    groups = group_pdf_page_extractions(
        [
            (1, document("page-1")),
            (3, document("page-3")),
        ],
        SOURCE_HASH,
    )

    assert len(groups) == 2


def test_grouping_rejects_empty_input():
    try:
        group_pdf_page_extractions([], SOURCE_HASH)
    except ValueError as exc:
        assert "at least one" in str(exc).casefold()
    else:
        raise AssertionError("Empty PDF page input must be rejected")
