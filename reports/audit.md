# Phase 0 Read-Only Audit Report: Maharashtra Scheme Navigator
**Date:** 2026-11-18  
**Branch:** `feat/catalogue-v2`  
**Author:** Principal Engineer & Data Quality Lead  

---

## 1. System Map, Stack & Test Baseline

### 1.1 Architecture & Tech Stack
- **Backend Framework:** FastAPI 0.115+ served with Uvicorn on Python 3.11.4.
- **Data Validation & Schemas:** Pydantic v2 (`src/scheme_navigator/domain/models.py`, `src/scheme_navigator/source_registry/models.py`).
- **Rule Engine:** Deterministic JSON Logic AST evaluator (`RuleNode`) with three-valued logic (True, False, None/Unknown) supporting strict boundary comparisons (`eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `exists`) and temporal cut-off dates (`src/scheme_navigator/services/rule_engine.py`).
- **Data Persistence:** SQLite development and staging stores:
  - `data/citizen_profiles.sqlite3`: Citizen session profiles and provenance.
  - `data/document_reviews.sqlite3`: Human review records, caseworker audit notes, and OCR extraction findings.
  - `data/interviews.sqlite3`: LangGraph adaptive slot-filling interview checkpoints.
  - `data/ingestion.sqlite3`: Source ingestion manifests, content hashes, and lineage tracking.
- **Frontend Architecture:** Single Page Application (`static/index.html`) using vanilla JavaScript, Semantic HTML5, CSS custom properties adhering to Maharashtra State Government design tokens, and dual-language switching (English / Marathi). Separate casework review dashboard in `static/reviewer.html`.
- **Document Pre-Audit Pipeline:** Hybrid OCR + multimodal vision extractor (`src/scheme_navigator/documents/audit.py`) using Gemini Vision models (`GeminiVisionExtractor`) with local fallback, phonetic/transliteration name matcher (`compare_person_names`), and scheme-specific requirement matcher (`src/scheme_navigator/services/document_prep.py`).
- **How to Run the Application:**
  ```powershell
  & .venv\Scripts\python.exe -m uvicorn scheme_navigator.api.main:app --host 127.0.0.1 --port 8000
  ```

### 1.2 Existing Test Suite Status
- **Test Discovery:** Pytest collects **518 test items** across 43 test modules in `scheme-navigator/tests`.
- **Test Categories:**
  - `test_rule_boundary_matrix.py` (22 tests): Strict boundary conditions (income, age, temporal cut-offs, three-valued short circuiting).
  - `test_rule_engine.py` (15 tests): AST logic, unapproved fields rejection, deterministic evaluation.
  - `test_fail_closed_activation.py` (21 tests): Fail-closed production eligibility gates and legal metadata enforcement.
  - `test_auth_and_sessions_hardening.py` (9 tests): Session tokens, RBAC, cross-session isolation.
  - `test_browser_citizen_experience.py` (20 tests): Playwright browser verification of catalogue, interview, scoreboards, and navigation.
  - `test_browser_municipal_citizen_journey.py` (5 tests): Municipal schemes, PMC vs PCMC isolation, local body filtering.
  - `test_multilingual_voice.py` (11 tests): Marathi/English strings, privacy storage invariants (`test_no_sensitive_browser_storage_in_ui`).
  - `test_document_audit.py`, `test_document_upload.py`, `test_pdf_conflicts.py`: Document ingestion, OCR, and multi-page conflict detection.

---

## 2. Current Catalogue Audit & Criteria Distribution

### 2.1 Inventory Summary
- **Total Schemes in Canonical Registry (`data/source_registry/canonical_schemes.json`):** 75 schemes.
- **Active Demo Fixtures (`data/demo/schemes.json`):** 2 schemes (`demo-majhi-ladki-bahin`, `demo-indira-gandhi-old-age-pension`).
- **Candidate Schemes (`data/candidates/candidate_schemes.json`):** 7 schemes (`candidate-majhi-ladki-bahin`, `candidate-sanjay-gandhi-niradhar`, `candidate-shravanbal-nivruttivetan`, `candidate-post-matric-sc`, `candidate-post-matric-obc`, etc.).
- **Total Document Requirements (`data/source_registry/scheme_document_requirements.json`):** 319 requirements across 75 schemes.

### 2.2 Criteria Distribution & The Defect Breakdown
Analyzing the compiled rule trees in `CanonicalCatalogService`:
- **Schemes with ONLY Residency (`resident_state == 'maharashtra'`):** **54 of 75 schemes (72.0%)**.
- **Schemes with < 2 substantive criteria:** **56 of 75 schemes (74.7%)**.
- **Schemes with >= 2 substantive criteria:** **19 of 75 schemes (25.3%)**.

#### Schemes with >= 2 Substantive Criteria (Only 19 Total):
1. `demo-majhi-ladki-bahin` (5 criteria: gender, min_age, max_age, annual_family_income, aadhaar_linked_bank_account)
2. `demo-indira-gandhi-old-age-pension` (3 criteria: min_age, bpl, receiving_other_pension)
3. `candidate-majhi-ladki-bahin` (6 criteria: gender, min_age, max_age, income, bank_account, pension)
4. `candidate-post-matric-sc` (3 criteria: caste_category, is_student, annual_family_income)
5. `candidate-post-matric-obc` (3 criteria: caste_category, is_student, annual_family_income)
6. `candidate-post-matric-obc-girls-professional` (4 criteria: caste_category, gender, is_student, income)
7. `pcmc-free-bicycle-girls` (3 criteria: gender, municipal_corporation, residence_years)
8. `pcmc-sewing-machine-women` (3 criteria: gender, municipal_corporation, residence_years)
9. `pcmc-mscit-women` (3 criteria: gender, municipal_corporation, residence_years)
10. `pcmc-disability-scholarship` (2 criteria: municipal_corporation, residence_years)
11. `pcmc-disability-assistive-devices` (2 criteria: municipal_corporation, residence_years)
12. `pcmc-backward-class-scholarship` (2 criteria: municipal_corporation, residence_years)
13. `pmc-maulana-azad-scholarship` (2 criteria: municipal_corporation, residence_years)
14. `pmc-annabhau-sathe-scholarship` (2 criteria: municipal_corporation, residence_years)
15. `pmc-shahari-garib-arogya` (2 criteria: municipal_corporation, residence_years)
16. `bmc-anand-dighe-divyang` (2 criteria: municipal_corporation, residence_years)
17. `bmc-mahila-arthik-vikas` (3 criteria: gender, municipal_corporation, residence_years)
18. `tmc-divyang-kalyan` (2 criteria: municipal_corporation, residence_years)
19. `nmmc-divyang-education-grant` (2 criteria: municipal_corporation, residence_years)

#### Major Flagship Schemes Currently Stuck on Lone-Residency:
- `candidate-sanjay-gandhi-niradhar-anudan`: SGNAY (`resident_state == 'maharashtra'` only)
- `candidate-shravanbal-sewa-rajya-nivruttivetan`: Shravanbal (`resident_state == 'maharashtra'` only)
- `scheme-ebc-tuition-waiver`: EBC tuition waiver (`resident_state == 'maharashtra'` only)
- `scheme-majhi-kanya-bhagyashree`: MKBY (`resident_state == 'maharashtra'` only)
- `scheme-bhausaheb-fundkar-phalbag`: Phalbag Lagwad (`resident_state == 'maharashtra'` only)
- `scheme-punyashlok-ahilyadevi-holkar-post-matric`: Post-matric girls hostel (`resident_state == 'maharashtra'` only)
- `scheme-ramai-gharkul`: Ramai Awas Gharkul (`resident_state == 'maharashtra'` only)
- `scheme-shabari-gharkul`: Shabari Awas Gharkul (`resident_state == 'maharashtra'` only)
- `scheme-namo-shetkari-mahasanman`: Namo Shetkari (`resident_state == 'maharashtra'` only)
- `scheme-balasaheb-thackeray-accident-insurance`: Accident insurance (`resident_state == 'maharashtra'` only)

---

## 3. Root Cause Analysis: How Rules Flow and Why Lone-Residency Occurs

The investigation definitively traced the rule lifecycle from data files to the citizen UI:

```
+-------------------------------------------------------------+
| 1. data/source_registry/canonical_schemes.json              |
| Raw text fields: age_requirements: "21 - 65 Years",        |
| family_income_requirements: "<= ₹2,50,000", gender, etc.    |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| 2. src/scheme_navigator/services/catalog.py                 |
| CanonicalCatalogService._load()                             |
| Checks: if cid in demo_schemes: load demo AST               |
|         elif cid in cand_schemes: load candidate AST        |
|         else: fallback loop:                                |
|           children = [RuleNode(field='resident_state',      |
|                                op='eq', value='maharashtra')]|
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| 3. src/scheme_navigator/services/rule_engine.py             |
| evaluate_scheme() evaluates RuleNode tree.                 |
| Since rule contains ONLY resident_state == 'maharashtra',   |
| citizen with resident_state='maharashtra' gets TRUE.        |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| 4. Production Fail-Closed Gate                              |
| check_production_eligibility_gate() flags lack of legal     |
| approval metadata -> Status downgraded to CASEWORKER_REVIEW |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| 5. static/index.html (UI Renderer)                          |
| renderResultsCards iterates condition_evaluations:          |
| Emits exactly 1 bullet: "✓ resident_state must equal        |
| 'maharashtra'".                                             |
+-------------------------------------------------------------+
```

### The Root Cause
In `CanonicalCatalogService._load()` (lines 100–160 of `catalog.py`):
For 68 out of 75 schemes in `canonical_schemes.json`, there was no compiled `RuleNode` tree. The code fell back to synthesizing a placeholder tree containing only:
```python
RuleNode(op="eq", field="resident_state", value="maharashtra", condition_id=f"c_{cid.replace('-', '_')}_state")
```
It completely bypassed the descriptive eligibility criteria present in the metadata fields (`age_requirements`, `family_income_requirements`, `social_category_requirements`, etc.), because these were stored as unstructured free text without compiled JSON Logic representations and without verbatim source quote validation.

---

## 4. Current Document-Review Pipeline Audit

### 4.1 Ingestion & Extraction Architecture
- **Entry Points:**
  - `POST /documents/upload`: Generic multipart file upload with OCR extraction.
  - `POST /canonical-schemes/{scheme_id}/documents/audit`: Scheme-specific document audit evaluating uploaded documents against scheme requirements.
- **Vision Models:** `GeminiVisionExtractor` calling Google Gemini Vision with schema `GeminiCertificateExtraction` extracting:
  - `document_type`, `applicant_name`, `date_of_birth`, `age_years`, `income_amount`, `valid_financial_year`, `valid_until`, `issuing_authority`, `certificate_number`, `caste_category`.
- **Supported Document Types:**
  - `income_certificate` (उत्पन्नाचा दाखला)
  - `domicile_certificate` (अधिवास प्रमाणपत्र)
  - `caste_certificate` (जात प्रमाणपत्र)
  - `disability_certificate` (दिव्यांग प्रमाणपत्र)
  - `ration_card` (शिधापत्रिका)
  - `seven_twelve_extract` (७/१२ उतारा)
  - `aadhaar_card` (आधार कार्ड)
  - `bank_passbook` (बँक पासबुक)

### 4.2 Checks Currently Performed (`src/scheme_navigator/documents/audit.py`)
1. **Extraction Confidence Check:** Flags `LOW_EXTRACTION_CONFIDENCE` when confidence < 0.75.
2. **Document Expiration:** Flags `CERTIFICATE_EXPIRED` if `valid_until` < today.
3. **Financial Year Matching:** Flags `FINANCIAL_YEAR_MISMATCH` if document FY does not match the target financial year.
4. **Missing FY on Income Certificates:** Flags `INCOME_FY_NOT_EXTRACTED`.
5. **Cross-Document Name Consistency:** Checks applicant names across documents using `compare_person_names()`, which applies Jaro-Winkler string similarity with transliteration heuristics between Devanagari and Latin scripts.
6. **Multi-Page Conflict Detection:** Flags conflicting income numbers across different pages of a single PDF (`add_pdf_page_conflict_findings`).

### 4.3 Hardcoded & Brittle Elements Identified
- **Target Financial Year:** Hardcoded default `target_financial_year = "2026-27"` in `audit.py`.
- **Hardcoded Type Mappings:** Static dictionary `direct_types` in `_match_document_type()` in `document_prep.py`.
- **Missing Income Threshold Comparison:** The document auditor extracts `income_amount`, but did not compare it directly against the scheme's compiled numerical income limit (e.g. ₹2,50,000 for Ladki Bahin or ₹8,00,000 for EBC).
- **Missing Age / DOB Comparison:** The auditor extracts `date_of_birth`, but did not evaluate it against the scheme's minimum/maximum age boundaries.
- **Missing Direct User Prompting on Mismatch:** When an uploaded document differed from an interview answer, the UI lacked a prominent confirmation prompt for the citizen to update their profile or re-upload.

---

## 5. Risk Assessment (48-Hour Deadline)

| Risk Factor | Severity | Threat to 48h Deadline | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Government Portal Rate Limiting & Bot Blocks** | High | Scraping official GR and department portals may trigger HTTP 429/403 blocks. | Tier 1 local caching under `data/raw/` with SHA-256 hash digests; respect robots.txt (2s throttle); fallback to official archive snapshots. |
| **Scanned Marathi PDF OCR Fidelity** | High | Government Resolutions (GRs) in Maharashtra are frequently raster scans without embedded text. | Multi-tier OCR: PyPDF/pdfplumber text extraction first, Tesseract Devanagari (`mar+eng`) and Gemini multimodal vision fallback. Verbatim quote verifier strictly requires substring match. |
| **Regression in 518 Existing Pytest Tests** | Medium | Changing `Scheme` or `CanonicalSchemeRecord` schemas could break existing tests. | Contract-first migration: Extend models backward-compatibly in `domain/catalogue_v2.py` and bridge through `CanonicalCatalogService`. |
| **Data Protection & PII Violations** | High | Aadhaar numbers present in test certificates or real documents leaking into logs. | Automatic regex + Verhoeff checksum validator masking all Aadhaar numbers to `XXXX-XXXX-1234` before any LLM call or disk logging. |
| **Scope Overrun Across 75 Schemes** | High | Attempting manual GR research on all 75 schemes in 48h could exhaust time. | Strict Tiering: Focus 100% full verification and golden personas on **Tier A** (15+ flagship schemes); automate cross-checks on Tier B; mark remaining Tier C as exploratory. |

---

## 6. Audit Verdict & Immediate Next Action

The audit confirms that the core engine, UI framework, and document extraction pipeline are sound, but the catalogue and rule compilation layer suffered from a severe bottleneck: fallback generation of dummy residency-only rules.

**Immediate Next Action:** Transition to **Phase 1: Contract-First Data Model**. Define `catalogue_v2.py` with strict Pydantic v2 schemas, create the Canonical Profile Vocabulary registry, implement the hard validator for `< 2 substantive criteria`, and write the CI guard test.
