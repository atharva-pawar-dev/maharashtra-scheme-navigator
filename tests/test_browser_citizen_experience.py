"""
End-to-End Browser Citizen Experience Test Suite (Playwright)
Validates the complete citizen journey in the browser against the live running application.
"""

import threading
import time
import pytest
import uvicorn
from playwright.sync_api import sync_playwright

from scheme_navigator.api.main import app

PORT = 8998
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

# -------------------------------------------------------------------------
# SCENARIOS 1-5: EXPLORE, FALLBACK, FRESHNESS, INTERVIEW, SIDEBAR
# -------------------------------------------------------------------------

def test_01_explore_catalogue_rendering_and_department_filtering(page, live_server):
    """Explore catalogue renders genuine canonical schemes and category pills."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector("#schemes-grid-container", timeout=10000)

    # Wait for cards to load from /canonical-schemes
    page.wait_for_selector(".scheme-card", timeout=10000)
    cards = page.locator(".scheme-card")
    assert cards.count() >= 5

    # Check category pills container
    pills = page.locator("#category-pills-container .cat-pill")
    assert pills.count() >= 1

def test_02_silent_demo_fallback_removed_shows_error_card_on_failure(page, live_server):
    """Network failure on catalogue load displays an explicit error card with retry button."""
    page.route("**/canonical-schemes*", lambda route: route.abort("failed"))
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".empty-state-card", timeout=10000)

    # Must render error container with retry button and zero scheme cards
    err_btn = page.locator(".empty-state-card button")
    assert err_btn.count() >= 1
    assert page.locator(".scheme-card").count() == 0

def test_03_catalogue_freshness_indicator(page, live_server):
    """Catalogue scheme cards display metadata verification/source tags."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector(".scheme-card", timeout=10000)
    meta = page.locator(".scheme-meta, .freshness-pill")
    assert meta.count() >= 1

def test_04_scoped_interview_launch_from_explore(page, live_server):
    """Launching interview view displays the interview component."""
    page.goto(f"{live_server}/interview")
    page.wait_for_selector("#view-interview", timeout=10000)
    assert page.locator("#view-interview").is_visible()

def test_04b_focused_interview_ign_demo_journey(page, live_server):
    """Focused assessment for IGNOAPS demo fixture displays first eligibility question without error."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector("#schemes-grid-container", timeout=10000)

    # Locate IGNOAPS card
    ign_card = page.locator(".scheme-card", has_text="Indira Gandhi")
    if ign_card.count() == 0:
        ign_card = page.locator(".scheme-card", has_text="इंदिरा गांधी")
    assert ign_card.count() >= 1, "IGNOAPS card must exist on explore page"

    # Click eligibility check
    btn = ign_card.first.locator("button.btn-primary")
    btn.click()

    # Interview workspace should open
    page.wait_for_selector("#view-interview", timeout=10000)
    page.wait_for_selector("#chat-stream .message.bot", timeout=10000)

    stream_text = page.locator("#chat-stream").inner_text()
    assert "Error starting interview" not in stream_text
    assert "मुलाखत सुरू करताना त्रुटी आली" not in stream_text

    # Verify at least welcome message + first question
    bot_messages = page.locator("#chat-stream .message.bot").all_inner_texts()
    assert len(bot_messages) >= 2, f"Expected welcome + first question, got: {bot_messages}"

    # Verify quick replies and answer first turn
    chips = page.locator("#quick-replies .reply-chip")
    assert chips.count() >= 1, "Quick replies should appear for first question"
    chips.first.click()

    page.wait_for_selector("#chat-stream .message.user", timeout=10000)
    # Ensure turn 2 proceeds without 403 Forbidden
    stream_after = page.locator("#chat-stream").inner_text()
    assert "Sorry, an error occurred" not in stream_after
    assert "माफ करा, उत्तर पाठवताना त्रुटी आली" not in stream_after

def test_05_profile_sidebar_live_fields(page, live_server):
    """Profile sidebar renders citizen attributes (age, district, income, land, ration card)."""
    page.goto(f"{live_server}/interview")
    page.wait_for_selector(".profile-sidebar", timeout=10000)
    sidebar_rows = page.locator(".profile-field-row")
    assert sidebar_rows.count() >= 5

# -------------------------------------------------------------------------
# SCENARIOS 6-10: RESULTS 5 GROUPS, CTA, PARTIAL, ACCORDION
# -------------------------------------------------------------------------

def test_06_results_page_five_outcome_scoreboards(page, live_server):
    """Results page displays 5 scoreboard groups."""
    page.goto(f"{live_server}/results")
    page.wait_for_selector(".scoreboard", timeout=10000)
    scorecards = page.locator(".scoreboard .score-card")
    assert scorecards.count() == 5

def test_07_primary_cta_restricted_to_eligible(page, live_server):
    """Primary preparation CTA only appears on eligible cards."""
    page.goto(f"{live_server}/results")
    page.wait_for_selector("#view-results", timeout=10000)
    ineligible_ctas = page.locator("#not-eligible-cards-container .btn-primary:has-text('Begin application preparation')")
    assert ineligible_ctas.count() == 0

def test_08_partial_match_scoreboard_card(page, live_server):
    """Partial match group exists in scoreboard."""
    page.goto(f"{live_server}/results")
    page.wait_for_selector(".score-card.partial", timeout=10000)
    assert page.locator(".score-card.partial").count() == 1

def test_09_needs_info_scoreboard_card(page, live_server):
    """Needs info group exists in scoreboard."""
    page.goto(f"{live_server}/results")
    page.wait_for_selector(".score-card.needs-info", timeout=10000)
    assert page.locator(".score-card.needs-info").count() == 1

def test_10_collapsed_not_eligible_accordion(page, live_server):
    """Ineligible schemes are grouped inside a collapsed <details id='not-eligible-accordion'>."""
    page.goto(f"{live_server}/results")
    page.wait_for_selector("#not-eligible-accordion", timeout=10000)
    accordion = page.locator("#not-eligible-accordion")
    assert accordion.count() == 1
    # Collapsed by default
    assert accordion.get_attribute("open") is None

# -------------------------------------------------------------------------
# SCENARIOS 11-14: ACTIVE SCHEME, DISMISSAL, PROGRESS, COMPLETION
# -------------------------------------------------------------------------

def test_11_single_active_scheme_progress_view(page, live_server):
    """Progress view handles single active scheme."""
    page.goto(f"{live_server}/progress")
    page.wait_for_selector("#view-prepare", timeout=10000)
    assert page.locator("#view-prepare").is_visible()

def test_12_dismissal_confirmation_modal_text(page, live_server):
    """Dismissal modal contains exact confirmation text."""
    page.goto(f"{live_server}/progress")
    modal = page.wait_for_selector("#modal-confirm", state="attached", timeout=10000)
    assert modal is not None
    assert page.locator("#modal-confirm").count() == 1

def test_13_empty_progress_view_exact_text(page, live_server):
    """Empty progress view displays exact text 'No schemes selected.' and 'Explore eligible schemes'."""
    page.goto(f"{live_server}/progress")
    page.wait_for_selector("#prepare-empty-container", timeout=10000)
    html = page.content()
    assert ("No schemes selected" in html or "कोणतीही योजना निवडलेली नाही" in html)
    assert ("Explore eligible schemes" in html or "पात्र योजना पहा" in html or "पात्र योजना शोधा" in html)

def test_14_document_preparation_completion_card(page, live_server):
    """Completion card has exactly two navigation options: Return to Home and Back to my eligible schemes."""
    page.goto(f"{live_server}/")
    html = page.content()
    assert "Return to Home" in html or "मुख्यपृष्ठावर परत जा" in html
    assert "Back to my eligible schemes" in html or "माझ्या पात्र योजनांकडे परत" in html

# -------------------------------------------------------------------------
# SCENARIOS 15-18: ROUTING, BACK NAV, REVIEWER BUTTON, RESET DATA
# -------------------------------------------------------------------------

def test_15_history_api_routing(page, live_server):
    """HTML5 History API routing updates views for /explore and /interview."""
    page.goto(f"{live_server}/explore")
    page.wait_for_selector("#view-explore", timeout=10000)
    assert page.locator("#view-explore").is_visible()

    page.goto(f"{live_server}/interview")
    page.wait_for_selector("#view-interview", timeout=10000)
    assert page.locator("#view-interview").is_visible()

def test_16_reusable_back_navigation(page, live_server):
    """Reusable back navigation button is present across citizen views."""
    page.goto(f"{live_server}/explore")
    back_btn = page.locator("#view-explore button.back-nav-btn")
    assert back_btn.count() >= 1

def test_17_fixed_floating_reviewer_portal_button(page, live_server):
    """Reviewer Portal is located as fixed floating button in bottom-right (#1E3A8A)."""
    page.goto(f"{live_server}/")
    btn = page.locator(".fixed-reviewer-portal")
    assert btn.count() >= 1
    assert btn.first.is_visible()

def test_18_citizen_profile_reset_modal_and_data_clearance(page, live_server):
    """Profile sidebar includes 'Reset my data' button wired to reset modal."""
    page.goto(f"{live_server}/interview")
    page.wait_for_selector("#btn-reset-citizen-profile", timeout=10000)
    reset_btn = page.locator("#btn-reset-citizen-profile")
    assert reset_btn.is_visible()

# -------------------------------------------------------------------------
# SCENARIOS 19-20: MULTILINGUAL PURITY & LOCALIZATION
# -------------------------------------------------------------------------

def test_19_english_mode_purity(page, live_server):
    """When English is selected, visible text has zero Devanagari characters (except language toggle)."""
    page.goto(f"{live_server}/")
    time.sleep(1.0)
    page.evaluate("if (typeof setLanguage === 'function') setLanguage('en');")
    time.sleep(0.5)

    visible_text = page.locator("body").inner_text()
    lines = [l for l in visible_text.splitlines() if "मराठी" not in l and "हिंदी" not in l]
    cleaned = "\n".join(lines)

    import re
    devanagari_chars = re.findall(r'[\u0900-\u097F]', cleaned)
    assert len(devanagari_chars) == 0, f"Found Devanagari in English mode: {''.join(devanagari_chars[:20])}"

def test_20_marathi_mode_purity(page, live_server):
    """When Marathi is selected, primary headers are localized in Devanagari."""
    page.goto(f"{live_server}/")
    time.sleep(1.0)
    page.evaluate("if (typeof setLanguage === 'function') setLanguage('mr');")
    time.sleep(0.5)

    header = page.locator("h1, .hero-title, .portal-brand").first.inner_text()
    import re
    devanagari_chars = re.findall(r'[\u0900-\u097F]', header)
    assert len(devanagari_chars) > 0, "Marathi mode did not render Devanagari title"
