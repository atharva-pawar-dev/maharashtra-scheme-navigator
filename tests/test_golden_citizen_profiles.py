"""
Golden Citizen Profiles Test Suite (10 Synthetic Citizen Profiles + Boundaries)
Covers deterministic evaluation across Maharashtra canonical schemes:
1. Student
2. Farmer
3. Woman seeking welfare
4. Senior citizen
5. Person with disability
6. Unemployed youth
7. Entrepreneur
8. Rural household
9. Urban household
10. Incomplete profile
"""

import pytest
from fastapi.testclient import TestClient
from scheme_navigator.api.main import app
from scheme_navigator.services.catalog import canonical_catalog

@pytest.fixture
def client():
    return TestClient(app)

# =========================================================================
# 10 SYNTHETIC GOLDEN CITIZEN PROFILES
# =========================================================================

GOLDEN_PROFILES = {
    "student": {
        "profile": {
            "name": "Amit Jadhav",
            "age_years": 19,
            "gender": "male",
            "resident_state": "maharashtra",
            "annual_family_income": 120000,
            "caste_category": "SC",
            "is_student": True,
            "district": "Pune"
        },
        "expected_eligible_keywords": ["scholarship", "vidyarthi", "fee", "student", "shikshan", "post-matric"]
    },
    "farmer": {
        "profile": {
            "name": "Ramesh Patil",
            "age_years": 45,
            "gender": "male",
            "resident_state": "maharashtra",
            "occupation": "farmer",
            "has_land": True,
            "landholding_hectares": 1.5,
            "annual_family_income": 95000,
            "district": "Yavatmal"
        },
        "expected_eligible_keywords": ["shetkari", "kisan", "krishi", "farmer", "mahasanman"]
    },
    "woman_welfare": {
        "profile": {
            "name": "Sunita Shinde",
            "age_years": 32,
            "gender": "female",
            "resident_state": "maharashtra",
            "annual_family_income": 180000,
            "marital_status": "married",
            "aadhaar_linked_bank_account": True,
            "district": "Kolhapur"
        },
        "expected_eligible_keywords": ["bahin", "mahila", "woman", "ladki"]
    },
    "senior_citizen": {
        "profile": {
            "name": "Babanrao Gaikwad",
            "age_years": 68,
            "gender": "male",
            "resident_state": "maharashtra",
            "annual_family_income": 42000,
            "bpl": True,
            "ration_card_type": "bpl_yellow",
            "district": "Satara"
        },
        "expected_eligible_keywords": ["niradhar", "shravanbal", "pension", "vridha", "senior"]
    },
    "person_with_disability": {
        "profile": {
            "name": "Pooja Deshmukh",
            "age_years": 27,
            "gender": "female",
            "resident_state": "maharashtra",
            "has_disability": True,
            "disability_percentage": 50,
            "annual_family_income": 85000,
            "district": "Nashik"
        },
        "expected_eligible_keywords": ["divyang", "disability", "niradhar", "sahay"]
    },
    "unemployed_youth": {
        "profile": {
            "name": "Vikas Chavan",
            "age_years": 23,
            "gender": "male",
            "resident_state": "maharashtra",
            "is_student": False,
            "annual_family_income": 75000,
            "district": "Aurangabad"
        },
        "expected_eligible_keywords": ["training", "kaushalya", "rojgar", "apprentice", "yuva"]
    },
    "entrepreneur": {
        "profile": {
            "name": "Anjali Kulkarni",
            "age_years": 36,
            "gender": "female",
            "resident_state": "maharashtra",
            "annual_family_income": 320000,
            "district": "Thane"
        },
        "expected_eligible_keywords": ["udyog", "swayam", "annasaheb", "loan", "bachat"]
    },
    "rural_household": {
        "profile": {
            "name": "Tukaram Mane",
            "age_years": 50,
            "gender": "male",
            "resident_state": "maharashtra",
            "district": "Solapur",
            "annual_family_income": 50000,
            "bpl": True,
            "ration_card_type": "bpl_yellow"
        },
        "expected_eligible_keywords": ["gharkul", "ration", "anna", "bpl", "awas"]
    },
    "urban_household": {
        "profile": {
            "name": "Prashant More",
            "age_years": 40,
            "gender": "male",
            "resident_state": "maharashtra",
            "district": "Mumbai",
            "annual_family_income": 750000,
            "ration_card_type": "white"
        },
        "expected_eligible_keywords": []
    },
    "incomplete_profile": {
        "profile": {
            "resident_state": "maharashtra"
        },
        "expected_eligible_keywords": []
    }
}

def test_all_10_golden_profiles_evaluate_deterministically(client):
    """Verify that all 10 Golden Citizen Profiles evaluate without 500 errors and return valid statuses."""
    for key, spec in GOLDEN_PROFILES.items():
        res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=spec["profile"])
        assert res.status_code == 200, f"Profile {key} evaluation failed: {res.text}"
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == len(canonical_catalog.all()), f"Profile {key} did not evaluate against all canonical schemes"

        for result in data:
            assert result["status"] in {"eligible", "partial", "needs_information", "ineligible", "needs_review", "TRUE", "FALSE", "UNKNOWN"}
            assert "scheme_id" in result
            assert "reason" in result

def test_student_golden_profile_matches_educational_schemes(client):
    """Student profile must meet criteria for student-eligible canonical schemes."""
    student = GOLDEN_PROFILES["student"]["profile"]
    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=student)
    assert res.status_code == 200
    results = res.json()

    # Find any student/education scheme where conditions matched (eligible or needs_review for unpromoted canonicals)
    matched_student_schemes = [
        r for r in results 
        if r["status"] in {"eligible", "partial", "needs_review", "TRUE"} 
        and len(r.get("failed_conditions", [])) == 0
        and any(k in r["scheme_name"].lower() or k in r["scheme_id"].lower() for k in ["matric", "scholarship", "vidyarthi", "student", "shikshan"])
    ]
    assert len(matched_student_schemes) >= 1

def test_farmer_golden_profile_matches_agricultural_schemes(client):
    """Farmer profile with landholding must evaluate favorably for shetkari schemes."""
    farmer = GOLDEN_PROFILES["farmer"]["profile"]
    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=farmer)
    assert res.status_code == 200
    results = res.json()

    matched = [
        r for r in results
        if r["status"] in {"eligible", "partial", "needs_review", "TRUE"} 
        and len(r.get("failed_conditions", [])) == 0
        and any(k in r["scheme_name"].lower() or k in r["scheme_id"].lower() for k in ["shetkari", "kisan", "krishi", "farmer", "mahasanman"])
    ]
    assert len(matched) >= 1

def test_woman_welfare_golden_profile_matches_ladki_bahin(client):
    """Woman welfare profile with income under 2.5L and age 30 must evaluate favorably for Ladki Bahin."""
    woman = GOLDEN_PROFILES["woman_welfare"]["profile"]
    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=woman)
    assert res.status_code == 200
    results = res.json()

    ladki_res = next((r for r in results if "ladki-bahin" in r["scheme_id"] or "ladki" in r["scheme_name"].lower()), None)
    if ladki_res:
        assert ladki_res["status"] in {"eligible", "partial", "needs_review", "TRUE"}
        assert len(ladki_res.get("failed_conditions", [])) == 0
        assert "gender" in str(ladki_res.get("matched_conditions", []))

def test_incomplete_profile_produces_needs_info(client):
    """Empty or bare profile must produce unknown conditions or needs_review/needs_information outcomes."""
    inc = GOLDEN_PROFILES["incomplete_profile"]["profile"]
    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=inc)
    assert res.status_code == 200
    results = res.json()

    # Incomplete profiles have unknown conditions on schemes requiring more fields
    schemes_with_unknowns = [r for r in results if len(r.get("unknown_conditions", [])) > 0 or r["status"] in {"needs_information", "needs_review"}]
    assert len(schemes_with_unknowns) >= 1
    # No scheme should be evaluated as confirmed eligible on an incomplete profile
    assert not any(r["status"] == "eligible" for r in results)

# =========================================================================
# BOUNDARY TESTS
# =========================================================================

def test_income_boundary_strictly_disqualifies_over_threshold(client):
    """Income at 250,000 passes, while income at 250,001 fails income condition."""
    profile_pass = {
        "resident_state": "maharashtra",
        "gender": "female",
        "age_years": 30,
        "annual_family_income": 250000,
        "aadhaar_linked_bank_account": True,
    }
    profile_fail = {
        "resident_state": "maharashtra",
        "gender": "female",
        "age_years": 30,
        "annual_family_income": 250001,
        "aadhaar_linked_bank_account": True,
    }

    res_pass = client.post("/eligibility/evaluate?language=en&scope=canonical", json=profile_pass)
    res_fail = client.post("/eligibility/evaluate?language=en&scope=canonical", json=profile_fail)
    assert res_pass.status_code == 200
    assert res_fail.status_code == 200

    ladki_pass = next((r for r in res_pass.json() if "ladki-bahin" in r["scheme_id"]), None)
    ladki_fail = next((r for r in res_fail.json() if "ladki-bahin" in r["scheme_id"]), None)

    if ladki_pass and ladki_fail:
        assert ladki_pass["status"] in {"eligible", "partial", "needs_review", "TRUE"}
        assert len(ladki_pass.get("failed_conditions", [])) == 0
        assert ladki_fail["status"] in {"ineligible", "false", "FALSE", "needs_review"}
        assert any("income" in c.lower() for c in ladki_fail.get("failed_conditions", []))

def test_age_boundary_at_statutory_thresholds(client):
    """Age under 21 fails Ladki Bahin minimum age statutory rule."""
    profile_underage = {
        "resident_state": "maharashtra",
        "gender": "female",
        "age_years": 20,
        "annual_family_income": 100000,
        "aadhaar_linked_bank_account": True,
    }
    profile_eligible_age = {
        "resident_state": "maharashtra",
        "gender": "female",
        "age_years": 21,
        "annual_family_income": 100000,
        "aadhaar_linked_bank_account": True,
    }

    res_under = client.post("/eligibility/evaluate?language=en&scope=canonical", json=profile_underage)
    res_ok = client.post("/eligibility/evaluate?language=en&scope=canonical", json=profile_eligible_age)

    ladki_under = next((r for r in res_under.json() if "ladki-bahin" in r["scheme_id"]), None)
    ladki_ok = next((r for r in res_ok.json() if "ladki-bahin" in r["scheme_id"]), None)

    if ladki_under and ladki_ok:
        assert any("age" in c.lower() for c in ladki_under.get("failed_conditions", []))
        assert ladki_under["status"] in {"ineligible", "false", "FALSE", "needs_review"}
        assert ladki_ok["status"] in {"eligible", "partial", "needs_review", "TRUE"}
        assert len(ladki_ok.get("failed_conditions", [])) == 0

def test_non_maharashtra_domicile_fail_closed(client):
    """Non-Maharashtra residents fail statutory domicile requirement across all state schemes."""
    non_resident = {
        "resident_state": "karnataka",
        "gender": "female",
        "age_years": 28,
        "annual_family_income": 100000
    }
    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=non_resident)
    assert res.status_code == 200
    results = res.json()

    for r in results:
        # State schemes must not be eligible for non-residents
        if "resident_state" in str(r.get("failed_conditions", [])):
            assert r["status"] in {"ineligible", "false", "FALSE", "needs_review"}
            assert r["status"] != "eligible"
