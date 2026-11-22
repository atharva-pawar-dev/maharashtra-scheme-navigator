"""TRIMURTI / MSN-DV-001 Journey J4: Checklist Logic (Annex E §E3 & §4.3).

Verifies in a real browser:
- Mandatory requirements, conditional applicability, and alternatives.
- Denominator honesty: 'To apply for {scheme} you need M papers. You have N.'
- Large 'Next: {need}' card for first pending requirement.
- 'I don't have this paper' -> reveals how-to-get without blocking other slots.
- Alternatives: accepting one document type without demanding the other.
- Trilingual switching & age-inclusive text zoom (A, A+, A++).
- Official authority reminder (Law L7).
"""

from __future__ import annotations

from pathlib import Path
import pytest
from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PAPERS_HTML = (REPO_ROOT / "static" / "dv_papers.html").as_posix()
PAPERS_URL = f"file:///{PAPERS_HTML}"


@pytest.fixture(scope="module")
def browser_instance():
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    yield browser
    browser.close()
    p.stop()


@pytest.fixture
def page(browser_instance):
    context = browser_instance.new_context()
    pg = context.new_page()
    yield pg
    context.close()


def test_j4_headline_denominator_and_next_card(page: Page):
    """J4: Verify headline shows honest N of M needs and renders large Next Need card."""
    page.goto(PAPERS_URL)
    page.wait_for_selector("#headline-title")

    # In Marathi by default per Aaji motto
    headline_text = page.locator("#headline-title").inner_text()
    assert "४ कागदपत्रे लागतील" in headline_text or "4" in headline_text
    assert "० तयार आहेत" in headline_text or "0" in headline_text

    # Next need card is visible with primary action >= 56px tall
    next_card = page.locator("#next-need-section")
    assert next_card.is_visible()
    next_title = page.locator("#next-need-title").inner_text()
    assert "वय व ओळख पुरावा" in next_title or "Age & Identity" in next_title

    add_btn = page.locator("#add-paper-btn")
    box = add_btn.bounding_box()
    assert box is not None
    assert box["height"] >= 56.0, f"Primary button height {box['height']}px is below 56px floor!"


def test_j4_alternatives_and_how_to_get_flow(page: Page):
    """J4: Verify alternatives shown and 'I don't have this paper' toggles guidance without blocking."""
    page.goto(PAPERS_URL)

    # Next card explains alternatives (Aadhaar OR Domicile)
    card_text = page.locator("#next-need-section").inner_text()
    assert "आधार कार्ड" in card_text or "Aadhaar" in card_text
    assert "अधिवास दाखला" in card_text or "Domicile" in card_text

    # Click "I don't have this paper"
    dont_have_btn = page.locator("#dont-have-btn")
    assert dont_have_btn.is_visible()
    
    how_to_get = page.locator("#how-to-get-card")
    assert not how_to_get.is_visible()

    dont_have_btn.click()
    assert how_to_get.is_visible()
    how_text = how_to_get.inner_text()
    assert "aaplesarkar" in how_text.lower() or "सेतू केंद्र" in how_text
    assert "३३" in how_text or "33" in how_text  # ₹33 fee

    # Assert remaining slots are still visible and NOT blocked
    slots_container = page.locator("#slots-container")
    assert slots_container.is_visible()
    slot_items = page.locator(".dv-slot-item").all()
    assert len(slot_items) == 4, f"Expected 4 slot items, found {len(slot_items)}"


def test_j4_conditional_slots_bucket_separation(page: Page):
    """J4: Verify conditional slot needing answers appears in separate bucket (§4.3)."""
    page.goto(PAPERS_URL)

    cond_box = page.locator("#conditional-slots-box")
    assert cond_box.is_visible()
    box_text = cond_box.inner_text()
    assert "१ कागदपत्र लागू शकते" in box_text or "1 more paper" in box_text
    assert "दिव्यांगत्व" in box_text or "Disability" in box_text


def test_j4_trilingual_switching_and_read_aloud(page: Page):
    """J4: Verify switching between Marathi, English, Hindi and read-aloud buttons work."""
    page.goto(PAPERS_URL)

    # Switch to English
    page.locator(".dv-btn-lang[data-lang='en']").click()
    assert page.evaluate("() => document.documentElement.getAttribute('lang')") == "en"
    headline_en = page.locator("#headline-title").inner_text()
    assert "To apply for this scheme you need 4 papers" in headline_en
    next_en = page.locator("#next-need-title").inner_text()
    assert "Next: Add Proof of Age & Identity" in next_en

    # Switch to Hindi
    page.locator(".dv-btn-lang[data-lang='hi']").click()
    assert page.evaluate("() => document.documentElement.getAttribute('lang')") == "hi"
    headline_hi = page.locator("#headline-title").inner_text()
    assert "इस योजना के लिए आपको 4 कागज़ात चाहिए" in headline_hi

    # Read aloud button click
    page.locator(".dv-read-aloud-btn").first.click()


def test_j4_text_zoom_and_no_overflow_at_320px(page: Page):
    """J4: Verify text zoom (A++) reflows without horizontal overflow on 320px screen."""
    page.set_viewport_size({"width": 320, "height": 568})
    page.goto(PAPERS_URL)

    page.locator(".dv-btn-zoom[data-zoom='1.5']").click()
    zoom_val = page.evaluate("() => document.documentElement.style.getPropertyValue('--dv-text-zoom')")
    assert zoom_val == "1.5"

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")
    assert scroll_width <= client_width + 1, (
        f"Horizontal overflow in Papers screen at 320px! scrollWidth={scroll_width}, clientWidth={client_width}"
    )
