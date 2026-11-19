# Application State Ledger (STATE.md)
**Project:** Maharashtra Scheme Navigator  
**Last Updated:** 2026-11-19T23:15:00+05:30  
**Active Execution Program:** RC4 — Real-World Document Intelligence & Citizen Trust Acceptance  
**Governing Standard:** Production Release Program v2.0 (Evidence-Gated & Honest by Construction)  
**Git Branch:** `feat/catalogue-v2`  
**Base Baseline:** Commit `ab2a640` (Tagged `rc3-hardened`)  
**Accepted Milestone:** Tag `rc4-accepted`  
**Execution Environment:** Authorisation Level A0 (Local Windows Developer Machine, Python 3.11.4, SQLite 3.x, Chromium Headless)

---

## 1. Derived Launch State

$$\mathbf{Launch\ State:\ INTERNAL\_DEMO\_READY}$$

- **Evaluation Rule (Section E2):** Requires G1, G2, G3, G5, and G23 to PASS locally with zero regressions.
- **Summary Scorecard:**
  - **PASS:** 8 gates (G1, G2, G3, G5, G11, G13, G23, G24-local)
  - **PARTIAL:** 11 gates (G4, G7, G8, G9, G14, G15, G16, G17, G18, G21, G22)
  - **BLOCKED:** 5 gates (G6, G10, G12, G19, G20-production)
  - **NOT_APPLICABLE:** 0 gates

---

## 2. Test Execution & Quality Baseline

- **Total Unit & Integration Tests:** **613 passed, 0 failed** (`pytest tests/`)
  - Baseline RC3 tests: 606 passed
  - Added RC4 test suites:
    - `tests/test_rc4_document_intelligence_accuracy.py`: 4 passed
    - `tests/test_rc4_scheme_diverse_e2e_journeys.py`: 1 passed (12 complete citizen upload journeys)
    - `tests/test_rc4_retention_and_readiness_math.py`: 2 passed (5-requirement proportional readiness math)
- **Browser Playwright Suites:**
  - `tests/test_playwright_15_citizen_journeys.py`: 15 passed
  - `tests/test_playwright_backend_restart_persistence.py`: 1 passed (P0 restart durability drill)
  - `tests/test_trilingual_parity.py`: 3 passed (Language switching & full UI verification)
  - `tests/test_browser_citizen_experience.py`: 21 passed
  - `tests/test_browser_document_auditor_journey.py`: 4 passed
  - `tests/test_browser_municipal_citizen_journey.py`: 5 passed
  - **Total Browser Tests:** 47 passed (0 failed)
- **Mutation Canary Verification:** 12/12 individual canary mutations caught (`release/evidence/ws15/E-WS15-002_canary_mutations_individual.json`)

---

## 3. RC4 Real-World Document Intelligence & Citizen Trust Invariants

1. **Deterministic Document Processing Across 6 Routes:**
   - Routes: Searchable PDF, Scanned PDF, JPG Photograph, PNG Scan/Image, Multi-page PDF, Front/Back Pair.
   - Text extraction vs. OCR explicitly distinguished; PyMuPDF stream parsing never misrepresented as OCR.
   - 100% field extraction accuracy (64/64 fields matched vs ground truth across English, Marathi, and Hindi).
2. **Image Quality & Smartphone Photo Resilience:**
   - Resolution minimum ($250 \times 250$ px), OpenCV Laplacian blur threshold ($45.0$).
   - Normalized edge sharpness ($\ge 150.0$) preserves readable low-contrast official scans.
   - EXIF camera rotation auto-transposed via `PIL.ImageOps.exif_transpose`.
3. **Scheme-Diverse End-to-End Ingestion (12 Families):**
   - 12 representative scheme families (`MHA-S-0001` through `MHA-S-0012`) executed end-to-end through discovery, requirements, upload, audit, SQLite persistence, and official portal handoff.
   - Dual-key alias resolution in catalog without dictionary inflation.
   - Evidence Artifact: `reports/rc4_scheme_diverse_journey_evidence.json`.
4. **Trilingual Language Parity (112 Keys):**
   - 112 keys across EN, MR, HI with zero English sentence leaks.
   - Devanagari numerals (`०-९`) formatted dynamically across counts, currencies, and percentages.
   - Seamless cross-language document handling (EN doc in MR UI, MR doc in EN UI).
   - Evidence Artifact: `reports/rc4_multilingual_acceptance.md`.
5. **Statutory Retention Alignment & 7 Data Classes:**
   - MeitY DPDP staged commencement facts reflected; 24-hour purge correctly governed under IT (SPDI) Rules 2011 and data minimization.
   - 7 distinct data classes governed across lifecycle and citizen UI states.
   - Configurable retention via `data_retention_hours`.
   - Evidence Artifact: `reports/rc4_retention_and_privacy_audit.md`.
6. **Proportional Readiness Mathematics:**
   - 5 mandatory requirements: 5/5 = 100%; purging 1 document drops readiness to exactly 80% (never resetting to 0%).
   - Stale green checks cleared immediately; clear vernacular re-upload guidance provided.
7. **Immutable Audit Lineage:**
   - SQLite triggers enforce immutable audit history; original hashes and findings preserved across document replacements.
