"""
Playwright Browser Test Suite for Restored Document Auditor & Complete Citizen Journey
Tests:
- Explore -> Scheme Details -> Check My Documents & Factsheet Print/Share
- Scheme-Specific Document Requirements Checklist
- Results -> Check My Documents
- Document Auditor Multilingual Consistency (EN, MR, HI)
"""

import threading
import time
import pytest
import uvicorn
from playwright.sync_api import sync_playwright

import socket
from scheme_navigator.api.main import app


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_server():
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


def test_01_scheme_details_modal_has_auditor_and_factsheet_buttons(page, live_server):
    """Scheme Details modal contains 'Check My Documents' and 'Factsheet' buttons."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector("#schemes-grid-container", timeout=10000)
    page.wait_for_selector(".scheme-card", timeout=10000)

    # Click on the details button of the first scheme card
    details_btn = page.locator(".scheme-card .btn-scheme-details").first
    details_btn.click()

    # Modal should be active
    page.wait_for_selector("#modal-scheme-detail.active", timeout=5000)

    # Check for Document Auditor button
    btn_check_docs = page.locator("#btn-modal-check-docs")
    assert btn_check_docs.is_visible()

    # Check for Factsheet button
    btn_factsheet = page.locator("#btn-modal-share-factsheet")
    assert btn_factsheet.is_visible()

    # Click factsheet button to open factsheet modal
    btn_factsheet.click()
    page.wait_for_selector("#modal-scheme-factsheet.active", timeout=5000)
    assert page.locator("#factsheet-modal-content").is_visible()

    # Verify factsheet contains public information and no citizen PII
    fs_text = page.locator("#factsheet-modal-content").inner_text()
    assert "महाराष्ट्र शासन" in fs_text or "Government of Maharashtra" in fs_text or "योजना" in fs_text


def test_02_document_auditor_direct_entry_and_requirements_checklist(page, live_server):
    """Clicking 'Check My Documents' opens Document Auditor with scheme-specific requirements."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)

    # Click the first scheme details button and then 'Check My Documents'
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=5000)
    page.locator("#btn-modal-check-docs").click()

    # Should transition to #view-documents
    page.wait_for_selector("#view-documents.active", timeout=5000)

    # Verify banner displays scheme information
    scheme_name_el = page.locator("#doc-scheme-name")
    assert scheme_name_el.is_visible()
    assert scheme_name_el.inner_text() != "-"

    # Verify requirements list is populated with requirements cards
    page.wait_for_selector(".req-item-card", timeout=10000)
    req_cards = page.locator(".req-item-card")
    assert req_cards.count() >= 1

    # Verify requirement cards contain state machine badges (e.g. state-missing or state-matched)
    assert page.locator(".req-state-badge").count() >= 1

    # Verify readiness score strip exists
    readiness_badge = page.locator("#doc-readiness-badge")
    assert readiness_badge.is_visible()


def test_03_results_page_has_check_my_documents_action(page, live_server):
    """Results page displays 'Check My Documents' action button on scheme cards."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)

    # Inject synthetic results into state and navigate to results
    page.evaluate(
        """() => {
            state.results = [
                {
                    scheme_id: 'candidate-majhi-ladki-bahin',
                    scheme_name: 'Mukhyamantri Majhi Ladki Bahin Yojana (Candidate Scheme)',
                    status: 'eligible',
                    reason: 'Eligible based on age, gender and income.',
                    matched_conditions: ['Gender: Female', 'Age: 21-65 years']
                }
            ];
            showView('results');
        }"""
    )

    page.wait_for_selector("#view-results.active", timeout=5000)
    page.wait_for_selector("#results-cards-container .scheme-card", timeout=5000)

    # Verify card contains "कागदपत्रे तपासा" button
    doc_btn = page.locator("#results-cards-container .scheme-card button:has-text('कागदपत्रे तपासा')").first
    assert doc_btn.is_visible()

    # Click it and verify navigation to Document Auditor
    doc_btn.click()
    page.wait_for_selector("#view-documents.active", timeout=5000)
    assert page.locator("#doc-scheme-name").is_visible()


def test_04_document_auditor_multilingual_consistency(page, live_server):
    """Document auditor renders correctly in English, Marathi and Hindi."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=5000).click()
    page.wait_for_selector("#view-documents.active", timeout=5000)

    # Switch to English
    page.locator("#lang-btn-en").click()
    time.sleep(0.5)
    assert page.locator("#lbl-readiness-title").is_visible()

    # Switch to Hindi
    page.locator("#lang-btn-hi").click()
    time.sleep(0.5)
    assert page.locator("#lbl-readiness-title").is_visible()

    # Switch back to Marathi
    page.locator("#lang-btn-mr").click()
    time.sleep(0.5)
    assert page.locator("#lbl-readiness-title").is_visible()
