"""Integration tests for Maharashtra Comprehensive Scheme Integration.
Verifies canonical scheme catalogue, category coverage, search and filtering,
application channels, and strict monolingual UI invariants.
"""
from __future__ import annotations

import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.source_registry.registry import SourceRegistry


@pytest.fixture
def client():
    return TestClient(app)


def test_comprehensive_schemes_inventory_coverage():
    """Verify that canonical scheme database holds comprehensive real schemes across Maharashtra."""
    registry = SourceRegistry()
    schemes = registry.list_canonical_schemes()
    assert len(schemes) >= 60

    # Ensure coverage of classifications
    classifications = {s.state_central_joint_classification for s in schemes}
    assert "STATE_SCHEME" in classifications
    assert any("SPONSORED" in c for c in classifications)
    assert any("CENTRAL" in c for c in classifications)

    # Check key departments and sectors
    depts = {s.responsible_department for s in schemes}
    assert any("Agriculture" in d for d in depts)
    assert any("Women and Child Development" in d for d in depts)
    assert any("Social Justice" in d for d in depts)
    assert any("Tribal Development" in d for d in depts)
    assert any("Higher and Technical Education" in d or "School Education" in d for d in depts)
    assert any("Public Health" in d for d in depts)
    assert any("Housing" in d for d in depts)
    assert any("Skill" in d or "Industries" in d for d in depts)

    # Check specific flagship schemes exist
    scheme_ids = {s.canonical_scheme_id for s in schemes}
    assert "scheme-namo-shetkari-maha-samman" in scheme_ids
    assert "scheme-mjpjay-ayushman-bharat" in scheme_ids
    assert "scheme-pmay-gramin" in scheme_ids
    assert "scheme-pm-fasal-bima" in scheme_ids
    assert "scheme-bocw-construction-welfare" in scheme_ids
    assert "scheme-cmegp-self-employment" in scheme_ids
    assert "scheme-annasaheb-patil-ir2" in scheme_ids
    assert "scheme-mukhyamantri-vayoshri" in scheme_ids


def test_canonical_schemes_api_endpoints_and_filtering(client):
    """Test /canonical-schemes API query parameters and category discovery."""
    # 1. Full listing
    resp = client.get("/canonical-schemes")
    assert resp.status_code == 200
    all_schemes = resp.json()
    assert len(all_schemes) >= 60

    # 2. Categories discovery endpoint
    cats_resp = client.get("/canonical-schemes/categories")
    assert cats_resp.status_code == 200
    cats_data = cats_resp.json()
    assert cats_data["total_schemes"] >= 60
    assert len(cats_data["departments"]) >= 10
    assert len(cats_data["classifications"]) >= 3
    assert len(cats_data["beneficiary_categories"]) >= 5

    # 3. Search query in Marathi
    search_mr = client.get("/canonical-schemes?search=लाडकी")
    assert search_mr.status_code == 200
    mr_results = search_mr.json()
    assert len(mr_results) >= 1
    assert any("ladki" in r["canonical_scheme_id"] or "लाडकी" in r["marathi_name"] for r in mr_results)

    # 4. Search query in English
    search_en = client.get("/canonical-schemes?search=Shetkari")
    assert search_en.status_code == 200
    en_results = search_en.json()
    assert len(en_results) >= 1
    assert any("shetkari" in r["canonical_scheme_id"] for r in en_results)

    # 5. Department filter
    dept_resp = client.get("/canonical-schemes?department=Agriculture")
    assert dept_resp.status_code == 200
    agri_schemes = dept_resp.json()
    assert len(agri_schemes) >= 3
    assert all("agriculture" in s["responsible_department"].lower() for s in agri_schemes)

    # 6. Classification filter
    class_resp = client.get("/canonical-schemes?category=STATE_SCHEME")
    assert class_resp.status_code == 200
    state_schemes = class_resp.json()
    assert len(state_schemes) >= 20
    assert all(s["state_central_joint_classification"] == "STATE_SCHEME" for s in state_schemes)

    # 7. Single scheme details
    single_resp = client.get("/canonical-schemes/scheme-namo-shetkari-maha-samman")
    assert single_resp.status_code == 200
    single_data = single_resp.json()
    assert single_data["canonical_scheme_id"] == "scheme-namo-shetkari-maha-samman"
    assert "Namo Shetkari" in single_data["official_scheme_name"]
    assert single_data["benefit_amount"] == "₹6,000 / year"
    assert len(single_data["government_source_references"]) >= 1
    assert single_data["application_portal_url"].startswith("https://")


def test_application_channel_coverage_and_hand_off(client):
    """Verify that schemes have mapped application channels with statutory hand-off notices."""
    registry = SourceRegistry()
    channels = registry.list_channels()
    assert len(channels) >= 60

    # Test sample channels via API
    for scheme_id in ["scheme-namo-shetkari-maha-samman", "scheme-mjpjay-ayushman-bharat", "demo-majhi-ladki-bahin"]:
        ch_resp = client.get(f"/channels/{scheme_id}")
        assert ch_resp.status_code == 200
        ch = ch_resp.json()
        assert ch["scheme_id"] == scheme_id
        assert ch["portal_url"].startswith("https://")
        assert len(ch["statutory_hand_off_notice"]) > 20
        assert ch["channel_type"] in [
            "DIRECT_OFFICIAL_PORTAL",
            "AUTHORIZED_ASSISTANCE_CENTRE",
            "OFFLINE_OFFICE_APPLICATION",
            "AUTHORIZED_API_INTEGRATION",
        ]


def test_strict_monolingual_separation_invariants_in_html():
    """Verify static/index.html enforces 100% pure English and pure Marathi strings with zero bilingual leaks."""
    portal_path = Path(__file__).resolve().parents[1] / "static" / "index.html"
    assert portal_path.is_file()
    html_content = portal_path.read_text(encoding="utf-8")

    # 1. Verify I18N_PAGE exists with en, mr, hi definitions
    assert "const I18N_PAGE = {" in html_content
    assert "en: {" in html_content
    assert "mr: {" in html_content
    assert "hi: {" in html_content

    # 2. Extract I18N_PAGE mr block and ensure zero Latin/English word leakage in values
    mr_block_match = re.search(r"mr:\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}", html_content)
    assert mr_block_match is not None, "mr translation block must be present"
    mr_block = mr_block_match.group(1)

    # In Marathi strings, we allow HTML tags, Devanagari, digits, and punctuation,
    # but not mixed English words like '(All)', '(Demo Fixture)', '(How It Works)', '(State)'
    forbidden_mixed_patterns = [
        r"\(All\)",
        r"\(Demo Fixture\)",
        r"\(How It Works\)",
        r"\(Discover\)",
        r"\(Understand\)",
        r"\(Prepare\)",
        r"\(Apply\)",
        r"\(State\)",
        r"\(Gender\)",
        r"\(Age\)",
        r"\(Income\)",
        r"\(Category\)",
        r"\(Student\)",
        r"\(BPL\)",
        r"\(Roadmap\)",
        r"\(Document Workspace\)",
        r"\(Extraction Preview\)",
        r"\(Official Portal Direct Link\)",
        r"\(View Results\)",
    ]
    for pattern in forbidden_mixed_patterns:
        assert not re.search(pattern, mr_block, re.IGNORECASE), f"Forbidden pattern {pattern} found in mr translation block"

    # 3. Check English translation block for pure English (no Devanagari characters)
    en_block_match = re.search(r"en:\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}", html_content)
    assert en_block_match is not None, "en translation block must be present"
    en_block = en_block_match.group(1)

    devanagari_pattern = r"[\u0900-\u097F]"
    # Ensure zero Devanagari in en block
    devanagari_in_en = re.findall(devanagari_pattern, en_block)
    assert len(devanagari_in_en) == 0, f"Devanagari characters found in English translation block: {devanagari_in_en[:10]}"
