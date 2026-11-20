# Application State Ledger (STATE.md)
**Project:** Maharashtra Scheme Navigator  
**Last Updated:** 2026-11-20T22:15:00+05:30  
**Active Execution Program:** TRIMURTI v3 — Scheme Universe Intelligence Master Execution Specification  
**Governing Standard:** Evidence-Gated · Human-Governed · UI-First · Self-Auditing · Resumable  
**Git Branch:** `feat/catalogue-v2`  
**Base Baselines:** Commit `ad0385e` (Tagged `rc4-accepted`), Tag `sc-m0-accepted` (`06580fe`), Tag `sc-g1-accepted`  
**Execution Environment:** Authorisation Level A0 (Local Windows Developer Machine, Python 3.11.4, SQLite 3.x, Chromium Headless)

---

## 1. Derived Launch & Scheme Program State

$$\mathbf{Launch\ State:\ INTERNAL\_DEMO\_READY}$$
$$\mathbf{TRIMURTI\ v3\ Ladder:\ SC\text{-}M0\ PASS\ \longrightarrow\ SC\text{-}G1\ PASS\ \longrightarrow\ SC\text{-}G2\ PASS\ \longrightarrow\ SC\text{-}G3\ PENDING}$$
$$\mathbf{Honest\ Quality\ Baseline:\ 78.88\ /\ 100\ (Target:\ 95.0\ /\ 100)}$$

- **Evaluation Rule (Section E2):** Requires G1, G2, G3, G5, and G23 to PASS locally with zero regressions.
- **Summary Scorecard:**
  - **PASS:** 8 gates (G1, G2, G3, G5, G11, G13, G23, G24-local)
  - **PARTIAL:** 11 gates (G4, G7, G8, G9, G14, G15, G16, G17, G18, G21, G22)
  - **BLOCKED:** 5 gates (G6, G10, G12, G19, G20-production)
  - **NOT_APPLICABLE:** 0 gates

---

## 2. Test Execution & Quality Baseline

- **Total Unit & Integration Tests:** **631 passed, 0 failed** (`pytest tests/`)
  - Baseline RC4 tests: 613 passed
  - Added SC-M0 test suites:
    - `tests/invariants/test_trimurti_invariants.py`: 7 passed (Invariants I-02, I-03, I-04, I-05, I-06, I-07, I-15, I-17)
    - `tests/test_playwright_scheme_issue_reporting.py`: 1 passed (Real Playwright trilingual report submission flow)
  - Added SC-G1 test suites:
    - `tests/test_governance_review_queue.py`: 4 passed (Review packet endpoints, RBAC enforcement, Invariant I-05 non-self-authorization)
    - `tests/test_playwright_five_citizen_acceptance.py`: 6 passed (Citizen A-E journeys + Decision-Ready vs Limited-Info UI distinction)
- **Browser Playwright Suites:** 25 real Chromium browser tests passing with 0 failures (19 earlier + 6 Five-Citizen acceptance tests)
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
