import asyncio
import json
import os
from playwright.async_api import async_playwright

async def run():
    os.makedirs("artifacts/screenshots", exist_ok=True)
    console_logs = []
    failed_requests = []
    api_responses = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.method} {req.url} - {req.failure}"))
        async def on_response(res):
            if "/eligibility/" in res.url or "/canonical-schemes" in res.url:
                api_responses.append(f"{res.status} {res.url}")
        page.on("response", on_response)

        print("Navigating to http://127.0.0.1:8000/results ...")
        await page.goto("http://127.0.0.1:8000/results", wait_until="networkidle")

        # Call triggerEvaluationFromProfile to evaluate schemes against citizen profile
        print("Triggering evaluation from profile...")
        await page.evaluate("window.triggerEvaluationFromProfile()")
        await page.wait_for_timeout(3000)

        # Count cards in #results-cards-container
        results_cards = await page.locator("#results-cards-container .scheme-card").count()
        print(f"Results cards container count: {results_cards}")

        # Check scoreboard
        c_eligible = await page.locator("#count-eligible").inner_text()
        c_partial = await page.locator("#count-partial").inner_text()
        c_moreinfo = await page.locator("#count-moreinfo").inner_text()
        c_review = await page.locator("#count-review").inner_text()
        c_rejected = await page.locator("#count-rejected").inner_text()
        print(f"Scoreboard counts: Eligible={c_eligible}, Partial={c_partial}, NeedsInfo={c_moreinfo}, Review={c_review}, Ineligible={c_rejected}")

        # Inspect first 5 cards in #results-cards-container
        cards_detail = []
        for i in range(min(5, results_cards)):
            card = page.locator("#results-cards-container .scheme-card").nth(i)
            title = await card.locator("h4").inner_text()
            badges = await card.locator(".scheme-badge").all_inner_texts()
            buttons = await card.locator("button").all_inner_texts()
            footer_html = await card.locator(".scheme-card-footer").inner_html()
            cards_detail.append({
                "index": i,
                "title": title,
                "badges": badges,
                "buttons": buttons,
                "footer": footer_html.strip()
            })

        print("Results Cards Detail:")
        print(json.dumps(cards_detail, indent=2, ensure_ascii=False))

        # Check rejected container cards
        rejected_cards = await page.locator("#results-rejected-container .scheme-card").count()
        print(f"Rejected cards container count: {rejected_cards}")

        screenshot_path = "artifacts/screenshots/01_baseline_results_cards.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"Saved screenshot to {screenshot_path}")

        print("Console logs:", console_logs[:10])
        print("Failed requests:", failed_requests)
        print("API responses:", api_responses)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
