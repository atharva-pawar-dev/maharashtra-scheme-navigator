from __future__ import annotations

from fastapi.testclient import TestClient

from scheme_navigator.api.main import app

client = TestClient(app)


def test_health_schemes_and_plan():
    assert client.get("/healthz").status_code == 200
    schemes = client.get("/schemes")
    assert schemes.status_code == 200 and len(schemes.json()) >= 2
    plan = client.post("/plans/demo-majhi-ladki-bahin")
    assert plan.status_code == 200
    assert plan.json()["estimated_notified_days_on_critical_path"] == 15


def test_interview_returns_one_question_then_updates_profile():
    thread = "test-interview-question-loop"
    started = client.post("/interview/start", json={"thread_id": thread, "language": "en", "profile": {}})
    assert started.status_code == 200
    question = started.json()["question"]
    assert question and question["field"]
    answers = {
        "age_years": "24",
        "resident_state": "Maharashtra",
        "gender": "female",
        "annual_family_income": "2.5 lakh",
        "aadhaar_linked_bank_account": "yes",
        "bpl": "no",
        "receiving_other_pension": "no",
        "is_student": "yes",
        "has_disability": "no",
        "caste_category": "OBC",
    }
    answered = client.post("/interview/answer", json={"thread_id": thread, "answer": answers.get(question["field"], "24"), "language": "en"})
    assert answered.status_code == 200
    assert answered.json()["profile"] is not None
    assert answered.json()["question"] is None or answered.json()["question"]["field"] != question["field"]


def test_bhashini_requires_explicit_cloud_consent():
    response = client.post(
        "/voice/transcribe?provider=bhashini&language=mr&consent_to_cloud_processing=false",
        files={"file": ("voice.wav", b"not-real-audio", "audio/wav")},
    )
    assert response.status_code == 400
    assert "consent" in response.json()["detail"].lower()
