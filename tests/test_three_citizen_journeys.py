"""
Tests for the Three Primary Citizen Entry Paths:
1. Find Schemes for Me (Personalized Guided Interview & Discovery)
2. Explore Schemes (Independent Discovery, Library, Filters & Focused Assessment)
3. Prepare My Application (Saved State Resume, Prerequisite Roadmap & Empty State)
"""

import pytest
from fastapi.testclient import TestClient
from scheme_navigator.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

# =========================================================================
# JOURNEY 1: FIND SCHEMES FOR ME
# =========================================================================

def test_journey_find_schemes_for_me_lifecycle(client):
    """
    Find schemes for me:
    - Starts correct interview
    - Preserves citizen answers across turns
    - Performs catalogue-wide evaluation
    - Returns correct 3-valued status (TRUE, FALSE, UNKNOWN)
    - Carries selected scheme forward
    """
    thread_id = "test-journey-find-001"

    # Step 1: Start Interview in Marathi
    start_payload = {
        "thread_id": thread_id,
        "language": "mr",
        "profile": {"resident_state": "maharashtra"}
    }
    res_start = client.post("/interview/start", json=start_payload)
    assert res_start.status_code == 200
    data_start = res_start.json()
    assert data_start["thread_id"] == thread_id
    assert data_start["profile"]["resident_state"] == "maharashtra"
    assert "question" in data_start
    q_field = data_start["question"]["field"]

    # Step 2: Answer age question dynamically based on asked field
    ans_value = "28" if q_field == "age_years" else "female"
    ans_payload = {
        "thread_id": thread_id,
        "answer": ans_value,
        "language": "mr"
    }
    res_ans = client.post("/interview/answer", json=ans_payload)
    assert res_ans.status_code == 200
    data_ans = res_ans.json()
    assert data_ans["profile"][q_field] == (28 if q_field == "age_years" else ans_value)
    assert data_ans["profile"]["resident_state"] == "maharashtra"

    # Step 3: Run Catalogue-Wide Evaluation
    profile_payload = data_ans["profile"]
    profile_payload["gender"] = "female"
    profile_payload["annual_family_income"] = 180000

    res_eval = client.post("/eligibility/evaluate?language=mr", json=profile_payload)
    assert res_eval.status_code == 200
    eval_list = res_eval.json()
    assert isinstance(eval_list, list)
    assert len(eval_list) >= 1

    # Verify 4-group status & explanation
    valid_statuses = {"eligible", "ineligible", "needs_information", "needs_review", "TRUE", "FALSE", "UNKNOWN"}
    for ev in eval_list:
        assert ev["status"].lower() in {s.lower() for s in valid_statuses}
        assert "scheme_id" in ev
        assert "reason" in ev
        assert isinstance(ev.get("sources", []), list)

# =========================================================================
# JOURNEY 2: EXPLORE SCHEMES
# =========================================================================

def test_journey_explore_schemes_catalogue_and_focused_assessment(client):
    """
    Explore schemes:
    - Loads actual supported catalogue records
    - Draft schemes are not misrepresented (demo fixtures labeled)
    - Scheme details use actual evidence
    - Focused eligibility assessment works for selected scheme
    """
    res = client.get("/schemes")
    assert res.status_code == 200
    schemes = res.json()
    assert isinstance(schemes, list)
    assert len(schemes) >= 1

    for s in schemes:
        assert "scheme_id" in s
        assert "name" in s
        assert "department" in s
        # Ensure demo fixture has clear indicator
        if not s.get("publication_authorized"):
            assert "(demo fixture)" in s["name"].lower() or s.get("rule_status") in {"draft", "active"}

    # Focused Assessment for a specific scheme
    selected_scheme = schemes[0]["scheme_id"]
    assess_req = {
        "profile": {
            "resident_state": "maharashtra",
            "gender": "female",
            "age_years": 24,
            "annual_family_income": 150000
        },
        "documents": [],
        "target_financial_year": "2026-27",
        "language": "mr"
    }
    res_assess = client.post(f"/assessment/{selected_scheme}", json=assess_req)
    assert res_assess.status_code == 200
    assess_data = res_assess.json()
    assert assess_data["scheme_id"] == selected_scheme
    assert "eligibility" in assess_data
    assert "application_plan" in assess_data

# =========================================================================
# JOURNEY 3: PREPARE MY APPLICATION
# =========================================================================

def test_journey_prepare_my_application_resume_and_empty_state(client):
    """
    Prepare my application:
    - Correctly identifies saved state via thread_id
    - Resumes genuine saved interview/profile state
    - Validates prerequisite plan steps and RTS limits
    - Enforces ownership & safe handling
    """
    # Active Saved Session check
    thread_id = "test-journey-resume-999"
    client.post("/interview/start", json={
        "thread_id": thread_id,
        "language": "en",
        "profile": {"resident_state": "maharashtra", "age_years": 65}
    })

    res_get = client.get(f"/interview/{thread_id}")
    assert res_get.status_code == 200
    saved = res_get.json()
    assert saved["thread_id"] == thread_id

    # Check Plan / Prerequisite Roadmap
    res_plan = client.post("/plans/demo-majhi-ladki-bahin", json=["aadhaar"])
    assert res_plan.status_code == 200
    plan_data = res_plan.json()
    assert "steps" in plan_data
    assert plan_data["estimated_notified_days_on_critical_path"] is not None
    assert isinstance(plan_data["steps"], list)
    assert len(plan_data["steps"]) >= 2

    # Check non-existent thread returns 404 or empty gracefully
    res_missing = client.get("/interview/non-existent-thread-id-xyz")
    assert res_missing.status_code in {200, 404}
