from __future__ import annotations

import hashlib
from io import BytesIO

import fitz
from fastapi.testclient import TestClient
from PIL import Image

import scheme_navigator.api.main as api_module
from scheme_navigator.domain.models import ExtractedDocument


class ConflictingReviewExtractor:
    def __init__(self):
        self.calls = 0

    def extract(self, image_bytes: bytes, filename: str) -> ExtractedDocument:
        self.calls += 1
        income = 180000 if self.calls == 1 else 280000
        return ExtractedDocument(
            document_id=f"fake-page-{self.calls}",
            document_type="income_certificate",
            person_name="Demo Citizen",
            date_of_birth="2000-01-01",
            valid_financial_year="2026-27",
            annual_family_income=income,
            income_currency="INR",
            confidence=0.97,
            source_file_sha256=hashlib.sha256(image_bytes).hexdigest(),
            field_evidence={
                "person_name": "Applicant Name: Demo Citizen",
                "annual_family_income": f"Annual Family Income: INR {income}",
            },
            extraction_notes=["Synthetic test only."],
        )


class SingleImageExtractor:
    def extract(self, image_bytes: bytes, filename: str) -> ExtractedDocument:
        return ExtractedDocument(
            document_id="image-document-1",
            document_type="income_certificate",
            person_name="Demo Citizen",
            date_of_birth="2000-01-01",
            valid_financial_year="2026-27",
            annual_family_income=180000,
            income_currency="INR",
            confidence=0.97,
            source_file_sha256=hashlib.sha256(image_bytes).hexdigest(),
            field_evidence={"annual_family_income": "INR 180000"},
            extraction_notes=["Synthetic test only."],
        )


def make_two_page_pdf() -> bytes:
    pdf = fitz.open()
    for page_number in (1, 2):
        page = pdf.new_page(width=595, height=842)
        page.insert_text((72, 72), f"Synthetic income certificate page {page_number}")
    result = pdf.tobytes()
    pdf.close()
    return result


def make_png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (120, 80), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_pdf_review_correction_preserves_original_and_resolves_conflict(monkeypatch, tmp_path):
    monkeypatch.setenv("DOCUMENT_REVIEW_DB_PATH", str(tmp_path / "reviews.sqlite3"))
    extractor = ConflictingReviewExtractor()
    monkeypatch.setattr(api_module, "GeminiVisionExtractor", lambda: extractor)

    with TestClient(api_module.app) as client:
        upload = client.post(
            "/documents/audit-upload",
            files={"file": ("conflict.pdf", make_two_page_pdf(), "application/pdf")},
            data={"target_financial_year": "2026-27"},
        )
        assert upload.status_code == 200, upload.text
        uploaded = upload.json()
        review_id = uploaded["review"]["review_id"]
        assert uploaded["review"]["status"] == "pending_review"
        assert len(uploaded["extracted_documents"]) == 2

        page_two_group_id = uploaded["document_groups"][1]["document_id"]
        correction = client.patch(
            f"/documents/reviews/{review_id}/documents/{page_two_group_id}",
            json={
                "reviewer_id": "reviewer-01",
                "note": "Checked the original page and confirmed the amount is INR 180000.",
                "corrections": {"annual_family_income": 180000},
            },
        )
        assert correction.status_code == 200, correction.text
        reviewed = correction.json()

        # Original Gemini extraction is immutable and still shows the discrepancy.
        assert len(reviewed["original_extracted_documents"]) == 2
        assert reviewed["page_extractions"][1]["annual_family_income"] == 280000
        assert reviewed["original_audit"]["findings"]

        # Current page value reflects the human correction; pages can now be grouped.
        assert reviewed["current_page_extractions"][1]["annual_family_income"] == 180000
        assert len(reviewed["extracted_documents"]) == 1
        assert reviewed["extracted_documents"][0]["annual_family_income"] == 180000
        assert reviewed["document_groups"][0]["page_numbers"] == [1, 2]
        assert not any(
            finding["code"] == "DOCUMENT_FIELD_CONFLICT"
            for finding in reviewed["audit"]["findings"]
        )

        events = reviewed["events"]
        assert len(events) == 1
        assert events[0]["action"] == "field_corrected"
        assert events[0]["reviewer_id"] == "reviewer-01"
        assert events[0]["field_name"] == "annual_family_income"
        assert events[0]["original_value"] == [{"page_number": 2, "value": 280000}]
        assert events[0]["previous_value"] == 280000
        assert events[0]["new_value"] == 180000


def test_image_review_can_be_completed_and_then_becomes_read_only(monkeypatch, tmp_path):
    monkeypatch.setenv("DOCUMENT_REVIEW_DB_PATH", str(tmp_path / "reviews.sqlite3"))
    monkeypatch.setattr(api_module, "GeminiVisionExtractor", lambda: SingleImageExtractor())

    with TestClient(api_module.app) as client:
        upload = client.post(
            "/documents/audit-upload",
            files={"file": ("certificate.png", make_png(), "image/png")},
        )
        assert upload.status_code == 200, upload.text
        review_id = upload.json()["review"]["review_id"]
        document_id = upload.json()["extracted_documents"][0]["document_id"]

        incomplete = client.post(
            f"/documents/reviews/{review_id}/complete",
            json={
                "reviewer_id": "reviewer-01",
                "confirm_review_complete": False,
                "note": "I have not finished review.",
            },
        )
        assert incomplete.status_code == 400

        complete = client.post(
            f"/documents/reviews/{review_id}/complete",
            json={
                "reviewer_id": "reviewer-01",
                "confirm_review_complete": True,
                "note": "I inspected the document and completed the pre-audit review.",
            },
        )
        assert complete.status_code == 200, complete.text
        assert complete.json()["status"] == "review_completed"
        assert complete.json()["events"][-1]["action"] == "review_completed"

        locked = client.patch(
            f"/documents/reviews/{review_id}/documents/{document_id}",
            json={
                "reviewer_id": "reviewer-01",
                "note": "Attempt to modify after completion.",
                "corrections": {"annual_family_income": 200000},
            },
        )
        assert locked.status_code == 409


def test_review_delete_removes_case_and_event_history(monkeypatch, tmp_path):
    monkeypatch.setenv("DOCUMENT_REVIEW_DB_PATH", str(tmp_path / "reviews.sqlite3"))
    monkeypatch.setattr(api_module, "GeminiVisionExtractor", lambda: SingleImageExtractor())

    with TestClient(api_module.app) as client:
        upload = client.post(
            "/documents/audit-upload",
            files={"file": ("certificate.png", make_png(), "image/png")},
        )
        assert upload.status_code == 200, upload.text
        review_id = upload.json()["review"]["review_id"]

        deleted = client.delete(f"/documents/reviews/{review_id}")
        assert deleted.status_code == 200
        assert deleted.json()["deleted"] is True

        missing = client.get(f"/documents/reviews/{review_id}")
        assert missing.status_code == 404


def test_review_correction_rejects_unknown_or_sensitive_fields():
    with TestClient(api_module.app) as client:
        invalid = client.patch(
            "/documents/reviews/fake/documents/fake-document",
            json={
                "reviewer_id": "reviewer-01",
                "note": "Do not allow source hash editing.",
                "corrections": {"source_file_sha256": "a" * 64},
            },
        )
    assert invalid.status_code == 422
