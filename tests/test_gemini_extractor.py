from __future__ import annotations

import hashlib
import json
from io import BytesIO
from types import SimpleNamespace

from PIL import Image

from scheme_navigator.documents.audit import GeminiVisionExtractor, audit_extracted_documents


def png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (160, 100), "white").save(buffer, format="PNG")
    return buffer.getvalue()


class FakeInteractions:
    def __init__(self, output: dict):
        self.output = output
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return SimpleNamespace(output_text=json.dumps(self.output))


class FakeGeminiClient:
    def __init__(self, output: dict):
        self.interactions = FakeInteractions(output)


def test_gemini_extractor_normalizes_dates_and_preserves_evidence():
    output = {
        "document_type": "income_certificate",
        "person_name": "Demo Citizen",
        "date_of_birth": "01/01/2000",
        "issue_date": None,
        "valid_until": None,
        "valid_financial_year": "2025-26",
        "annual_family_income": 180000,
        "income_currency": "INR",
        "certificate_number_masked": None,
        "field_evidence": {
            "person_name": "Applicant Name: Demo Citizen",
            "annual_family_income": "Annual Family Income: INR 180000",
        },
        "confidence": 0.98,
        "extraction_notes": [],
    }
    client = FakeGeminiClient(output)
    raw = png_bytes()

    extractor = GeminiVisionExtractor(model="test-model", client=client)
    document = extractor.extract(raw, "demo-certificate.png")

    assert document.document_type == "income_certificate"
    assert document.person_name == "Demo Citizen"
    assert document.date_of_birth.isoformat() == "2000-01-01"
    assert document.annual_family_income == 180000
    assert document.income_currency == "INR"
    assert document.valid_financial_year == "2025-26"
    assert document.field_evidence["person_name"] == "Applicant Name: Demo Citizen"
    assert document.source_file_sha256 == hashlib.sha256(raw).hexdigest()
    assert document.document_id == hashlib.sha256(
        b"demo-certificate.png"
    ).hexdigest()[:16]

    request = client.interactions.last_request
    assert request["model"] == "test-model"
    assert request["generation_config"]["thinking_level"] == "minimal"
    assert request["response_format"]["mime_type"] == "application/json"


def test_gemini_extractor_suppresses_full_aadhaar_from_fields_and_evidence():
    output = {
        "document_type": "aadhaar_card",
        "person_name": "Demo Citizen",
        "date_of_birth": "2000-01-01",
        "certificate_number_masked": "1234 5678 9012",
        "field_evidence": {
            "person_name": "Name: Demo Citizen",
            "aadhaar_number": "Aadhaar: 1234 5678 9012",
        },
        "confidence": 0.95,
        "extraction_notes": [],
    }
    extractor = GeminiVisionExtractor(client=FakeGeminiClient(output))

    document = extractor.extract(png_bytes(), "synthetic-aadhaar.png")

    assert document.certificate_number_masked is None
    assert "aadhaar_number" not in document.field_evidence
    assert any("suppressed" in note.casefold() for note in document.extraction_notes)


def test_missing_fields_remain_null_and_trigger_income_review_findings():
    output = {
        "document_type": "income_certificate",
        "person_name": None,
        "date_of_birth": None,
        "valid_financial_year": None,
        "annual_family_income": None,
        "confidence": 0.40,
        "extraction_notes": ["The income and applicant details are not legible."],
    }
    extractor = GeminiVisionExtractor(client=FakeGeminiClient(output))

    document = extractor.extract(png_bytes(), "unclear-certificate.png")
    result = audit_extracted_documents([document], target_financial_year="2026-27")
    codes = {item.code for item in result.findings}

    assert document.person_name is None
    assert document.date_of_birth is None
    assert document.valid_financial_year is None
    assert document.annual_family_income is None
    assert "LOW_EXTRACTION_CONFIDENCE" in codes
    assert "INCOME_FY_NOT_EXTRACTED" in codes
    assert "INCOME_AMOUNT_NOT_EXTRACTED" in codes
    assert result.status == "review_required"


def test_gemini_extractor_rejects_non_image_input():
    extractor = GeminiVisionExtractor(
        client=FakeGeminiClient({"document_type": "unknown"})
    )

    try:
        extractor.extract(b"not-an-image", "bad.png")
    except ValueError as exc:
        assert "valid image" in str(exc).casefold()
    else:
        raise AssertionError("Invalid image input should be rejected")


# --------------------------------------------------------------------------
# Configuration, SDK Availability, and Failure Handling Tests
# --------------------------------------------------------------------------

def test_gemini_extractor_missing_configuration(monkeypatch):
    from scheme_navigator.core.config import settings

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(settings, "gemini_api_key", None)

    import pytest

    with pytest.raises(RuntimeError) as exc_info:
        GeminiVisionExtractor(client=None)

    assert "GEMINI_API_KEY is not set" in str(exc_info.value)


def test_gemini_extractor_sdk_unavailable(monkeypatch):
    import sys
    import pytest
    from scheme_navigator.core.config import settings

    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setitem(sys.modules, "google.genai", None)

    with pytest.raises(RuntimeError) as exc_info:
        GeminiVisionExtractor(client=None, api_key="test-key")

    assert "google-genai" in str(exc_info.value)


def test_gemini_extractor_reads_settings_and_default_model(monkeypatch):
    from scheme_navigator.core.config import settings

    fake_output = {
        "document_type": "income_certificate",
        "person_name": "Settings Citizen",
        "annual_family_income": 150000,
        "income_currency": "INR",
        "confidence": 0.95,
        "extraction_notes": [],
    }
    fake_client = FakeGeminiClient(fake_output)

    monkeypatch.setattr(settings, "gemini_api_key", "mock-settings-api-key")
    monkeypatch.setattr(settings, "gemini_model", "gemini-3.5-flash-lite")

    import google.genai as genai_module
    monkeypatch.setattr(genai_module, "Client", lambda api_key: fake_client)

    extractor = GeminiVisionExtractor()
    assert extractor.model == "gemini-3.5-flash-lite"
    assert extractor.client == fake_client

    doc = extractor.extract(png_bytes(), "test.png")
    assert doc.document_type == "income_certificate"
    assert doc.person_name == "Settings Citizen"
    assert doc.annual_family_income == 150000


def test_gemini_extractor_api_request_failure():
    import pytest

    class FailingInteractions:
        def create(self, **kwargs):
            raise Exception("401 Unauthorized: Invalid API key provided.")

    class FailingGeminiClient:
        def __init__(self):
            self.interactions = FailingInteractions()

    extractor = GeminiVisionExtractor(client=FailingGeminiClient())

    with pytest.raises(RuntimeError) as exc_info:
        extractor.extract(png_bytes(), "test.png")

    assert "Gemini model request failed" in str(exc_info.value)
    assert "401 Unauthorized" in str(exc_info.value)


def test_gemini_extractor_client_init_failure(monkeypatch):
    import pytest
    from scheme_navigator.core.config import settings

    monkeypatch.setattr(settings, "gemini_api_key", "bad-key")
    import google.genai as genai_module

    def failing_client_init(api_key):
        raise ValueError("Invalid authentication configuration")

    monkeypatch.setattr(genai_module, "Client", failing_client_init)

    with pytest.raises(RuntimeError) as exc_info:
        GeminiVisionExtractor(api_key="bad-key")

    assert "Gemini client initialization failed" in str(exc_info.value)


def test_audit_upload_endpoint_handles_missing_configuration_safely(monkeypatch):
    from fastapi.testclient import TestClient
    from scheme_navigator.api.main import app, _document_review_store
    from scheme_navigator.core.config import settings

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(settings, "gemini_api_key", None)

    review_store = _document_review_store()
    with review_store._connect() as conn:
        initial_reviews = conn.execute("SELECT count(*) FROM document_reviews").fetchone()[0]

    with TestClient(app) as client:
        response = client.post(
            "/documents/audit-upload",
            files={"file": ("cert.png", png_bytes(), "image/png")},
            data={"target_financial_year": "2026-27"},
        )

    assert response.status_code == 503
    assert "GEMINI_API_KEY is not set" in response.json()["detail"]
    assert "No file was persisted" in response.json()["detail"]
    with review_store._connect() as conn:
        assert conn.execute("SELECT count(*) FROM document_reviews").fetchone()[0] == initial_reviews


def test_audit_upload_endpoint_handles_api_failure_without_persisting_records(monkeypatch):
    from fastapi.testclient import TestClient
    import scheme_navigator.api.main as api_module

    class FailingExtractor:
        def extract(self, image_bytes, filename):
            raise RuntimeError("Gemini model request failed: 503 Model overloaded. No file was persisted.")

    monkeypatch.setattr(api_module, "GeminiVisionExtractor", FailingExtractor)

    review_store = api_module._document_review_store()
    with review_store._connect() as conn:
        initial_reviews = conn.execute("SELECT count(*) FROM document_reviews").fetchone()[0]

    with TestClient(api_module.app) as client:
        response = client.post(
            "/documents/audit-upload",
            files={"file": ("cert.png", png_bytes(), "image/png")},
            data={"target_financial_year": "2026-27"},
        )

    assert response.status_code == 503
    assert "Gemini model request failed" in response.json()["detail"]
    assert "No file was persisted" in response.json()["detail"]
    with review_store._connect() as conn:
        assert conn.execute("SELECT count(*) FROM document_reviews").fetchone()[0] == initial_reviews


# --------------------------------------------------------------------------
# IPv4 Networking & Transport Scoping Tests
# --------------------------------------------------------------------------

def test_gemini_extractor_ipv4_configuration_applied_to_gemini_client():
    import httpx
    extractor = GeminiVisionExtractor(api_key="mock-api-key", force_ipv4=True)
    try:
        assert extractor._httpx_client is not None
        assert isinstance(extractor._httpx_client, httpx.Client)
        # Verify transport is configured with local_address="0.0.0.0"
        transport = extractor._httpx_client._transport
        assert isinstance(transport, httpx.HTTPTransport)
        assert transport._pool._local_address == "0.0.0.0"
        assert not extractor._httpx_client.is_closed
    finally:
        extractor.close()
    assert extractor._httpx_client.is_closed


def test_gemini_extractor_allows_disabling_force_ipv4():
    extractor = GeminiVisionExtractor(api_key="mock-api-key", force_ipv4=False)
    try:
        assert extractor._httpx_client is None
    finally:
        extractor.close()


def test_gemini_extractor_other_application_networking_unaffected():
    import httpx
    # Extractor with IPv4 forced
    extractor = GeminiVisionExtractor(api_key="mock-api-key", force_ipv4=True)
    try:
        # Standard httpx client created elsewhere in the application
        standard_client = httpx.Client()
        try:
            transport = standard_client._transport
            assert isinstance(transport, httpx.HTTPTransport)
            # Default HTTPTransport must NOT have local_address set to 0.0.0.0
            assert transport._pool._local_address is None
        finally:
            standard_client.close()
    finally:
        extractor.close()


def test_gemini_extractor_context_manager_closes_client():
    with GeminiVisionExtractor(api_key="mock-api-key", force_ipv4=True) as extractor:
        assert extractor._httpx_client is not None
        assert not extractor._httpx_client.is_closed
    assert extractor._httpx_client.is_closed


def test_gemini_extractor_custom_client_bypasses_custom_transport():
    fake_client = FakeGeminiClient({})
    extractor = GeminiVisionExtractor(client=fake_client)
    assert extractor._httpx_client is None
    extractor.close()  # No-op when no custom httpx client is owned


