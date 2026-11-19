# Application State Ledger (STATE.md)
**Project:** Maharashtra Scheme Navigator  
**Last Updated:** 2026-11-19T22:25:00+05:30  
**Active Execution Program:** RC3 — Document Intelligence, Scheme Coverage & Citizen Trust Hardening  
**Governing Standard:** Production Release Program v2.0 (Evidence-Gated & Honest by Construction)  
**Git Branch:** `feat/catalogue-v2`  
**Base Commit:** `f10a0a0` (Tagged `rc2-forensic-accepted`)  
**Hardened Milestone:** Tag `rc3-hardened`  
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

- **Total Unit & Integration Tests:** **606 passed, 0 failed** (`pytest tests/`)
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

## 3. RC3 Document Intelligence & Trust Invariants

1. **Real OCR Classification & Quality Rejections:**
   - Physical medium classification: `SEARCHABLE_PDF`, `SCANNED_PDF`, `PHOTOGRAPH`, `IMAGE`.
   - Quality rejection thresholds: Resolution < 250px (`LOW_RESOLUTION_IMAGE`), Blur Laplacian variance < 45.0 (`IMAGE_EXCESSIVE_BLUR`).
   - Multi-page missing page detection (`MISSING_PAGE_IN_SEQUENCE`).
   - Devanagari numerals (`०-९`), currency (`₹`, `INR`), and FY parsing.
   - Separation of OCR uncertainty (`OCR_UNCERTAINTY`) from statutory rule failures.
2. **Representative Scheme-Diverse Coverage:**
   - 12 representative scheme families with specific document requirement models, alternative acceptance (ANY_OF), and issuing authorities.
   - Deliverable: `docs/quality/scheme_diverse_document_coverage.md`.
3. **Immutable Document Audit History:**
   - SQLite Migration 5 triggers prevent UPDATE on document content, hashes, version, or created_at in `citizen_scheme_documents`, and strictly enforce append-only on `citizen_scheme_audit_history`.
4. **24-Hour Privacy Retention & Reactive Invalidation:**
   - Expired documents marked `purged_expired` under 24-hr privacy retention ceiling.
   - Readiness engine reactively drops score to 0% and issues localized re-upload notices in EN, MR, and HI.
5. **Eligibility State Normalization:**
   - `EligibilityStatus.MEETS_VERIFIED_CRITERIA = "meets_verified_criteria"` standard in models and UI.
   - Fail-closed evaluation: demo fixtures and unapproved rules fail closed to `NEEDS_REVIEW` (Caseworker Review).
6. **End-to-End Trilingual Parity:**
   - Exact 1:1 symmetry across 112 keys in EN, MR, HI in `static/index.html`.
   - Complete browser journey validation across EN, MR, and HI in Chromium headless.

---

## 4. Data & Catalogue Verification State

- **Total Catalogued Records:** 75 records in `data/catalogue/schemes.json` (74 canonical schemes + 1 quarantined demo fixture).
- **Tier A (Flagship Schemes):** 17 schemes with 100% verified verbatim Marathi Government Resolution (GR) quotes cached in `data/raw/` with SHA-256 hashes.
- **Tier B (Municipal Schemes):** 13 schemes covering PMC, PCMC, BMC, TMC, and NMMC with strict geographic isolation.
- **Tier C (Discovered / Exploratory Schemes):** 44 schemes explicitly flagged `verification_status="unverified"` and `eligibility_incomplete=true`.
- **Demo Fixture:** `demo-old-age-pension-mh` physically quarantined and disabled by startup guard in production.

---

## 5. Audit Reports Manifest

1. `reports/rc3_hardening_audit.md` (RC3 Hardening Forensic Report)
2. `docs/quality/scheme_diverse_document_coverage.md` (Scheme-Diverse Document Requirements Coverage)
3. `reports/rc2_forensic_acceptance_audit.md` (RC2 Forensic Audit Report)
4. `reports/final_citizen_journey_evidence.json` (Playwright Browser Journey Evidence)
