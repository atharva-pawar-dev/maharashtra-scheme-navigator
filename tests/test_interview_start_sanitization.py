import pytest
from fastapi.testclient import TestClient
from scheme_navigator.api.main import app
from scheme_navigator.domain.models import CitizenProfile, InterviewStart, Language, InterviewMode

@pytest.fixture
def client():
    return TestClient(app)

def test_citizen_profile_strips_metadata_envelope():
    """CitizenProfile cleanly strips session_id, provenance, and unwraps nested profile dict."""
    raw = {
        "session_id": "sess_1234567890abcdef",
        "profile": {
            "name": "Eknath Shinde",
            "age_years": 60,
            "gender": "male",
            "resident_state": "Maharashtra",
            "annual_family_income": 200000,
        },
        "provenance": {"source": "test_env"}
    }
    p = CitizenProfile.model_validate(raw)
    assert p.name == "Eknath Shinde"
    assert p.age_years == 60
    assert p.resident_state == "maharashtra"
    assert not hasattr(p, "session_id")
    assert not hasattr(p, "provenance")

def test_citizen_profile_maps_age_to_age_years():
    """CitizenProfile maps legacy age field to age_years."""
    p = CitizenProfile.model_validate({"age": 68, "resident_state": "Maharashtra"})
    assert p.age_years == 68
    assert p.age == 68

def test_interview_start_sanitizes_nested_and_extra_fields():
    """InterviewStart cleanly strips unknown and envelope fields from profile."""
    payload = {
        "thread_id": "thread_test_sanitization",
        "language": "en",
        "profile": {
            "session_id": "sess_leaked_session_id",
            "name": "Sunita Patil",
            "age_years": 70,
            "gender": "female",
            "resident_state": "Maharashtra",
            "profile": {
                "name": "Sunita Patil",
                "age_years": 70,
                "resident_state": "Maharashtra",
            },
            "provenance": {},
            "unrelated_extra_key": "some_value",
        },
        "mode": "FOCUSED_SCHEME",
        "scheme_id": "demo-indira-gandhi-old-age-pension",
        "target_scheme_id": "demo-indira-gandhi-old-age-pension",
    }
    start_req = InterviewStart.model_validate(payload)
    assert start_req.profile.name == "Sunita Patil"
    assert start_req.profile.age_years == 70
    assert start_req.profile.resident_state == "maharashtra"

def test_api_interview_start_with_profile_envelope_returns_200(client):
    """API endpoint /interview/start accepts profile envelope from GET /profile without 422."""
    prof_res = client.get("/profile")
    assert prof_res.status_code == 200
    leaked_profile = prof_res.json()

    start_payload = {
        "thread_id": "thread_envelope_api_test",
        "language": "en",
        "profile": leaked_profile,
        "mode": "FOCUSED_SCHEME",
        "scheme_id": "demo-indira-gandhi-old-age-pension",
        "target_scheme_id": "demo-indira-gandhi-old-age-pension",
        "scope": "canonical",
    }
    res = client.post("/interview/start", json=start_payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "question" in data
    assert data["question"] is not None
    assert "text" in data["question"]

def test_api_anonymous_interview_flow_start_and_answer(client):
    """Anonymous citizen can start and answer interview without 403 Forbidden."""
    thread_id = "thread_anon_flow_test"
    start_payload = {
        "thread_id": thread_id,
        "language": "mr",
        "profile": {},
        "mode": "FOCUSED_SCHEME",
        "scheme_id": "demo-indira-gandhi-old-age-pension",
        "target_scheme_id": "demo-indira-gandhi-old-age-pension",
        "scope": "canonical",
    }
    start_res = client.post("/interview/start", json=start_payload)
    assert start_res.status_code == 200
    q = start_res.json().get("question")
    assert q is not None

    # Answer the first question
    answer_res = client.post("/interview/answer", json={
        "thread_id": thread_id,
        "answer": "होय",
        "language": "mr",
    })
    assert answer_res.status_code == 200, f"Expected 200, got {answer_res.status_code}: {answer_res.text}"
    ans_data = answer_res.json()
    assert "question" in ans_data or ans_data.get("complete") is True
