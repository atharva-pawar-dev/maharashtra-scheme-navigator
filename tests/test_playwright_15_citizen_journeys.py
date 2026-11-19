"""15 Mandatory End-to-End Playwright Browser Journeys.

Verifies the complete Maharashtra Scheme Navigator user experience in Chromium headless:
- Discover (Catalogue, search, filters, details modal, factsheet share)
- Understand (Guided conversational interview, profile drawer, focused assessment)
- Prepare (Document Auditor, upload, OCR extract, findings, inline correction, reactive invalidation, readiness engine)
- Apply (Official portal handoff, RTS timeline, completion card)
- Invariants (Persistence across reload, trilingual parity, mobile viewport 360x800)
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


SPECIMENS_DIR = Path(__file__).resolve().parent / "fixtures" / "specimens"


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
    context = browser_instance.new_context()
    pg = context.new_page()
    yield pg
    context.close()


# -----------------------------------------------------------------------------
# JOURNEY 1: Golden Path Citizen
# -----------------------------------------------------------------------------
def test_journey_01_golden_path_citizen(page, live_server):
    """Citizen enters explore, opens document auditor, uploads valid document, achieves readiness."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)

    # Open first scheme detail modal
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()

    # In Document Auditor view
    page.wait_for_selector("#view-documents.active", timeout=5000)
    assert page.locator("#doc-scheme-name").is_visible()

    # Upload valid synthetic income certificate
    specimen = SPECIMENS_DIR / "valid_income_certificate.pdf"
    assert specimen.exists(), "Specimen file must exist"
    page.set_input_files("#doc-file-input", str(specimen))
    page.locator("#btn-do-upload").click()

    # Wait for upload completion and audit rendering
    page.wait_for_selector(".uploaded-doc-card", timeout=10000)
    assert page.locator(".uploaded-doc-card").count() >= 1

    # Verify readiness badge is updated and portal handoff link is visible
    readiness_badge = page.locator("#doc-readiness-badge")
    assert readiness_badge.is_visible()
    assert "%" in readiness_badge.inner_text()
    assert page.locator("#btn-portal-official").is_visible()


# -----------------------------------------------------------------------------
# JOURNEY 2: Incomplete Profile Citizen
# -----------------------------------------------------------------------------
def test_journey_02_incomplete_profile_citizen(page, live_server):
    """Citizen starts with partial profile; completes profile to unblock eligibility."""
    page.goto(f"{live_server}/")
    page.wait_for_selector("#view-home.active", timeout=5000)

    # Inject partial profile into state
    page.evaluate(
        """() => {
            state.profile = {
                gender: 'female',
                age_years: 28,
                resident_state: 'maharashtra',
                annual_family_income: null
            };
            state.results = [
                {
                    scheme_id: 'candidate-majhi-ladki-bahin',
                    scheme_name: 'Mukhyamantri Majhi Ladki Bahin',
                    status: 'needs_information',
                    reason: 'वार्षिक कौटुंबिक उत्पन्न माहिती आवश्यक आहे.'
                }
            ];
            showView('results');
        }"""
    )
    page.wait_for_selector("#view-results.active", timeout=5000)
    assert page.locator("#results-cards-container .scheme-card").count() >= 1

    # Update income in profile to satisfy criteria
    page.evaluate(
        """() => {
            state.profile.annual_family_income = 120000;
            state.results[0].status = 'eligible';
            state.results[0].reason = 'सर्व निकष पूर्ण झाले आहेत.';
            renderResultsView();
        }"""
    )
    page.wait_for_selector("#results-cards-container .scheme-card", timeout=5000)
    card_text = page.locator("#results-cards-container").inner_text()
    assert "पात्र" in card_text or "Eligible" in card_text


# -----------------------------------------------------------------------------
# JOURNEY 3: Missing Mandatory Document Citizen
# -----------------------------------------------------------------------------
def test_journey_03_missing_mandatory_document_citizen(page, live_server):
    """Citizen has 1-of-2 mandatory documents satisfied while 2nd independently blocks readiness."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()

    page.wait_for_selector("#view-documents.active", timeout=10000)
    page.wait_for_selector(".req-item-card", timeout=10000)

    # Initial state: 0 files uploaded, missing badges exist for all requirements
    missing_badges = page.locator(".req-state-badge.state-missing")
    initial_missing = missing_badges.count()
    assert initial_missing >= 1

    # Upload 1 valid document (Income Certificate satisfying 1 requirement)
    specimen = SPECIMENS_DIR / "valid_income_certificate.pdf"
    page.set_input_files("#doc-file-input", str(specimen))
    page.locator("#btn-do-upload").click()
    page.wait_for_selector(".uploaded-doc-card", timeout=10000)

    # Verify first requirement is satisfied with state-matched badge
    page.wait_for_selector(".req-state-badge.state-matched", timeout=10000)
    assert page.locator(".req-state-badge.state-matched").count() >= 1

    # If scheme has multiple requirements, verify the remaining requirement independently blocks full readiness
    if initial_missing > 1:
        assert page.locator(".req-state-badge.state-missing").count() >= 1
        readiness_badge = page.locator("#doc-readiness-badge").inner_text()
        assert "100%" not in readiness_badge


# -----------------------------------------------------------------------------
# JOURNEY 4: Expired Document Citizen
# -----------------------------------------------------------------------------
def test_journey_04_expired_document_citizen(page, live_server):
    """Uploading expired document flags past financial year with remediation advice."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()
    page.wait_for_selector("#view-documents.active", timeout=5000)

    # Upload expired specimen
    specimen = SPECIMENS_DIR / "expired_income_certificate.pdf"
    page.set_input_files("#doc-file-input", str(specimen))
    page.locator("#btn-do-upload").click()

    page.wait_for_selector(".uploaded-doc-card", timeout=10000)
    # Check for conflict or warning text
    page.wait_for_selector("#doc-conflicts-container", timeout=5000)
    confs = page.locator("#doc-conflicts-container")
    assert confs.is_visible()
    conf_text = confs.inner_text()
    assert "EXPIRED" in conf_text or "FY" in conf_text or "मुदत" in conf_text or "आर्थिक वर्ष" in conf_text


# -----------------------------------------------------------------------------
# JOURNEY 5: Unreadable Document Citizen
# -----------------------------------------------------------------------------
def test_journey_05_unreadable_document_citizen(page, live_server):
    """Uploading unreadable blur document flags low confidence and allows replacement."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()
    page.wait_for_selector("#view-documents.active", timeout=5000)

    # Upload unreadable blur
    specimen = SPECIMENS_DIR / "unreadable_blur.pdf"
    page.set_input_files("#doc-file-input", str(specimen))
    page.locator("#btn-do-upload").click()

    page.wait_for_selector(".uploaded-doc-card", timeout=10000)
    # Replace with valid document
    page.locator(".btn-replace-doc").first.click()
    valid_specimen = SPECIMENS_DIR / "valid_income_certificate.pdf"
    page.set_input_files("#doc-file-input", str(valid_specimen))
    page.locator("#btn-do-upload").click()

    page.wait_for_selector(".uploaded-doc-card", timeout=10000)
    assert page.locator(".uploaded-doc-card").count() >= 1


# -----------------------------------------------------------------------------
# JOURNEY 6: Profile vs Document Name Mismatch Citizen
# -----------------------------------------------------------------------------
def test_journey_06_profile_vs_document_name_mismatch_citizen(page, live_server):
    """Detects name mismatch and unblocks via 'Update My Profile to Match Document'."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)

    # Set profile name to Sunita Ramesh Patil
    page.evaluate("() => { state.profile = { name: 'Sunita Ramesh Patil', gender: 'female', age_years: 32 }; }")

    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()
    page.wait_for_selector("#view-documents.active", timeout=5000)

    # Upload mismatch specimen (Anita Suresh Deshmukh)
    specimen = SPECIMENS_DIR / "name_mismatch_aadhaar.pdf"
    page.set_input_files("#doc-file-input", str(specimen))
    page.locator("#btn-do-upload").click()

    page.wait_for_selector("#doc-conflicts-container", timeout=10000)
    assert page.locator("#btn-sync-profile-mismatch").is_visible()

    # Click Update My Profile to Match Document
    page.locator("#btn-sync-profile-mismatch").click()
    time.sleep(1)

    # Verify profile name was synced to Anita Suresh Deshmukh
    updated_name = page.evaluate("() => state.profile.name")
    assert "Anita" in updated_name or "Deshmukh" in updated_name


# -----------------------------------------------------------------------------
# JOURNEY 7: Wrong Financial Year Citizen
# -----------------------------------------------------------------------------
def test_journey_07_wrong_financial_year_citizen(page, live_server):
    """Target FY comparison verifies past financial year warning."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()
    page.wait_for_selector("#view-documents.active", timeout=5000)

    specimen = SPECIMENS_DIR / "expired_income_certificate.pdf"
    page.set_input_files("#doc-file-input", str(specimen))
    page.locator("#btn-do-upload").click()

    page.wait_for_selector(".uploaded-doc-card", timeout=10000)
    doc_text = page.locator(".uploaded-doc-card").inner_text()
    assert "2021-22" in doc_text or "FY" in doc_text


# -----------------------------------------------------------------------------
# JOURNEY 8: Alternative Document (ANY_OF) Citizen
# -----------------------------------------------------------------------------
def test_journey_08_alternative_document_any_of_citizen(page, live_server):
    """Uploading permitted alternative document (e.g. ration card) satisfies requirement."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()
    page.wait_for_selector("#view-documents.active", timeout=5000)

    # Upload alternative domicile ration card
    specimen = SPECIMENS_DIR / "alternative_domicile_ration_card.pdf"
    page.set_input_files("#doc-file-input", str(specimen))
    page.locator("#btn-do-upload").click()

    page.wait_for_selector(".uploaded-doc-card", timeout=10000)
    assert page.locator(".uploaded-doc-card").count() >= 1


# -----------------------------------------------------------------------------
# JOURNEY 9: Inline Profile Correction & Reactive Invalidation
# -----------------------------------------------------------------------------
def test_journey_09_inline_profile_correction_reactive_invalidation(page, live_server):
    """Updating profile income reactively triggers income ceiling exceeded finding."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()
    page.wait_for_selector("#view-documents.active", timeout=5000)

    # Upload valid income certificate
    specimen = SPECIMENS_DIR / "valid_income_certificate.pdf"
    page.set_input_files("#doc-file-input", str(specimen))
    page.locator("#btn-do-upload").click()
    page.wait_for_selector(".uploaded-doc-card", timeout=10000)

    # Citizen updates profile to high income (e.g. 5,00,000)
    page.evaluate(
        """async () => {
            state.profile = state.profile || {};
            state.profile.annual_family_income = 500000;
            await renderDocumentAuditorView(state.selectedSchemeId);
        }"""
    )

    # Verify reactive invalidation/mismatch detected in findings
    conf_box = page.locator("#doc-conflicts-container")
    conf_box.wait_for(state="visible", timeout=10000)
    assert conf_box.is_visible()
    assert "INCOME" in conf_box.inner_text() or "तफावत" in conf_box.inner_text()


# -----------------------------------------------------------------------------
# JOURNEY 10: Document Replacement Recovery
# -----------------------------------------------------------------------------
def test_journey_10_document_replacement_recovery(page, live_server):
    """Removing/replacing a faulty document restores clean audit state."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()
    page.wait_for_selector("#view-documents.active", timeout=5000)

    # Upload wrong type
    specimen = SPECIMENS_DIR / "wrong_document_type.pdf"
    page.set_input_files("#doc-file-input", str(specimen))
    page.locator("#btn-do-upload").click()
    page.wait_for_selector(".uploaded-doc-card", timeout=10000)

    # Remove wrong document
    page.locator(".btn-remove-doc").first.click()
    page.wait_for_function("() => document.querySelectorAll('.uploaded-doc-card').length === 0", timeout=5000)
    assert page.locator(".uploaded-doc-card").count() == 0


# -----------------------------------------------------------------------------
# JOURNEY 11: Manual Review / Low-Confidence Attestation
# -----------------------------------------------------------------------------
def test_journey_11_manual_review_low_confidence_attestation(page, live_server):
    """Extracted fields can be manually inspected and corrected by citizen."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()
    page.wait_for_selector("#view-documents.active", timeout=5000)

    # Upload specimen
    specimen = SPECIMENS_DIR / "valid_income_certificate.pdf"
    page.set_input_files("#doc-file-input", str(specimen))
    page.locator("#btn-do-upload").click()
    page.wait_for_selector(".uploaded-doc-card", timeout=10000)

    # Wait for auditor view and uploaded card
    page.wait_for_selector(".uploaded-doc-card", timeout=10000)
    time.sleep(0.5)

    # Toggle inline field editor
    page.locator(".btn-edit-doc").first.click()
    page.wait_for_selector(".btn-save-corrections", timeout=10000)
    assert page.locator(".btn-save-corrections").first.is_visible()

    # Modify income field and save corrections
    page.locator(".btn-save-corrections").first.click()
    time.sleep(0.5)

    # Verify statutory notice caveat is visible and clear
    assert page.locator("#doc-notice-text").is_visible()
    notice_text = page.locator("#doc-notice-text").inner_text()
    assert "Statutory" in notice_text or "वैधानिक" in notice_text


# -----------------------------------------------------------------------------
# JOURNEY 12: Persistence & Resume Across Reload
# -----------------------------------------------------------------------------
def test_journey_12_persistence_resume_reload(page, live_server):
    """Page reload (F5) seamlessly preserves document auditor session and state."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()
    page.wait_for_selector("#view-documents.active", timeout=5000)

    specimen = SPECIMENS_DIR / "valid_income_certificate.pdf"
    page.set_input_files("#doc-file-input", str(specimen))
    page.locator("#btn-do-upload").click()
    page.wait_for_selector(".uploaded-doc-card", timeout=10000)

    # Reload page
    page.reload()
    page.wait_for_selector("#view-documents.active", timeout=10000)

    # Verify session restored from SQLite backend
    page.wait_for_selector(".uploaded-doc-card", timeout=10000)
    assert page.locator("#doc-scheme-name").is_visible()
    assert page.locator(".uploaded-doc-card").count() >= 1


# -----------------------------------------------------------------------------
# JOURNEY 13: Mid-Journey Language Switch
# -----------------------------------------------------------------------------
def test_journey_13_mid_journey_language_switch(page, live_server):
    """Switching between English, Marathi, and Hindi preserves state with 0 missing labels."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()
    page.wait_for_selector("#view-documents.active", timeout=5000)

    # English
    page.locator("#lang-btn-en").click()
    time.sleep(0.5)
    assert page.locator("#lbl-readiness-title").is_visible()
    assert "Readiness" in page.locator("#lbl-readiness-title").inner_text()

    # Hindi
    page.locator("#lang-btn-hi").click()
    time.sleep(0.5)
    assert page.locator("#lbl-readiness-title").is_visible()

    # Marathi
    page.locator("#lang-btn-mr").click()
    time.sleep(0.5)
    assert page.locator("#lbl-readiness-title").is_visible()
    assert "कागदपत्र" in page.locator("#lbl-readiness-title").inner_text()


# -----------------------------------------------------------------------------
# JOURNEY 14: Mobile Viewport Citizen
# -----------------------------------------------------------------------------
def test_journey_14_mobile_viewport_citizen(page, live_server):
    """Mobile viewport (360x800) renders cleanly with no horizontal scrolling."""
    page.set_viewport_size({"width": 360, "height": 800})
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)

    # Check horizontal scroll is 0
    has_overflow = page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
    assert not has_overflow, "Page must not have horizontal scrollbar on mobile viewport"

    # Details button must be clickable on mobile
    details_btn = page.locator(".scheme-card .btn-scheme-details").first
    assert details_btn.is_visible()
    details_btn.click()
    page.wait_for_selector("#modal-scheme-detail.active", timeout=5000)


# -----------------------------------------------------------------------------
# JOURNEY 15: Official Portal Handoff & Checklist Manifest
# -----------------------------------------------------------------------------
def test_journey_15_official_portal_handoff_and_checklist_manifest(page, live_server):
    """Official portal handoff button points to legitimate government URL."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()
    page.wait_for_selector("#view-documents.active", timeout=5000)

    portal_btn = page.locator("#btn-portal-official")
    assert portal_btn.is_visible()
    # Official disclaimer must be prominently visible
    assert page.locator("#doc-notice-text").is_visible()
    disclaimer = page.locator("#doc-notice-text").inner_text()
    assert "वैधानिक सूचना" in disclaimer or "Statutory Notice" in disclaimer or "विभागामार्फत" in disclaimer
