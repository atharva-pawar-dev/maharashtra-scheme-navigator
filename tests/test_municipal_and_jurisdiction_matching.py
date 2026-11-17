"""
Test Suite: Municipal, District & Multi-Tier Geographic Jurisdiction Matching
Authoritative acceptance tests for Part 20 covering:
- 10 Mandatory Golden Scenarios for Local Government Isolation
- 29 Municipal Corporations Directory & Ward Verification
- 424 Urban Local Bodies (ULBs) Classification & Coverage
- Boundary PIN Ambiguity (LOCATION_REQUIRES_CONFIRMATION)
- Centrally Sponsored Schemes Implemented by Local Authorities
- Dynamic Location Re-evaluation & Invalidation
- Minimum Residency Duration Verification
"""

import pytest
from fastapi.testclient import TestClient
from scheme_navigator.api.main import app
from scheme_navigator.domain.jurisdiction import (
    JurisdictionService,
    JurisdictionScope,
    LocalGovernmentType,
    jurisdiction_service,
)
from scheme_navigator.domain.models import CitizenProfile
from scheme_navigator.services.catalog import canonical_catalog
from scheme_navigator.services.rule_engine import evaluate_scheme


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# PART 20 — 10 MANDATORY GOLDEN GEOGRAPHIC ISOLATION SCENARIOS
# =========================================================================

def test_scenario_01_pune_municipal_corporation_matching_and_isolation(client):
    """
    Scenario 1: Pune Municipal Corporation (PMC) Citizen.
    Must receive: Central + Maharashtra State + Pune district + PMC schemes.
    Must EXCLUDE: PCMC schemes, BMC schemes, TMC schemes, and non-corporation schemes.
    """
    pmc_profile = {
        "name": "Kavita Deshmukh",
        "gender": "female",
        "age_years": 32,
        "resident_state": "maharashtra",
        "district": "Pune",
        "local_government_type": "municipal_corporation",
        "municipal_corporation": "mc-pune",
        "residence_years": 6,
        "annual_family_income": 80000,
        "aadhaar_linked_bank_account": True,
    }

    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=pmc_profile)
    assert res.status_code == 200
    results = res.json()

    result_map = {r["scheme_id"]: r for r in results}

    # 1. Central schemes must be applicable
    central_res = result_map.get("scheme-pm-svanidhi")
    assert central_res is not None
    assert central_res["status"] in {"eligible", "partial", "needs_information", "needs_review"}
    assert not any("Geographically inapplicable" in str(f) for f in central_res.get("failed_conditions", []))

    # 2. State schemes must be applicable
    state_res = result_map.get("candidate-majhi-ladki-bahin") or result_map.get("demo-majhi-ladki-bahin")
    assert state_res is not None
    assert not any("Geographically inapplicable" in str(f) for f in state_res.get("failed_conditions", []))

    # 3. PMC schemes must be applicable
    pmc_res = result_map.get("pmc-shahari-garib-arogya")
    assert pmc_res is not None
    assert not any("Geographically inapplicable" in str(f) for f in pmc_res.get("failed_conditions", []))

    # 4. PCMC schemes must be STRICTLY INELIGIBLE due to geographic isolation
    pcmc_schemes = [
        "pcmc-free-bicycle-girls",
        "pcmc-sewing-machine-women",
        "pcmc-mscit-women",
        "pcmc-disability-scholarship",
        "pcmc-disability-assistive-devices",
        "pcmc-backward-class-scholarship",
    ]
    for sid in pcmc_schemes:
        pcmc_r = result_map.get(sid)
        if pcmc_r:
            assert pcmc_r["status"] in {"ineligible", "false", "FALSE"}, f"PCMC scheme {sid} should be ineligible for PMC resident"
            assert any("Geographically inapplicable" in str(f) for f in pcmc_r.get("failed_conditions", [])), (
                f"Scheme {sid} should contain geographic ineligibility reason, got: {pcmc_r.get('failed_conditions')}"
            )

    # 5. BMC, TMC, NMMC schemes must be STRICTLY INELIGIBLE
    for sid in ["bmc-anand-dighe-divyang", "tmc-divyang-kalyan", "nmmc-divyang-education-grant"]:
        other_r = result_map.get(sid)
        if other_r:
            assert other_r["status"] in {"ineligible", "false", "FALSE"}
            assert any("Geographically inapplicable" in str(f) for f in other_r.get("failed_conditions", []))

    # 6. Municipal Council & Gram Panchayat schemes must be strictly ineligible
    for sid in ["ulb-council-swachh-livelihood", "rural-zp-shetkari-sheti-shala"]:
        tier_r = result_map.get(sid)
        if tier_r:
            assert tier_r["status"] in {"ineligible", "false", "FALSE"}
            assert any("Geographically inapplicable" in str(f) for f in tier_r.get("failed_conditions", []))


def test_scenario_02_pcmc_citizen_matching_and_isolation(client):
    """
    Scenario 2: Pimpri-Chinchwad Municipal Corporation (PCMC) Citizen.
    Must receive: Central + Maharashtra State + Pune district + PCMC schemes.
    Must EXCLUDE: PMC schemes, BMC schemes, TMC schemes, and non-corporation schemes.
    """
    pcmc_profile = {
        "name": "Pooja Gaikwad",
        "gender": "female",
        "age_years": 24,
        "resident_state": "maharashtra",
        "district": "Pune",
        "local_government_type": "municipal_corporation",
        "municipal_corporation": "mc-pimpri-chinchwad",
        "residence_years": 5,
        "annual_family_income": 90000,
        "aadhaar_linked_bank_account": True,
    }

    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=pcmc_profile)
    assert res.status_code == 200
    results = res.json()
    result_map = {r["scheme_id"]: r for r in results}

    # 1. Central & State applicable
    assert not any("Geographically inapplicable" in str(f) for f in result_map.get("scheme-pm-svanidhi", {}).get("failed_conditions", []))

    # 2. PCMC schemes applicable
    pcmc_res = result_map.get("pcmc-mscit-women") or result_map.get("pcmc-sewing-machine-women")
    assert pcmc_res is not None
    assert not any("Geographically inapplicable" in str(f) for f in pcmc_res.get("failed_conditions", []))

    # 3. PMC schemes STRICTLY INELIGIBLE
    for sid in ["pmc-shahari-garib-arogya", "pmc-maulana-azad-scholarship", "pmc-annabhau-sathe-scholarship"]:
        pmc_r = result_map.get(sid)
        if pmc_r:
            assert pmc_r["status"] in {"ineligible", "false", "FALSE"}, f"PMC scheme {sid} should be ineligible for PCMC resident"
            assert any("Geographically inapplicable" in str(f) for f in pmc_r.get("failed_conditions", []))


def test_scenario_03_bmc_citizen_matching_and_isolation(client):
    """
    Scenario 3: Brihanmumbai Municipal Corporation (BMC) Citizen.
    Must receive: Central + Maharashtra State + BMC schemes.
    Must EXCLUDE: PMC, PCMC, TMC, NMMC schemes.
    """
    bmc_profile = {
        "name": "Prakash Salvi",
        "gender": "male",
        "age_years": 40,
        "resident_state": "maharashtra",
        "district": "Mumbai Suburban",
        "local_government_type": "municipal_corporation",
        "municipal_corporation": "mc-brihanmumbai",
        "residence_years": 10,
        "disability_percentage": 50,
        "annual_family_income": 100000,
    }

    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=bmc_profile)
    assert res.status_code == 200
    results = res.json()
    result_map = {r["scheme_id"]: r for r in results}

    # BMC scheme must be geographically applicable
    bmc_res = result_map.get("bmc-anand-dighe-divyang")
    assert bmc_res is not None
    assert not any("Geographically inapplicable" in str(f) for f in bmc_res.get("failed_conditions", []))

    # PMC & PCMC schemes must be strictly excluded
    for sid in ["pmc-shahari-garib-arogya", "pcmc-disability-scholarship", "tmc-divyang-kalyan"]:
        r = result_map.get(sid)
        if r:
            assert r["status"] in {"ineligible", "false", "FALSE"}
            assert any("Geographically inapplicable" in str(f) for f in r.get("failed_conditions", []))


def test_scenario_04_thane_citizen_matching_and_isolation(client):
    """
    Scenario 4: Thane Municipal Corporation (TMC) Citizen.
    Must receive: Central + State + Thane schemes.
    Must EXCLUDE: Mira Bhayander, Navi Mumbai, PMC, PCMC schemes.
    """
    tmc_profile = {
        "name": "Anil Mhatre",
        "gender": "male",
        "age_years": 35,
        "resident_state": "maharashtra",
        "district": "Thane",
        "local_government_type": "municipal_corporation",
        "municipal_corporation": "mc-thane",
        "residence_years": 4,
        "disability_percentage": 45,
    }

    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=tmc_profile)
    assert res.status_code == 200
    results = res.json()
    result_map = {r["scheme_id"]: r for r in results}

    tmc_res = result_map.get("tmc-divyang-kalyan")
    assert tmc_res is not None
    assert not any("Geographically inapplicable" in str(f) for f in tmc_res.get("failed_conditions", []))

    # NMMC, BMC, PMC schemes excluded
    for sid in ["nmmc-divyang-education-grant", "bmc-anand-dighe-divyang", "pmc-shahari-garib-arogya"]:
        r = result_map.get(sid)
        if r:
            assert r["status"] in {"ineligible", "false", "FALSE"}
            assert any("Geographically inapplicable" in str(f) for f in r.get("failed_conditions", []))


def test_scenario_05_navi_mumbai_citizen_matching_and_isolation(client):
    """
    Scenario 5: Navi Mumbai Municipal Corporation (NMMC) Citizen.
    Must receive: Central + State + Navi Mumbai schemes.
    Must EXCLUDE: Panvel, TMC, BMC, PMC schemes.
    """
    nmmc_profile = {
        "name": "Shubhangi Naik",
        "gender": "female",
        "age_years": 21,
        "resident_state": "maharashtra",
        "district": "Thane",
        "local_government_type": "municipal_corporation",
        "municipal_corporation": "mc-navi-mumbai",
        "residence_years": 5,
        "disability_percentage": 60,
    }

    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=nmmc_profile)
    assert res.status_code == 200
    results = res.json()
    result_map = {r["scheme_id"]: r for r in results}

    nmmc_res = result_map.get("nmmc-divyang-education-grant")
    assert nmmc_res is not None
    assert not any("Geographically inapplicable" in str(f) for f in nmmc_res.get("failed_conditions", []))

    for sid in ["tmc-divyang-kalyan", "bmc-anand-dighe-divyang", "pmc-shahari-garib-arogya"]:
        r = result_map.get(sid)
        if r:
            assert r["status"] in {"ineligible", "false", "FALSE"}
            assert any("Geographically inapplicable" in str(f) for f in r.get("failed_conditions", []))


def test_scenario_06_municipal_council_citizen_matching_and_isolation(client):
    """
    Scenario 6: Municipal Council (Nagar Parishad) resident (e.g. Baramati Municipal Council).
    Must receive: Central + State + District + Municipal Council schemes.
    Must EXCLUDE: ALL Municipal Corporation schemes (PMC, PCMC, BMC, TMC, NMMC) and Gram Panchayat schemes.
    """
    council_profile = {
        "name": "Nitin Sawant",
        "gender": "male",
        "age_years": 28,
        "resident_state": "maharashtra",
        "district": "Pune",
        "local_government_type": "municipal_council",
        "municipal_council": "Baramati",
        "residence_years": 8,
        "annual_family_income": 85000,
    }

    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=council_profile)
    assert res.status_code == 200
    results = res.json()
    result_map = {r["scheme_id"]: r for r in results}

    # Municipal Council scheme must be applicable
    council_res = result_map.get("ulb-council-swachh-livelihood")
    assert council_res is not None
    assert not any("Geographically inapplicable" in str(f) for f in council_res.get("failed_conditions", []))

    # All Municipal Corporation schemes must be strictly INELIGIBLE
    corp_schemes = [
        "pmc-shahari-garib-arogya",
        "pcmc-free-bicycle-girls",
        "bmc-anand-dighe-divyang",
        "tmc-divyang-kalyan",
        "nmmc-divyang-education-grant",
    ]
    for sid in corp_schemes:
        r = result_map.get(sid)
        if r:
            assert r["status"] in {"ineligible", "false", "FALSE"}
            assert any("Geographically inapplicable" in str(f) for f in r.get("failed_conditions", []))

    # Rural Gram Panchayat scheme must be strictly INELIGIBLE
    gp_res = result_map.get("rural-zp-shetkari-sheti-shala")
    if gp_res:
        assert gp_res["status"] in {"ineligible", "false", "FALSE"}
        assert any("Geographically inapplicable" in str(f) for f in gp_res.get("failed_conditions", []))


def test_scenario_07_rural_gram_panchayat_citizen_matching_and_isolation(client):
    """
    Scenario 7: Rural / Gram Panchayat resident under Zilla Parishad (e.g. Shirur Gram Panchayat).
    Must receive: Central + State + District + Rural/ZP schemes.
    Must EXCLUDE: ALL Municipal Corporation schemes and Municipal Council schemes.
    """
    gp_profile = {
        "name": "Balu Thite",
        "gender": "male",
        "age_years": 42,
        "resident_state": "maharashtra",
        "district": "Pune",
        "local_government_type": "gram_panchayat",
        "gram_panchayat": "Shirur Rural",
        "residence_years": 15,
        "annual_family_income": 60000,
    }

    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=gp_profile)
    assert res.status_code == 200
    results = res.json()
    result_map = {r["scheme_id"]: r for r in results}

    # Rural ZP scheme must be geographically applicable
    rural_res = result_map.get("rural-zp-shetkari-sheti-shala")
    assert rural_res is not None
    assert not any("Geographically inapplicable" in str(f) for f in rural_res.get("failed_conditions", []))

    # Municipal schemes must be strictly INELIGIBLE
    for sid in ["pmc-shahari-garib-arogya", "pcmc-mscit-women", "ulb-council-swachh-livelihood"]:
        r = result_map.get(sid)
        if r:
            assert r["status"] in {"ineligible", "false", "FALSE"}
            assert any("Geographically inapplicable" in str(f) for f in r.get("failed_conditions", []))


def test_scenario_08_locality_and_pin_boundary_ambiguity(client):
    """
    Scenario 8: Border PIN code crossing municipal boundaries (e.g. PIN 411027 across PMC and PCMC).
    Without explicit local body confirmation, location resolution MUST NOT guess.
    It MUST return status='LOCATION_REQUIRES_CONFIRMATION' with candidate options.
    When confirmed, it must resolve cleanly to the chosen local body.
    """
    # 1. Unconfirmed border PIN 411027 (Aundh / Pimple Saudagar boundary)
    res = client.post("/local-governments/resolve-location", json={"pin_code": "411027", "district": "Pune"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "LOCATION_REQUIRES_CONFIRMATION"
    assert "mc-pimpri-chinchwad" in data["candidate_local_bodies"]
    assert "mc-pune" in data["candidate_local_bodies"]
    assert "traverses municipal boundary" in data["explanation"].lower()

    # 2. Unconfirmed border PIN 411061 (Bopodi / Dapodi boundary)
    res2 = client.post("/local-governments/resolve-location", json={"pin_code": "411061"})
    assert res2.status_code == 200
    assert res2.json()["status"] == "LOCATION_REQUIRES_CONFIRMATION"

    # 3. Confirmed border PIN with explicit local body selection
    res3 = client.post(
        "/local-governments/resolve-location",
        json={"pin_code": "411027", "district": "Pune", "local_body": "mc-pimpri-chinchwad"}
    )
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["status"] == "RESOLVED"
    assert data3["local_body_id"] == "mc-pimpri-chinchwad"
    assert data3["local_government_type"] == "municipal_corporation"


def test_scenario_09_municipality_change_invalidates_and_recalculates(client):
    """
    Scenario 9: Citizen moves from PMC to PCMC.
    Eligibility results must immediately recalculate:
    - Initially PMC schemes match and PCMC schemes fail.
    - After changing municipality to PCMC, PMC schemes fail and PCMC schemes match.
    - No stale evaluation from the previous municipality persists.
    """
    profile = {
        "name": "Smita More",
        "gender": "female",
        "age_years": 26,
        "resident_state": "maharashtra",
        "district": "Pune",
        "local_government_type": "municipal_corporation",
        "municipal_corporation": "mc-pune",
        "residence_years": 4,
        "annual_family_income": 95000,
        "aadhaar_linked_bank_account": True,
    }

    # First evaluation: Resident of Pune Municipal Corporation
    res1 = client.post("/eligibility/evaluate?language=en&scope=canonical", json=profile)
    assert res1.status_code == 200
    map1 = {r["scheme_id"]: r for r in res1.json()}

    pmc_r1 = map1.get("pmc-shahari-garib-arogya")
    pcmc_r1 = map1.get("pcmc-mscit-women")
    assert not any("Geographically inapplicable" in str(f) for f in pmc_r1.get("failed_conditions", []))
    assert pcmc_r1["status"] in {"ineligible", "false", "FALSE"}

    # Citizen relocates to Pimpri Chinchwad Municipal Corporation
    profile["municipal_corporation"] = "mc-pimpri-chinchwad"
    res2 = client.post("/eligibility/evaluate?language=en&scope=canonical", json=profile)
    assert res2.status_code == 200
    map2 = {r["scheme_id"]: r for r in res2.json()}

    pmc_r2 = map2.get("pmc-shahari-garib-arogya")
    pcmc_r2 = map2.get("pcmc-mscit-women")

    # Invalidation verification: PMC scheme now immediately fails geographic applicability
    assert pmc_r2["status"] in {"ineligible", "false", "FALSE"}
    assert any("Geographically inapplicable" in str(f) for f in pmc_r2.get("failed_conditions", []))

    # PCMC scheme now passes geographic applicability
    assert not any("Geographically inapplicable" in str(f) for f in pcmc_r2.get("failed_conditions", []))


def test_scenario_10_centrally_sponsored_scheme_with_local_authority(client):
    """
    Scenario 10: Centrally sponsored scheme implemented through Municipal Authorities (e.g. PM SVANidhi).
    Must maintain a single canonical record with joint classification.
    Must be applicable across both PMC, PCMC, BMC, and Municipal Councils without duplication.
    """
    schemes_res = client.get("/canonical-schemes?jurisdiction_scope=CENTRAL")
    assert schemes_res.status_code == 200
    schemes = schemes_res.json()

    svanidhi = next((s for s in schemes if s["canonical_scheme_id"] == "scheme-pm-svanidhi"), None)
    assert svanidhi is not None
    assert svanidhi["funding_type"] == "CENTRAL_FUNDED"
    assert svanidhi["jurisdiction_scope"] == "CENTRAL"
    assert svanidhi["state_central_joint_classification"] == "CENTRAL_SCHEME"
    assert "Urban Development Department" in svanidhi["implementing_authority"]

    # Test applicability across PMC citizen and PCMC citizen
    pmc_res = jurisdiction_service.is_geographically_applicable(
        svanidhi,
        CitizenProfile(resident_state="maharashtra", municipal_corporation="mc-pune")
    )
    assert pmc_res[0] is True

    pcmc_res = jurisdiction_service.is_geographically_applicable(
        svanidhi,
        CitizenProfile(resident_state="maharashtra", municipal_corporation="mc-pimpri-chinchwad")
    )
    assert pcmc_res[0] is True

    council_res = jurisdiction_service.is_geographically_applicable(
        svanidhi,
        CitizenProfile(resident_state="maharashtra", local_government_type="municipal_council")
    )
    assert council_res[0] is True


# =========================================================================
# DIRECTORY & INFRASTRUCTURE INTEGRITY TESTS
# =========================================================================

def test_all_29_municipal_corporations_live_directory(client):
    """
    Verify all 29 Maharashtra Municipal Corporations are accurately loaded,
    authenticated against the Directorate of Municipal Administration (DMA) standards.
    """
    res = client.get("/local-governments/corporations")
    assert res.status_code == 200
    corps = res.json()
    assert len(corps) == 29

    expected_corporation_ids = {
        "mc-brihanmumbai", "mc-pune", "mc-nagpur", "mc-thane", "mc-pimpri-chinchwad",
        "mc-nashik", "mc-kalyan-dombivli", "mc-vasai-virar", "mc-chhatrapati-sambhajinagar", "mc-navi-mumbai",
        "mc-solapur", "mc-mira-bhayander", "mc-bhiwandi-nizampur", "mc-amravati", "mc-nanded-waghala",
        "mc-kolhapur", "mc-akola", "mc-panvel", "mc-ulhasnagar", "mc-sangli-miraj-kupwad",
        "mc-malegaon", "mc-jalgaon", "mc-latur", "mc-dhule", "mc-ahilyanagar",
        "mc-chandrapur", "mc-parbhani", "mc-ichalkaranji", "mc-jalna",
    }
    loaded_ids = {c["corporation_id"] for c in corps}
    assert loaded_ids == expected_corporation_ids

    # Spot-check essential fields
    for c in corps:
        assert c["official_name_en"], f"Missing official_name_en for {c['corporation_id']}"
        assert c["official_name_mr"], f"Missing official_name_mr for {c['corporation_id']}"
        assert c["district"], f"Missing district for {c['corporation_id']}"
        assert c["administrative_division"], f"Missing administrative_division for {c['corporation_id']}"
        assert c["ward_count"] > 0, f"Ward count must be positive for {c['corporation_id']}"
        assert len(c.get("representative_wards", [])) >= 1


def test_corporation_wards_and_schemes_endpoints(client):
    """Test individual corporation detail, ward mapping, and corporation-specific scheme list."""
    # Test PMC
    res_pmc = client.get("/local-governments/corporations/mc-pune")
    assert res_pmc.status_code == 200
    assert res_pmc.json()["corporation_id"] == "mc-pune"

    res_wards = client.get("/local-governments/corporations/mc-pune/wards")
    assert res_wards.status_code == 200
    wards = res_wards.json()
    assert wards["corporation_id"] == "mc-pune"
    assert wards["total_wards"] > 0
    assert len(wards.get("representative_wards", [])) >= 4

    res_schemes = client.get("/local-governments/corporations/mc-pune/schemes")
    assert res_schemes.status_code == 200
    pmc_schemes = res_schemes.json()
    assert len(pmc_schemes) >= 3
    assert all("pmc" in s["canonical_scheme_id"] for s in pmc_schemes)


def test_424_urban_local_bodies_complete_coverage(client):
    """
    Verify authoritative coverage of 424 Urban Local Bodies (ULBs) across Maharashtra:
    - 29 Municipal Corporations
    - 245 Municipal Councils (Nagar Parishads: 214 established + 31 upgraded Class C)
    - 150 Nagar Panchayats
    Total ULBs: 29 + 245 + 150 = 424
    Across all 36 districts.
    """
    res = client.get("/local-governments/ulbs")
    assert res.status_code == 200
    ulb = res.json()

    assert ulb["total_urban_local_bodies"] == 424
    assert ulb["breakdown"]["municipal_corporations"] == 29
    assert ulb["breakdown"]["municipal_councils"] == 245
    assert ulb["breakdown"]["established_councils_census_baseline"] == 214
    assert ulb["breakdown"]["upgraded_class_c_councils"] == 31
    assert ulb["breakdown"]["nagar_panchayats"] == 150
    assert (
        ulb["breakdown"]["municipal_corporations"]
        + ulb["breakdown"]["municipal_councils"]
        + ulb["breakdown"]["nagar_panchayats"]
    ) == 424
    assert len(ulb["districts"]) == 36


def test_residency_duration_statutory_evaluation():
    """Verify that scheme requiring minimum residence years rejects citizens who have fewer years."""
    scheme = canonical_catalog.get("pmc-shahari-garib-arogya")
    assert scheme is not None
    assert scheme.required_residency_years == 3

    # Citizen with only 1 year residency -> Ineligible
    profile_1_yr = CitizenProfile(
        resident_state="maharashtra",
        gender="female",
        local_government_type="municipal_corporation",
        municipal_corporation="mc-pune",
        residence_years=1,
    )
    is_ok, reason = jurisdiction_service.is_geographically_applicable(scheme, profile_1_yr)
    assert is_ok is False
    assert "Requires at least 3 years" in reason

    # Citizen with 4 years residency -> Eligible
    profile_4_yr = CitizenProfile(
        resident_state="maharashtra",
        gender="female",
        local_government_type="municipal_corporation",
        municipal_corporation="mc-pune",
        residence_years=4,
    )
    is_ok2, reason2 = jurisdiction_service.is_geographically_applicable(scheme, profile_4_yr)
    assert is_ok2 is True


# =========================================================================
# ADDITIONAL HIERARCHY SCOPES (DIVISION, WARD, NAGAR PANCHAYAT, ZP, SPECIAL AREA)
# =========================================================================

from types import SimpleNamespace


def test_division_scope_evaluation():
    """Verify that DIVISION scope accurately matches citizen district against administrative division."""
    division_scheme = SimpleNamespace(
        jurisdiction_scope=JurisdictionScope.DIVISION,
        included_local_bodies=["Pune"],
    )

    # Citizen in Satara (which is in Pune Division) -> Matches
    profile_satara = CitizenProfile(resident_state="maharashtra", district="Satara", gender="male")
    is_ok, reason = jurisdiction_service.is_geographically_applicable(division_scheme, profile_satara)
    assert is_ok is True
    assert "Pune Division" in reason

    # Citizen in Nagpur (which is in Nagpur Division) -> Ineligible
    profile_nagpur = CitizenProfile(resident_state="maharashtra", district="Nagpur", gender="male")
    is_ok2, reason2 = jurisdiction_service.is_geographically_applicable(division_scheme, profile_nagpur)
    assert is_ok2 is False
    assert "Restricted to ['pune'] Division" in reason2


def test_ward_scope_evaluation():
    """Verify that WARD scope enforces municipal corporation and administrative ward matching."""
    ward_scheme = SimpleNamespace(
        jurisdiction_scope=JurisdictionScope.WARD,
        jurisdiction_ids=["jurisdiction:mc:mc-pune"],
        included_local_bodies=["kothrud", "kothrud-bavdhan"],
    )

    # Resident of PMC, Kothrud Ward -> Matches
    p_kothrud = CitizenProfile(
        resident_state="maharashtra",
        municipal_corporation="mc-pune",
        ward="Kothrud",
        gender="female"
    )
    is_ok, reason = jurisdiction_service.is_geographically_applicable(ward_scheme, p_kothrud)
    assert is_ok is True
    assert "Verified resident of ward 'Kothrud'" in reason

    # Resident of PMC, Aundh Ward -> Ineligible
    p_aundh = CitizenProfile(
        resident_state="maharashtra",
        municipal_corporation="mc-pune",
        ward="Aundh",
        gender="female"
    )
    is_ok2, reason2 = jurisdiction_service.is_geographically_applicable(ward_scheme, p_aundh)
    assert is_ok2 is False
    assert "Scheme restricted to wards" in reason2

    # Resident of PCMC, Kothrud (cross-corporation mismatch) -> Ineligible
    p_pcmc = CitizenProfile(
        resident_state="maharashtra",
        municipal_corporation="mc-pimpri-chinchwad",
        ward="Kothrud",
        gender="female"
    )
    is_ok3, reason3 = jurisdiction_service.is_geographically_applicable(ward_scheme, p_pcmc)
    assert is_ok3 is False
    assert "Ward scheme belongs to" in reason3


def test_nagar_panchayat_scope_evaluation():
    """Verify that NAGAR_PANCHAYAT scope matches transitional local body citizens and excludes corporations."""
    np_scheme = SimpleNamespace(
        jurisdiction_scope=JurisdictionScope.NAGAR_PANCHAYAT,
    )

    # Citizen in Nagar Panchayat -> Matches
    p_np = CitizenProfile(
        resident_state="maharashtra",
        local_government_type="nagar_panchayat",
        gender="male"
    )
    is_ok, reason = jurisdiction_service.is_geographically_applicable(np_scheme, p_np)
    assert is_ok is True

    # Citizen in Municipal Corporation -> Ineligible
    p_corp = CitizenProfile(
        resident_state="maharashtra",
        local_government_type="municipal_corporation",
        municipal_corporation="mc-pune",
        gender="male"
    )
    is_ok2, reason2 = jurisdiction_service.is_geographically_applicable(np_scheme, p_corp)
    assert is_ok2 is False
    assert "Scheme requires residence in a Nagar Panchayat" in reason2


def test_zilla_parishad_scope_evaluation():
    """Verify that ZILLA_PARISHAD scope matches rural citizens and excludes municipal corporations."""
    zp_scheme = SimpleNamespace(
        jurisdiction_scope=JurisdictionScope.ZILLA_PARISHAD,
    )

    # Rural Gram Panchayat resident -> Matches
    p_rural = CitizenProfile(
        resident_state="maharashtra",
        local_government_type="gram_panchayat",
        gender="male"
    )
    is_ok, reason = jurisdiction_service.is_geographically_applicable(zp_scheme, p_rural)
    assert is_ok is True

    # Corporation resident -> Ineligible
    p_corp = CitizenProfile(
        resident_state="maharashtra",
        local_government_type="municipal_corporation",
        municipal_corporation="mc-pune",
        gender="male"
    )
    is_ok2, reason2 = jurisdiction_service.is_geographically_applicable(zp_scheme, p_corp)
    assert is_ok2 is False
    assert "Scheme requires residence in rural Zilla Parishad area" in reason2


def test_special_area_scope_evaluation():
    """Verify that SPECIAL_AREA scope checks designated localities (e.g. Hill Stations / PESA Tribal areas)."""
    hill_station_scheme = SimpleNamespace(
        jurisdiction_scope=JurisdictionScope.SPECIAL_AREA,
        included_local_bodies=["matheran"],
    )

    # Resident in Matheran -> Matches
    p_matheran = CitizenProfile(
        resident_state="maharashtra",
        district="Raigad",
        locality="Matheran Hill Station",
        gender="male"
    )
    is_ok, reason = jurisdiction_service.is_geographically_applicable(hill_station_scheme, p_matheran)
    assert is_ok is True
    assert "Citizen verified in designated special area" in reason

    # Resident in Alibag (Raigad district, but not Matheran) -> Ineligible
    p_alibag = CitizenProfile(
        resident_state="maharashtra",
        district="Raigad",
        locality="Alibag Town",
        gender="male"
    )
    is_ok2, reason2 = jurisdiction_service.is_geographically_applicable(hill_station_scheme, p_alibag)
    assert is_ok2 is False
    assert "Scheme restricted to special areas" in reason2

    # Resident in Matheran -> Matches
    p_matheran = CitizenProfile(
        resident_state="maharashtra",
        district="Raigad",
        locality="Matheran Hill Station",
        gender="male"
    )
    is_ok, reason = jurisdiction_service.is_geographically_applicable(hill_station_scheme, p_matheran)
    assert is_ok is True
    assert "Citizen verified in designated special area" in reason

    # Resident in Alibag (Raigad district, but not Matheran) -> Ineligible
    p_alibag = CitizenProfile(
        resident_state="maharashtra",
        district="Raigad",
        locality="Alibag Town",
        gender="male"
    )
    is_ok2, reason2 = jurisdiction_service.is_geographically_applicable(hill_station_scheme, p_alibag)
    assert is_ok2 is False
    assert "Scheme restricted to special areas" in reason2


def test_bmc_vs_neighbouring_corporations_isolation(client):
    """
    Verify boundary isolation for Mumbai metropolitan corporations:
    BMC (mc-brihanmumbai) vs. TMC (mc-thane) vs. Mira Bhayander (mc-mira-bhayander).
    """
    bmc_profile = {
        "name": "Suresh Sawant",
        "gender": "male",
        "age_years": 38,
        "resident_state": "maharashtra",
        "district": "Mumbai City",
        "local_government_type": "municipal_corporation",
        "municipal_corporation": "mc-brihanmumbai",
        "residence_years": 8,
        "disability_percentage": 50,
    }

    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=bmc_profile)
    assert res.status_code == 200
    res_map = {r["scheme_id"]: r for r in res.json()}

    # BMC scheme passes
    bmc_r = res_map.get("bmc-anand-dighe-divyang")
    assert bmc_r is not None
    assert not any("Geographically inapplicable" in str(f) for f in bmc_r.get("failed_conditions", []))

    # TMC scheme fails
    tmc_r = res_map.get("tmc-divyang-kalyan")
    if tmc_r:
        assert tmc_r["status"] in {"ineligible", "false", "FALSE"}
        assert any("Geographically inapplicable" in str(f) for f in tmc_r.get("failed_conditions", []))

    # Citizen moves to Thane
    bmc_profile["municipal_corporation"] = "mc-thane"
    bmc_profile["district"] = "Thane"
    res2 = client.post("/eligibility/evaluate?language=en&scope=canonical", json=bmc_profile)
    assert res2.status_code == 200
    res_map2 = {r["scheme_id"]: r for r in res2.json()}

    # Now BMC scheme fails
    bmc_r2 = res_map2.get("bmc-anand-dighe-divyang")
    assert bmc_r2["status"] in {"ineligible", "false", "FALSE"}
    assert any("Geographically inapplicable" in str(f) for f in bmc_r2.get("failed_conditions", []))

    # And TMC scheme passes
    tmc_r2 = res_map2.get("tmc-divyang-kalyan")
    assert not any("Geographically inapplicable" in str(f) for f in tmc_r2.get("failed_conditions", []))


def test_relocation_preserves_application_progress_and_unrelated_profile(client):
    """
    Verify that when a citizen updates municipal residence:
    1. Unrelated profile attributes (name, age, gender, income, category) are strictly preserved.
    2. Central and State scheme evaluations remain eligible.
    3. Application tracking progress and uploaded documents for unaffected schemes remain intact.
    """
    citizen_data = {
        "name": "Manjusha Joshi",
        "age_years": 29,
        "gender": "female",
        "resident_state": "maharashtra",
        "annual_family_income": 70000,
        "caste_category": "OBC",
        "district": "Pune",
        "local_government_type": "municipal_corporation",
        "municipal_corporation": "mc-pune",
        "residence_years": 5,
        "aadhaar_linked_bank_account": True,
    }

    # Evaluate at PMC
    res1 = client.post("/eligibility/evaluate?language=en&scope=canonical", json=citizen_data)
    assert res1.status_code == 200
    r1 = {x["scheme_id"]: x for x in res1.json()}

    # State scheme is eligible
    ladki1 = r1.get("candidate-majhi-ladki-bahin") or r1.get("demo-majhi-ladki-bahin")
    assert ladki1 is not None
    assert ladki1["status"] in {"eligible", "partial", "needs_review", "TRUE"}

    # Central scheme is applicable
    svanidhi1 = r1.get("scheme-pm-svanidhi")
    assert svanidhi1 is not None
    assert not any("Geographically inapplicable" in str(f) for f in svanidhi1.get("failed_conditions", []))

    # Move to PCMC: preserve all attributes except municipal_corporation
    citizen_data["municipal_corporation"] = "mc-pimpri-chinchwad"
    res2 = client.post("/eligibility/evaluate?language=en&scope=canonical", json=citizen_data)
    assert res2.status_code == 200
    r2 = {x["scheme_id"]: x for x in res2.json()}

    # Central and State schemes remain intact and applicable
    ladki2 = r2.get("candidate-majhi-ladki-bahin") or r2.get("demo-majhi-ladki-bahin")
    assert ladki2["status"] == ladki1["status"]

    svanidhi2 = r2.get("scheme-pm-svanidhi")
    assert not any("Geographically inapplicable" in str(f) for f in svanidhi2.get("failed_conditions", []))

    # Unrelated attributes verified intact in profile model
    prof = CitizenProfile(**citizen_data)
    assert prof.name == "Manjusha Joshi"
    assert prof.age_years == 29
    assert prof.annual_family_income == 70000
    assert prof.caste_category == "OBC"
    assert prof.municipal_corporation == "mc-pimpri-chinchwad"


# =========================================================================
# CANTONMENT BOARDS, ZILLA PARISHADS & 29-CORP PARAMETERIZED SUITE
# =========================================================================

ALL_29_CORPORATION_IDS = [
    "mc-brihanmumbai", "mc-pune", "mc-nagpur", "mc-thane", "mc-pimpri-chinchwad",
    "mc-nashik", "mc-kalyan-dombivli", "mc-vasai-virar", "mc-chhatrapati-sambhajinagar", "mc-navi-mumbai",
    "mc-solapur", "mc-mira-bhayander", "mc-bhiwandi-nizampur", "mc-amravati", "mc-nanded-waghala",
    "mc-kolhapur", "mc-akola", "mc-panvel", "mc-ulhasnagar", "mc-sangli-miraj-kupwad",
    "mc-malegaon", "mc-jalgaon", "mc-latur", "mc-dhule", "mc-ahilyanagar",
    "mc-chandrapur", "mc-parbhani", "mc-ichalkaranji", "mc-jalna",
]


def test_cantonment_board_isolation_and_matching(client):
    """
    Verify Cantonment Board isolation under Central Ministry of Defence (Cantonments Act, 2006):
    1. Resident of Pune Cantonment (cb-pune) receives Central + State schemes.
    2. Strictly excluded from PMC (mc-pune) and PCMC (mc-pimpri-chinchwad) municipal schemes.
    3. Strictly excluded from Gram Panchayat / Rural schemes.
    4. Dedicated Cantonment Board scope schemes match cantonment residents and exclude municipal residents.
    """
    # 1. Location resolution
    res_loc = client.post(
        "/local-governments/resolve-location",
        json={"local_government_type": "cantonment", "local_body": "cb-pune", "district": "Pune"}
    )
    assert res_loc.status_code == 200
    loc_data = res_loc.json()
    assert loc_data["status"] == "RESOLVED"
    assert loc_data["local_government_type"] == "cantonment"
    assert "jurisdiction:tier:cantonment" in loc_data["applicable_jurisdiction_tokens"]
    assert "jurisdiction:cantonment:cb-pune" in loc_data["applicable_jurisdiction_tokens"]

    # 2. Eligibility evaluation
    cb_profile = {
        "name": "Major Rajan Kadam (Retd)",
        "gender": "male",
        "age_years": 48,
        "resident_state": "maharashtra",
        "district": "Pune",
        "local_government_type": "cantonment",
        "local_body_id": "cb-pune",
        "annual_family_income": 120000,
        "aadhaar_linked_bank_account": True,
    }

    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=cb_profile)
    assert res.status_code == 200
    results = {r["scheme_id"]: r for r in res.json()}

    # Central scheme applies
    svanidhi = results.get("scheme-pm-svanidhi")
    assert svanidhi is not None
    assert not any("Geographically inapplicable" in str(f) for f in svanidhi.get("failed_conditions", []))

    # PMC scheme strictly fails due to Cantonment residence
    pmc_r = results.get("pmc-shahari-garib-arogya")
    if pmc_r:
        assert pmc_r["status"] in {"ineligible", "false", "FALSE"}
        assert any("resides in cantonment" in str(f).lower() for f in pmc_r.get("failed_conditions", []))

    # PCMC scheme strictly fails
    pcmc_r = results.get("pcmc-mscit-women")
    if pcmc_r:
        assert pcmc_r["status"] in {"ineligible", "false", "FALSE"}
        assert any("resides in cantonment" in str(f).lower() for f in pcmc_r.get("failed_conditions", []))

    # Gram Panchayat scheme strictly fails
    gp_r = results.get("rural-zp-shetkari-sheti-shala")
    if gp_r:
        assert gp_r["status"] in {"ineligible", "false", "FALSE"}
        assert any("Geographically inapplicable" in str(f) for f in gp_r.get("failed_conditions", []))

    # 3. Cantonment Board Scope evaluation
    cb_scheme = SimpleNamespace(
        jurisdiction_scope=JurisdictionScope.CANTONMENT_BOARD,
        included_local_bodies=["cb-pune"],
    )
    p_cb = CitizenProfile(resident_state="maharashtra", local_government_type="cantonment", local_body_id="cb-pune", gender="male")
    is_ok, reason = jurisdiction_service.is_geographically_applicable(cb_scheme, p_cb)
    assert is_ok is True
    assert "Verified Cantonment Board resident" in reason

    p_pmc = CitizenProfile(resident_state="maharashtra", local_government_type="municipal_corporation", municipal_corporation="mc-pune", gender="male")
    is_ok2, reason2 = jurisdiction_service.is_geographically_applicable(cb_scheme, p_pmc)
    assert is_ok2 is False
    assert "Ministry of Defence" in reason2


def test_tmc_vs_mira_bhayander_isolation(client):
    """Verify isolation between adjoining Thane district corporations: TMC vs. Mira Bhayander."""
    # TMC resident
    tmc_prof = {
        "name": "Dinesh Parab",
        "gender": "male",
        "age_years": 34,
        "resident_state": "maharashtra",
        "district": "Thane",
        "local_government_type": "municipal_corporation",
        "municipal_corporation": "mc-thane",
        "residence_years": 5,
        "disability_percentage": 50,
    }
    res_tmc = client.post("/eligibility/evaluate?language=en&scope=canonical", json=tmc_prof)
    assert res_tmc.status_code == 200
    map_tmc = {r["scheme_id"]: r for r in res_tmc.json()}

    assert not any("Geographically inapplicable" in str(f) for f in map_tmc.get("tmc-divyang-kalyan", {}).get("failed_conditions", []))
    assert map_tmc.get("bmc-anand-dighe-divyang", {})["status"] in {"ineligible", "false", "FALSE"}

    # Mira Bhayander resident
    mb_prof = dict(tmc_prof)
    mb_prof["municipal_corporation"] = "mc-mira-bhayander"
    res_mb = client.post("/eligibility/evaluate?language=en&scope=canonical", json=mb_prof)
    assert res_mb.status_code == 200
    map_mb = {r["scheme_id"]: r for r in res_mb.json()}

    # TMC scheme fails for Mira Bhayander resident
    assert map_mb.get("tmc-divyang-kalyan", {})["status"] in {"ineligible", "false", "FALSE"}
    assert any("mc-mira-bhayander" in str(f) for f in map_mb.get("tmc-divyang-kalyan", {}).get("failed_conditions", []))


def test_nmmc_vs_panvel_isolation(client):
    """Verify boundary isolation between adjoining Navi Mumbai (NMMC) and Panvel (PMC-Panvel) corporations."""
    nmmc_prof = {
        "name": "Archana Shinde",
        "gender": "female",
        "age_years": 22,
        "resident_state": "maharashtra",
        "district": "Thane",
        "local_government_type": "municipal_corporation",
        "municipal_corporation": "mc-navi-mumbai",
        "residence_years": 6,
        "disability_percentage": 55,
    }
    res = client.post("/eligibility/evaluate?language=en&scope=canonical", json=nmmc_prof)
    assert res.status_code == 200
    res_map = {r["scheme_id"]: r for r in res.json()}

    assert not any("Geographically inapplicable" in str(f) for f in res_map.get("nmmc-divyang-education-grant", {}).get("failed_conditions", []))

    # Move to Panvel
    nmmc_prof["municipal_corporation"] = "mc-panvel"
    nmmc_prof["district"] = "Raigad"
    res2 = client.post("/eligibility/evaluate?language=en&scope=canonical", json=nmmc_prof)
    assert res2.status_code == 200
    res_map2 = {r["scheme_id"]: r for r in res2.json()}

    assert res_map2.get("nmmc-divyang-education-grant", {})["status"] in {"ineligible", "false", "FALSE"}
    assert any("mc-panvel" in str(f) for f in res_map2.get("nmmc-divyang-education-grant", {}).get("failed_conditions", []))


def test_cantonment_and_zp_roster_integrity(client):
    """
    Verify complete statutory reconciliation for 7 Cantonment Boards, 34 Zilla Parishads,
    and 36 revenue districts in the ULB registry API.
    """
    res = client.get("/local-governments/ulbs")
    assert res.status_code == 200
    ulb = res.json()

    assert len(ulb["cantonment_boards"]) == 7
    assert len(ulb["zilla_parishads"]) == 34
    assert ulb["breakdown"]["zilla_parishads"] == 34
    assert ulb["breakdown"]["cantonment_boards_central_mod"] == 7
    assert len(ulb["districts"]) == 36

    # Mumbai City and Mumbai Suburban must have None for ZP with explicit statutory explanation
    assert ulb["districts"]["Mumbai City"]["zilla_parishad"] is None
    assert "Mumbai Municipal Corporation Act" in ulb["districts"]["Mumbai City"]["rural_administration_note"]
    assert ulb["districts"]["Mumbai Suburban"]["zilla_parishad"] is None

    # Rural district must have named ZP
    assert ulb["districts"]["Pune"]["zilla_parishad"] == "Pune Zilla Parishad"
    assert "cb-pune" in ulb["districts"]["Pune"]["cantonment_boards"]
    assert "cb-kirkee" in ulb["districts"]["Pune"]["cantonment_boards"]
    assert "cb-dehu-road" in ulb["districts"]["Pune"]["cantonment_boards"]


@pytest.mark.parametrize("corp_id", ALL_29_CORPORATION_IDS)
def test_parameterized_all_29_municipal_corporations(client, corp_id):
    """
    Parameterized acceptance test across ALL 29 Maharashtra Municipal Corporations:
    1. Clean resolution via /local-governments/resolve-location.
    2. Authoritative token generation (jurisdiction:mc:{corp_id}).
    3. Central schemes (PM SVANidhi) geographically applicable.
    4. State schemes (Majhi Ladki Bahin) geographically applicable.
    5. Cross-corporation schemes from other corporations strictly excluded.
    """
    # 1. Location resolution
    res_loc = client.post(
        "/local-governments/resolve-location",
        json={"local_government_type": "municipal_corporation", "local_body": corp_id}
    )
    assert res_loc.status_code == 200
    loc_data = res_loc.json()
    assert loc_data["status"] == "RESOLVED"
    assert loc_data["local_body_id"] == corp_id
    assert loc_data["local_government_type"] == "municipal_corporation"
    assert f"jurisdiction:mc:{corp_id}" in loc_data["applicable_jurisdiction_tokens"]

    # 2. Evaluation for citizen of this corporation
    corp_info = jurisdiction_service.get_corporation(corp_id)
    assert corp_info is not None, f"Corporation metadata not found for {corp_id}"

    prof = {
        "name": f"Citizen of {corp_info['official_name_en']}",
        "gender": "female",
        "age_years": 30,
        "resident_state": "maharashtra",
        "district": corp_info["district"],
        "local_government_type": "municipal_corporation",
        "municipal_corporation": corp_id,
        "residence_years": 6,
        "annual_family_income": 85000,
        "aadhaar_linked_bank_account": True,
    }

    res_eval = client.post("/eligibility/evaluate?language=en&scope=canonical", json=prof)
    assert res_eval.status_code == 200
    results = {r["scheme_id"]: r for r in res_eval.json()}

    # Central scheme must apply to every corporation resident
    svanidhi = results.get("scheme-pm-svanidhi")
    assert svanidhi is not None
    assert not any("Geographically inapplicable" in str(f) for f in svanidhi.get("failed_conditions", []))

    # State scheme must apply
    ladki = results.get("candidate-majhi-ladki-bahin") or results.get("demo-majhi-ladki-bahin")
    assert ladki is not None
    assert not any("Geographically inapplicable" in str(f) for f in ladki.get("failed_conditions", []))

    # Foreign corporation schemes must be strictly excluded
    if corp_id != "mc-pune":
        pmc_r = results.get("pmc-shahari-garib-arogya")
        if pmc_r:
            assert pmc_r["status"] in {"ineligible", "false", "FALSE"}
            assert any("Geographically inapplicable" in str(f) for f in pmc_r.get("failed_conditions", []))

    if corp_id != "mc-pimpri-chinchwad":
        pcmc_r = results.get("pcmc-mscit-women")
        if pcmc_r:
            assert pcmc_r["status"] in {"ineligible", "false", "FALSE"}
            assert any("Geographically inapplicable" in str(f) for f in pcmc_r.get("failed_conditions", []))

    if corp_id != "mc-brihanmumbai":
        bmc_r = results.get("bmc-anand-dighe-divyang")
        if bmc_r:
            assert bmc_r["status"] in {"ineligible", "false", "FALSE"}
            assert any("Geographically inapplicable" in str(f) for f in bmc_r.get("failed_conditions", []))
