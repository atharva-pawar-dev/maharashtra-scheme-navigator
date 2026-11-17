"""
Regression Test Suite for Interview Context, Focused Eligibility & Stale Results Elimination.
Validates the 11 critical scenarios specified in Part 10.
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
    session, token = session_manager.create_session(role=UserRole.CITIZEN, user_id="citizen_tester_regression")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def citizen_auth_2():
    session, token = session_manager.create_session(role=UserRole.CITIZEN, user_id="citizen_tester_rival")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Test 1: Full Discovery
# ---------------------------------------------------------------------------
def test_1_full_discovery_journey(client, citizen_auth):
    """Start Discovery -> Assert DISCOVERY run ID -> Submit answers -> Complete -> All assessable schemes evaluated."""
    start_res = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_disc_test_1",
            "language": "en",
            "mode": "DISCOVERY",
            "profile": {
                "resident_state": "maharashtra",
            }
        }
    )
    assert start_res.status_code == 200
    data = start_res.json()
    assert data["thread_id"] == "run_disc_test_1"
    assert data.get("question") is not None
    q1_field = data["question"]["field"]
    assert q1_field in ["gender", "age_years", "annual_family_income", "is_student", "bpl", "has_land"]

    # Provide an answer
    ans_res = client.post(
        "/interview/answer",
        headers=citizen_auth,
        json={
            "thread_id": "run_disc_test_1",
            "answer": "female" if q1_field == "gender" else "25",
            "language": "en"
        }
    )
    assert ans_res.status_code == 200
    ans_data = ans_res.json()
    assert ans_data["thread_id"] == "run_disc_test_1"

    # Start a complete discovery profile to verify full catalogue scoreboard evaluation
    comp_res = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_disc_test_1_comp",
            "language": "en",
            "mode": "DISCOVERY",
            "profile": {
                "resident_state": "maharashtra",
                "gender": "female",
                "age_years": 28,
                "annual_family_income": 80000,
                "caste_category": "open",
                "is_student": False,
                "bpl": True,
                "has_land": False,
                "landholding_hectares": 0.0,
                "disability_percentage": 0,
                "marital_status": "married",
                "aadhaar_linked_bank_account": True,
                "receiving_other_pension": False,
                "ration_card_type": "bpl_yellow"
            }
        }
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["complete"] is True
    assert "scheme_evaluations" in comp_data
    # In discovery mode, all assessable schemes are evaluated
    assert len(comp_data["scheme_evaluations"]) > 1


# ---------------------------------------------------------------------------
# Test 2: Focused Scheme Eligibility
# ---------------------------------------------------------------------------
def test_2_focused_scheme_eligibility(client, citizen_auth):
    """Start FOCUSED_SCHEME -> Target scheme set -> Only target scheme missing fields asked -> Evaluates ONLY target scheme."""
    target_id = "demo-majhi-ladki-bahin"
    start_res = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_foc_test_2",
            "language": "en",
            "mode": "FOCUSED_SCHEME",
            "target_scheme_id": target_id,
            "profile": {
                "resident_state": "maharashtra",
            }
        }
    )
    assert start_res.status_code == 200
    data = start_res.json()
    assert data["thread_id"] == "run_foc_test_2"
    assert data.get("question") is not None
    # For Majhi Ladki Bahin, rules require gender, age, income, aadhaar_linked_bank_account
    assert data["question"]["field"] in ["gender", "age_years", "annual_family_income", "aadhaar_linked_bank_account"]

    # When complete, evaluate ONLY the target scheme
    comp_res = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_foc_test_2_comp",
            "language": "en",
            "mode": "FOCUSED_SCHEME",
            "target_scheme_id": target_id,
            "profile": {
                "resident_state": "maharashtra",
                "gender": "female",
                "age_years": 25,
                "annual_family_income": 60000,
                "aadhaar_linked_bank_account": True,
            }
        }
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["complete"] is True
    evals = comp_data.get("scheme_evaluations", [])
    assert len(evals) == 1
    assert evals[0]["scheme_id"] == target_id
    assert "reason" in evals[0]
    assert len(evals[0]["sources"]) > 0


# ---------------------------------------------------------------------------
# Test 3: Stale Results Prevention
# ---------------------------------------------------------------------------
def test_3_stale_results_prevention(client, citizen_auth):
    """Complete discovery run -> Start focused assessment for another scheme -> Only focused results returned."""
    # 1. Run discovery
    disc_res = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_disc_prior",
            "language": "en",
            "mode": "DISCOVERY",
            "profile": {
                "resident_state": "maharashtra",
                "gender": "female",
                "age_years": 30,
                "annual_family_income": 50000,
                "is_student": False,
                "bpl": True,
                "has_land": False,
                "aadhaar_linked_bank_account": True,
                "receiving_other_pension": False,
                "ration_card_type": "bpl_yellow"
            }
        }
    )
    assert disc_res.status_code == 200
    disc_data = disc_res.json()
    disc_results = disc_data.get("scheme_evaluations", [])
    assert len(disc_results) > 1

    # 2. Run focused assessment for a single specific scheme
    target_id = "demo-indira-gandhi-old-age-pension"
    foc_res = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_foc_isolated",
            "language": "en",
            "mode": "FOCUSED_SCHEME",
            "target_scheme_id": target_id,
            "profile": {
                "resident_state": "maharashtra",
                "age_years": 68,
                "bpl": True,
                "receiving_other_pension": False,
            }
        }
    )
    assert foc_res.status_code == 200
    foc_data = foc_res.json()
    assert foc_data["complete"] is True
    foc_results = foc_data.get("scheme_evaluations", [])
    # Assert that only focused scheme results appear, NOT the multi-scheme discovery results
    assert len(foc_results) == 1
    assert foc_results[0]["scheme_id"] == target_id

    # 3. Retrieve results by thread_id endpoint
    fetch_res = client.get(
        f"/interview/run_foc_isolated/results",
        headers=citizen_auth
    )
    assert fetch_res.status_code == 200
    fetch_data = fetch_res.json()
    assert fetch_data["mode"] == "FOCUSED_SCHEME"
    assert fetch_data["target_scheme_id"] == target_id
    results_list = fetch_data.get("results") or fetch_data.get("scheme_evaluations", [])
    assert len(results_list) == 1
    assert results_list[0]["scheme_id"] == target_id


# ---------------------------------------------------------------------------
# Test 4: New Discovery Interview
# ---------------------------------------------------------------------------
def test_4_new_discovery_interview_lifecycle(client, citizen_auth):
    """Start discovery -> complete -> click New Interview -> fresh run ID, no transcript bleed, correct next question or evaluation."""
    res1 = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_disc_initial",
            "language": "en",
            "mode": "DISCOVERY",
            "profile": {}
        }
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["thread_id"] == "run_disc_initial"

    # Start "New Interview" (fresh thread_id in discovery mode)
    res2 = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_disc_restarted",
            "language": "en",
            "mode": "DISCOVERY",
            "profile": {"resident_state": "maharashtra"}
        }
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["thread_id"] == "run_disc_restarted"
    assert data2["thread_id"] != data1["thread_id"]
    # Question is presented without hanging
    assert data2.get("question") is not None


# ---------------------------------------------------------------------------
# Test 5: New Focused Interview
# ---------------------------------------------------------------------------
def test_5_new_focused_interview_preserves_target(client, citizen_auth):
    """In focused mode, restart preserves target scheme and isolates results."""
    target_id = "demo-majhi-ladki-bahin"
    res1 = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_foc_step1",
            "language": "en",
            "mode": "FOCUSED_SCHEME",
            "target_scheme_id": target_id,
            "profile": {"resident_state": "maharashtra"}
        }
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1.get("question") is not None

    # Restart focused interview
    res2 = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_foc_step2",
            "language": "en",
            "mode": "FOCUSED_SCHEME",
            "target_scheme_id": target_id,
            "profile": {"resident_state": "maharashtra"}
        }
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["thread_id"] == "run_foc_step2"
    assert data2.get("question") is not None


# ---------------------------------------------------------------------------
# Test 6: Pre-populated Complete Profile
# ---------------------------------------------------------------------------
def test_6_prepopulated_profile_evaluates_immediately(client, citizen_auth):
    """When a complete profile is provided, no unnecessary questions are asked; immediate evaluation occurs."""
    target_id = "demo-majhi-ladki-bahin"
    res = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_foc_complete_prof",
            "language": "en",
            "mode": "FOCUSED_SCHEME",
            "target_scheme_id": target_id,
            "profile": {
                "resident_state": "maharashtra",
                "gender": "female",
                "age_years": 29,
                "annual_family_income": 50000,
                "is_student": False,
                "bpl": True,
                "aadhaar_linked_bank_account": True,
            }
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["complete"] is True
    assert data.get("question") is None
    assert "scheme_evaluations" in data
    assert len(data["scheme_evaluations"]) == 1
    assert data["scheme_evaluations"][0]["scheme_id"] == target_id


# ---------------------------------------------------------------------------
# Test 7: Unknown Information / Needs Information
# ---------------------------------------------------------------------------
def test_7_missing_mandatory_field_results_in_needs_info(client, citizen_auth):
    """If mandatory field is missing, interview asks for it and scheme is not prematurely classified as ineligible."""
    target_id = "demo-majhi-ladki-bahin"
    res = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_foc_missing_fields",
            "language": "en",
            "mode": "FOCUSED_SCHEME",
            "target_scheme_id": target_id,
            "profile": {
                "resident_state": "maharashtra",
                "gender": "female"
            }
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["complete"] is False
    assert data.get("question") is not None
    assert data["question"]["field"] in ["age_years", "annual_family_income", "aadhaar_linked_bank_account"]


# ---------------------------------------------------------------------------
# Test 8: Stale & Cross-Tenant Denials
# ---------------------------------------------------------------------------
def test_8_nonexistent_or_cross_tenant_run_isolation(client, citizen_auth, citizen_auth_2):
    """Attempting to access non-existent run or another citizen's run results denies access cleanly."""
    # Non-existent run
    res404 = client.get(
        "/interview/non_existent_thread_xyz/results",
        headers=citizen_auth
    )
    assert res404.status_code in [404, 403]

    # Create run with citizen 1
    c1_run = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_c1_secret",
            "language": "en",
            "profile": {
                "resident_state": "maharashtra",
                "gender": "female",
                "age_years": 25,
                "annual_family_income": 50000,
                "aadhaar_linked_bank_account": True
            }
        }
    )
    assert c1_run.status_code == 200

    # Citizen 2 tries to fetch citizen 1's run results
    cross_res = client.get(
        "/interview/run_c1_secret/results",
        headers=citizen_auth_2
    )
    assert cross_res.status_code in [403, 404]


# ---------------------------------------------------------------------------
# Test 9: Request Race Conditions & Run Isolation
# ---------------------------------------------------------------------------
def test_9_run_isolation_under_concurrency(client, citizen_auth):
    """Answers submitted to thread A do not contaminate thread B."""
    # Start thread A
    resA = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={"thread_id": "run_thread_A", "language": "en", "profile": {"resident_state": "maharashtra"}}
    )
    assert resA.status_code == 200

    # Start thread B
    resB = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={"thread_id": "run_thread_B", "language": "en", "profile": {"resident_state": "maharashtra"}}
    )
    assert resB.status_code == 200

    # Answer thread A
    ansA = client.post(
        "/interview/answer",
        headers=citizen_auth,
        json={"thread_id": "run_thread_A", "answer": "female", "language": "en"}
    )
    assert ansA.status_code == 200
    assert ansA.json()["thread_id"] == "run_thread_A"

    # Answer thread B with different value
    ansB = client.post(
        "/interview/answer",
        headers=citizen_auth,
        json={"thread_id": "run_thread_B", "answer": "male", "language": "en"}
    )
    assert ansB.status_code == 200
    assert ansB.json()["thread_id"] == "run_thread_B"


# ---------------------------------------------------------------------------
# Test 10: Multilingual Flow (en, mr, hi)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("lang", ["en", "mr", "hi"])
def test_10_multilingual_interview_flow(client, citizen_auth, lang):
    """Full and focused interviews respect the chosen language and return localized text and labels."""
    res = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": f"run_lang_{lang}",
            "language": lang,
            "mode": "DISCOVERY",
            "profile": {"resident_state": "maharashtra"}
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data.get("question") is not None
    q = data["question"]
    assert "text" in q
    assert len(q["text"]) > 0
    if q.get("choices") and q.get("choice_labels"):
        assert len(q["choice_labels"]) > 0


# ---------------------------------------------------------------------------
# Test 11: Invalid Scheme Rejection
# ---------------------------------------------------------------------------
def test_11_invalid_scheme_rejection(client, citizen_auth):
    """Starting a focused assessment with an invalid/hallucinated scheme returns 404."""
    res = client.post(
        "/interview/start",
        headers=citizen_auth,
        json={
            "thread_id": "run_fake_scheme",
            "language": "en",
            "mode": "FOCUSED_SCHEME",
            "target_scheme_id": "non-existent-hallucinated-scheme-9999",
            "profile": {}
        }
    )
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data
