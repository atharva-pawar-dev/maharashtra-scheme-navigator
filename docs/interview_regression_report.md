# Interview Context & Regression Verification Report

## 1. Test Suite Architecture

The regression battery validates the complete lifecycle of citizen interviews, context separation, and deterministic eligibility evaluations across 11 core scenarios specified in Part 10.

| Test Scenario | Test Implementation | Key Assertions | Result |
|---|---|---|---|
| **Test 1: Full Discovery** | `test_1_full_discovery_journey` | `run_disc_...` ID generated; adaptive questions asked; all published assessable schemes evaluated upon completion; results tied to run. | **PASSED** |
| **Test 2: Focused Scheme Eligibility** | `test_2_focused_scheme_eligibility` | `run_foc_...` ID generated; only target scheme criteria asked; evaluates strictly target scheme; statutory reasons & GR sources present. | **PASSED** |
| **Test 3: Stale Results Prevention** | `test_3_stale_results_prevention` | Completing a discovery run followed by a focused run isolates results; discovery catalogue results do not contaminate focused assessment; isolated via `GET /interview/{thread_id}/results`. | **PASSED** |
| **Test 4: New Discovery Interview** | `test_4_new_discovery_interview_lifecycle` | Clicking New Interview in discovery mode generates fresh run ID; old transcript discarded; presents valid next question or immediate evaluation; zero hanging. | **PASSED** |
| **Test 5: New Focused Interview** | `test_5_new_focused_interview_preserves_target` | In focused mode, New Interview preserves target scheme ID; generates fresh run ID; asks only missing fields for that scheme. | **PASSED** |
| **Test 6: Pre-populated Profile** | `test_6_prepopulated_profile_evaluates_immediately` | When a complete profile is supplied, no unnecessary questions are asked; immediate evaluation occurs; valid result returned. | **PASSED** |
| **Test 7: Unknown Information** | `test_7_missing_mandatory_field_results_in_needs_info` | Missing mandatory fields trigger targeted questions; applicant is not prematurely classified as ineligible. | **PASSED** |
| **Test 8: Invalid / Stale Context** | `test_8_nonexistent_or_cross_tenant_run_isolation` | Nonexistent runs return 404; cross-tenant run result access returns 403 Forbidden; tenant boundaries enforced. | **PASSED** |
| **Test 9: Run Isolation Under Concurrency** | `test_9_run_isolation_under_concurrency` | Answers submitted to Run A do not overwrite or leak into Run B; state idempotency guaranteed. | **PASSED** |
| **Test 10: Multilingual Flow** | `test_10_multilingual_interview_flow` | Validates interview questions, choices, labels, and reasons across English (`en`), Marathi (`mr`), and Hindi (`hi`). | **PASSED** |
| **Test 11: Invalid Scheme Rejection** | `test_11_invalid_scheme_rejection` | Hallucinated or non-existent scheme IDs return HTTP 404; fail-closed catalogue verification. | **PASSED** |

---

## 2. Playwright Browser Citizen Experience Verification

The end-to-end browser test suite (`tests/test_browser_citizen_experience.py`) was executed with Chromium:

```
tests/test_browser_citizen_experience.py::test_01_explore_catalogue_rendering_and_department_filtering PASSED
tests/test_browser_citizen_experience.py::test_02_silent_demo_fallback_removed_shows_error_card_on_failure PASSED
tests/test_browser_citizen_experience.py::test_03_catalogue_freshness_indicator PASSED
tests/test_browser_citizen_experience.py::test_04_scoped_interview_launch_from_explore PASSED
tests/test_browser_citizen_experience.py::test_05_profile_sidebar_live_fields PASSED
tests/test_browser_citizen_experience.py::test_06_results_page_five_outcome_scoreboards PASSED
tests/test_browser_citizen_experience.py::test_07_primary_cta_restricted_to_eligible PASSED
tests/test_browser_citizen_experience.py::test_08_partial_match_scoreboard_card PASSED
tests/test_browser_citizen_experience.py::test_09_needs_info_scoreboard_card PASSED
tests/test_browser_citizen_experience.py::test_10_collapsed_not_eligible_accordion PASSED
tests/test_browser_citizen_experience.py::test_11_single_active_scheme_progress_view PASSED
tests/test_browser_citizen_experience.py::test_12_dismissal_confirmation_modal_text PASSED
tests/test_browser_citizen_experience.py::test_13_empty_progress_view_exact_text PASSED
tests/test_browser_citizen_experience.py::test_14_document_preparation_completion_card PASSED
tests/test_browser_citizen_experience.py::test_15_history_api_routing PASSED
tests/test_browser_citizen_experience.py::test_16_reusable_back_navigation PASSED
tests/test_browser_citizen_experience.py::test_17_fixed_floating_reviewer_portal_button PASSED
tests/test_browser_citizen_experience.py::test_18_citizen_profile_reset_modal_and_data_clearance PASSED
tests/test_browser_citizen_experience.py::test_19_english_mode_purity PASSED
tests/test_browser_citizen_experience.py::test_20_marathi_mode_purity PASSED

======================== 20 passed in 88.20s (0:01:28) ========================
```

---

## 3. Language Purity Invariant

- In English mode (`en`), 100% of visible page text contains **zero Devanagari characters** (verified by `test_19_english_mode_purity`).
- In Marathi mode (`mr`), primary headers and navigation labels render in pure Devanagari (verified by `test_20_marathi_mode_purity`).
