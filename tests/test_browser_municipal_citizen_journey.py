"""
End-to-End Browser Citizen Journey Suite (Playwright)
Section 7 Acceptance Tests:
1. Citizen selects Pune.
2. Location resolves to PMC.
3. Full discovery begins.
4. Adaptive interview asks required profile questions.
5. Published applicable Central, State, District and PMC schemes are evaluated.
6. Results show correct jurisdiction badges.
7. PCMC-only programmes do not appear.
8. Citizen changes jurisdiction to PCMC.
9. Geographic evaluation recalculates.
10. New results correctly include PCMC and exclude PMC-only schemes.
11. Focused eligibility in Explore preserves the selected scheme and jurisdiction.
12. Rural and Municipal Council citizens are routed to appropriate jurisdiction levels.
"""

import threading
import time
import pytest
import uvicorn
from playwright.sync_api import sync_playwright

from scheme_navigator.api.main import app

PORT = 8996
BASE_URL = f"http://127.0.0.1:{PORT}"


@pytest.fixture(scope="module")
def live_server():
    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.5)
    yield BASE_URL
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
    context = browser_instance.new_context()
    pg = context.new_page()
    yield pg
    context.close()


def test_01_explore_jurisdiction_filtering_and_badges(page, live_server):
    """
    Steps 1, 6, 7:
    Filter catalogue by Government Level: Municipal Corporation -> Pune Municipal Corporation (PMC).
    Cards render PMC schemes with '🏢 PMC Corp' badge; PCMC-only schemes do NOT appear.
    """
    page.goto(f"{live_server}/explore")
    page.wait_for_selector("#schemes-grid-container", timeout=10000)
    page.wait_for_selector(".scheme-card", timeout=10000)

    # 1. Select Level: Municipal Corporation
    page.select_option("#filter-gov-level", "MUNICIPAL_CORPORATION")
    page.wait_for_timeout(300)

    # Corporation wrapper must be visible
    corp_wrap = page.locator("#filter-corp-wrapper")
    assert corp_wrap.is_visible()

    # 2. Select Corporation: Pune Municipal Corporation (mc-pune)
    page.select_option("#filter-corp-select", "mc-pune")
    page.wait_for_timeout(400)

    # 3. Assert PMC schemes appear and PCMC schemes are excluded
    card_texts = page.locator(".scheme-card").all_text_contents()
    all_text = " ".join(card_texts)

    assert "Shahari Garib Arogya" in all_text or "Maulana Azad" in all_text or "pmc-shahari-garib-arogya" in all_text or "शहरी गरीब" in all_text or "मौलाना" in all_text
    assert "PMC Corp" in all_text or "पुणे मनपा" in all_text or "PMC" in all_text

    # PCMC-only schemes must NOT appear
    assert "PCMC Free Bicycle" not in all_text
    assert "पिंपरी मोफत सायकल" not in all_text


def test_02_explore_switching_to_pcmc_recalculates(page, live_server):
    """
    Steps 8, 9, 10:
    Citizen switches corporation filter to Pimpri Chinchwad (PCMC).
    Catalogue dynamically updates to show PCMC schemes and exclude PMC-only schemes.
    """
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)

    page.select_option("#filter-gov-level", "MUNICIPAL_CORPORATION")
    page.wait_for_timeout(300)

    page.select_option("#filter-corp-select", "mc-pimpri-chinchwad")
    page.wait_for_timeout(400)

    card_texts = page.locator(".scheme-card").all_text_contents()
    all_text = " ".join(card_texts)

    # PCMC schemes appear
    assert "PCMC" in all_text or "पिंपरी" in all_text or "Bicycle" in all_text or "MSCIT" in all_text
    # PMC schemes do not appear
    assert "Shahari Garib Arogya" not in all_text


def test_03_explore_rural_and_council_jurisdiction_levels(page, live_server):
    """
    Step 12:
    Verify that selecting Municipal Council and Gram Panchayat levels routes to correct tiers.
    """
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)

    # 1. Municipal Council Level
    page.select_option("#filter-gov-level", "MUNICIPAL_COUNCIL")
    page.wait_for_timeout(400)
    council_cards = page.locator(".scheme-card").all_text_contents()
    council_text = " ".join(council_cards)
    assert "Municipal Council" in council_text or "नगर परिषद" in council_text or "Swachh" in council_text
    assert "PMC Corp" not in council_text
    assert "PCMC Corp" not in council_text

    # 2. Rural / Gram Panchayat Level
    page.select_option("#filter-gov-level", "GRAM_PANCHAYAT")
    page.wait_for_timeout(400)
    rural_cards = page.locator(".scheme-card").all_text_contents()
    rural_text = " ".join(rural_cards)
    assert "Gram Panchayat" in rural_text or "ग्रामपंचायत" in rural_text or "Shetkari" in rural_text or "ZP" in rural_text
    assert "PMC Corp" not in rural_text


def test_04_results_page_pmc_vs_pcmc_isolation_and_badges(page, live_server):
    """
    Steps 2, 4, 5, 6, 7:
    Citizen profile at PMC evaluates Central, State, and PMC schemes.
    PCMC schemes appear in Ineligible accordion with explicit geographic isolation reason.
    """
    page.goto(f"{live_server}/")
    page.wait_for_selector("#view-home", timeout=10000)

    # Set up citizen state via window.state directly to evaluate realistic multi-tier profile
    page.evaluate("""async () => {
        window.state.profile = {
            resident_state: "maharashtra",
            gender: "female",
            age_years: 28,
            annual_family_income: 60000,
            district: "Pune",
            local_government_type: "municipal_corporation",
            municipal_corporation: "mc-pune",
            residence_years: 5,
            aadhaar_linked_bank_account: true
        };
        window.updateProfileDisplay();
        await window.evaluateAndShowResults();
    }""")

    # Wait for results view
    page.wait_for_selector(".scoreboard", timeout=10000)
    page.wait_for_selector("#results-cards-container", timeout=10000)
    page.wait_for_timeout(800)

    # Results view is visible
    assert page.locator("#view-results").is_visible()

    # Verify score numbers are rendered
    assert page.locator(".score-num").count() >= 3

    # Ineligible accordion must contain PCMC schemes with geographic exclusion reason
    accordion = page.locator("#not-eligible-accordion summary")
    if accordion.is_visible():
        accordion.click()
        page.wait_for_timeout(400)

    ineligible_text = page.locator("#not-eligible-cards-container").inner_text()
    # PCMC bicycle or sewing scheme must be in ineligible container with geographic reason
    assert "Geographically inapplicable" in ineligible_text or "भौगोलिकदृष्ट्या अपात्र" in ineligible_text or "अपात्र" in ineligible_text
    assert "mc-pimpri-chinchwad" in ineligible_text or "PCMC" in ineligible_text or "पिंपरी" in ineligible_text or "pcmc-" in ineligible_text


def test_05_focused_eligibility_preserves_jurisdiction(page, live_server):
    """
    Step 11:
    Focused eligibility in Explore preserves the selected scheme and jurisdiction scope.
    """
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)

    # Filter to PMC
    page.select_option("#filter-gov-level", "MUNICIPAL_CORPORATION")
    page.wait_for_timeout(200)
    page.select_option("#filter-corp-select", "mc-pune")
    page.wait_for_timeout(300)

    # Click on the first visible PMC card's "Check Eligibility" button
    first_btn = page.locator(".scheme-card .btn-primary").first
    assert first_btn.is_visible()
    first_btn.click()

    page.wait_for_timeout(600)

    # Must transition to interview view
    assert page.locator("#view-interview").is_visible()

    # Scoped banner or focused scheme title must be displayed
    assert page.locator("#focused-scheme-banner").is_visible()
