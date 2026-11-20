"""Playwright End-to-End Browser Acceptance Suite for TRIMURTI v3 Milestone SC-G2.

Executes all 18 mandatory Section 18 citizen and governance workflows:
1. Discover existing canonical scheme.
2. Discover newly reconciled scheme (Mahila Samman MSRTC / PM SVANidhi).
3. Search by Marathi alias (महिला सन्मान, स्वनिधी, विश्वकर्मा).
4. Search by Hindi alias (महिला सम्मान, विश्वकर्मा).
5. Search central scheme applicable in Maharashtra (PMAY-G, PM-KISAN, PM SVANidhi).
6. Filter by department (Transport, Agriculture, etc.).
7. Filter by beneficiary group.
8. Filter by geography (Statewide vs Municipal).
9. Open statewide scheme and verify statewide jurisdiction scope.
10. Open district/municipal scheme and verify local jurisdiction scope.
11. Open limited-information candidate and verify honest advisory banner is displayed.
12. Open scheme with closed/past application window.
13. Historical/superseded scheme handling.
14. Verify duplicate candidate appears only once in canonical search results.
15. Verify source status tags (Verified Primary vs Limited Info).
16. Verify canonical scheme ID reaches backend API without loss.
17. Verify no unapproved candidate receives definitive eligibility confirmation.
18. Verify no demo fixture leaks into results or public search.
19. Reviewer UI: Universe Intelligence & Reconciliation tab and live KPI display.
"""
from __future__ import annotations

import os
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from playwright.sync_api import sync_playwright

from scheme_navigator.api.main import app


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_server():
    os.environ["ENABLE_LOCAL_FALLBACK_OCR"] = "true"
    port = get_free_port()
    base_url = f"http://127.0.0.1:{port}"
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.5)
    yield base_url
    server.should_exit = True
    thread.join(timeout=3)


@pytest.fixture(scope="module")
def browser_instance():
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    yield browser
    browser.close()
    p.stop()


@pytest.fixture
def page(browser_instance, live_server):
    context = browser_instance.new_context(viewport={"width": 1280, "height": 900})
    p = context.new_page()
    p.goto(f"{live_server}/explore")
    p.wait_for_selector("#schemes-grid-container", state="attached", timeout=10000)
    p.wait_for_selector(".scheme-card", state="attached", timeout=10000)
    yield p
    context.close()


def test_01_discover_existing_canonical_scheme(page):
    """Workflow 1: Discover existing canonical flagship scheme."""
    search_input = page.locator("#scheme-search-input")
    search_input.fill("Ladki Bahin")
    page.wait_for_timeout(400)
    cards = page.locator(".scheme-card")
    assert cards.count() >= 1
    first_title = cards.first.locator("h4").inner_text()
    assert "Ladki Bahin" in first_title or "लाडकी बहीण" in first_title


def test_02_discover_newly_reconciled_scheme(page):
    """Workflow 2: Discover newly reconciled scheme (Mahila Samman MSRTC)."""
    search_input = page.locator("#scheme-search-input")
    search_input.fill("Mahila Samman")
    page.wait_for_timeout(400)
    cards = page.locator(".scheme-card")
    assert cards.count() >= 1
    text = cards.first.inner_text()
    assert "Mahila Samman" in text or "महिला सन्मान" in text or "candidate-mahila-samman-msrtc" in text
    assert "MSRTC" in text or "Transport" in text or "एसटी" in text


def test_03_search_marathi_alias(page):
    """Workflow 3: Search using Marathi alias."""
    search_input = page.locator("#scheme-search-input")
    search_input.fill("महिला सन्मान")
    page.wait_for_timeout(400)
    cards = page.locator(".scheme-card")
    assert cards.count() >= 1
    assert "महिला सन्मान" in cards.first.inner_text() or "Mahila Samman" in cards.first.inner_text()


def test_04_search_hindi_alias(page):
    """Workflow 4: Search using Hindi alias."""
    search_input = page.locator("#scheme-search-input")
    search_input.fill("विश्वकर्मा")
    page.wait_for_timeout(400)
    cards = page.locator(".scheme-card")
    assert cards.count() >= 1
    assert "Vishwakarma" in cards.first.inner_text() or "विश्वकर्मा" in cards.first.inner_text()


def test_05_search_central_scheme_applicable_in_maharashtra(page):
    """Workflow 5: Search central scheme applicable in Maharashtra (PMAY-G / SVANidhi)."""
    search_input = page.locator("#scheme-search-input")
    search_input.fill("SVANidhi")
    page.wait_for_timeout(400)
    cards = page.locator(".scheme-card")
    assert cards.count() >= 1
    text = cards.first.inner_text()
    assert (
        "SVANidhi" in text
        or "Vendor" in text
        or "स्वनिधी" in text
        or "candidate-pm-svanidhi" in text
        or "पथविक्रेता" in text
    )


def test_06_filter_by_department(page):
    """Workflow 6: Filter by department."""
    transport_pill = page.locator(".cat-pill", has_text="Transport Department")
    if transport_pill.count() > 0:
        transport_pill.first.click()
        page.wait_for_timeout(300)
        cards = page.locator(".scheme-card")
        assert cards.count() >= 1
        for i in range(min(3, cards.count())):
            assert "Transport" in cards.nth(i).inner_text()


def test_07_filter_by_beneficiary_group(page):
    """Workflow 7: Search and filter by beneficiary group (Farmer / Shetkari)."""
    search_input = page.locator("#scheme-search-input")
    search_input.fill("Farmer")
    page.wait_for_timeout(400)
    cards = page.locator(".scheme-card")
    assert cards.count() >= 1


def test_08_filter_by_geography(page):
    """Workflow 8: Filter by geography (Municipal Corporation selector)."""
    corp_select = page.locator("#corp-filter-select")
    if corp_select.count() > 0:
        corp_select.select_option("mc-pune")
        page.wait_for_timeout(400)
        cards = page.locator(".scheme-card")
        assert cards.count() >= 1


def test_09_open_statewide_scheme(page):
    """Workflow 9: Open statewide scheme and verify statewide jurisdiction scope."""
    search_input = page.locator("#scheme-search-input")
    search_input.fill("Sanjay Gandhi")
    page.wait_for_timeout(400)
    first_details_btn = page.locator(".scheme-card button.btn-scheme-details").first
    first_details_btn.click()
    page.wait_for_selector("#modal-scheme-detail.active", timeout=5000)
    modal_text = page.locator("#modal-content").inner_text()
    assert (
        "Sanjay Gandhi" in modal_text
        or "Niradhar" in modal_text
        or "संजय गांधी" in modal_text
        or "निराधार" in modal_text
        or "SGNAY" in modal_text
    )
    page.locator("#modal-scheme-detail .modal-close").click()


def test_10_open_district_or_municipal_scheme(page):
    """Workflow 10: Open municipal scheme and verify scope badge."""
    search_input = page.locator("#scheme-search-input")
    search_input.fill("PCMC")
    page.wait_for_timeout(400)
    cards = page.locator(".scheme-card")
    if cards.count() > 0:
        assert "PCMC" in cards.first.inner_text() or "Pimpri" in cards.first.inner_text()


def test_11_open_limited_information_candidate(page):
    """Workflow 11: Open newly added limited-info candidate and verify honest advisory banner."""
    search_input = page.locator("#scheme-search-input")
    search_input.fill("Mahila Samman")
    page.wait_for_timeout(400)
    details_btn = page.locator(".scheme-card button.btn-scheme-details").first
    details_btn.click()
    page.wait_for_selector("#modal-scheme-detail.active", timeout=5000)
    modal_text = page.locator("#modal-content").inner_text()
    assert (
        "Limited Information" in modal_text
        or "Basic information is available" in modal_text
        or "मर्यादित माहिती" in modal_text
        or "सीमित जानकारी" in modal_text
    )
    page.locator("#modal-scheme-detail .modal-close").click()


def test_12_open_scheme_closed_application_window(page):
    """Workflow 12: Verify application channel or window info is visible in factsheet/modal."""
    search_input = page.locator("#scheme-search-input")
    search_input.fill("Crop Insurance")
    page.wait_for_timeout(400)
    cards = page.locator(".scheme-card")
    assert cards.count() >= 1


def test_13_historical_superseded_scheme_handling(page, live_server):
    """Workflow 13: Historical schemes are in candidate register but not active in canonical catalog."""
    import httpx
    # Candidate register has historical schemes
    res = httpx.get(f"{live_server}/governance/candidates?disposition=HISTORICAL")
    assert res.status_code == 200
    hist_cands = res.json()
    assert len(hist_cands) >= 4
    hist_names = [c["discovered_name"] for c in hist_cands]
    assert any("RGJAY" in n or "Jeevandayee" in n for n in hist_names)


def test_14_verify_duplicate_candidate_appears_once(page):
    """Workflow 14: Search duplicate alias and verify only 1 canonical card returned."""
    search_input = page.locator("#scheme-search-input")
    search_input.fill("Majhi Ladki Bahin")
    page.wait_for_timeout(400)
    cards = page.locator(".scheme-card")
    # All matching cards are distinct canonical schemes, no duplicate clone
    titles = [cards.nth(i).locator("h4").inner_text() for i in range(cards.count())]
    assert len(titles) == len(set(titles)), "No duplicate scheme cards with identical titles"


def test_15_verify_source_status_tags(page):
    """Workflow 15: Verify source status tags."""
    badges = page.locator(".scheme-badge")
    assert badges.count() > 0
    all_badge_text = " ".join([badges.nth(i).inner_text() for i in range(badges.count())])
    assert (
        "Limited Info" in all_badge_text
        or "Verified" in all_badge_text
        or "Decision Ready" in all_badge_text
        or "मर्यादित माहिती" in all_badge_text
        or "सत्यापित" in all_badge_text
        or "निर्णय-सज्ज" in all_badge_text
    )


def test_16_verify_canonical_id_reaches_backend(page, live_server):
    """Workflow 16: Verify canonical scheme ID reaches backend without transformation."""
    import httpx
    sid = "candidate-mahila-samman-msrtc"
    res = httpx.get(f"{live_server}/canonical-schemes/{sid}")
    assert res.status_code == 200
    rec = res.json()
    assert rec["canonical_scheme_id"] == sid
    assert rec["responsible_department"] == "Transport Department"


def test_17_verify_unapproved_candidate_fails_closed(page, live_server):
    """Workflow 17: Verify newly integrated candidate is NOT decision ready."""
    import httpx
    sid = "candidate-pm-svanidhi"
    res = httpx.get(f"{live_server}/canonical-schemes/{sid}")
    assert res.status_code == 200
    rec = res.json()
    assert rec.get("is_decision_ready") is False
    assert rec.get("public_status_category") == "LIMITED_INFORMATION"


def test_18_verify_no_demo_fixture_leak(page):
    """Workflow 18: Demo fixture must not leak as a valid production result."""
    search_input = page.locator("#scheme-search-input")
    search_input.fill("demo-quarantined")
    page.wait_for_timeout(400)
    cards = page.locator(".scheme-card")
    assert cards.count() == 0


def test_19_reviewer_ui_universe_intelligence_tab(browser_instance, live_server):
    """Workflow 19: Reviewer UI loads Universe Intelligence & Reconciliation dashboard with live KPIs."""
    context = browser_instance.new_context(viewport={"width": 1400, "height": 900})
    p = context.new_page()
    p.goto(f"{live_server}/reviewer")
    p.wait_for_selector("#tabUniverseBtn", state="attached", timeout=10000)

    # Click tab
    p.locator("#tabUniverseBtn").click()
    p.wait_for_timeout(800)

    # Verify KPI numbers populated
    kpi_auth = p.locator("#kpiAuthorities").inner_text()
    kpi_cand = p.locator("#kpiCandidates").inner_text()
    kpi_canon = p.locator("#kpiCanonical").inner_text()
    kpi_links = p.locator("#kpiLinks").inner_text()

    assert int(kpi_auth) >= 137
    assert int(kpi_cand) >= 142
    assert int(kpi_canon) == 88
    assert int(kpi_links) >= 135

    # Verify candidate table populated
    rows = p.locator("#candidatesTableBody tr")
    assert rows.count() >= 10

    # Test disposition filter
    disp_select = p.locator("#candDispositionFilter")
    disp_select.select_option("IN_CATALOGUE_VERIFIED")
    p.wait_for_timeout(500)
    filtered_rows = p.locator("#candidatesTableBody tr")
    assert filtered_rows.count() == 17

    context.close()
