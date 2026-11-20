"""Automated tests for TRIMURTI v3 Milestone SC-G2: Universe Reconciliation.

Verifies:
- Universe snapshot U-20261120 integrity and authority counts
- Master candidate register disposition completeness across all 9 categories
- Canonical catalogue preservation (74 original + 14 integrated = 88 schemes)
- Demo fixture quarantine enforcement
- Non-definitive eligibility boundary for new candidates (is_decision_ready == False)
- Governance research summary, candidates, and authorities API endpoints
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app

REPO_ROOT = Path(__file__).resolve().parents[1]
UNIVERSE_PATH = REPO_ROOT / "data" / "research" / "universe" / "U-20261120.json"
CANDIDATES_CSV = REPO_ROOT / "docs" / "catalogue" / "scheme_discovery_master_register.csv"
SCHEMES_JSON = REPO_ROOT / "data" / "catalogue" / "schemes.json"
CANONICAL_JSON = REPO_ROOT / "data" / "source_registry" / "canonical_schemes.json"
LINK_HEALTH_CSV = REPO_ROOT / "reports" / "sc_g2_source_link_health.csv"


@pytest.fixture
def client():
    return TestClient(app)


def test_universe_snapshot_integrity():
    assert UNIVERSE_PATH.exists(), "U-20261120.json must exist"
    data = json.loads(UNIVERSE_PATH.read_text(encoding="utf-8"))
    assert data["universe_snapshot_id"] == "U-20261120"
    assert data["milestone"] == "SC-G2"
    authorities = data["authorities"]
    assert len(authorities) >= 137, f"Expected at least 137 authorities, found {len(authorities)}"

    categories = {a["category"] for a in authorities}
    assert "STATE_DEPARTMENT" in categories
    assert "STATE_CORPORATION" in categories
    assert "CENTRAL_MINISTRY" in categories
    assert "MUNICIPAL_CORPORATION" in categories
    assert "DISTRICT_COLLECTORATE" in categories

    dept_count = sum(1 for a in authorities if a["category"] in ("STATE_DEPARTMENT", "STATE_DIRECTORATE"))
    corp_count = sum(1 for a in authorities if a["category"] == "STATE_CORPORATION")
    cen_count = sum(1 for a in authorities if a["category"] == "CENTRAL_MINISTRY")
    mc_count = sum(1 for a in authorities if a["category"] == "MUNICIPAL_CORPORATION")
    dist_count = sum(1 for a in authorities if a["category"] == "DISTRICT_COLLECTORATE")

    assert dept_count >= 40
    assert corp_count >= 18
    assert cen_count >= 14
    assert mc_count == 29
    assert dist_count == 36


def test_candidate_register_completeness_and_9_dispositions():
    assert CANDIDATES_CSV.exists(), "scheme_discovery_master_register.csv must exist"
    with CANDIDATES_CSV.open(encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) >= 142, f"Expected at least 142 candidates, got {len(reader)}"

    dispositions = set()
    for row in reader:
        assert row["candidate_id"].startswith("CAND-")
        assert row["discovered_name"]
        assert row["authority"]
        assert row["disposition"]
        assert row["reason"]
        assert row["next_action"]
        dispositions.add(row["disposition"])

    required_dispositions = {
        "IN_CATALOGUE_VERIFIED",
        "IN_CATALOGUE_LIMITED",
        "NEEDS_RESEARCH",
        "BLOCKED_SOURCE",
        "DUPLICATE_OF",
        "SUB_SCHEME_OF",
        "HISTORICAL",
        "EXCLUDED_NOT_INDIVIDUAL_BENEFIT",
        "EXCLUDED_OUT_OF_GEOGRAPHIC_SCOPE",
    }
    missing = required_dispositions - dispositions
    assert not missing, f"Missing required candidate dispositions: {missing}"


def test_canonical_catalogue_preservation_and_growth():
    schemes = json.loads(SCHEMES_JSON.read_text(encoding="utf-8"))
    assert len(schemes) == 88, f"Expected 88 canonical schemes, got {len(schemes)}"

    canonical = json.loads(CANONICAL_JSON.read_text(encoding="utf-8"))
    assert len(canonical) == 89, f"Expected 89 schemes including demo fixture, got {len(canonical)}"

    # Check demo fixture quarantined
    demo = next((s for s in canonical if "demo" in s["canonical_scheme_id"]), None)
    assert demo is not None
    assert demo.get("is_decision_ready", False) is False
    assert demo["publication_status"] == "ACTIVE_DEMO_FIXTURE"


def test_new_candidates_non_definitive_eligibility():
    """Verify that all 14 newly integrated candidates fail closed to LIMITED_INFORMATION and are not decision ready."""
    schemes = json.loads(SCHEMES_JSON.read_text(encoding="utf-8"))
    new_ids = [
        "candidate-mahila-samman-msrtc",
        "candidate-amrit-jyeshtha-nagrik-msrtc",
        "candidate-pm-svanidhi",
        "candidate-pm-vishwakarma",
        "candidate-pmmvy",
        "candidate-pmay-gramin",
        "candidate-pmay-urban",
        "candidate-pm-fasal-bima",
        "candidate-saur-krushi-pump",
        "candidate-shabari-awas",
        "candidate-mbocw-toolkit",
        "candidate-mahajyoti-fellowship",
        "candidate-sarthi-csmnrf",
        "candidate-mslsa-free-legal-aid",
    ]

    found_ids = {s.get("scheme_id") or s.get("id") for s in schemes}
    for nid in new_ids:
        assert nid in found_ids, f"Expected newly integrated scheme '{nid}' in schemes.json"
        entry = next(s for s in schemes if (s.get("scheme_id") or s.get("id")) == nid)
        assert entry.get("is_decision_ready") is False, f"Scheme {nid} must not be decision ready"
        assert entry.get("public_status_category") == "LIMITED_INFORMATION"
        assert "advisory_banner" in entry
        assert entry["advisory_banner"].get("en")


def test_governance_research_summary_api(client):
    res = client.get("/governance/research-summary")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["milestone"] == "SC-G2"
    assert data["universe_snapshot"]["snapshot_id"] == "U-20261120"
    assert data["universe_snapshot"]["total_authorities"] >= 137
    assert data["candidates"]["total"] >= 142
    assert data["canonical_catalogue"]["total_canonical"] == 88
    assert data["canonical_catalogue"]["verified_flagships"] == 17
    assert data["canonical_catalogue"]["limited_information"] == 71
    assert data["canonical_catalogue"]["demo_fixtures_quarantined"] == 1
    assert data["source_link_health"]["total_urls_checked"] >= 135


def test_governance_candidates_api(client):
    res = client.get("/governance/candidates")
    assert res.status_code == 200
    all_cands = res.json()
    assert len(all_cands) >= 142

    # Test filtering by disposition
    res_verified = client.get("/governance/candidates?disposition=IN_CATALOGUE_VERIFIED")
    assert res_verified.status_code == 200
    verified = res_verified.json()
    assert len(verified) == 17
    assert all(c["disposition"] == "IN_CATALOGUE_VERIFIED" for c in verified)

    # Test filtering by search query
    res_search = client.get("/governance/candidates?search=Ladki")
    assert res_search.status_code == 200
    found = res_search.json()
    assert len(found) >= 1
    assert any("Ladki" in c["discovered_name"] for c in found)


def test_governance_authorities_api(client):
    res = client.get("/governance/authorities")
    assert res.status_code == 200
    authorities = res.json()
    assert len(authorities) >= 137

    # Filter municipal corporations
    res_mc = client.get("/governance/authorities?category=MUNICIPAL_CORPORATION")
    assert res_mc.status_code == 200
    mcs = res_mc.json()
    assert len(mcs) == 29
    assert all(m["category"] == "MUNICIPAL_CORPORATION" for m in mcs)
