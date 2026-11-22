"""TRIMURTI / MSN-DV-001 Age-Inclusion Battery (Annex C §C3 & Annex E §E4).

Automated ergonomics and accessibility tests for elderly citizens (The Aaji Test):
- Viewports: 320x568, 360x640, 390x844, 1366x768.
- Zero horizontal scroll at 320 CSS px width.
- Hard typography floors: body >= 18px (20px mobile), Devanagari line-height >= 1.7.
- Touch target sizes: all buttons >= 48x48px, primary action >= 56px tall.
- Contrast & focus ring: visible focus ring >= 3px.
- Dynamic text zoom (A, A+, A++) reflow without horizontal overflow.
- Trilingual switching (EN, MR, HI).
- Read-aloud interaction and assisted mode toggle.
"""

from __future__ import annotations

from pathlib import Path
import pytest
from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GALLERY_HTML = (REPO_ROOT / "static" / "dv_gallery.html").as_posix()
GALLERY_URL = f"file:///{GALLERY_HTML}"


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


VIEWPORTS = [
    {"name": "iPhone 5/SE (320px)", "width": 320, "height": 568, "is_mobile": True},
    {"name": "Standard Android (360px)", "width": 360, "height": 640, "is_mobile": True},
    {"name": "Modern Mobile (390px)", "width": 390, "height": 844, "is_mobile": True},
    {"name": "Desktop (1366px)", "width": 1366, "height": 768, "is_mobile": False},
]


@pytest.mark.parametrize("vp", VIEWPORTS, ids=[v["name"] for v in VIEWPORTS])
def test_no_horizontal_scroll_and_typography_across_viewports(page: Page, vp: dict):
    """Assert no horizontal overflow and verify font size floors across all target viewports."""
    page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
    page.goto(GALLERY_URL)
    page.wait_for_selector("#gallery-title")

    # 1. Assert no horizontal scrollbar
    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")
    assert scroll_width <= client_width + 1, (
        f"Horizontal overflow detected at {vp['width']}px! scrollWidth={scroll_width}, clientWidth={client_width}"
    )

    # 2. Assert body font size floor: >= 18px (>= 20px on mobile <= 640px)
    body_font_size = page.evaluate("() => parseFloat(window.getComputedStyle(document.body).fontSize)")
    if vp["is_mobile"] and vp["width"] <= 640:
        assert body_font_size >= 20.0, f"Mobile body font size {body_font_size}px is below 20px floor!"
    else:
        assert body_font_size >= 18.0, f"Desktop body font size {body_font_size}px is below 18px floor!"


def test_touch_target_dimensions(page: Page):
    """Assert all interactive buttons meet >= 48x48px and primary button >= 56px tall."""
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(GALLERY_URL)
    page.wait_for_selector("#gallery-title")

    # Primary action button
    primary_btn = page.locator("#primary-action-btn")
    box = primary_btn.bounding_box()
    assert box is not None
    assert box["height"] >= 56.0, f"Primary button height {box['height']}px is below 56px floor!"

    # Test all visible buttons have height and width >= 48px
    buttons = page.locator(".dv-btn").all()
    assert len(buttons) >= 6
    for btn in buttons:
        bbox = btn.bounding_box()
        if bbox and bbox["width"] > 0 and bbox["height"] > 0:
            assert bbox["height"] >= 48.0 - 0.5, f"Button '{btn.inner_text()}' height {bbox['height']}px < 48px!"
            assert bbox["width"] >= 48.0 - 0.5, f"Button '{btn.inner_text()}' width {bbox['width']}px < 48px!"


def test_devanagari_line_height(page: Page):
    """Assert Devanagari line-height is >= 1.7 (matras clip below 1.7)."""
    page.goto(GALLERY_URL)
    page.wait_for_selector("#gallery-title")

    # In Marathi mode (default)
    line_height = page.evaluate("""() => {
        const title = document.getElementById('gallery-title');
        const style = window.getComputedStyle(title);
        const lh = parseFloat(style.lineHeight);
        const fs = parseFloat(style.fontSize);
        return lh / fs;
    }""")
    assert line_height >= 1.69, f"Devanagari line-height ratio {line_height:.2f} is below 1.7 floor!"


def test_focus_ring_visibility(page: Page):
    """Assert interactive buttons show a visible focus ring >= 3px."""
    page.goto(GALLERY_URL)
    primary_btn = page.locator("#primary-action-btn")
    primary_btn.focus()

    outline_width = page.evaluate("""() => {
        const btn = document.getElementById('primary-action-btn');
        const style = window.getComputedStyle(btn);
        return parseFloat(style.outlineWidth) || 0;
    }""")
    assert outline_width >= 3.0, f"Focus outline width {outline_width}px is below 3px!"


def test_text_zoom_controls_and_reflow(page: Page):
    """Assert A, A+, A++ zoom changes scale correctly and does not cause overflow at 320px."""
    page.set_viewport_size({"width": 320, "height": 568})
    page.goto(GALLERY_URL)

    # Click A++ button
    btn_zoom_max = page.locator(".dv-btn-zoom[data-zoom='1.5']")
    btn_zoom_max.click()

    zoom_val = page.evaluate("() => document.documentElement.style.getPropertyValue('--dv-text-zoom')")
    assert zoom_val == "1.5"

    # Assert layout survives without horizontal overflow even at 150% text zoom on 320px screen
    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")
    assert scroll_width <= client_width + 1, (
        f"Horizontal overflow at A++ (150% zoom)! scrollWidth={scroll_width}, clientWidth={client_width}"
    )

    # Click A button to reset
    btn_zoom_normal = page.locator(".dv-btn-zoom[data-zoom='1']")
    btn_zoom_normal.click()
    zoom_reset = page.evaluate("() => document.documentElement.style.getPropertyValue('--dv-text-zoom')")
    assert zoom_reset == "1"


def test_trilingual_switching(page: Page):
    """Assert switching between English, Marathi and Hindi works properly."""
    page.goto(GALLERY_URL)

    # 1. Switch to English
    page.locator(".dv-btn-lang[data-lang='en']").click()
    assert page.evaluate("() => document.documentElement.getAttribute('lang')") == "en"
    title_en = page.locator("#gallery-title").inner_text()
    assert "Your Papers, Ready" in title_en

    # 2. Switch to Hindi
    page.locator(".dv-btn-lang[data-lang='hi']").click()
    assert page.evaluate("() => document.documentElement.getAttribute('lang')") == "hi"
    title_hi = page.locator("#gallery-title").inner_text()
    assert "आपके दस्तावेज़, तैयार" in title_hi

    # 3. Switch back to Marathi
    page.locator(".dv-btn-lang[data-lang='mr']").click()
    assert page.evaluate("() => document.documentElement.getAttribute('lang')") == "mr"
    title_mr = page.locator("#gallery-title").inner_text()
    assert "तुमची कागदपत्रे, तयार" in title_mr


def test_assisted_mode_and_read_aloud_elements(page: Page):
    """Assert assisted mode toggles and read-aloud buttons are interactive."""
    page.goto(GALLERY_URL)

    # Test assisted mode toggle
    banner = page.locator("#dv-assisted-banner")
    assert not banner.is_visible()

    toggle_btn = page.locator("#dv-toggle-assisted")
    toggle_btn.click()
    assert banner.is_visible()

    toggle_btn.click()
    assert not banner.is_visible()

    # Read-aloud buttons
    read_buttons = page.locator(".dv-read-aloud-btn").all()
    assert len(read_buttons) >= 4
    # Clicking should not throw any unhandled error
    read_buttons[0].click()
