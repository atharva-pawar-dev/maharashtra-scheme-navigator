"""Real Playwright Browser E2E Test: Backend Restart & Document Replacement Durability.

Proves:
1. User interacts in real browser (select scheme -> upload doc -> replace doc).
2. Document replacement creates v2, preserving v1 as superseded in SQLite.
3. Server is completely stopped.
4. Browser sessionStorage is cleared.
5. Server is restarted.
6. Browser reloads and recovers full state authoritatively from SQLite.
7. Screenshots and SQLite evidence captured.
"""
from __future__ import annotations

import os
import socket
import sqlite3
import threading
import time
from pathlib import Path
import pytest
import uvicorn
from playwright.sync_api import sync_playwright

from scheme_navigator.api.main import app

SPECIMENS_DIR = Path(__file__).resolve().parent / "fixtures" / "specimens"
SCREENSHOTS_DIR = Path(__file__).resolve().parents[1] / "reports" / "evidence_screenshots"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DB_PATH = DATA_DIR / "citizen_profiles.sqlite3"


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
            if self.thread:
                self.thread.join(timeout=4)
            time.sleep(0.5)


def test_browser_restart_durability_and_document_replacement():
    os.environ["ENABLE_LOCAL_FALLBACK_OCR"] = "true"
    os.environ["SCHEME_NAVIGATOR_AUTH_SECRET"] = "fixed_test_secret_for_restart_durability_32bytes!"
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    port = get_free_port()

    # Phase 1: Start Server 1
    srv = ManagedServer(port)
    srv.start()

    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.on("console", lambda msg: print(f"BROWSER LOG: {msg.type}: {msg.text}"))
    page.on("pageerror", lambda exc: print(f"BROWSER ERROR: {exc}"))
    page.on("response", lambda res: print(f"NET: {res.status} {res.url}") if "/documents" in res.url or "/canonical-schemes" in res.url else None)

    try:
        # 1. Visit Explore and open Document Auditor for candidate-majhi-ladki-bahin
        page.goto(f"{srv.base_url}/explore")
        page.wait_for_selector(".scheme-card", timeout=10000)

        # Navigate directly to the scheme workspace documents
        page.goto(f"{srv.base_url}/workspace/candidate-majhi-ladki-bahin/documents")
        page.wait_for_selector("#doc-file-input", timeout=10000)

        # 2. Upload expired document (v1)
        expired_doc_path = SPECIMENS_DIR / "expired_income_certificate.pdf"
        assert expired_doc_path.is_file()

        file_input = page.locator("#doc-file-input")
        file_input.set_input_files(str(expired_doc_path))
        page.locator("#btn-do-upload").click()

        # Wait for document to be uploaded and audited
        page.wait_for_selector(".uploaded-doc-card", timeout=10000)
        assert page.locator(".uploaded-doc-card").count() >= 1

        # 3. Replace document with valid income certificate (v2)
        valid_doc_path = SPECIMENS_DIR / "valid_income_certificate.pdf"
        assert valid_doc_path.is_file()

        # Click the replace button on the uploaded document
        replace_btn = page.locator(".btn-replace-doc").first
        replace_btn.click()

        # Set the valid file on the input and click upload
        file_input.set_input_files(str(valid_doc_path))
        page.locator("#btn-do-upload").click()

        # Wait for audit update
        page.wait_for_selector(".badge:has-text('v2 (Active)')", timeout=10000)

        # Verify Document History section displays superseded v1 record
        page.wait_for_selector("#doc-history-section", timeout=10000)
        assert page.locator("#doc-history-section").is_visible()
        assert page.locator(".history-doc-card").count() >= 1
        assert page.locator(".badge:has-text('v1 (Superseded)')").is_visible()

        # Capture evidence screenshot before restart
        screen_1 = SCREENSHOTS_DIR / "01_before_restart_replacement.png"
        page.screenshot(path=str(screen_1))
        assert screen_1.is_file()

        # 4. Verify SQLite state before restart for this exact citizen session
        cookies = context.cookies()
        sn_cookie = next((c for c in cookies if c["name"] in ("sn_session", "__Host-sn_session")), None)
        assert sn_cookie is not None, "Browser must have received sn_session cookie"
        current_session_id = sn_cookie["value"].split(":")[0]

        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM citizen_scheme_documents WHERE session_id = ? AND scheme_id = 'candidate-majhi-ladki-bahin' ORDER BY version ASC",
                (current_session_id,),
            ).fetchall()
            assert len(rows) >= 2, "Must have at least v1 and v2 records in SQLite"
            assert rows[0]["status"] == "superseded"
            assert rows[0]["version"] == 1
            assert rows[0]["superseded_by"] == rows[1]["document_id"]
            assert rows[1]["status"] == "active"
            assert rows[1]["version"] == 2

        # 5. STOP BACKEND COMPLETELY
        srv.stop()

        # 6. CLEAR BROWSER SESSIONSTORAGE COMPLETELY (simulate fresh page revisit)
        page.evaluate("() => { sessionStorage.clear(); localStorage.clear(); }")

        # 7. RESTART BACKEND ON SAME PORT
        srv2 = ManagedServer(port)
        srv2.start()

        # 8. Reload page in browser
        page.reload()
        page.wait_for_selector("#doc-file-input", timeout=10000)

        # 9. Verify state is 100% restored from SQLite:
        # Active v2 document must be visible
        page.wait_for_selector(".uploaded-doc-card", timeout=10000)
        assert page.locator(".badge:has-text('v2 (Active)')").is_visible(), "Active v2 document must be restored from SQLite"

        # Superseded v1 document must be visible in history
        page.wait_for_selector("#doc-history-section", timeout=10000)
        assert page.locator(".badge:has-text('v1 (Superseded)')").is_visible(), "Superseded v1 document must be restored from SQLite"

        # Capture evidence screenshot after restart
        screen_2 = SCREENSHOTS_DIR / "02_after_restart_restored_from_sqlite.png"
        page.screenshot(path=str(screen_2))
        assert screen_2.is_file()

        srv2.stop()

    finally:
        context.close()
        browser.close()
        p.stop()
