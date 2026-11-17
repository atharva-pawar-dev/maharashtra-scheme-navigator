from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app, catalog
import scheme_navigator.api.main as api_main
from scheme_navigator.domain.models import (
    CitizenProfile,
    EligibilityStatus,
    InterviewStart,
    Scheme,
)
from scheme_navigator.services.catalog import SchemeCatalog


@pytest.fixture
def client():
    return TestClient(app)


def test_empty_profile_evaluates_all_catalogue_schemes_as_unknown(client):
    response = client.post("/eligibility/evaluate", json={})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(catalog.all())
    for item in data:
        assert item["scheme_id"]
        assert item["status"] in {
            EligibilityStatus.NEEDS_INFORMATION.value,
            EligibilityStatus.NEEDS_REVIEW.value,
        }
        assert len(item["unknown_conditions"]) > 0 or len(item["missing_fields"]) > 0
        assert len(item["failed_conditions"]) == 0


def test_three_valued_boolean_handling(client):
    # 1. bpl = True: matches for old-age pension scheme
    res_true = client.post(
        "/eligibility/evaluate",
        json={"age_years": 70, "resident_state": "Maharashtra", "bpl": True},
    )
    assert res_true.status_code == 200
    data_true = {item["scheme_id"]: item for item in res_true.json()}
    pension_true = data_true["demo-indira-gandhi-old-age-pension"]
    assert any("bpl must equal True" in c for c in pension_true["matched_conditions"])
    assert not any("bpl must equal True" in c for c in pension_true["failed_conditions"])

    # 2. bpl = False: fails for old-age pension scheme
    res_false = client.post(
        "/eligibility/evaluate",
        json={"age_years": 70, "resident_state": "Maharashtra", "bpl": False},
    )
    assert res_false.status_code == 200
    data_false = {item["scheme_id"]: item for item in res_false.json()}
    pension_false = data_false["demo-indira-gandhi-old-age-pension"]
    assert any("bpl must equal True" in c for c in pension_false["failed_conditions"])

    # 3. bpl = None (omitted): unknown for pension scheme, not failed
    res_none = client.post(
        "/eligibility/evaluate",
        json={"age_years": 70, "resident_state": "Maharashtra"},
    )
    assert res_none.status_code == 200
    data_none = {item["scheme_id"]: item for item in res_none.json()}
    pension_none = data_none["demo-indira-gandhi-old-age-pension"]
    assert any("bpl must equal True" in c for c in pension_none["unknown_conditions"])
    assert "bpl" in pension_none["missing_fields"]
    assert not any("bpl must equal True" in c for c in pension_none["failed_conditions"])


def test_explicit_residency_handling(client):
    # 1. residency = None (omitted): unknown, does not fail
    res_none = client.post("/eligibility/evaluate", json={"age_years": 25})
    assert res_none.status_code == 200
    ladki_none = next(
        s for s in res_none.json() if s["scheme_id"] == "demo-majhi-ladki-bahin"
    )
    assert any("resident_state must equal 'maharashtra'" in c for c in ladki_none["unknown_conditions"])
    assert "resident_state" in ladki_none["missing_fields"]

    # 2. residency = "Maharashtra": matched
    res_mh = client.post("/eligibility/evaluate", json={"resident_state": "Maharashtra"})
    assert res_mh.status_code == 200
    ladki_mh = next(
        s for s in res_mh.json() if s["scheme_id"] == "demo-majhi-ladki-bahin"
    )
    assert any("resident_state must equal 'maharashtra'" in c for c in ladki_mh["matched_conditions"])

    # 3. residency = "Other state": failed
    res_other = client.post("/eligibility/evaluate", json={"resident_state": "Other state"})
    assert res_other.status_code == 200
    ladki_other = next(
        s for s in res_other.json() if s["scheme_id"] == "demo-majhi-ladki-bahin"
    )
    assert any("resident_state must equal 'maharashtra'" in c for c in ladki_other["failed_conditions"])


def test_gender_prefer_not_to_say_normalizes_to_none_and_does_not_fail(client):
    payload = {
        "gender": "prefer_not_to_say",
        "resident_state": "Maharashtra",
        "age_years": 25,
        "annual_family_income": 200000,
    }
    response = client.post("/eligibility/evaluate", json=payload)
    assert response.status_code == 200
    ladki = next(
        s for s in response.json() if s["scheme_id"] == "demo-majhi-ladki-bahin"
    )
    # Gender condition must be in unknown_conditions, NOT failed_conditions
    assert any("gender must equal 'female'" in c for c in ladki["unknown_conditions"])
    assert "gender" in ladki["missing_fields"]
    assert not any("gender must equal 'female'" in c for c in ladki["failed_conditions"])


def test_interview_start_scopes_to_selected_scheme(client):
    thread_id = "test-scope-ladki-bahin"
    payload = {
        "thread_id": thread_id,
        "language": "en",
        "scheme_id": "demo-majhi-ladki-bahin",
        "profile": {
            "age_years": 25,
            "gender": "female",
            "resident_state": "Maharashtra",
            "annual_family_income": 200000,
        },
    }
    response = client.post("/interview/start", json=payload)
    assert response.status_code == 200
    data = response.json()
    question = data.get("question")
    assert question is not None
    # Because only demo-majhi-ladki-bahin is in candidate_schemes,
    # the question picker must only ask for its missing field (aadhaar_linked_bank_account),
    # never pension scheme fields like bpl or receiving_other_pension!
    assert question["field"] == "aadhaar_linked_bank_account"


def test_interview_start_returns_404_for_invalid_scheme_id(client):
    thread_id = "test-invalid-scheme-id"
    payload = {
        "thread_id": thread_id,
        "language": "en",
        "scheme_id": "invalid-or-nonexistent-scheme",
        "profile": {},
    }
    response = client.post("/interview/start", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_interview_start_falls_back_to_catalog_wide_when_scheme_id_omitted(client):
    thread_id = "test-catalog-wide-omitted-scheme"
    payload = {
        "thread_id": thread_id,
        "language": "en",
        "profile": {},
    }
    response = client.post("/interview/start", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["question"] is not None


def test_interview_get_state_returns_active_question_without_profile_leak(client):
    thread_id = "test-interview-get-state"
    start_payload = {
        "thread_id": thread_id,
        "language": "en",
        "scheme_id": "demo-majhi-ladki-bahin",
        "profile": {
            "age_years": 25,
            "gender": "female",
            "resident_state": "Maharashtra",
            "annual_family_income": 200000,
        },
    }
    client.post("/interview/start", json=start_payload)

    # State recovery retrieval
    response = client.get(f"/interview/{thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == thread_id
    assert data["question"] is not None
    assert data["question"]["field"] == "aadhaar_linked_bank_account"
    assert data["complete"] is False
    # CRITICAL SECURITY CHECK: profile must NOT be leaked
    assert "profile" not in data or not data["profile"]


def test_interview_get_state_enforces_environment_restriction(monkeypatch, client):
    monkeypatch.setattr(api_main.settings, "app_env", "production")
    response = client.get("/interview/test-prod-env-check")
    assert response.status_code == 503
    assert "disabled in production" in response.json()["detail"].lower()


def test_assessment_reconstructs_profile_from_server_thread_id(client):
    thread_id = "test-assessment-thread-reconstruction"
    start_payload = {
        "thread_id": thread_id,
        "language": "en",
        "scheme_id": "demo-majhi-ladki-bahin",
        "profile": {
            "age_years": 25,
            "gender": "female",
            "resident_state": "Maharashtra",
            "annual_family_income": 200000,
        },
    }
    client.post("/interview/start", json=start_payload)
    # Answer the remaining missing condition
    client.post(
        "/interview/answer",
        json={"thread_id": thread_id, "answer": "yes", "language": "en"},
    )

    # Request assessment WITHOUT client-side profile, passing only thread_id
    assessment_res = client.post(
        "/assessment/demo-majhi-ladki-bahin",
        json={
            "thread_id": thread_id,
            "target_financial_year": "2026-27",
        },
    )
    assert assessment_res.status_code == 200
    assessment_data = assessment_res.json()
    assert assessment_data["scheme_id"] == "demo-majhi-ladki-bahin"
    # Check that conditions were evaluated using the server-reconstructed profile!
    matched = assessment_data["eligibility"]["matched_conditions"]
    assert any("gender must equal 'female'" in c for c in matched)
    assert any("annual_family_income must be at most 250000" in c for c in matched)
    assert any("aadhaar_linked_bank_account must equal True" in c for c in matched)


def test_demo_schemes_never_return_confirmed_eligibility(client):
    payload = {
        "gender": "female",
        "resident_state": "Maharashtra",
        "age_years": 25,
        "annual_family_income": 200000,
        "aadhaar_linked_bank_account": True,
    }
    response = client.post("/eligibility/evaluate", json=payload)
    assert response.status_code == 200
    for item in response.json():
        if "demo" in item["scheme_id"]:
            assert item["status"] == EligibilityStatus.NEEDS_REVIEW.value
            assert "demo fixture" in item["reason"].lower()


def test_catalogue_sources_strictly_use_https_and_valid_hashes():
    for scheme in catalog.all():
        assert len(scheme.sources) >= 1
        for source in scheme.sources:
            assert source.source_url.startswith("https://")
            assert len(source.evidence_sha256) == 64
