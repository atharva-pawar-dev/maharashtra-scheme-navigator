# Document Verification & Pre-Audit Test Matrix
**Document ID:** `DOC-QA-DOCMATRIX-001`  
**Version:** 2.0.0  
**Status:** Canonical & Audited  
**Date:** 2026-11-18  
**Scope:** Verification Matrix for Multi-Page PDF Handling, OCR Extraction, Consistency Rules, and Readiness Computation  

---

## 1. Executive Summary

This matrix specifies the verification boundaries, test specimens, expected findings, and automated test coverage for the **Maharashtra Scheme Navigator** Document Auditor pipeline. All 9 synthetic test specimens are generated with the mandatory watermark:
`SYNTHETIC TEST SPECIMEN - NOT A REAL GOVERNMENT DOCUMENT`.

---

## 2. Document Verification Test Matrix

| Test Case ID | Document Type | Specimen File | Input Condition / Defect | Expected Finding Code | Expected Readiness State | Automated Test Reference | Status |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-DOC-01** | Tahsil Income Certificate | `valid_income_certificate.pdf` | Clean scan, FY 2026-27, ₹1,20,000, Tahsildar seal | `RULE_CHECK_PASSED` | `READY_FOR_APPLICATION` (100%) | `test_playwright_15_citizen_journeys.py::test_journey_01_golden_path_citizen` | **PASS** |
| **TC-DOC-02** | Tahsil Income Certificate | `expired_income_certificate.pdf` | Issued for FY 2021-22 (past period) | `INCOME_CERTIFICATE_EXPIRED_OR_WRONG_FY` | `CORRECTIONS_REQUIRED` ($\le 75\%$) | `test_playwright_15_citizen_journeys.py::test_journey_04_expired_document_citizen` | **PASS** |
| **TC-DOC-03** | Aadhaar Identity Card | `name_mismatch_aadhaar.pdf` | Name on card ("Anita Suresh Deshmukh") differs from profile | `PROFILE_DOCUMENT_NAME_MISMATCH` | `CORRECTIONS_REQUIRED` | `test_playwright_15_citizen_journeys.py::test_journey_06_profile_vs_document_name_mismatch_citizen` | **PASS** |
| **TC-DOC-04** | Tahsil Income Certificate | `income_exceeded_certificate.pdf` | Income ₹4,50,000 exceeds ₹2,50,000 ceiling | `INCOME_EXCEEDS_SCHEME_THRESHOLD` | `CORRECTIONS_REQUIRED` | `test_playwright_15_citizen_journeys.py::test_journey_09_inline_profile_correction_reactive_invalidation` | **PASS** |
| **TC-DOC-05** | Blurred Document | `unreadable_blur.pdf` | Gaussian blurred image (low contrast, unreadable) | `UNREADABLE_LOW_CONFIDENCE` | `CORRECTIONS_REQUIRED` / Missing | `test_playwright_15_citizen_journeys.py::test_journey_05_unreadable_document_citizen` | **PASS** |
| **TC-DOC-06** | Incomplete Multi-page PDF | `incomplete_multipage.pdf` | Page 1 present; page 2 (revenue seal & signature) missing | `INCOMPLETE_MULTI_PAGE_DOCUMENT` | `DOCUMENTS_PENDING` | `test_document_review.py::test_incomplete_multipage_pdf` | **PASS** |
| **TC-DOC-07** | Motor Driving License | `wrong_document_type.pdf` | Driving license uploaded where income/domicile needed | `WRONG_DOCUMENT_TYPE` | `DOCUMENTS_PENDING` | `test_playwright_15_citizen_journeys.py::test_journey_10_document_replacement_recovery` | **PASS** |
| **TC-DOC-08** | PDS Yellow Ration Card | `alternative_domicile_ration_card.pdf` | Yellow BPL ration card uploaded for domicile proof | `ANY_OF_GROUP_SATISFIED` | `READY_FOR_APPLICATION` | `test_playwright_15_citizen_journeys.py::test_journey_08_alternative_document_any_of_citizen` | **PASS** |
| **TC-DOC-09** | Domicile Certificate | `transliterated_name_certificate.pdf` | Name in Devanagari (*सुनीता रमेश पाटील*) vs Latin | `RULE_CHECK_PASSED` (Transliteration match) | `READY_FOR_APPLICATION` | `test_actionable_document_report.py::test_transliteration_matching` | **PASS** |
| **TC-DOC-10** | Aadhaar Number Redaction | Any Aadhaar specimen | Contains 12-digit Aadhaar number | `AADHAAR_NUMBER_MASKED` (`XXXX-XXXX-1234`) | Pass | `test_aadhaar_privacy.py::test_verhoeff_and_masking` | **PASS** |
| **TC-DOC-11** | Multi-page Field Conflict | 2-Page Certificate | Page 1 says ₹1,20,000; Page 2 says ₹1,80,000 | `DOCUMENT_FIELD_CONFLICT` | `CASEWORKER_REVIEW` | `test_pdf_conflicts.py::test_conflicting_income_fields_across_pages` | **PASS** |
| **TC-DOC-12** | Inline Extracted Edit | Any uploaded document | Citizen edits income from ₹1,20,000 to ₹1,50,000 | Field updated; audit log event generated | Recomputed dynamically | `test_playwright_15_citizen_journeys.py::test_journey_11_manual_review_low_confidence_attestation` | **PASS** |
| **TC-DOC-13** | Document Replacement | Faulty document in review | Citizen uploads fresh document via `[Replace Document]` | Previous document archived; new document audited | Updated to match new doc | `test_playwright_15_citizen_journeys.py::test_journey_10_document_replacement_recovery` | **PASS** |
| **TC-DOC-14** | Reactive Profile Update | Valid document in review | Profile income edited from ₹1,20,000 to ₹5,00,000 | `INCOME_EXCEEDS_SCHEME_THRESHOLD` | Reduced to $\le 75\%$ | `test_playwright_15_citizen_journeys.py::test_journey_09_inline_profile_correction_reactive_invalidation` | **PASS** |
| **TC-DOC-15** | State Persistence | Document Auditor session | Browser page reloaded via `F5` / `page.reload()` | Session restored from SQLite cookie | Preserves readiness & docs | `test_playwright_15_citizen_journeys.py::test_journey_12_persistence_resume_reload` | **PASS** |

---

## 3. Statutory Notice & Disclaimer Invariant

All document audit reports render the following statutory notice:
> **वैधानिक सूचना (Statutory Disclaimer):** *स्थानिक अल्गोरिदम व मशिन निष्कर्षण हे केवळ प्राथमिक पडताळणी व मार्गदर्शनासाठी आहे. अर्जाची अंतिम शासकीय मान्यता संबंधित सक्षम विभागामार्फतच दिली जाते.*  
> *(Local algorithmic and machine extraction is strictly for preliminary pre-checking and guidance. Final government approval is exclusively determined by the designated competent department).*
