"""Playwright Browser Test for Public Scheme Issue / Error Reporting Flow.

Enforces Invariant I-17, I-18, and Section 22.6:
Citizen clicks 'Report Issue' on a scheme detail modal, submits structured feedback,
and verifies audit logging and ticket generation in the real browser.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

from scheme_navigator.api.main import app
import uvicorn
import socket
import threading
import time


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def running_server():
    port = _find_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()

    # Wait for server ready
    timeout = 10.0
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.1)

    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    t.join(timeout=2.0)


def test_public_scheme_issue_reporting_in_browser(running_server: str):
    reports_file = Path(__file__).resolve().parents[1] / "data" / "citizen_reports.jsonl"
    initial_count = 0
    if reports_file.exists():
        initial_count = len([line for line in reports_file.read_text(encoding="utf-8").splitlines() if line.strip()])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{running_server}/explore")
        page.wait_for_selector(".scheme-card", timeout=10000)

        # Open details for the first scheme
        first_details_btn = page.locator(".btn-scheme-details").first
        first_details_btn.click()
        page.wait_for_selector("#modal-scheme-detail.active", timeout=5000)

        # Click Report Issue button
        report_btn = page.locator("#btn-modal-report-issue")
        assert report_btn.is_visible()
        report_btn.click()

        # Verify Report modal is active
        page.wait_for_selector("#modal-report-issue.active", timeout=5000)

        # Fill in report details
        page.select_option("#report-issue-type", "incorrect_criteria")
        page.fill("#report-description", "E2E Playwright audit test: Sourced criterion income threshold is verified against GR 2024.")
        page.fill("#report-contact", "citizen.test@maharashtra.gov.in")

        # Submit
        page.click("#btn-submit-report")

        # Verify status displays ticket ID
        page.wait_for_selector("#report-result-status div", timeout=5000)
        status_text = page.locator("#report-result-status").inner_text()
        assert "Ticket ID:" in status_text

        browser.close()

    # Verify audit persistence in data/citizen_reports.jsonl
    assert reports_file.exists(), "data/citizen_reports.jsonl must exist"
    lines = [l for l in reports_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) > initial_count, "Expected new report record in citizen_reports.jsonl"
    latest_report = json.loads(lines[-1])
    assert latest_report["issue_type"] == "incorrect_criteria"
    assert "E2E Playwright audit test" in latest_report["description"]
