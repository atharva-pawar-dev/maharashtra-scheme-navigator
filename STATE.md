# Application State Ledger (STATE.md)
**Project:** Maharashtra Scheme Navigator  
**Last Updated:** 2026-11-18T22:15:00+05:30  
**Active Execution Program:** Trimurti 10/10 Master Autonomous Execution Specification  
**Governing Standard:** Production Release Program v2.0 (Evidence-Gated & Honest by Construction)  
**Git Branch:** `feat/catalogue-v2`  
**Base Commit:** `9e8f31d` (Tagged `catalogue-v2-rc1`)  
**Safety Backup:** `_backups/safety-backup-20261118-221135`  
**Execution Environment:** Authorisation Level A0 (Local Windows Developer Machine, Python 3.11.4, SQLite 3.x, Chromium Headless)

---

## 1. Derived Launch State

$$\mathbf{Launch\ State:\ INTERNAL\_DEMO\_READY}$$

- **Evaluation Rule (Section E2):** Requires G1, G2, G3, G5, and G23 to PASS locally with zero regressions.
- **Summary Scorecard:**
  - **PASS:** 8 gates (G1, G2, G3, G5, G11, G13, G23, G24)
  - **PARTIAL:** 11 gates (G4, G7, G8, G9, G14, G15, G16, G17, G18, G21, G22)
  - **BLOCKED:** 5 gates (G6, G10, G12, G19, G20)
  - **NOT_APPLICABLE:** 0 gates

---

## 2. Test Execution & Quality Baseline

- **Total Unit & Integration Tests:** 550 passed, 0 failed (`pytest tests/`)
- **Browser Playwright Suites:**
  - `tests/test_browser_citizen_experience.py`: 21 passed
  - `tests/test_browser_document_auditor_journey.py`: 4 passed
  - `tests/test_browser_municipal_citizen_journey.py`: 5 passed
  - Automated canary verification: 12/12 individual canary mutations caught (`release/evidence/ws15/E-WS15-002_canary_mutations_individual.json`)

---

## 3. Data & Catalogue Verification State

- **Total Canonical Schemes:** 75 schemes in `data/catalogue/schemes.json`
- **Tier A (Flagship Schemes):** 17 schemes with 100% verified verbatim Marathi Government Resolution (GR) quotes cached in `data/raw/` with SHA-256 hashes.
- **Tier B (Municipal Schemes):** 13 schemes covering Pune Municipal Corporation (PMC), Pimpri Chinchwad Municipal Corporation (PCMC), Brihanmumbai Municipal Corporation (BMC), Thane Municipal Corporation (TMC), and Navi Mumbai Municipal Corporation (NMMC) with strict geographic isolation.
- **Tier C (Discovered / Exploratory Schemes):** 44 schemes explicitly flagged `verification_status="unverified"` and `eligibility_incomplete=true` to prevent false eligibility promises.
- **Demo Fixtures:** Physically segregated and disabled by startup guard in production.

---

## 4. Active Workstreams & Next Milestones

1. **[DONE] UI-to-Backend Integration Inventory:** `docs/quality/ui_to_backend_integration_inventory.md`
2. **[DONE] Safety Backup:** `_backups/safety-backup-20261118-221135`
3. **[IN PROGRESS] Synthetic Document Fixture Generator:** `tests/fixtures/generate_synthetic_documents.py` (9 watermarked specimens)
4. **[IN PROGRESS] 15 Mandatory End-to-End Playwright Browser Journeys:** `tests/test_playwright_15_citizen_journeys.py`
5. **[PENDING] Complete Architecture & Quality Deliverables Manifest:** (G1-G14 reports and diagrams)
