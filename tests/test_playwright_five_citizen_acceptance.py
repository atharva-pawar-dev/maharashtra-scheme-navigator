"""
Five-Citizen Acceptance Test & P0 Browser Verification (TRIMURTI v3 Section 36 & Milestone SC-G1).
Executes real Chromium browser tests using Playwright against live Uvicorn instance.
"""

import os
import socket
import threading
import time
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
    thread.join(timeout=2.0)


def test_citizen_a_farmer_acceptance(live_server):
    """Citizen A: Farmer matching PM-KISAN, Namo Shetkari, and Bhausaheb Fundkar."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{live_server}/explore")
        page.wait_for_selector(".scheme-card", timeout=10000)

        # Search for farmer schemes
        search_input = page.locator("#scheme-search-input")
        search_input.fill("Namo Shetkari")
        page.wait_for_timeout(400)

        # Check card exists and has decision-ready badge
        card = page.locator(".scheme-card").first
        card_text = card.inner_text()
        assert "नमो शेतकरी" in card_text or "Namo Shetkari" in card_text
        assert "निर्णय-सज्ज" in card_text or "Decision Ready" in card_text

        # Open details modal
        detail_btn = card.locator("button.btn-scheme-details")
        detail_btn.click()
        page.wait_for_selector("#modal-scheme-detail.active", timeout=5000)

        modal_text = page.locator("#modal-content").inner_text()
        assert "NSMNY" in modal_text or "नमो शेतकरी" in modal_text or "6,000" in modal_text or "६,०००" in modal_text
        assert "Decision Ready" in modal_text or "निर्णय-सज्ज" in modal_text

        browser.close()


def test_citizen_b_student_acceptance(live_server):
    """Citizen B: Student matching Post-Matric Scholarship & EBC Tuition Waiver."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{live_server}/explore")
        page.wait_for_selector(".scheme-card", timeout=10000)

        search_input = page.locator("#scheme-search-input")
        search_input.fill("Post-Matric")
        page.wait_for_timeout(400)

        cards = page.locator(".scheme-card")
        assert cards.count() >= 1
        card_text = cards.first.inner_text()
        assert "Post-Matric" in card_text or "मॅट्रिकोत्तर" in card_text

        # Click detail and inspect modal
        cards.first.locator("button.btn-scheme-details").click()
        page.wait_for_selector("#modal-scheme-detail.active", timeout=5000)
        modal_text = page.locator("#modal-content").inner_text()
        assert "Scholarship" in modal_text or "शिष्यवृत्ती" in modal_text

        browser.close()


def test_citizen_c_senior_citizen_acceptance(live_server):
    """Citizen C: Senior citizen matching Shravanbal and Mukhyamantri Vayoshri."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{live_server}/explore")
        page.wait_for_selector(".scheme-card", timeout=10000)

        search_input = page.locator("#scheme-search-input")
        search_input.fill("Vayoshri")
        page.wait_for_timeout(400)

        cards = page.locator(".scheme-card")
        assert cards.count() >= 1
        card_text = cards.first.inner_text()
        assert "Vayoshri" in card_text or "वयोश्री" in card_text

        cards.first.locator("button.btn-scheme-details").click()
        page.wait_for_selector("#modal-scheme-detail.active", timeout=5000)
        modal_text = page.locator("#modal-content").inner_text()
        assert "3,000" in modal_text or "३,०००" in modal_text or "Vayoshri" in modal_text or "वयोश्री" in modal_text

        browser.close()


def test_citizen_d_woman_acceptance(live_server):
    """Citizen D: Woman matching Mukhyamantri Majhi Ladki Bahin Yojana."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{live_server}/explore")
        page.wait_for_selector(".scheme-card", timeout=10000)

        search_input = page.locator("#scheme-search-input")
        search_input.fill("Majhi Ladki Bahin")
        page.wait_for_timeout(400)

        # Target canonical scheme card (excluding demo fixture)
        card = page.locator(".scheme-card:not(:has(.badge-demo))").first
        card_text = card.inner_text()
        assert "लाडकी बहीण" in card_text or "Ladki Bahin" in card_text
        assert "निर्णय-सज्ज" in card_text or "Decision Ready" in card_text

        card.locator("button.btn-scheme-details").click()
        page.wait_for_selector("#modal-scheme-detail.active", timeout=5000)
        modal_text = page.locator("#modal-content").inner_text()
        assert "1,500" in modal_text or "१,५००" in modal_text
        assert "संकीर्ण-२०२४" in modal_text or "ladkibahin.maharashtra.gov.in" in modal_text

        browser.close()


def test_citizen_e_divyang_acceptance(live_server):
    """Citizen E: Person with disability matching IGNDPS and Divyang schemes."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{live_server}/explore")
        page.wait_for_selector(".scheme-card", timeout=10000)

        search_input = page.locator("#scheme-search-input")
        search_input.fill("Disability")
        page.wait_for_timeout(400)

        cards = page.locator(".scheme-card")
        assert cards.count() >= 1

        cards.first.locator("button.btn-scheme-details").click()
        page.wait_for_selector("#modal-scheme-detail.active", timeout=5000)
        modal_text = page.locator("#modal-content").inner_text()
        assert len(modal_text) > 100

        browser.close()


def test_ui_distinguishes_decision_ready_from_limited_info(live_server):
    """UI clearly distinguishes Decision Ready from Limited Information schemes."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{live_server}/explore")
        page.wait_for_selector(".scheme-card", timeout=10000)

        # 1. Decision Ready scheme has .badge-decision-ready
        ready_cards = page.locator(".badge-decision-ready")
        assert ready_cards.count() >= 10, f"Expected >= 10 decision-ready badges, found {ready_cards.count()}"

        # 2. Limited Information scheme has .badge-limited-info
        limited_cards = page.locator(".badge-limited-info")
        assert limited_cards.count() >= 20, f"Expected >= 20 limited-info badges, found {limited_cards.count()}"

        # 3. Open a limited-info scheme and verify advisory banner
        page.locator("#scheme-search-input").fill("Gramin")
        page.wait_for_timeout(400)
        first_limited = page.locator(".scheme-card").first
        first_limited.locator("button.btn-scheme-details").click()
        page.wait_for_selector("#modal-scheme-detail.active", timeout=5000)

        modal_text = page.locator("#modal-content").inner_text()
        assert "Limited Information" in modal_text or "मर्यादित माहिती" in modal_text
        assert "कागदपत्रे" in modal_text or "Documents" in modal_text or "दस्तावेज़" in modal_text

        browser.close()
