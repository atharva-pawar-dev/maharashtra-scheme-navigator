import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright

async def verify_all():
    os.makedirs("artifacts/screenshots", exist_ok=True)
    results_summary = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # -------------------------------------------------------------
        # Part 1: Desktop Viewport (1280x800)
        # -------------------------------------------------------------
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        console_logs = []
        page.on("console", lambda m: console_logs.append(f"[{m.type}] {m.text}"))

        print("--- Step 1: Baseline Real Application Navigation ---")
        await page.goto("http://127.0.0.1:8000/results", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # Trigger evaluation if empty
        cards_count = await page.locator("#results-cards-container .scheme-card").count()
        if cards_count == 0:
            print("Triggering evaluation from profile...")
            await page.evaluate("window.triggerEvaluationFromProfile()")
            await page.wait_for_timeout(3000)

        total_cards = await page.locator("#results-cards-container .scheme-card").count()
        print(f"Total cards rendered in #results-cards-container: {total_cards}")
        
        c_eligible = await page.locator("#count-eligible").inner_text()
        c_partial = await page.locator("#count-partial").inner_text()
        c_moreinfo = await page.locator("#count-moreinfo").inner_text()
        c_review = await page.locator("#count-review").inner_text()
        c_rejected = await page.locator("#count-rejected").inner_text()
        print(f"Scoreboard: Eligible={c_eligible}, Partial={c_partial}, NeedsInfo={c_moreinfo}, Review={c_review}, Ineligible={c_rejected}")

        # Check buttons on the first 3 Caseworker Review cards
        card_0 = page.locator("#results-cards-container .scheme-card").first
        card_0_title = await card_0.locator("h4").inner_text()
        card_0_buttons = await card_0.locator("button").all_inner_texts()
        card_0_footer = await card_0.locator(".scheme-card-footer").inner_html()
        print(f"Card 0 ('{card_0_title}') buttons: {card_0_buttons}")
        assert len(card_0_buttons) >= 2, f"Expected at least 2 action buttons on review card, got {card_0_buttons}"
        assert any("कागदपत्रे" in b or "Documents" in b for b in card_0_buttons), "Missing document review button"

        # Check that demo fixture has clear warning & badge
        demo_card = page.locator("#results-cards-container .scheme-card", has_text="डेमो नमुना").first
        if await demo_card.count() > 0:
            demo_badges = await demo_card.locator(".scheme-badge").all_inner_texts()
            print("Demo card badges:", demo_badges)
            assert any("डेमो नमुना" in b or "DEMO FIXTURE" in b for b in demo_badges), "Missing demo fixture badge"

        # Capture Screenshot 2: Fixed Result Cards
        await page.screenshot(path="artifacts/screenshots/02_results_cards_fixed_actions.png", full_page=True)
        print("Saved artifacts/screenshots/02_results_cards_fixed_actions.png")
        results_summary["review_cards_buttons_verified"] = True

        # -------------------------------------------------------------
        # Part 2: Isolated Synthetic Scenario with an ELIGIBLE Scheme
        # -------------------------------------------------------------
        print("\n--- Step 2: Isolated Scenario with ELIGIBLE Scheme ---")
        synthetic_eligible_result = [
            {
                "scheme_id": "candidate-majhi-ladki-bahin",
                "scheme_name": "Mukhyamantri Majhi Ladki Bahin Yojana (Verified Eligible Test)",
                "status": "eligible",
                "reason": "Citizen satisfies all verified criteria for monthly direct benefit transfer.",
                "matched_conditions": ["Age 21-65 years", "Maharashtra Domicile", "Annual Family Income <= 2.5 Lakhs"],
                "failed_conditions": [],
                "unknown_conditions": []
            }
        ]
        await page.evaluate(f"window.state.results = {json.dumps(synthetic_eligible_result)}; window.state.interviewMode = 'DISCOVERY'; window.renderResultsCards('all');")
        await page.wait_for_timeout(500)

        eligible_card = page.locator("#results-cards-container .scheme-card").first
        el_buttons = await eligible_card.locator("button").all_inner_texts()
        print("Eligible card buttons:", el_buttons)
        assert any("Check My Documents" in b or "कागदपत्रे तपासा" in b for b in el_buttons), "Missing 'Check My Documents' on eligible card"
        assert any("Details" in b or "तपशील" in b for b in el_buttons), "Missing Details button on eligible card"
        assert any("Begin application" in b or "तयारी सुरू" in b for b in el_buttons), "Missing Start Prep button on eligible card"

        await page.screenshot(path="artifacts/screenshots/03_eligible_scheme_card.png")
        print("Saved artifacts/screenshots/03_eligible_scheme_card.png")
        results_summary["eligible_card_buttons_verified"] = True

        # -------------------------------------------------------------
        # Part 3: Click 'Check My Documents' & Verify Document Auditor
        # -------------------------------------------------------------
        print("\n--- Step 3: Open Document Auditor for Scheme ---")
        check_docs_btn = eligible_card.locator("button", has_text="कागदपत्रे तपासा").first
        if await check_docs_btn.count() == 0:
            check_docs_btn = eligible_card.locator("button", has_text="Check My Documents").first
        await check_docs_btn.click()
        await page.wait_for_selector("#view-documents.active", timeout=5000)
        await page.wait_for_timeout(1500)

        # Verify banner and scheme name
        doc_scheme_name = await page.locator("#doc-scheme-name").inner_text()
        print(f"Document Auditor opened for: {doc_scheme_name}")
        assert "लाडकी बहीण" in doc_scheme_name or "Majhi Ladki Bahin" in doc_scheme_name or "candidate-majhi-ladki-bahin" in doc_scheme_name

        # Verify requirement checklist loaded
        req_items = await page.locator("#doc-requirements-list .req-item-card").count()
        print(f"Requirements checklist rendered items count: {req_items}")
        assert req_items > 0, "No requirement checklist items rendered"

        await page.screenshot(path="artifacts/screenshots/04_document_auditor_requirements.png", full_page=True)
        print("Saved artifacts/screenshots/04_document_auditor_requirements.png")
        results_summary["document_auditor_opened_and_reqs_rendered"] = True

        # -------------------------------------------------------------
        # Part 4: Upload Synthetic Document & Match Requirements
        # -------------------------------------------------------------
        print("\n--- Step 4: Upload Synthetic Test Document ---")
        test_file_path = os.path.abspath("demo_income_certificate.png")
        file_input = page.locator("#doc-file-input")
        await file_input.set_input_files(test_file_path)

        upload_btn = page.locator("#btn-do-upload")
        await upload_btn.click()

        # Wait for upload and audit to complete (uploading calls Gemini Vision, so give it up to 60s)
        print("Waiting for upload and extraction...")
        await page.wait_for_selector("#doc-uploaded-section[style*='display: block'], #doc-uploaded-list .uploaded-doc-card", timeout=60000)
        await page.wait_for_timeout(1000)

        uploaded_count = await page.locator("#doc-uploaded-list .uploaded-doc-card").count()
        print(f"Uploaded documents verified count: {uploaded_count}")
        assert uploaded_count >= 1, "Expected at least 1 uploaded document card"

        first_up_card = page.locator("#doc-uploaded-list .uploaded-doc-card").first
        card_text = await first_up_card.inner_text()
        print(f"Uploaded card summary:\n{card_text}")

        # Check readiness score updated
        readiness_badge = await page.locator("#doc-readiness-badge").inner_text()
        print(f"Readiness Score: {readiness_badge}")

        await page.screenshot(path="artifacts/screenshots/05_document_auditor_uploaded_and_matched.png", full_page=True)
        print("Saved artifacts/screenshots/05_document_auditor_uploaded_and_matched.png")
        results_summary["document_uploaded_and_audited"] = True

        # -------------------------------------------------------------
        # Part 5: Inspect and Correct Extracted Field
        # -------------------------------------------------------------
        print("\n--- Step 5: Field Inspection and Correction ---")
        edit_btn = first_up_card.locator(".btn-edit-doc").first
        await edit_btn.click()
        await page.wait_for_timeout(500)

        # Verify edit form is visible
        edit_form = first_up_card.locator("div[id^='edit-doc-']").first
        assert await edit_form.is_visible(), "Edit document form should be visible"

        # Change income field
        income_input = edit_form.locator("input[id^='edit-income-']").first
        old_income = await income_input.input_value()
        print(f"Original extracted income: {old_income}")
        await income_input.fill("120000")

        # Save corrections
        save_btn = edit_form.locator(".btn-save-corrections").first
        await save_btn.click()
        await page.wait_for_timeout(1500)

        # Verify updated value in card
        updated_card_text = await first_up_card.inner_text()
        print(f"Updated card text:\n{updated_card_text}")
        assert "120000" in updated_card_text or "१२००००" in updated_card_text, "Updated income not reflected in card text"

        await page.screenshot(path="artifacts/screenshots/06_field_corrected_and_saved.png", full_page=True)
        print("Saved artifacts/screenshots/06_field_corrected_and_saved.png")
        results_summary["field_correction_saved"] = True

        # -------------------------------------------------------------
        # Part 6: Refresh Page and Verify Session Preservation & Resume
        # -------------------------------------------------------------
        print("\n--- Step 6: Page Refresh & Resume Verification ---")
        await page.goto("http://127.0.0.1:8000/results", wait_until="networkidle")
        await page.wait_for_timeout(1500)

        # Check results resume banner
        resume_banner = page.locator("#results-resume-banner")
        banner_visible = await resume_banner.is_visible()
        print(f"Resume banner visible on /results after refresh: {banner_visible}")
        assert banner_visible, "Resume banner should be visible on /results when session exists"

        banner_text = await resume_banner.inner_text()
        print(f"Resume banner text: {banner_text}")

        # Click resume button
        resume_btn = page.locator(".btn-resume-doc-audit").first
        await resume_btn.click()
        await page.wait_for_selector("#view-documents.active", timeout=5000)
        await page.wait_for_timeout(1000)

        # Verify documents and requirements still present
        restored_up_count = await page.locator("#doc-uploaded-list .uploaded-doc-card").count()
        print(f"Restored uploaded documents count after refresh: {restored_up_count}")
        assert restored_up_count >= 1, "Uploaded document should remain preserved across reload"

        await page.screenshot(path="artifacts/screenshots/07_document_auditor_resumed_after_refresh.png", full_page=True)
        print("Saved artifacts/screenshots/07_document_auditor_resumed_after_refresh.png")
        results_summary["session_restored_after_refresh"] = True

        await context.close()

        # -------------------------------------------------------------
        # Part 7: Mobile Viewport Verification (390x844)
        # -------------------------------------------------------------
        print("\n--- Step 7: Mobile Viewport Verification (390x844) ---")
        mobile_context = await browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
        mobile_page = await mobile_context.new_page()

        await mobile_page.goto("http://127.0.0.1:8000/results", wait_until="networkidle")
        await mobile_page.wait_for_timeout(1000)

        # Trigger evaluation on mobile
        m_cards = await mobile_page.locator("#results-cards-container .scheme-card").count()
        if m_cards == 0:
            await mobile_page.evaluate("window.triggerEvaluationFromProfile()")
            await mobile_page.wait_for_timeout(3000)

        m_total_cards = await mobile_page.locator("#results-cards-container .scheme-card").count()
        print(f"Mobile results cards count: {m_total_cards}")
        assert m_total_cards > 0, "Mobile view should render result cards"

        # Check first card action buttons on mobile
        m_first_card = mobile_page.locator("#results-cards-container .scheme-card").first
        m_btns = await m_first_card.locator("button").all_inner_texts()
        print(f"Mobile first card buttons: {m_btns}")
        assert len(m_btns) >= 2, "Mobile card should have action buttons"

        await mobile_page.screenshot(path="artifacts/screenshots/08_mobile_results_cards.png", full_page=True)
        print("Saved artifacts/screenshots/08_mobile_results_cards.png")

        # Click document audit on mobile
        m_doc_btn = m_first_card.locator(".btn-doc-audit").first
        await m_doc_btn.click()
        await mobile_page.wait_for_selector("#view-documents.active", timeout=5000)
        await mobile_page.wait_for_timeout(1500)

        await mobile_page.screenshot(path="artifacts/screenshots/09_mobile_document_auditor.png", full_page=True)
        print("Saved artifacts/screenshots/09_mobile_document_auditor.png")

        results_summary["mobile_viewport_verified"] = True

        await mobile_context.close()
        await browser.close()

    print("\n=======================================================")
    print("ALL REAL BROWSER AUDIT VERIFICATION TESTS PASSED!")
    print(json.dumps(results_summary, indent=2))
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(verify_all())
