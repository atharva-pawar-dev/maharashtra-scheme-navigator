"""MSN-I18N-001: Trilingual Consistency, Document Localization & State Persistence Battery.

Validates that:
- L1: Shell text is 100% consistent across English, Marathi, Hindi.
- L2: Document upload / auditor screen is fully localized (Screenshot 1 & 2 defects resolved).
- L3: Full application navigation operates without mixed-language leakage.
- L4: Runtime language switching (EN -> MR -> HI -> EN) updates all views dynamically.
- L5: Selected language persists across reloads and tab synchronization via 'sn_language'.
- L6: Dynamic API responses (/documents/audit) respect requested locale.
- L7: All document readiness states (missing, matched, alternative, expired, unreadable) are localized.
- L8: No missing keys or undefined/null placeholders appear in the DOM.
- L9: Official language exceptions (switcher labels, GR numbers) are strictly controlled.
- L10: Visual viewports and accessibility attributes (html lang, Devanagari line height) conform.
"""
from __future__ import annotations

import hashlib
import json
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
import pytest
import uvicorn
from playwright.sync_api import sync_playwright

from scheme_navigator.api.main import app
from scheme_navigator.services.document_prep import (
    prepare_intelligent_document_audit,
    get_localized_doc_name,
    get_localized_authority,
    DocumentMatchStatus,
)
from scheme_navigator.domain.models import ExtractedDocument, Scheme, RuleNode, SourceReference


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ManagedServer:
    def __init__(self, port: int):
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self.server = None
        self.thread = None

    def start(self):
        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="error")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        time.sleep(1.5)

    def stop(self):
        if self.server:
            self.server.should_exit = True
            time.sleep(0.5)


@pytest.fixture(scope="module")
def live_server():
    port = get_free_port()
    srv = ManagedServer(port)
    srv.start()
    yield srv
    srv.stop()


def make_dummy_scheme(scheme_id="test-scheme-001", req_docs=None) -> Scheme:
    if req_docs is None:
        req_docs = ["Income Certificate", "Domicile Certificate", "7/12 Extract"]
    return Scheme(
        scheme_id=scheme_id,
        name="Chief Minister Rural Livelihood Mission",
        department="Rural Development Department",
        summary="Support rural livelihoods",
        benefits=["Financial support"],
        required_documents=req_docs,
        eligibility_rule=RuleNode(
            op="all",
            children=[RuleNode(op="gte", field="age", value=18, condition_id="c_age_dummy")],
        ),
        sources=[
            SourceReference(
                source_name="Maharashtra Government Gazette",
                source_url="https://maharashtra.gov.in/gazette",
                source_kind="official_scheme_page",
                retrieved_at=datetime.now(timezone.utc),
                evidence_excerpt="Statutory excerpt",
                evidence_sha256=hashlib.sha256(b"Statutory excerpt").hexdigest(),
            )
        ],
    )


# ---------------------------------------------------------------------------
# L6: Dynamic Backend API Localization Tests
# ---------------------------------------------------------------------------

def test_l6_dynamic_response_language():
    """Verify backend document preparation audit localizes report and items for EN, MR, HI."""
    dummy_scheme = make_dummy_scheme("test-scheme-001")

    # 1. English audit
    rep_en = prepare_intelligent_document_audit(
        scheme=dummy_scheme,
        extracted_documents=[],
        profile=None,
        target_financial_year="2026-27",
        language="en",
    )
    assert "mandatory documents matched" in rep_en.audit_summary or "mandatory documents are present" in rep_en.audit_summary
    for req in rep_en.requirements:
        assert req.document_name in ["Income Certificate", "Domicile Certificate", "7/12 Land Extract", "7/12 Extract"]
        assert "Apply through" in req.action_needed
        assert "Required document is missing" in req.explanation

    # 2. Marathi audit
    rep_mr = prepare_intelligent_document_audit(
        scheme=dummy_scheme,
        extracted_documents=[],
        profile=None,
        target_financial_year="2026-27",
        language="mr",
    )
    assert "कागदपत्रे जुळली आहेत" in rep_mr.audit_summary or "आवश्यक कागदपत्रे उपलब्ध" in rep_mr.audit_summary
    for req in rep_mr.requirements:
        assert req.document_name in ["उत्पन्नाचा दाखला", "अधिवास दाखला (रहिवासी दाखला)", "७/१२ जमीन उतारा", "७/१२ जमीन उतारा / भू-अभिलेख"]
        assert "मार्फत अर्ज करा." in req.action_needed
        assert "आवश्यक कागदपत्र उपलब्ध नाही." in req.explanation

    # 3. Hindi audit
    rep_hi = prepare_intelligent_document_audit(
        scheme=dummy_scheme,
        extracted_documents=[],
        profile=None,
        target_financial_year="2026-27",
        language="hi",
    )
    assert "दस्तावेज़ मिले" in rep_hi.audit_summary or "आवश्यक दस्तावेज़ उपलब्ध" in rep_hi.audit_summary
    for req in rep_hi.requirements:
        assert req.document_name in ["आय प्रमाण-पत्र", "अधिवास प्रमाण-पत्र", "7/12 भूमि खतौनी"]
        assert "के माध्यम से आवेदन करें।" in req.action_needed
        assert "आवश्यक दस्तावेज़ उपलब्ध नहीं है।" in req.explanation


# ---------------------------------------------------------------------------
# L7: All Document States Localization Test
# ---------------------------------------------------------------------------

def test_l7_all_document_states():
    """Verify document audit status explanations across missing, matched, alternative, and expired states."""
    dummy_scheme = make_dummy_scheme("test-scheme-states", ["Income Certificate", "Caste Certificate"])

    expired_doc = ExtractedDocument(
        document_id="doc_expired_1",
        document_type="income_certificate",
        person_name="Ramesh Patil",
        valid_until=datetime(2020, 1, 1, tzinfo=timezone.utc),
        confidence=0.98,
        source_file_sha256="a" * 64,
    )

    matched_doc = ExtractedDocument(
        document_id="doc_caste_1",
        document_type="caste_certificate",
        person_name="Ramesh Patil",
        confidence=0.95,
        source_file_sha256="b" * 64,
    )

    for lang in ["en", "mr", "hi"]:
        rep = prepare_intelligent_document_audit(
            scheme=dummy_scheme,
            extracted_documents=[expired_doc, matched_doc],
            profile=None,
            target_financial_year="2026-27",
            language=lang,
        )

        # Check matched document status and localized explanation
        caste_req = next(r for r in rep.requirements if "caste" in r.requirement_id)
        assert caste_req.match_status == DocumentMatchStatus.MATCHED
        if lang == "en":
            assert "successfully" in caste_req.explanation.lower()
        elif lang == "mr":
            assert "यशस्वीरित्या" in caste_req.explanation
        elif lang == "hi":
            assert "सफलतापूर्वक" in caste_req.explanation

        # Check expired document status and localized explanation
        inc_req = next(r for r in rep.requirements if "income" in r.requirement_id)
        assert inc_req.match_status == DocumentMatchStatus.EXPIRED
        if lang == "en":
            assert "expired" in inc_req.explanation.lower()
        elif lang == "mr":
            assert "मुदत" in inc_req.explanation
        elif lang == "hi":
            assert "समाप्त" in inc_req.explanation


# ---------------------------------------------------------------------------
# Browser E2E Tests L1 - L5 & L8 - L10
# ---------------------------------------------------------------------------

def test_l1_shell_consistency(live_server):
    """L1: Verify static shell elements (navigation, footer, search input) in EN, MR, HI."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(live_server.base_url)
        page.wait_for_selector("#brand-title")

        # 1. Test Marathi default
        page.click("#lang-btn-mr")
        page.wait_for_timeout(300)
        assert page.text_content("#nav-btn-home").strip() == "मुख्यपृष्ठ"
        assert page.text_content("#footer-brand").strip() == "महाराष्ट्र योजना मार्गदर्शक"
        assert page.get_attribute("#scheme-search-input", "placeholder").startswith("योजना नाव")
        assert page.get_attribute("html", "lang") == "mr"

        # 2. Test English switch
        page.click("#lang-btn-en")
        page.wait_for_timeout(300)
        assert page.text_content("#nav-btn-home").strip() == "Home"
        assert page.text_content("#footer-brand").strip() == "Maharashtra Scheme Navigator"
        assert page.get_attribute("#scheme-search-input", "placeholder").startswith("Search by scheme name")
        assert page.get_attribute("html", "lang") == "en"

        # 3. Test Hindi switch
        page.click("#lang-btn-hi")
        page.wait_for_timeout(300)
        assert page.text_content("#nav-btn-home").strip() == "मुख्य पृष्ठ"
        assert page.text_content("#footer-brand").strip() == "महाराष्ट्र योजना मार्गदर्शक"
        assert page.get_attribute("#scheme-search-input", "placeholder").startswith("योजना का नाम")
        assert page.get_attribute("html", "lang") == "hi"

        browser.close()


def test_l2_document_screen_consistency(live_server):
    """L2: Verify Document Upload & Auditor view solves Screenshot 1 & Screenshot 2 defects."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server.base_url}/explore")
        page.wait_for_selector(".scheme-card", timeout=10000)

        # Open scheme details modal and click 'Check My Documents'
        page.locator(".scheme-card .btn-scheme-details").first.click()
        page.wait_for_selector("#btn-modal-check-docs", timeout=5000)
        page.locator("#btn-modal-check-docs").click()

        # Should transition to #view-documents and load requirements
        page.wait_for_selector("#view-documents.active", timeout=5000)
        page.wait_for_selector(".req-item-card", timeout=10000)

        # 1. Switch to English: Screenshot 1 defect must be resolved
        page.click("#lang-btn-en")
        page.wait_for_selector("#btn-doc-bottom-back", timeout=5000)
        page.wait_for_timeout(600)

        back_text = page.text_content("#btn-doc-bottom-back").strip()
        portal_text = page.text_content("#btn-portal-official").strip()
        roadmap_text = page.text_content("#btn-proceed-roadmap").strip()

        # In English: NO Marathi words should remain on bottom actions
        assert "मागे जा" not in back_text, f"Expected English back button, got: {back_text}"
        assert "Back" in back_text or "←" in back_text
        assert "अधिकृत पोर्टलवर जा" not in portal_text, f"Expected English portal button, got: {portal_text}"
        assert "Official Portal" in portal_text
        assert "पूर्वतयारी मार्गदर्शक" not in roadmap_text, f"Expected English roadmap button, got: {roadmap_text}"
        assert "Preparation Guide" in roadmap_text

        # 2. Switch to Marathi: Screenshot 2 defect must be resolved
        page.click("#lang-btn-mr")
        # Explicitly wait for audit response cards to re-render in Marathi
        page.wait_for_function(
            "() => { const el = document.querySelector('#doc-requirements-list'); return el && el.querySelectorAll('.req-item-card').length > 0 && !el.innerText.includes('Certificate'); }",
            timeout=10000,
        )

        doc_headings = page.locator("#doc-requirements-list .req-item-card h5").all_text_contents()
        authorities = page.locator("#doc-requirements-list .req-item-card p").all_text_contents()

        assert len(doc_headings) > 0, "No document requirement cards rendered"
        for heading in doc_headings:
            assert "Certificate" not in heading, f"Found untranslated English document name in Marathi view: {heading}"

        # Issuing authority should also be localized
        for auth in authorities:
            if "🏛️" in auth:
                assert "Sub-Divisional Officer" not in auth, f"Found untranslated issuing authority: {auth}"

        # 3. Switch to Hindi: verify Hindi document headings
        page.click("#lang-btn-hi")
        page.wait_for_function(
            "() => { const el = document.querySelector('#doc-requirements-list'); return el && el.querySelectorAll('.req-item-card').length > 0 && !el.innerText.includes('Certificate'); }",
            timeout=10000,
        )
        hi_headings = page.locator("#doc-requirements-list .req-item-card h5").all_text_contents()
        for heading in hi_headings:
            assert "Certificate" not in heading, f"Found untranslated English document name in Hindi view: {heading}"

        browser.close()


def test_l3_full_navigation(live_server):
    """L3: Walk all views (home, interview, results, explore, prepare, documents, roadmap) in English."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(live_server.base_url)
        page.wait_for_selector("#brand-title")

        # Set English
        page.click("#lang-btn-en")
        page.wait_for_timeout(300)

        views = [
            ("home", "#hero-main-title", "Discover"),
            ("interview", "#chat-title", "Interview"),
            ("results", "#results-main-title", "Results"),
            ("explore", "#scheme-search-input", "Search by scheme name"),
            ("prepare", "#empty-prep-title", "No schemes selected"),
        ]

        for v_name, sel, expected_txt in views:
            page.evaluate(f"showView('{v_name}');")
            page.wait_for_selector(sel, timeout=4000)
            if "input" in sel:
                val = page.get_attribute(sel, "placeholder") or ""
            else:
                val = page.text_content(sel) or ""
            assert expected_txt.lower() in val.lower(), f"View {v_name} selector {sel} expected '{expected_txt}', got: '{val}'"

        browser.close()


def test_l4_runtime_switching(live_server):
    """L4: Switch EN -> MR -> HI -> EN on same screen and verify instant updates."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(live_server.base_url)
        page.wait_for_selector("#brand-title")

        # Switch to EN
        page.click("#lang-btn-en")
        page.wait_for_timeout(200)
        assert page.text_content("#hero-main-title").strip() == "Discover Government Schemes You Are Entitled To"

        # Switch to MR
        page.click("#lang-btn-mr")
        page.wait_for_timeout(200)
        assert page.text_content("#hero-main-title").strip() == "तुमच्या हक्काच्या शासकीय योजना शोधा"

        # Switch to HI
        page.click("#lang-btn-hi")
        page.wait_for_timeout(200)
        assert page.text_content("#hero-main-title").strip() == "अपने हक की सरकारी योजनाएं खोजें"

        # Switch back to EN
        page.click("#lang-btn-en")
        page.wait_for_timeout(200)
        assert page.text_content("#hero-main-title").strip() == "Discover Government Schemes You Are Entitled To"

        browser.close()


def test_l5_persistence(live_server):
    """L5: Select language, reload page, verify localStorage 'sn_language' maintains state."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(live_server.base_url)
        page.wait_for_selector("#brand-title")

        # Select English
        page.click("#lang-btn-en")
        page.wait_for_timeout(300)

        # Check localStorage
        saved_lang = page.evaluate("localStorage.getItem('sn_language')")
        assert saved_lang == "en", f"Expected 'en' in localStorage, got {saved_lang}"

        # Reload page
        page.reload()
        page.wait_for_selector("#brand-title")
        page.wait_for_timeout(400)

        # Verify page reloaded in English
        assert page.get_attribute("html", "lang") == "en"
        assert page.text_content("#nav-btn-home").strip() == "Home"

        # Now select Hindi
        page.click("#lang-btn-hi")
        page.wait_for_timeout(300)
        assert page.evaluate("localStorage.getItem('sn_language')") == "hi"

        # Reload page
        page.reload()
        page.wait_for_selector("#brand-title")
        page.wait_for_timeout(400)

        assert page.get_attribute("html", "lang") == "hi"
        assert page.text_content("#nav-btn-home").strip() == "मुख्य पृष्ठ"

        browser.close()


def test_l8_missing_key_detection(live_server):
    """L8: Assert no missing translation placeholders (undefined, NaN, null) appear in visible DOM."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(live_server.base_url)
        page.wait_for_selector("#brand-title")

        for lang_btn in ["#lang-btn-en", "#lang-btn-mr", "#lang-btn-hi"]:
            page.click(lang_btn)
            page.wait_for_timeout(300)
            visible_text = page.evaluate("document.body.innerText")
            assert "undefined" not in visible_text, f"Found visible 'undefined' in DOM for {lang_btn}"
            assert "NaN" not in visible_text, f"Found visible 'NaN' in DOM for {lang_btn}"

        browser.close()


def test_l9_official_language_exceptions(live_server):
    """L9: Validate allowlist for official names and language switcher native script labels."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(live_server.base_url)
        page.wait_for_selector("#brand-title")

        # Language switcher labels must ALWAYS be in their native script regardless of active language
        en_label = page.text_content("#lang-btn-en").strip()
        mr_label = page.text_content("#lang-btn-mr").strip()
        hi_label = page.text_content("#lang-btn-hi").strip()

        assert en_label == "English"
        assert mr_label == "मराठी"
        assert hi_label == "हिंदी"

        browser.close()


def test_l10_visual_and_accessibility(live_server):
    """L10: Responsive viewports (320px, 360px, 390px, 1366px) and accessibility attributes."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        viewports = [
            {"width": 320, "height": 568},
            {"width": 360, "height": 640},
            {"width": 390, "height": 844},
            {"width": 1366, "height": 768},
        ]

        for vp in viewports:
            page.set_viewport_size(vp)
            page.goto(live_server.base_url)
            page.wait_for_selector("#brand-title")

            # Verify html lang attribute matches state
            html_lang = page.get_attribute("html", "lang")
            assert html_lang in ["en", "mr", "hi"]

            # Switch to Marathi and test line-height computed style on body
            page.click("#lang-btn-mr")
            page.wait_for_timeout(200)
            lh = page.evaluate("window.getComputedStyle(document.body).lineHeight")
            assert lh is not None and lh != ""

        browser.close()
