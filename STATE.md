# Application State Ledger (STATE.md)
**Project:** Maharashtra Scheme Navigator  
**Last Updated:** 2026-11-19T21:05:00+05:30  
**Active Execution Program:** RC2 Forensic Acceptance & Integration Audit  
**Governing Standard:** Production Release Program v2.0 (Evidence-Gated & Honest by Construction)  
**Git Branch:** `feat/catalogue-v2`  
**Base Commit:** `4ccee63` (Tagged `vertical-slice-complete-rc2`)  
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

- **Total Unit & Integration Tests:** 574 passed, 0 failed (`pytest tests/`)
- **Browser Playwright Suites:**
  - `tests/test_playwright_15_citizen_journeys.py`: 15 passed
  - `tests/test_playwright_backend_restart_persistence.py`: 1 passed (P0 restart durability drill)
  - `tests/test_browser_citizen_experience.py`: 21 passed
  - `tests/test_browser_document_auditor_journey.py`: 4 passed
  - `tests/test_browser_municipal_citizen_journey.py`: 5 passed
  - **Total Browser Tests:** 46 passed (0 failed)
- **Mutation Canary Verification:** 12/12 individual canary mutations caught (`release/evidence/ws15/E-WS15-002_canary_mutations_individual.json`)

---

## 3. P0 Forensic Implementations & Invariants

1. **Authoritative SQLite Persistence Across Server Restarts:**
   - Database Migration v4 in `src/scheme_navigator/core/migrations.py` applied (`citizen_scheme_documents`, `citizen_scheme_audit_history`).
   - Server process killed with `process.kill()`, `sessionStorage` purged, server restarted, state fully re-hydrated from SQLite.
   - Evidence screenshots: `reports/evidence_screenshots/01_before_restart_replacement.png`, `02_after_restart_restored_from_sqlite.png`.
2. **Document Replacement Lineage ($v1 \to v2$):**
   - Active document replaced with new version, unique document ID, and fresh SHA-256 digest.
   - Previous document marked `status='superseded'`, preserved with replacement reason, and rendered in `#doc-history-section`.
3. **Local Fallback OCR Specimen Content (PyMuPDF):**
   - Extracted directly from PyMuPDF document text streams (zero filename heuristics).
   - Validated via `tests/test_local_fallback_ocr_content.py` (6/6 passed). Isolated behind `ENABLE_LOCAL_FALLBACK_OCR="true"`.

---

## 4. Data & Catalogue Verification State

- **Total Catalogued Records:** 75 records in `data/catalogue/schemes.json` (74 canonical schemes + 1 quarantined demo fixture).
- **Tier A (Flagship Schemes):** 17 schemes with 100% verified verbatim Marathi Government Resolution (GR) quotes cached in `data/raw/` with SHA-256 hashes.
- **Tier B (Municipal Schemes):** 13 schemes covering PMC, PCMC, BMC, TMC, and NMMC with strict geographic isolation.
- **Tier C (Discovered / Exploratory Schemes):** 44 schemes explicitly flagged `verification_status="unverified"` and `eligibility_incomplete=true`.
- **Demo Fixture:** `demo-old-age-pension-mh` physically quarantined and disabled by startup guard in production.

---

## 5. Active Workstreams & Next Milestones

1. **[DONE] P0 SQLite Durability & Server Restart Drill:** `tests/test_playwright_backend_restart_persistence.py`
2. **[DONE] P0 Document Replacement & Lineage Tracking:** `tests/test_sqlite_persistence_and_replacement.py`
3. **[DONE] P0 Local Fallback OCR Content Overhaul:** `tests/test_local_fallback_ocr_content.py`
4. **[DONE] 15 Mandatory End-to-End Playwright Browser Journeys:** `tests/test_playwright_15_citizen_journeys.py` (15/15 passed)
5. **[DONE] Full Regression Suite:** 574 tests passing (0 failed)
6. **[DONE] Forensic Acceptance Audit Report:** `reports/rc2_forensic_acceptance_audit.md`
