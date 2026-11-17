from __future__ import annotations

import hashlib
from io import BytesIO

import fitz
from fastapi.testclient import TestClient
from PIL import Image

import scheme_navigator.api.main as api_module
from scheme_navigator.domain.models import ExtractedDocument


class FakeGeminiExtractor:
    def __init__(self):
        self.calls: list[tuple[bytes, str]] = []

    def extract(self, image_bytes: bytes, filename: str) -> ExtractedDocument:
        self.calls.append((image_bytes, filename))
        page_number = len(self.calls)
        document_type = "income_certificate" if page_number == 1 else "domicile_certificate"
        return ExtractedDocument(
            document_id=f"fake-page-{page_number}",
            document_type=document_type,
            person_name="Demo Citizen",
            date_of_birth="2000-01-01",
            valid_financial_year="2026-27" if page_number == 1 else None,
            annual_family_income=180000 if page_number == 1 else None,
            income_currency="INR" if page_number == 1 else None,
            confidence=0.96,
            source_file_sha256=hashlib.sha256(image_bytes).hexdigest(),
            field_evidence={},
            extraction_notes=[],
        )


def make_two_page_pdf() -> bytes:
    pdf = fitz.open()
    first = pdf.new_page(width=595, height=842)
    first.insert_text((72, 72), "Synthetic income certificate - page 1")
    second = pdf.new_page(width=595, height=842)
    second.insert_text((72, 72), "Synthetic domicile certificate - page 2")
    content = pdf.tobytes()
    pdf.close()
    return content


def test_multi_page_pdf_is_rendered_and_each_page_is_sent_to_mocked_gemini(monkeypatch):
    fake_extractor = FakeGeminiExtractor()
    monkeypatch.setattr(
        api_module,
        "GeminiVisionExtractor",
        lambda: fake_extractor,
    )
    pdf_bytes = make_two_page_pdf()
    expected_source_hash = hashlib.sha256(pdf_bytes).hexdigest()

    with TestClient(api_module.app) as client:
        response = client.post(
            "/documents/audit-upload",
            files={"file": ("synthetic-certificates.pdf", pdf_bytes, "application/pdf")},
            data={"target_financial_year": "2026-27"},
        )

    assert response.status_code == 200, response.text
    body = response.json()

    assert len(fake_extractor.calls) == 2
    assert [name for _, name in fake_extractor.calls] == [
        "certificate-page-1.png",
        "certificate-page-2.png",
    ]
    assert all(image.startswith(b"\x89PNG\r\n\x1a\n") for image, _ in fake_extractor.calls)

    documents = body["extracted_documents"]
    assert len(documents) == 2
    assert documents[0]["source_file_sha256"] == expected_source_hash
    assert documents[1]["source_file_sha256"] == expected_source_hash
    assert documents[0]["document_id"] != documents[1]["document_id"]
    assert body["audit"]["cross_document_name_match"] == 1.0
    assert body["audit"]["cross_document_dob_match"] is True
    assert body["audit"]["status"] == "pass"
    assert "not an official verification" in body["notice"].casefold()


def test_image_upload_uses_mocked_gemini_and_returns_audit(monkeypatch):
    fake_extractor = FakeGeminiExtractor()
    monkeypatch.setattr(
        api_module,
        "GeminiVisionExtractor",
        lambda: fake_extractor,
    )
    image_buffer = BytesIO()
    Image.new("RGB", (160, 100), "white").save(image_buffer, format="PNG")

    with TestClient(api_module.app) as client:
        response = client.post(
            "/documents/audit-upload",
            files={"file": ("synthetic.png", image_buffer.getvalue(), "image/png")},
            data={"target_financial_year": "2026-27"},
        )

    assert response.status_code == 200, response.text
    assert len(fake_extractor.calls) == 1
    body = response.json()
    assert len(body["extracted_documents"]) == 1
    assert body["extracted_documents"][0]["annual_family_income"] == 180000
    assert body["audit"]["status"] == "pass"


def test_upload_rejects_unsupported_file_type_without_calling_gemini(monkeypatch):
    fake_extractor = FakeGeminiExtractor()
    monkeypatch.setattr(
        api_module,
        "GeminiVisionExtractor",
        lambda: fake_extractor,
    )

    with TestClient(api_module.app) as client:
        response = client.post(
            "/documents/audit-upload",
            files={"file": ("notes.txt", b"not a certificate", "text/plain")},
        )

    assert response.status_code == 415
    assert fake_extractor.calls == []


class SameIncomeCertificateExtractor:
    """Returns consistent fields for two pages of one synthetic certificate."""

    def __init__(self):
        self.calls: list[tuple[bytes, str]] = []

    def extract(self, image_bytes: bytes, filename: str) -> ExtractedDocument:
        self.calls.append((image_bytes, filename))
        page_number = len(self.calls)
        return ExtractedDocument(
            document_id=f"income-page-{page_number}",
            document_type="income_certificate",
            person_name="Demo Citizen",
            date_of_birth="2000-01-01",
            valid_financial_year="2025-26",
            annual_family_income=180000,
            income_currency="INR",
            confidence=0.96,
            source_file_sha256=hashlib.sha256(image_bytes).hexdigest(),
            field_evidence={
                "person_name": f"Applicant Name: Demo Citizen (page {page_number})",
                "annual_family_income": f"Annual Family Income: INR 180000 (page {page_number})",
            },
            extraction_notes=[f"Synthetic page {page_number}"],
        )


def test_same_certificate_pdf_pages_are_grouped_and_page_outputs_are_preserved(monkeypatch):
    fake_extractor = SameIncomeCertificateExtractor()
    monkeypatch.setattr(
        api_module,
        "GeminiVisionExtractor",
        lambda: fake_extractor,
    )
    pdf_bytes = make_two_page_pdf()

    with TestClient(api_module.app) as client:
        response = client.post(
            "/documents/audit-upload",
            files={"file": ("two-page-income-certificate.pdf", pdf_bytes, "application/pdf")},
            data={"target_financial_year": "2026-27"},
        )

    assert response.status_code == 200, response.text
    body = response.json()

    # Original page-level results remain available for traceability.
    assert len(body["page_extractions"]) == 2
    assert [item["document_id"] for item in body["page_extractions"]]
    assert len(body["document_groups"]) == 1
    assert body["document_groups"][0]["page_numbers"] == [1, 2]
    assert body["document_groups"][0]["page_count"] == 2

    # Audit works against one logical certificate, not duplicate page records.
    assert len(body["extracted_documents"]) == 1
    logical_document = body["extracted_documents"][0]
    assert logical_document["document_type"] == "income_certificate"
    assert logical_document["annual_family_income"] == 180000
    assert "Page 1:" in logical_document["field_evidence"]["person_name"]
    assert "Page 2:" in logical_document["field_evidence"]["person_name"]
    assert any("grouped" in note.casefold() for note in logical_document["extraction_notes"])

    fy_findings = [
        item for item in body["audit"]["findings"]
        if item["code"] == "FINANCIAL_YEAR_MISMATCH"
    ]
    assert len(fy_findings) == 1
    assert body["audit"]["status"] == "review_required"


class ConflictingIncomeCertificateExtractor:
    """Returns same identity but conflicting annual income across two PDF pages."""

    def __init__(self):
        self.calls: list[tuple[bytes, str]] = []

    def extract(self, image_bytes: bytes, filename: str) -> ExtractedDocument:
        self.calls.append((image_bytes, filename))
        page_number = len(self.calls)
        income = 180000 if page_number == 1 else 280000
        return ExtractedDocument(
            document_id=f"conflicting-page-{page_number}",
            document_type="income_certificate",
            person_name="Demo Citizen",
            date_of_birth="2000-01-01",
            valid_financial_year="2026-27",
            annual_family_income=income,
            income_currency="INR",
            confidence=0.96,
            source_file_sha256=hashlib.sha256(image_bytes).hexdigest(),
            field_evidence={
                "person_name": "Applicant Name: Demo Citizen",
                "annual_family_income": f"Annual Family Income: INR {income}",
                "valid_financial_year": "Financial Year: 2026-27",
            },
            extraction_notes=[],
        )


def test_conflicting_pdf_page_values_are_not_merged_and_are_reported_with_page_evidence(monkeypatch):
    fake_extractor = ConflictingIncomeCertificateExtractor()
    monkeypatch.setattr(
        api_module,
        "GeminiVisionExtractor",
        lambda: fake_extractor,
    )
    pdf_bytes = make_two_page_pdf()

    with TestClient(api_module.app) as client:
        response = client.post(
            "/documents/audit-upload",
            files={"file": ("conflicting-income-certificate.pdf", pdf_bytes, "application/pdf")},
            data={"target_financial_year": "2026-27"},
        )

    assert response.status_code == 200, response.text
    body = response.json()

    # Conflicting pages remain separately inspectable instead of silently merging.
    assert len(body["page_extractions"]) == 2
    assert len(body["extracted_documents"]) == 2
    assert [group["page_numbers"] for group in body["document_groups"]] == [[1], [2]]

    conflict_findings = [
        finding for finding in body["audit"]["findings"]
        if finding["code"] == "DOCUMENT_FIELD_CONFLICT"
    ]
    assert len(conflict_findings) == 1
    finding = conflict_findings[0]
    assert finding["severity"] == "warning"
    assert "annual family income" in finding["message"]
    assert "Page 1" in finding["message"]
    assert "Page 2" in finding["message"]
    assert "180000" in finding["message"]
    assert "280000" in finding["message"]
    assert finding["document_ids"] == [
        body["page_extractions"][0]["document_id"],
        body["page_extractions"][1]["document_id"],
    ]
    assert body["audit"]["status"] == "review_required"
