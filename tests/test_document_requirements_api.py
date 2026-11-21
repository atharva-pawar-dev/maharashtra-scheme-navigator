"""Tests for Scheme Document Requirements API, Factsheets, and Coverage Reports."""

import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.services.document_prep import (
    DocumentMatchStatus,
    RequirementItemStatus,
    get_all_scheme_document_requirements,
    get_scheme_document_requirements,
)


@pytest.fixture
def client():
    return TestClient(app)


# -------------------------------------------------------------------------
# Test Suite 1: Scheme Document Requirements Catalogue & Service
# -------------------------------------------------------------------------

def test_scheme_document_requirements_loaded():
    """Verify all 75 schemes have requirement entries in catalogue."""
    reqs = get_all_scheme_document_requirements()
    assert len(reqs) >= 75
    # Verify Ladki Bahin requirements
    lb_req = get_scheme_document_requirements("candidate-majhi-ladki-bahin")
    assert lb_req is not None
    assert lb_req["scheme_id"] == "candidate-majhi-ladki-bahin"
    assert len(lb_req["requirements"]) >= 4
    # Check mandatory flags and issuing authority
    mandatory_reqs = [r for r in lb_req["requirements"] if r.get("is_mandatory", True)]
    assert len(mandatory_reqs) >= 3


def test_scheme_document_requirements_not_found():
    """Verify non-existent scheme returns None."""
    req = get_scheme_document_requirements("non-existent-scheme-999")
    assert req is None


# -------------------------------------------------------------------------
# Test Suite 2: GET /canonical-schemes/{scheme_id}/documents
# -------------------------------------------------------------------------

def test_api_get_scheme_documents_success(client):
    """GET /canonical-schemes/{scheme_id}/documents returns requirements and metadata."""
    resp = client.get("/canonical-schemes/candidate-majhi-ladki-bahin/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scheme_id"] == "candidate-majhi-ladki-bahin"
    assert "scheme_name" in data
    assert "requirements" in data
    assert len(data["requirements"]) >= 4

    # Check requirement attributes
    first_req = data["requirements"][0]
    assert "document_name" in first_req
    assert "requirement_type" in first_req
    assert "is_mandatory" in first_req
    assert "issuing_authority" in first_req
    assert "rts_statutory_days" in first_req


def test_api_get_scheme_documents_404(client):
    """GET /canonical-schemes/{scheme_id}/documents returns 404 for unknown scheme."""
    resp = client.get("/canonical-schemes/completely-unknown-scheme-xyz/documents")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# -------------------------------------------------------------------------
# Test Suite 3: POST /canonical-schemes/{scheme_id}/documents/audit
# -------------------------------------------------------------------------

def test_api_audit_missing_all_documents(client):
    """Auditing with no uploaded documents produces NOT_PROVIDED states and 0% readiness."""
    payload = {
        "scheme_id": "candidate-majhi-ladki-bahin",
        "documents": [],
        "profile": {
            "age": 28,
            "gender": "Female",
            "annual_income": 120000,
        },
    }
    resp = client.post("/canonical-schemes/candidate-majhi-ladki-bahin/documents/audit", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["scheme_id"] == "candidate-majhi-ladki-bahin"
    assert data["readiness_percentage"] == 0
    assert data["mandatory_satisfied"] == 0
    assert data["mandatory_total"] >= 3
    assert data["all_mandatory_satisfied"] is False

    # Verify requirement items have NOT_PROVIDED status
    for item in data["requirements"]:
        if item.get("is_mandatory"):
            assert item["state"] == RequirementItemStatus.NOT_PROVIDED.value


def test_api_audit_with_matching_valid_documents(client):
    """Auditing with verified matching documents produces MATCHED_FOR_PREPARATION states."""
    payload = {
        "scheme_id": "candidate-majhi-ladki-bahin",
        "target_financial_year": "2026-27",
        "documents": [
            {
                "document_id": "doc_aadhaar_001",
                "document_type": "aadhaar_card",
                "person_name": "Sunita Patil",
                "confidence": 0.98,
                "source_file_sha256": "a" * 64,
                "field_evidence": {"document_title": "Aadhaar Card"},
            },
            {
                "document_id": "doc_domicile_002",
                "document_type": "domicile_certificate",
                "person_name": "Sunita Patil",
                "confidence": 0.95,
                "source_file_sha256": "b" * 64,
                "field_evidence": {"document_title": "Domicile Certificate"},
            },
            {
                "document_id": "doc_income_003",
                "document_type": "income_certificate",
                "person_name": "Sunita Patil",
                "valid_financial_year": "2026-27",
                "confidence": 0.96,
                "source_file_sha256": "c" * 64,
                "field_evidence": {"document_title": "Income Certificate"},
            },
            {
                "document_id": "doc_passbook_004",
                "document_type": "other",
                "person_name": "Sunita Patil",
                "confidence": 0.92,
                "source_file_sha256": "d" * 64,
                "field_evidence": {"document_title": "Bank Passbook"},
            },
        ],
        "profile": {
            "name": "Sunita Patil",
            "age": 28,
            "gender": "Female",
            "annual_income": 120000,
        },
    }
    resp = client.post("/canonical-schemes/candidate-majhi-ladki-bahin/documents/audit", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["readiness_percentage"] == 100
    assert data["mandatory_satisfied"] == data["mandatory_total"]
    assert data["all_mandatory_satisfied"] is True

    # Verify requirements are MATCHED_FOR_PREPARATION
    for item in data["requirements"]:
        if item.get("is_mandatory"):
            assert item["state"] in (
                RequirementItemStatus.MATCHED_FOR_PREPARATION.value,
                RequirementItemStatus.MATCHED.value,
            )


def test_api_audit_expired_document_detection(client):
    """Auditing with expired income certificate produces EXPIRED_OR_STALE state."""
    payload = {
        "scheme_id": "candidate-majhi-ladki-bahin",
        "documents": [
            {
                "document_id": "doc_inc_exp",
                "document_type": "income_certificate",
                "valid_until": "2020-03-31",  # Expired date
                "confidence": 0.95,
                "source_file_sha256": "e" * 64,
                "field_evidence": {"document_title": "Income Certificate"},
            }
        ],
        "profile": {"annual_income": 100000},
    }
    resp = client.post("/canonical-schemes/candidate-majhi-ladki-bahin/documents/audit", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    inc_item = next((i for i in data["requirements"] if "income" in i["document_name"].lower()), None)
    assert inc_item is not None
    assert inc_item["state"] in (
        RequirementItemStatus.EXPIRED_OR_STALE.value,
        RequirementItemStatus.REPLACEMENT_REQUIRED.value,
        DocumentMatchStatus.EXPIRED.value,
    )


def test_api_audit_unreadable_document_handling(client):
    """Auditing with low confidence upload produces UNREADABLE status."""
    payload = {
        "scheme_id": "candidate-majhi-ladki-bahin",
        "documents": [
            {
                "document_id": "doc_bad_aadhaar",
                "document_type": "aadhaar_card",
                "confidence": 0.20,  # Below threshold
                "source_file_sha256": "f" * 64,
                "field_evidence": {"document_title": "Aadhaar Card"},
                "extraction_notes": ["Blurry image, OCR unreadable"],
            }
        ],
    }
    resp = client.post("/canonical-schemes/candidate-majhi-ladki-bahin/documents/audit", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    aadhaar_item = next((i for i in data["requirements"] if "aadhaar" in i["document_name"].lower()), None)
    assert aadhaar_item is not None
    assert aadhaar_item["state"] in (
        RequirementItemStatus.UNREADABLE.value,
        RequirementItemStatus.REPLACEMENT_REQUIRED.value,
        RequirementItemStatus.NOT_PROVIDED.value,
    )


# -------------------------------------------------------------------------
# Test Suite 4: GET /canonical-schemes/{scheme_id}/factsheet
# -------------------------------------------------------------------------

def test_api_get_scheme_factsheet_success(client):
    """Factsheet returns official scheme details, GR references, and FAQs without citizen PII."""
    resp = client.get("/canonical-schemes/candidate-majhi-ladki-bahin/factsheet")
    assert resp.status_code == 200
    data = resp.json()
    assert "canonical_scheme_id" in data or "scheme_id" in data
    assert "official_scheme_name" in data
    assert "faqs" in data
    assert len(data["faqs"]) >= 3
    # Verify no PII
    for key in ("applicant_name", "aadhaar_number", "phone", "email"):
        assert key not in data


def test_api_get_scheme_factsheet_404(client):
    """Factsheet returns 404 for unknown scheme."""
    resp = client.get("/canonical-schemes/non-existent-xyz-999/factsheet")
    assert resp.status_code == 404


# -------------------------------------------------------------------------
# Test Suite 5: GET /admin/scheme-coverage
# -------------------------------------------------------------------------

def test_api_admin_scheme_coverage_report(client):
    """Admin scheme coverage report confirms scheme coverage contract and document requirements."""
    resp = client.get("/admin/scheme-coverage")
    assert resp.status_code == 200
    data = resp.json()
    assert data["registry_total"] == 89
    assert data["total_canonical_schemes"] == 89
    assert data["total_active_canonical_schemes"] == 87
    assert data["quarantined_fixture_count"] == 2
    assert data["schemes_with_detailed_document_requirements"] == 75
    assert data["coverage_percentage"] == 100
    assert data["verified_schemes"] >= 50
    assert data["all_75_schemes_covered"] is True


def test_quarantined_fixtures_excluded_from_confirmed_eligibility():
    """Invariant I-02: Quarantined fixtures never produce confirmed production eligibility."""
    from scheme_navigator.domain.models import CitizenProfile, EligibilityStatus
    from scheme_navigator.services.catalog import canonical_catalog
    from scheme_navigator.services.rule_engine import evaluate_scheme

    demo_scheme = canonical_catalog.get("demo-majhi-ladki-bahin")
    assert demo_scheme is not None
    assert not getattr(demo_scheme, "publication_authorized", True)

    profile = CitizenProfile(
        age_years=30,
        gender="female",
        annual_family_income=100000,
        resident_state="Maharashtra",
    )
    result = evaluate_scheme(demo_scheme, profile)
    assert result.status != EligibilityStatus.ELIGIBLE
    assert result.status == EligibilityStatus.NEEDS_REVIEW


def test_quarantined_fixtures_not_in_decision_ready_pool():
    """Quarantined demo fixtures are never flagged as decision ready."""
    from scheme_navigator.source_registry.registry import SourceRegistry
    reg = SourceRegistry()
    schemes = reg.list_canonical_schemes()
    fixtures = [s for s in schemes if s.canonical_scheme_id.startswith("demo-")]
    assert len(fixtures) >= 2
    for f in fixtures:
        assert getattr(f, "is_decision_ready", False) is False
        assert getattr(f, "publication_status", "") == "ACTIVE_DEMO_FIXTURE"


def test_quarantined_fixtures_isolated_from_production_attestations():
    """Real production attestation store does not hold completeness attestations for demo fixtures."""
    from pathlib import Path
    from scheme_navigator.governance.attestation_store import AttestationStore
    base_dir = Path(__file__).resolve().parents[1]
    prod_store = AttestationStore(db_path=base_dir / "data" / "ingestion.sqlite3")
    attestations = prod_store.list_attestations()
    demo_attestations = [a for a in attestations if a.scheme_id.startswith("demo-")]
    assert len(demo_attestations) == 0, f"Found demo fixture attestations in production DB: {demo_attestations}"
    # Verify exactly 16 genuine scheme attestations
    assert len(attestations) == 16, f"Expected 16 genuine attestations, found {len(attestations)}"
