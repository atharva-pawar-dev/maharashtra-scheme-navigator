"""Comprehensive Trilingual Parity Tests (English, Marathi, Hindi).

Verifies:
1. Static i18n dictionary completeness and symmetry across EN, MR, HI.
2. Backend document preparation & audit engine trilingual localized notices.
3. Playwright browser citizen experience trilingual parity and state preservation across EN, MR, HI.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import socket
import threading
import time

import pytest
import uvicorn
from playwright.sync_api import sync_playwright

from scheme_navigator.api.main import app
from scheme_navigator.domain.models import (
    CitizenProfile,
    ExtractedDocument,
    Language,
    RuleNode,
    Scheme,
    SourceReference,
)
from scheme_navigator.services.document_prep import (
    get_scheme_document_requirements,
    prepare_intelligent_document_audit,
)


# -----------------------------------------------------------------------------
# 1. DICTIONARY COMPLETENESS AND SYMMETRY TESTS
# -----------------------------------------------------------------------------
def test_static_i18n_page_symmetry():
    """Verify that all 112 keys in English have corresponding Marathi and Hindi entries."""
    html_path = Path(__file__).resolve().parents[1] / "static" / "index.html"
    assert html_path.exists(), "static/index.html must exist"
    content = html_path.read_text(encoding="utf-8")

    # Extract I18N_PAGE object
    match = re.search(r"const\s+I18N_PAGE\s*=\s*(\{.+?\n\s*\});", content, re.DOTALL)
    assert match is not None, "I18N_PAGE dictionary must exist in static/index.html"
    i18n_block = match.group(1)

    # Extract keys per language using multiline start
    langs = {}
    for lang in ["en", "mr", "hi"]:
        lang_match = re.search(rf"\b{lang}\s*:\s*\{{(.+?)\n\s*\}}(?:,|\s*}})", i18n_block, re.DOTALL)
        assert lang_match is not None, f"Language block for '{lang}' must exist"
        keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+)\s*:", lang_match.group(1), re.MULTILINE))
        langs[lang] = keys

    assert len(langs["en"]) >= 100, f"Expected >=100 keys, got {len(langs['en'])}"
    assert len(langs["mr"]) >= 100, f"Expected >=100 keys, got {len(langs['mr'])}"
    assert len(langs["hi"]) >= 100, f"Expected >=100 keys, got {len(langs['hi'])}"

    # Check for perfect key symmetry across all three languages
    missing_in_mr = langs["en"] - langs["mr"]
    missing_in_hi = langs["en"] - langs["hi"]
    surplus_in_mr = langs["mr"] - langs["en"]
    surplus_in_hi = langs["hi"] - langs["en"]

    assert not missing_in_mr, f"Missing Marathi translation keys: {missing_in_mr}"
    assert not missing_in_hi, f"Missing Hindi translation keys: {missing_in_hi}"
    assert not surplus_in_mr, f"Unexpected Marathi translation keys: {surplus_in_mr}"
    assert not surplus_in_hi, f"Unexpected Hindi translation keys: {surplus_in_hi}"


# -----------------------------------------------------------------------------
# 2. BACKEND LOCALIZED NOTICES AND AUDIT MESSAGES
# -----------------------------------------------------------------------------
def _make_dummy_scheme(scheme_id: str = "candidate-sanjay-gandhi-niradhar-anudan") -> Scheme:
    excerpt = "Official statutory guidelines for Sanjay Gandhi Niradhar Anudan Yojana."
    h = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
    req_data = get_scheme_document_requirements("MHA-S-0001")
    return Scheme(
        scheme_id=scheme_id,
        name="Sanjay Gandhi Niradhar Anudan Yojana",
        department="Social Justice and Special Assistance",
        summary="Statutory pension assistance",
        required_documents=[r["document_name"] for r in req_data.get("requirements", [])],
        eligibility_rule=RuleNode(
            op="all",
            children=[RuleNode(op="gte", field="age", value=18, condition_id="c_dummy_age")],
        ),
        sources=[
            SourceReference(
                source_name="Maharashtra Gazette",
                source_url="https://maharashtra.gov.in/gazette",
                source_kind="official_scheme_page",
                retrieved_at=datetime.now(timezone.utc),
                evidence_excerpt=excerpt,
                evidence_sha256=h,
            )
        ],
    )


def test_prepare_audit_trilingual_readiness():
    """Verify that prepare_intelligent_document_audit returns localized notices in requested language."""
    scheme_obj = _make_dummy_scheme()

    # Add expired document under 24-hr retention ceiling
    doc_expired = ExtractedDocument(
        document_id="purged_doc_expired_trilingual",
        document_type="income_certificate",
        person_name="Sunita Ramesh Patil",
        confidence=0.95,
        source_file_sha256="c" * 64,
        extraction_notes=["purged_expired under 24h retention ceiling"],
    )

    # 1. Test English audit
    report_en = prepare_intelligent_document_audit(
        scheme=scheme_obj,
        extracted_documents=[doc_expired],
        scheme_id="MHA-S-0001",
        language=Language.EN,
    )
    assert report_en.readiness_percentage == 0
    inc_req_en = next(r for r in report_en.requirements if r.matched_document_type == "income_certificate")
    assert "24-hour privacy retention ceiling" in inc_req_en.explanation

    # 2. Test Marathi audit
    report_mr = prepare_intelligent_document_audit(
        scheme=scheme_obj,
        extracted_documents=[doc_expired],
        scheme_id="MHA-S-0001",
        language=Language.MR,
    )
    assert report_mr.readiness_percentage == 0
    inc_req_mr = next(r for r in report_mr.requirements if r.matched_document_type == "income_certificate")
    assert "२४ तासांच्या गोपनीयता मर्यादा" in inc_req_mr.explanation

    # 3. Test Hindi audit
    report_hi = prepare_intelligent_document_audit(
        scheme=scheme_obj,
        extracted_documents=[doc_expired],
        scheme_id="MHA-S-0001",
        language=Language.HI,
    )
    assert report_hi.readiness_percentage == 0
    inc_req_hi = next(r for r in report_hi.requirements if r.matched_document_type == "income_certificate")
    assert "२४ घंटे की गोपनीयता समयसीमा" in inc_req_hi.explanation


# -----------------------------------------------------------------------------
# 3. PLAYWRIGHT BROWSER CITIZEN JOURNEY TRILINGUAL PARITY
# -----------------------------------------------------------------------------
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


def test_browser_trilingual_navigation_and_language_switching(page, live_server):
    """Test comprehensive trilingual switching across Home, Explore, and Document Auditor."""
    # 1. Home Page language switching
    page.goto(f"{live_server}/")
    page.wait_for_selector("#view-home.active", timeout=5000)

    # Switch to Marathi
    page.locator("#lang-btn-mr").click()
    time.sleep(0.3)
    assert "माझ्यासाठी योजना शोधा" in page.locator("#hero-cta-find").inner_text()
    assert "योजना ग्रंथालय पहा" in page.locator("#hero-cta-explore").inner_text()
    assert "माझी प्रगती" in page.locator("#nav-btn-prepare").inner_text()

    # Switch to Hindi
    page.locator("#lang-btn-hi").click()
    time.sleep(0.3)
    assert "मेरे लिए योजनाएं खोजें" in page.locator("#hero-cta-find").inner_text()
    assert "योजना पुस्तकालय देखें" in page.locator("#hero-cta-explore").inner_text()
    assert "मेरी प्रगति" in page.locator("#nav-btn-prepare").inner_text()

    # Switch to English
    page.locator("#lang-btn-en").click()
    time.sleep(0.3)
    assert "Find Schemes for Me" in page.locator("#hero-cta-find").inner_text()
    assert "Explore Scheme Library" in page.locator("#hero-cta-explore").inner_text()
    assert "My Progress" in page.locator("#nav-btn-prepare").inner_text()

    # 2. Explore Page trilingual navigation
    page.locator("#hero-cta-explore").click()
    page.wait_for_selector(".scheme-card", timeout=10000)
    assert page.locator(".scheme-card").count() > 0

    # Open first scheme detail modal
    page.locator(".scheme-card .btn-scheme-details").first.click()
    page.wait_for_selector("#btn-modal-check-docs", timeout=10000).click()

    # 3. Document Auditor view trilingual verification
    page.wait_for_selector("#view-documents.active", timeout=5000)

    # English
    page.locator("#lang-btn-en").click()
    time.sleep(0.3)
    assert "Readiness" in page.locator("#lbl-readiness-title").inner_text()

    # Marathi
    page.locator("#lang-btn-mr").click()
    time.sleep(0.3)
    assert "कागदपत्र" in page.locator("#lbl-readiness-title").inner_text()

    # Hindi
    page.locator("#lang-btn-hi").click()
    time.sleep(0.3)
    assert page.locator("#lbl-readiness-title").is_visible()
