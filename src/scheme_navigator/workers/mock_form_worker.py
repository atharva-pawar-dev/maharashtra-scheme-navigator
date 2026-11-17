from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from scheme_navigator.core.config import settings
from scheme_navigator.domain.models import CitizenProfile

ALLOWED_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _validate_mock_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in ALLOWED_LOOPBACK_HOSTS:
        raise ValueError("Safety stop: Playwright worker only permits localhost/loopback mock forms.")
    if parsed.path.rstrip("/") != "/demo-form":
        raise ValueError("Safety stop: Playwright worker only permits the /demo-form route.")


def run(profile_path: Path, mock_url: str, screenshot_path: Path, require_human_confirmation: bool = True) -> None:
    _validate_mock_url(mock_url)
    profile = CitizenProfile.model_validate(json.loads(profile_path.read_text(encoding="utf-8")))
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()  # isolated, ephemeral context: no saved cookies or state
        page = context.new_page()
        # Defense in depth: do not allow browser requests to reach any remote host.
        def local_only(route):
            host = urlparse(route.request.url).hostname
            if host in ALLOWED_LOOPBACK_HOSTS:
                route.continue_()
            else:
                route.abort()
        page.route("**/*", local_only)
        page.goto(mock_url, wait_until="domcontentloaded", timeout=15_000)
        page.get_by_label("Applicant name").fill(profile.name or "Demo Applicant")
        if profile.age is not None:
            page.get_by_label("Age (completed years)").fill(str(profile.age))
        if profile.annual_family_income is not None:
            page.get_by_label("Family annual income (INR)").fill(str(profile.annual_family_income))
        if profile.district:
            page.get_by_label("District").fill(profile.district)
        if profile.gender:
            page.get_by_label("Gender").select_option(profile.gender)
        if profile.caste_category:
            page.get_by_label("Caste category (optional)").fill(profile.caste_category)
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"Prefill complete. Local screenshot written to: {screenshot_path}")
        print("No external network requests are allowed. Review the values in the local mock form.")
        if require_human_confirmation:
            confirmation = input("Type SIMULATE to acknowledge the mock form (anything else cancels): ").strip()
            if confirmation != "SIMULATE":
                print("Cancelled: mock form was not submitted.")
                context.close()
                browser.close()
                return
        page.get_by_role("button", name="Human-approved: simulate submission").click()
        page.get_by_text("DEMO ONLY: mock submission acknowledged locally.").wait_for(timeout=3000)
        print("Mock submission succeeded locally. No government portal was contacted or submitted to.")
        context.close()
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Human-in-the-loop Playwright worker for the local mock form only.")
    parser.add_argument("--profile", type=Path, default=Path("data/demo/citizen_profile.json"))
    parser.add_argument("--url", default=settings.mock_form_url)
    parser.add_argument("--screenshot", type=Path, default=Path("artifacts/mock-form-preview.png"))
    parser.add_argument("--no-prompt", action="store_true", help="Disallowed: present for CLI compatibility but never bypasses approval.")
    args = parser.parse_args()
    if args.no_prompt:
        raise SystemExit("Human confirmation cannot be disabled for this worker.")
    run(args.profile, args.url, args.screenshot, require_human_confirmation=True)


if __name__ == "__main__":
    main()
