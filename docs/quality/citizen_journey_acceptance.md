# Quality Acceptance: The 15 Mandatory Citizen Journeys
**Document ID:** `DOC-QA-JOURNEY-001`  
**Version:** 2.0.0  
**Status:** Canonical & Audited  
**Date:** 2026-11-18  
**Scope:** Browser Acceptance Test Execution Report for the 15 Mandatory Playwright Citizen Journeys  

---

## 1. Executive Summary & Verification Ledger

All 15 mandatory citizen journeys specified in Section 17.3 of the Master Execution Specification were executed in Chromium headless against the running application server via Playwright.

$$\mathbf{Result:\ 15/15\ JOURNEYS\ PASSED\ (100\%)\ -\ 0\ FAILURES}$$

Execution runtime: **24.28 seconds**  
Test suite file: `tests/test_playwright_15_citizen_journeys.py`

---

## 2. Detailed Journey Acceptance Record

| Journey ID | Citizen Persona & Journey Scenario | Primary User Actions & Transitions | Key Assertions & DOM Verification | Status | Duration |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **J01** | **Golden Path Citizen** | Explore $\to$ Scheme Details $\to$ Check Documents $\to$ Upload valid income certificate $\to$ Complete | `#view-documents.active`, `.uploaded-doc-card` rendered, `#doc-readiness-badge` updated, `#btn-portal-official` clickable | **PASS** | 2.1s |
| **J02** | **Incomplete Profile Citizen** | Citizen starts with missing income; results show `NEEDS_INFORMATION`; updates income to ₹1,20,000 | Dynamic status change from `NEEDS_INFORMATION` to `ELIGIBLE`; cards re-rendered with green badge | **PASS** | 1.4s |
| **J03** | **Missing Mandatory Document Citizen** | Scheme requires multiple certificates; citizen uploads none initially | Requirements checklist rendered with `.req-state-badge.state-missing` on mandatory items | **PASS** | 1.2s |
| **J04** | **Expired Document Citizen** | Citizen uploads certificate for past financial year (`2021-22`) against target FY `2026-27` | `#doc-conflicts-container` renders warning; finding identifies expired validity with Tahsil reissue advice | **PASS** | 1.8s |
| **J05** | **Unreadable Document Citizen** | Citizen uploads blurry image; flagged low quality; clicks Replace Document and uploads clean PDF | Quality check flags `.state-unreadable`; `.btn-replace-doc` unblocks replacement; valid upload succeeds | **PASS** | 2.3s |
| **J06** | **Profile vs Document Name Mismatch** | Profile name "Sunita Ramesh Patil"; document has "Anita Suresh Deshmukh" | Finding displays `PROFILE_DOCUMENT_NAME_MISMATCH`; `#btn-sync-profile-mismatch` updates profile name instantly | **PASS** | 1.7s |
| **J07** | **Wrong Financial Year Citizen** | Uploads income certificate issued for prior year | Document card displays extracted FY (`2021-22`); mismatch conflict warning displayed | **PASS** | 1.5s |
| **J08** | **Alternative Document (`ANY_OF`) Citizen** | Scheme requires Domicile OR Ration Card; uploads Yellow BPL Ration Card | Requirement satisfied under alternative document rule; `.req-item-card` unblocked | **PASS** | 1.6s |
| **J09** | **Inline Profile Correction & Invalidation** | Valid document uploaded; citizen increases income in profile to ₹5,00,000 | Re-audit automatically triggered without file re-upload; `INCOME_EXCEEDS_SCHEME_THRESHOLD` flagged | **PASS** | 1.9s |
| **J10** | **Document Replacement Recovery** | Citizen uploads wrong document (Driving License); clicks Remove / Replace | Faulty document deleted via `removeUploadedDocument`; review card count resets to 0 | **PASS** | 1.4s |
| **J11** | **Manual Review / Field Editing** | Citizen opens extracted field editor, corrects income value, saves changes | `.btn-edit-doc` opens input form; `.btn-save-corrections` updates record and triggers readiness recalculation | **PASS** | 1.3s |
| **J12** | **Persistence & Resume Across Reload** | Citizen uploads document, readiness updates, browser triggers `page.reload()` (`F5`) | SPA router re-mounts `#view-documents.active`; active scheme, uploaded documents, and readiness restored | **PASS** | 1.8s |
| **J13** | **Mid-Journey Language Switch** | Switched `en` $\to$ `hi` $\to$ `mr` mid-flow in Document Auditor | All titles, button labels, and badges update dynamically with zero untranslated tokens or layout break | **PASS** | 1.5s |
| **J14** | **Mobile Viewport (`360x800`)** | Viewport configured to `360x800`; citizen navigates cards and modals | Horizontal scroll is 0 (`scrollWidth <= clientWidth`); touch targets $\ge 44\text{px}$; modals fully usable | **PASS** | 1.2s |
| **J15** | **Official Portal Handoff & Checklist** | Citizen prepares application; inspects official external handoff and disclaimers | `#btn-portal-official` resolves to legitimate government portal; statutory non-sanctioning notice displayed | **PASS** | 1.1s |

---

## 3. Acceptance Decision

$$\mathbf{Gate\ G1\ (Citizen\ Journeys):\ PASS}$$
$$\mathbf{Gate\ G2\ (Document\ Auditor):\ PASS}$$
The complete citizen experience across all four phases (Discover, Understand, Prepare, Apply) is evidenced by 15 reproducible, passing Playwright browser tests.
