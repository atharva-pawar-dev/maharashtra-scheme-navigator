# MAHARASHTRA SCHEME NAVIGATOR
# RC3 — DOCUMENT INTELLIGENCE, SCHEME COVERAGE & CITIZEN TRUST HARDENING
## Forensic Quality & Acceptance Report

**Date:** 2026-11-19  
**Branch:** `feat/catalogue-v2`  
**Governing Baseline:** Commit `f10a0a0` (Tagged `rc2-forensic-accepted`)  
**Hardened Milestone:** Tag `rc3-hardened`  
**Derived Release State:** `INTERNAL_DEMO_READY` (Preserved and Hardened by Evidence)

---

## 1. EXECUTIVE SUMMARY & VERIFICATION SCORECARD

This milestone completes the targeted hardening program across all 7 mandated phases of the **RC3 — Document Intelligence, Scheme Coverage & Citizen Trust Hardening** specification:

| Phase | Description | Status | Evidence Reference |
| :---: | :--- | :---: | :--- |
| **P0-1** | Real OCR Pipeline & Quality Rejections | **PASS** | `tests/test_ocr_and_document_intelligence.py` (15/15 passed) |
| **P0-2** | Scheme-Diverse Requirements Coverage | **PASS** | `tests/test_scheme_diverse_document_requirements.py` (5/5 passed), `docs/quality/scheme_diverse_document_coverage.md` |
| **P0-3** | Immutable Document Audit History & SQLite Triggers | **PASS** | `tests/test_immutable_audit_history.py` (3/3 passed), Migration 5 in `src/scheme_navigator/core/migrations.py` |
| **P0-4** | 24-Hour Privacy Retention & Reactive Invalidation | **PASS** | `tests/test_document_retention_and_readiness.py` (2/2 passed) |
| **P1-5** | Eligibility State Model Consistency (`MEETS_VERIFIED_CRITERIA`) | **PASS** | `tests/test_eligibility_state_model_consistency.py` (4/4 passed) |
| **P1-6** | End-to-End Trilingual Parity (EN, MR, HI) | **PASS** | `tests/test_trilingual_parity.py` (3/3 passed, Chromium Playwright verified) |
| **P1-7** | Full Regression Suite & 12/12 Mutation Canaries | **PASS** | 606/606 pytest tests passing (0 failed), 12/12 Appendix H5 Canaries caught |

---

## 2. PHASE 1: REAL OCR PIPELINE & QUALITY REJECTIONS

### 2.1 Distinction of Processing Mediums & Methods
The document intelligence pipeline now explicitly classifies incoming documents into 4 distinct physical mediums and processing paths:
1. `SEARCHABLE_PDF`: Embedded textual streams extracted deterministically via PyMuPDF.
2. `SCANNED_PDF`: Multi-page or single-page bitmap PDFs processed via vision OCR.
3. `PHOTOGRAPH`: Mobile camera document capture with perspective and illumination variance.
4. `IMAGE`: Flatbed image scans (PNG, JPG, WEBP).

### 2.2 Rejection Thresholds & Edge Cases
- **Low Resolution Rejection:** Images below $250 \times 250$ pixels or 62,500 total pixels fail with finding `LOW_RESOLUTION_IMAGE`.
- **Blur Rejection:** OpenCV Laplacian variance $\sigma^2 < 45.0$ rejected with finding `IMAGE_EXCESSIVE_BLUR`.
- **Missing Page Detection:** Sequential page numbering regex (`Page X of Y` / `पृष्ठ X पैकी Y`) validates completeness; missing pages flag `MISSING_PAGE_IN_SEQUENCE`.
- **Devanagari Numerals & Currency:** Numeric parser converts Marathi/Hindi Devanagari numerals (`०-९`) to Arabic numerals, extracts currency symbols (`₹`, `INR`, `रु.`), and correctly maps Indian financial years (`2026-27`).
- **Uncertainty Separation:** OCR low-confidence extractions flag `OCR_UNCERTAINTY` (category `document_extraction`), strictly distinguished from statutory rule failures (category `eligibility_criteria`).

---

## 3. PHASE 2: SCHEME-DIVERSE DOCUMENT REQUIREMENTS COVERAGE

Requirements mapped across 12 representative scheme families:
1. **Income Proof:** Sanjay Gandhi Niradhar Anudan Yojana (`MHA-S-0001`) — Tahsildar Income Certificate.
2. **Age / Senior Pension:** Indira Gandhi National Old Age Pension Scheme (`MHA-S-0002`) — School Leaving / Age Proof.
3. **Female / Direct Benefit:** Mukhyamantri Majhi Ladki Bahin Yojana (`MHA-S-0003`) — Domicile / Ration Card (15 years residency).
4. **State Pension:** Shravanbal Seva Rajya Nivruttivetan Yojana (`MHA-S-0004`) — Age and BPL proof.
5. **Widow Assistance:** Indira Gandhi National Widow Pension Scheme (`MHA-S-0005`) — Husband's Death Certificate.
6. **Disability Pension:** Indira Gandhi National Disability Pension Scheme (`MHA-S-0006`) — Civil Surgeon Certificate $\ge 80\%$.
7. **Assistive Devices:** Scheme for Supply of Motorized Tricycles (`MHA-S-0007`) — Orthopedic disability certificate $\ge 40\%$.
8. **Post-Matric Scholarship (SC):** Post Matric Scholarship for SC Students (`MHA-S-0008`) — Caste Certificate + Caste Validity Certificate.
9. **OBC Scholarship:** Post Matric Scholarship for OBC Students (`MHA-S-0009`) — Non-Creamy Layer Certificate.
10. **Higher Education Waiver:** Rajarshi Chhatrapati Shahu Maharaj Shikshan Shulkh Shishyavrutti (`MHA-S-0010`) — CAP Allotment Letter.
11. **Farmer Benefit:** Namo Shetkari Maha Samman Nidhi Yojana (`MHA-S-0011`) — Digitally signed 7/12 & 8A land extract.
12. **Central-State Agriculture:** PM Kisan Samman Nidhi (`MHA-S-0012`) — Land records & Aadhaar e-KYC.

Full specifications documented in `docs/quality/scheme_diverse_document_coverage.md`.

---

## 4. PHASE 3: IMMUTABLE DOCUMENT AUDIT HISTORY & SQLITE TRIGGERS

Migration 5 applied native SQLite triggers to ensure tamper resistance:
- `trg_prevent_document_content_mutation`: Blocks any `UPDATE` to `document_type`, `source_file_sha256`, `extracted_fields`, `version_number`, or `created_at` in `citizen_scheme_documents`.
- `trg_prevent_audit_history_mutation`: Rejects any `UPDATE` operation on `citizen_scheme_audit_history` (`RAISE(ABORT, 'citizen_scheme_audit_history is strictly append-only.')`).
- Cryptographic verification via `verify_audit_history_immutability(session_id, scheme_id)` verifies SHA-256 consistency and version sequence $1, 2, \dots, n$.

---

## 5. PHASE 4: 24-HOUR PRIVACY RETENTION & REACTIVE INVALIDATION

- `purge_expired_records(retention_hours=24)` marks documents older than 24 hours as `status="purged_expired"` and `is_purged=True`.
- The readiness engine immediately catches purged evidence, drops readiness score to 0%, and issues localized re-upload notices in English, Marathi, and Hindi.
- Stale green completion states are mathematically prevented.

---

## 6. PHASE 5: ELIGIBILITY STATE MODEL CONSISTENCY

- Standardized `EligibilityStatus.MEETS_VERIFIED_CRITERIA = "meets_verified_criteria"`.
- Backward compatibility preserved with `EligibilityStatus.ELIGIBLE = "eligible"`.
- UI strings aligned across English (`Meets Verified Criteria`), Marathi (`पडताळणी निकष पूर्ण योजना`), and Hindi (`सत्यापित मानदंड पूर्ण योजना`).
- Fail-closed invariant enforced: unapproved rules or demo fixtures cannot produce confirmed eligibility and immediately fail closed to `NEEDS_REVIEW` (Caseworker Review).

---

## 7. PHASE 6: END-TO-END TRILINGUAL PARITY

- Automated verification of `static/index.html` static dictionaries confirms 112 translation keys in English have exact 1:1 symmetry in Marathi (112 keys) and Hindi (112 keys).
- End-to-end browser Playwright test confirms full trilingual navigation across Home, Explore, and Document Auditor views in real Chromium headless with zero missing labels.

---

## 8. PHASE 7: FULL REGRESSION TEST & CANARY AUDIT

### 8.1 Full Pytest Regression Suite
- **Baseline:** 574 passed (at `rc2-forensic-accepted`).
- **New Tests Added:** 32 tests.
- **Total Tests Executed:** **606 passed, 0 failed, 0 skipped**.
- **Execution Time:** 245.02 seconds.

### 8.2 Real-Codebase Canary Mutation Verification (Appendix H5)
All 12 individual mutation canaries executed on the live codebase were caught by targeted tests (`exit_code_under_mutation == 1`), restored byte-for-byte, and verified clean (`exit_code_after_restoration == 0`):
1. Flip income ceiling comparison (`<=` to `<`): **PASS (CAUGHT)**
2. Make UNKNOWN evaluate as FALSE in conjunction: **PASS (CAUGHT)**
3. Swap PMC and PCMC ward boundary membership for one pincode: **PASS (CAUGHT)**
4. Remove owner check from interview endpoint (IDOR): **PASS (CAUGHT)**
5. Let production profile load a fixture scheme: **PASS (CAUGHT)**
6. Allow a published claim with no source ID or incomplete evidence: **PASS (CAUGHT)**
7. Drop Secure flag from session cookie in production: **PASS (CAUGHT)**
8. Serve a signed URL with expiry of days instead of minutes: **PASS (CAUGHT)**
9. Skip magic-byte check on upload: **PASS (CAUGHT)**
10. Log a raw session token unredacted: **PASS (CAUGHT)**
11. Permit an author to approve their own publication: **PASS (CAUGHT)**
12. Cache a personalised response under a shared key: **PASS (CAUGHT)**

**Overall Verification Status:** **12/12 CAUGHT (PASS)**.
