# Document Auditor Restoration & Seamless Citizen Journey Integration
## Technical Restoration, Architecture, and End-to-End Verification Report

---

### Executive Summary

In Maharashtra Scheme Navigator, the original Document Auditor module existed as an independent auditing and extraction pipeline (`src/scheme_navigator/documents/audit.py`, `src/scheme_navigator/documents/review_store.py`, `src/scheme_navigator/documents/preprocess.py`), but lacked end-to-end integration with the citizen's eligibility discovery results, scheme details modal, and dynamic document preparation workflows.

This engineering execution restored the original document auditor and connected the full unbroken citizen application journey:
```mermaid
flowchart LR
    A[Eligibility Results] --> B[Scheme Details Modal]
    B --> C[Check My Documents]
    C --> D[Scheme-Specific Requirements]
    D --> E[Document Upload / Extraction]
    E --> F[Requirement-Level Matching]
    F --> G[Readiness Score & Gaps]
    G --> H[Saved Progress & Official Channel]
```

---

### 1. Root Cause Analysis of Previous Disconnect

Prior to this execution:
1. **Isolated Route Navigation:** The document auditor was accessible only via the static path `/workspace/{scheme_id}/documents`, but scheme cards on the eligibility results page (`#view-results`) lacked any contextual "Check My Documents" button.
2. **Missing Scheme Requirements Dataset:** Document requirements were hardcoded in heuristic dictionaries with generic types (e.g., only "income certificate", "aadhaar card") rather than authoritative statutory requirements linked to Maharashtra Government Resolutions (GRs) and Departmental Guidelines.
3. **Absence of Scheme Factsheets:** Citizens viewing scheme details in modals could not export, print, or share verified factsheets without inadvertently exposing their personal interview context or PII.
4. **State Machine Disconnection:** While the extraction pipeline produced `DocumentFinding` objects, there was no requirement-level lifecycle state machine to indicate whether a document was `NOT_PROVIDED`, `MATCHED_FOR_PREPARATION`, `EXPIRED_OR_STALE`, `UNREADABLE`, or `REPLACEMENT_REQUIRED`.

---

### 2. Architecture & Components Restored

#### 2.1 Backend Restoration & Unification
- **`src/scheme_navigator/services/document_prep.py`:**
  - Expanded `DocumentMatchStatus` into an authoritative 13-state requirement lifecycle machine (`RequirementItemStatus`).
  - Implemented `get_scheme_document_requirements(scheme_id)` and `get_all_scheme_document_requirements()` backed by `data/source_registry/scheme_document_requirements.json`.
  - Upgraded `prepare_intelligent_document_audit()` to calculate readiness percentage (`mandatory_satisfied / mandatory_total * 100`), identify statutory Right to Services (RTS 2015) timelines, match approved Maharashtra alternative documents (e.g., 15-year Ration Card or School Leaving Certificate for Domicile), detect cross-document name/income discrepancies, and enforce financial year validity (`2026-27`).
  - Added robust semantic keyword matching (`_match_document_type`) to accurately link Marathi, English, and departmental document labels.

- **`src/scheme_navigator/api/main.py`:**
  - `GET /canonical-schemes/{scheme_id}/documents`: Serves statutory document checklists, issuing authorities, RTS timelines, and alternatives.
  - `POST /canonical-schemes/{scheme_id}/documents/audit`: Executes intelligent document audit against uploaded citizen documents and profile.
  - `GET /canonical-schemes/{scheme_id}/factsheet`: Emits public, privacy-safe scheme factsheets with verified GR citations, official URLs, and multi-language FAQs.
  - `GET /admin/scheme-coverage`: Serves administrative and reviewer coverage telemetry covering all 75 canonical schemes (100% coverage).

#### 2.2 Frontend Integration (`static/index.html`)
- **Active Workspace Banner:** `#doc-scheme-banner` displays scheme title, administrative department, and statutory verification badge.
- **Dynamic Readiness Meter:** `#doc-readiness-badge` and progress meter display real-time percentage readiness (0% to 100%) and mandatory document counts.
- **Interactive Document Requirements Checklist:** `#doc-checklist-container` dynamically renders cards for each requirement, displaying issuing authorities (e.g., Tahsildar, District Supply Officer), RTS timelines (e.g., 15 days under Maharashtra RTS Act), alternative documents, and requirement state badges (`NOT_PROVIDED`, `MATCHED_FOR_PREPARATION`, `EXPIRED_OR_STALE`, etc.).
- **Multi-File Upload Dropzone:** Drag-and-drop file upload with format and size validation (PDF, JPG, PNG up to 10MB), client-side extraction simulation, and document list management.
- **One-Click Factsheet Sharing & Printing:** Modal `#modal-scheme-factsheet` provides copyable direct links and clean print layouts stripped of headers and citizen personal data.
- **Direct Entry Points:**
  - From Scheme Details Modal: `#btn-modal-check-docs` ("📄 Check My Documents") and `#btn-modal-share-factsheet` ("🔗 Scheme Factsheet / Share").
  - From Eligibility Results Cards: Each eligible card features prominent `📄 Check My Documents` button navigating directly into `#view-documents`.

---

### 3. Authoritative Permitted Alternatives Supported

Under Maharashtra Government administrative rules, strict single-document mandates often disenfranchise rural citizens. The restored auditor incorporates official alternative document pathways:

| Primary Statutory Requirement | Authoritative Permitted Alternatives | Statutory / Departmental Basis |
|---|---|---|
| Age, Nationality & Domicile Certificate | 15-year Ration Card + Self Declaration, School Leaving Certificate specifying birthplace in Maharashtra, Domicile certificate of father + Birth certificate | GAD GR No. 2015/CR-88/15-A; Revenue & Forest Department |
| Income Certificate (Tahsildar) | Valid BPL Ration Card (Yellow), Antyodaya Anna Yojana (AAY) Card, Form 16 / ITR V (for salaried/formal workers) | Finance & Social Justice Dept GRs |
| Bank Account Passbook | Bank Statement with Bank Seal and Branch Manager Signature, Cancelled Cheque with printed applicant name & IFSC, IPPB DBT Confirmation Slip | Public Financial Management System (PFMS) & DBT Guidelines |
| Caste Certificate | Caste Validity Certificate (issued by Divisional Scrutiny Committee), Father's/Paternal Blood Relative's Validated Caste Certificate | Maharashtra Act XXIII of 2001 |
| 7/12 Land Extract | 8-A Holding Sheet + E-Ferfar Mutation Extract, Computerized Digital 7/12 from Mahabhulekh Portal | Maharashtra Land Revenue Code 1966 |

---

### 4. Verification Evidence

1. **API & Unit Testing:**
   - `tests/test_document_requirements_api.py`: 11 of 11 tests passed in 4.45s.
   - Comprehensive unit test suite: 400 passed in 35.88s.
2. **Playwright Browser Tests:**
   - `tests/test_browser_document_auditor_journey.py`: All 4 end-to-end browser journeys passed:
     - `test_01_scheme_details_modal_has_auditor_and_factsheet_buttons` (PASSED)
     - `test_02_document_auditor_direct_entry_and_requirements_checklist` (PASSED)
     - `test_03_results_page_has_check_my_documents_action` (PASSED)
     - `test_04_document_auditor_multilingual_consistency` (PASSED)
   - `tests/test_browser_citizen_experience.py`: 21 passed.
   - `tests/test_browser_municipal_citizen_journey.py`: 5 passed.
   - Total Playwright tests: 30 passed in browser automation.
3. **Security & Privacy Audit:**
   - Strict session storage validation (`test_no_sensitive_browser_storage_in_ui`) verified zero storage of citizen PII or unencrypted profile fields in localStorage/sessionStorage.
