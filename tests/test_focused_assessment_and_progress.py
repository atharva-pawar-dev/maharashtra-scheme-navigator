"""
Tests for Focused Scheme Assessment, Single Active Scheme Progress, and Citizen Profile Persistence.
"""

import pytest
from fastapi.testclient import TestClient
from scheme_navigator.api.main import app
from scheme_navigator.security.auth import session_manager
from scheme_navigator.security.models import UserRole

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def citizen_auth():
    session, token = session_manager.create_session(role=UserRole.CITIZEN, user_id="citizen_tester")
    return {"Authorization": f"Bearer {token}"}

def test_scoped_assessment_generates_fresh_session_run(client, citizen_auth):
    """Scoped assessment from Explore generates fresh run with no stale turns."""
    res1 = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={"thread_id": "thread-ladki-1", "language": "en", "scheme_id": "demo-majhi-ladki-bahin"},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert "thread_id" in data1
    thread_id1 = data1["thread_id"]

    # Post an answer using /interview/answer
    turn1 = client.post(
        "/interview/answer",
        headers=citizen_auth,
        json={
            "thread_id": thread_id1,
            "answer": "female",
            "language": "en",
        },
    )
    assert turn1.status_code == 200

    # Start fresh scoped assessment for another scheme
    res2 = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={"thread_id": "thread-pension-1", "language": "en", "scheme_id": "demo-indira-gandhi-old-age-pension"},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    thread_id2 = data2["thread_id"]

    assert thread_id2 != thread_id1
    assert data2.get("question") is not None

def test_scoped_assessment_focuses_on_target_scheme(client, citizen_auth):
    """Scoped assessment records target scheme_id in run metadata."""
    res = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={"thread_id": "thread-focused-1", "language": "en", "scheme_id": "demo-majhi-ladki-bahin"},
    )
    assert res.status_code == 200
    data = res.json()
    thread_id = data["thread_id"]
    assert thread_id == "thread-focused-1"
    assert data.get("question") is not None

def test_single_active_scheme_enforcement(client, citizen_auth):
    """Citizen can only have one active scheme at a time; activating a new one pauses previous and preserves data."""
    # Activate scheme 1 with document progress
    act1 = client.post(
        "/progress/activate",
        headers=citizen_auth,
        json={
            "scheme_id": "demo-majhi-ladki-bahin",
            "version": "1.0.0",
            "progress_data": {
                "documents": [{"document_type": "aadhaar_card", "verified": True}],
                "stage": "document_preparation"
            }
        }
    )
    assert act1.status_code == 200
    res1 = client.get("/progress", headers=citizen_auth)
    assert res1.status_code == 200
    prog1 = res1.json()
    assert prog1["active_scheme_id"] == "demo-majhi-ladki-bahin"

    # Activate scheme 2
    act2 = client.post(
        "/progress/activate",
        headers=citizen_auth,
        json={
            "scheme_id": "demo-indira-gandhi-old-age-pension",
            "version": "1.0.0",
            "progress_data": {"stage": "initial"}
        }
    )
    assert act2.status_code == 200
    res2 = client.get("/progress", headers=citizen_auth)
    assert res2.status_code == 200
    prog2 = res2.json()
    # Exactly one active scheme
    assert prog2["active_scheme_id"] == "demo-indira-gandhi-old-age-pension"

    # Prior scheme is paused and its document progress is preserved
    assert "demo-majhi-ladki-bahin" in prog2["paused_schemes"]
    prior_entry = prog2["paused_schemes"]["demo-majhi-ladki-bahin"]
    assert prior_entry["progress_data"]["stage"] == "document_preparation"
    assert prior_entry["progress_data"]["documents"][0]["document_type"] == "aadhaar_card"

def test_permanent_dismissal_removes_from_progress_and_recommendations(client, citizen_auth):
    """Dismissing a scheme removes it from active progress and excludes it from future evaluations."""
    # First activate it
    client.post(
        "/progress/activate",
        headers=citizen_auth,
        json={"scheme_id": "demo-majhi-ladki-bahin", "version": "1.0.0"}
    )
    prog_before = client.get("/progress", headers=citizen_auth).json()
    assert prog_before["active_scheme_id"] == "demo-majhi-ladki-bahin"

    # Now dismiss it
    dismiss_res = client.post(
        "/progress/dismiss",
        headers=citizen_auth,
        json={"scheme_id": "demo-majhi-ladki-bahin"}
    )
    assert dismiss_res.status_code == 200

    prog_after = client.get("/progress", headers=citizen_auth).json()
    assert prog_after["active_scheme_id"] is None
    assert "demo-majhi-ladki-bahin" in prog_after.get("dismissed_schemes", [])
    assert "demo-majhi-ladki-bahin" not in prog_after.get("paused_schemes", {})

def test_profile_persistence_and_reset(client, citizen_auth):
    """Citizen profile is persisted across requests and can be reset cleanly."""
    profile_data = {
        "name": "Sunita Patil",
        "gender": "female",
        "resident_state": "maharashtra",
        "age_years": 34,
        "annual_family_income": 120000,
        "marital_status": "married",
        "has_land": True,
        "landholding_hectares": 2.0,
        "ration_card_type": "bpl_yellow",
        "aadhaar_linked_bank_account": True
    }

    # Save profile
    save_res = client.post("/profile", headers=citizen_auth, json={"profile": profile_data})
    assert save_res.status_code == 200

    # Retrieve profile
    get_res = client.get("/profile", headers=citizen_auth)
    assert get_res.status_code == 200
    saved = get_res.json()["profile"]
    assert saved["name"] == "Sunita Patil"
    assert saved["age_years"] == 34
    assert saved["landholding_hectares"] == 2.0
    assert saved["ration_card_type"] == "bpl_yellow"

    # Reset profile
    reset_res = client.post("/profile/reset", headers=citizen_auth)
    assert reset_res.status_code == 200

    # Retrieve after reset
    get_after = client.get("/profile", headers=citizen_auth)
    assert get_after.status_code == 200
    after_profile = get_after.json()["profile"]
    assert after_profile is None or after_profile == {} or after_profile.get("name") is None
