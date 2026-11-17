from __future__ import annotations

import hashlib
import importlib

from fastapi.testclient import TestClient

from scheme_navigator.documents.audit import audit_extracted_documents
from scheme_navigator.domain.models import ExtractedDocument
from scheme_navigator.api.main import app


api_main = importlib.import_module("scheme_navigator.api.main")
client = TestClient(app)


def make_review_record(status: str) -> dict:
    document = ExtractedDocument(
        document_id="synthetic-review-income-001",
        document_type="income_certificate",
        person_name="Demo Citizen",
        annual_family_income=180000,
        income_currency="INR",
        valid_financial_year="2026-27",
        confidence=0.95,
        source_file_sha256=hashlib.sha256(
            b"synthetic-review-document"
        ).hexdigest(),
        field_evidence={
            "annual_family_income": "Annual income INR 180000"
        },
    )

    audit = audit_extracted_documents(
        [document],
        target_financial_year="2026-27",
    )

    return {
        "review_id": f"synthetic-review-{status}-001",
        "status": status,
        "extracted_documents": [
            document.model_dump(mode="json")
        ],
        "audit": audit.model_dump(mode="json"),
    }


class FakeReviewStore:
    def __init__(self, record: dict | None):
        self.record = record

    def get_review(self, review_id: str):
        if self.record and self.record["review_id"] == review_id:
            return self.record
        return None


def test_assessment_api_loads_pending_review(monkeypatch):
    record = make_review_record("pending_review")

    monkeypatch.setattr(
        api_main,
        "_ensure_local_review_api",
        lambda: None,
    )
    monkeypatch.setattr(
        api_main,
        "_document_review_store",
        lambda: FakeReviewStore(record),
    )

    response = client.post(
        "/assessment/demo-majhi-ladki-bahin",
        json={
            "review_id": record["review_id"],
            "profile": {
                "annual_family_income": 200000
            },
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["human_review_status"] == "pending_review"
    assert result["human_review_id"] == record["review_id"]
    assert result["document_authenticity_status"] == "not_verified"
    assert result["document_audit"] is not None

    assert any(
        action["code"] == "human-review:pending"
        for action in result["next_actions"]
    )


def test_assessment_api_loads_completed_review(monkeypatch):
    record = make_review_record("review_completed")

    monkeypatch.setattr(
        api_main,
        "_ensure_local_review_api",
        lambda: None,
    )
    monkeypatch.setattr(
        api_main,
        "_document_review_store",
        lambda: FakeReviewStore(record),
    )

    response = client.post(
        "/assessment/demo-majhi-ladki-bahin",
        json={
            "review_id": record["review_id"],
            "profile": {
                "annual_family_income": 180000
            },
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["human_review_status"] == "review_completed"
    assert result["human_review_id"] == record["review_id"]
    assert result["document_authenticity_status"] == "not_verified"

    assert any(
        action["code"] == "human-review:completed"
        for action in result["next_actions"]
    )


def test_assessment_api_returns_404_for_missing_review(monkeypatch):
    monkeypatch.setattr(
        api_main,
        "_ensure_local_review_api",
        lambda: None,
    )
    monkeypatch.setattr(
        api_main,
        "_document_review_store",
        lambda: FakeReviewStore(None),
    )

    response = client.post(
        "/assessment/demo-majhi-ladki-bahin",
        json={
            "review_id": "nonexistent-review-001",
            "profile": {},
        },
    )

    assert response.status_code == 404
    assert "not found or expired" in response.json()["detail"].lower()


def test_assessment_api_rejects_documents_with_review_id(monkeypatch):
    record = make_review_record("pending_review")

    monkeypatch.setattr(
        api_main,
        "_ensure_local_review_api",
        lambda: None,
    )
    monkeypatch.setattr(
        api_main,
        "_document_review_store",
        lambda: FakeReviewStore(record),
    )

    response = client.post(
        "/assessment/demo-majhi-ladki-bahin",
        json={
            "review_id": record["review_id"],
            "profile": {},
            "documents": record["extracted_documents"],
        },
    )

    assert response.status_code == 400
    assert "do not send documents again" in response.json()["detail"].lower()