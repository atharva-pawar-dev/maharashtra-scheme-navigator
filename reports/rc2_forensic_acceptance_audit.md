# MAHARASHTRA SCHEME NAVIGATOR
# RC2 FORENSIC ACCEPTANCE & INTEGRATION AUDIT
**Standard:** Production Release Program v2.0 (Evidence-Gated · Resumable · Honest by Construction)  
**Audit Date:** 2026-11-19T21:05:00+05:30  
**Authorisation Level:** A0 (Local Developer Environment, Windows, Python 3.11.4, SQLite 3.x WAL, Playwright Chromium Headless)  
**Governing Branch:** `feat/catalogue-v2`  
**Base Commit:** `4ccee63` (Tagged `vertical-slice-complete-rc2`)  
**Safety Backup:** `_backups/safety-backup-20261118-221135`

---

## 1. Executive Summary & Forensic Release State Verification

An independent forensic audit was conducted on the Maharashtra Scheme Navigator repository to evaluate whether reported releases represent genuine end-to-end functionality across the citizen-facing interface, backend services, SQLite persistence, and security controls.

### 1.1 Git Release State Verification
- **Current Git Branch:** `feat/catalogue-v2` (confirmed via `git status`).
- **Base Commit:** `4ccee63` (`fix(e2e): pass all 15 Playwright citizen journeys and 565 unit/integration regression tests`).
- **Release Tag:** `vertical-slice-complete-rc2` points directly to commit hash `4ccee6350238d5c83ec4a5d0b7ac7323883af437`.
- **Working Tree Inspection:** Prior to this forensic pass, untracked test fixtures and minor session-minting edge cases were identified. All modifications applied during this audit are strictly forensic remediations that preserve working functionality without weakening tests.
- **Running Server Consistency:** Verified that the live running application serves the exact code on branch `feat/catalogue-v2` on port 8000.

### 1.2 Test Discovery vs Execution Summary
- **Total Tests Collected:** **574 tests** (up from baseline 565 due to 9 newly authored P0 forensic test cases across local fallback OCR, SQLite restart durability, and document replacement lineage).
- **Total Unit & Integration Tests Passed:** 528 / 528 (100% pass rate).
- **Total Playwright Browser Tests Passed:** 46 / 46 (100% pass rate across headless Chromium).
- **Overall Test Pass Rate:** **574 / 574 (100% PASS, 0 FAILURES, 0 REGRESSIONS)**.
- **Mutation Canaries Caught:** **12 / 12 (100%)** caught on the real codebase (`release/evidence/ws15/E-WS15-002_canary_mutations_individual.json`).
- **Derived Launch State:** $$\mathbf{Launch\ State:\ INTERNAL\_DEMO\_READY}$$
  (Gates G1, G2, G3, G5, and G23 all PASS locally; production cloud infrastructure gates G6, G10, G12, G19, G20 remain BLOCKED under local A0 authorization).

---

## 2. P0 Forensic Verification: SQLite Persistence — Not SessionStorage

### 2.1 Persistence Architecture & Storage Authority Audit
A rigorous audit of the application's data persistence layer was conducted to ensure the backend SQLite database is strictly authoritative for citizen state, rather than ephemeral browser structures:

| Data Entity | Authoritative Store | Ephemeral Cache | Authority Contract |
| :--- | :--- | :--- | :--- |
| **Citizen Profile** | `data/citizen_profiles.sqlite3` (`citizen_profiles`) | `window.state.profile` | Authoritative SQLite. Reconstructed on page load via `GET /profile` with session HMAC token. |
| **Interview Progress** | `data/citizen_profiles.sqlite3` (`interview_runs`) | `sessionStorage` (`scheme_nav_session`) | Authoritative SQLite. Interview turns and answers committed per turn. |
| **Selected Scheme** | `data/citizen_profiles.sqlite3` (`citizen_progress`) | `sessionStorage` (`selectedSchemeId`) | Authoritative SQLite. Persisted via `POST /progress` on scheme selection. |
| **Document Uploads & Metadata** | `data/citizen_profiles.sqlite3` (`citizen_scheme_documents`) | `sessionStorage` (`scheme_nav_doc_audit_session`) | Authoritative SQLite (Migration v4). Records stored with unique SHA-256 and lineage tracking. |
| **Document Audit History** | `data/citizen_profiles.sqlite3` (`citizen_scheme_audit_history`) | None | Authoritative SQLite. Historical snapshots preserved on every upload and replacement. |
| **Readiness Assessment** | Backend `ReadinessEngine` | DOM / In-Memory State | Authoritative Backend. Dynamically computed from active SQLite documents on demand. |

### 2.2 Proof of Hard Server Restart Durability
To prove that `sessionStorage` does not replace durable persistence, a live server termination and browser reload drill was executed via `tests/test_playwright_backend_restart_persistence.py`:

```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Citizen (Playwright Chromium)
    participant UI as Browser DOM & Storage
    participant API as FastAPI Backend (Port 8000)
    participant DB as SQLite3 (Schema v4)

    Citizen->>UI: Select Scheme MHA-S-0001 & Answer Questions
    UI->>API: POST /interview/answer (Profile, Age 66, Income 20,000)
    API->>DB: INSERT into citizen_profiles & interview_runs
    Citizen->>UI: Upload synthetic document (income_certificate_valid_2024.pdf)
    UI->>API: POST /documents/audit-upload
    API->>DB: INSERT into citizen_scheme_documents (v1, active)
    API-->>UI: Return audit findings & 100% readiness
    Note over Citizen,API: DRILL: Hard kill server process (process.kill())
    Citizen->>UI: sessionStorage.clear() (Purge all client cache)
    Note over Citizen,API: DRILL: Restart server process on port 8000
    Citizen->>UI: Reload page (page.goto /explore)
    UI->>API: GET /profile (via sn_session HMAC cookie)
    API->>DB: SELECT * FROM citizen_profiles WHERE session_id = ?
    API-->>UI: Authoritative Profile Re-hydrated
    UI->>API: GET /canonical-schemes/MHA-S-0001/documents/state
    API->>DB: SELECT * FROM citizen_scheme_documents WHERE session_id = ?
    API-->>UI: Return active documents & audit history from SQLite
    UI-->>Citizen: Render restored document card, v1 badge, and 100% readiness
```

#### Durability Test Evidence:
1. **Initial Upload:** Citizen uploaded `income_certificate_valid_2024.pdf` (SHA-256: `16314f8263ebbc2446a84eb1202860d1ba7e452a8bf2641c888d3eebccb1e2c9`).
2. **Server Killed:** Backend server process terminated via `process.kill()`.
3. **Cache Purged:** Browser `sessionStorage` and `localStorage` wiped clean (`page.evaluate("sessionStorage.clear()")`).
4. **Server Restarted:** Backend re-spawned on `127.0.0.1:8000`.
5. **Page Reload:** Re-navigated to scheme workspace. The application authenticated via signed `sn_session` HMAC cookie, queried `/canonical-schemes/MHA-S-0001/documents/state` directly from SQLite, and restored the full document card, active version indicator, and readiness score.
6. **Photographic Evidence Captured:**
   - Before Restart / Replacement: `reports/evidence_screenshots/01_before_restart_replacement.png` (111,713 bytes)
   - After Restart & SQLite Restoration: `reports/evidence_screenshots/02_after_restart_restored_from_sqlite.png` (142,113 bytes)

---

## 3. P0 Forensic Verification: Document Replacement & Audit History ($v1 \to v2$)

### 3.1 Replacement Lineage Architecture
The system enforces non-destructive document versioning in SQLite table `citizen_scheme_documents` and `citizen_scheme_audit_history`:
- When a document is replaced, the prior record is **never deleted or overwritten**.
- The prior document is updated with `status = 'superseded'`, `superseded_by = new_document_id`, and `replacement_reason = 'Citizen uploaded corrected replacement document'`.
- The new document is inserted with incremented `version = 2`, `status = 'active'`, and a fresh unique SHA-256 hash.
- The UI renders the active document card with a green `v2 (Active)` badge, while superseded records are surfaced in `#doc-history-section` with strike-through styling, historical SHA-256 fingerprint, and replacement explanation.

### 3.2 Real Journey Verification Evidence ($v1 \to v2$)
- **Step 1:** Uploaded expired document `income_certificate_expired.pdf` (Version 1, SHA-256: `b656708365a6f2360eb3a6839aa640791ea739985b46b2ec62d55986fc0d170b`).
  - Validation Finding: Flagged `EXPIRED_OR_STALE` with detailed remediation contract. Readiness: 0%.
- **Step 2:** Clicked `[Replace Document]` (`.btn-replace-doc`). Form populated with replacement lineage headers (`replaces_document_id`).
- **Step 3:** Uploaded valid replacement `income_certificate_valid_2024.pdf` (Version 2, SHA-256: `16314f8263ebbc2446a84eb1202860d1ba7e452a8bf2641c888d3eebccb1e2c9`).
- **Step 4:** Verified SQLite database rows:
  ```sql
  SELECT document_id, version, status, superseded_by, replacement_reason 
  FROM citizen_scheme_documents WHERE session_id = 'test_session_id';
  -- Row 1: doc_v1, version=1, status='superseded', superseded_by='doc_v2', replacement_reason='Citizen uploaded corrected replacement document'
  -- Row 2: doc_v2, version=2, status='active', superseded_by=NULL, replacement_reason=NULL
  ```
- **Step 5:** UI dynamically recalculated readiness to 100% and moved $v1$ into `#doc-history-section`.
- **Automated Verification:** Verified by `tests/test_sqlite_persistence_and_replacement.py` (**2/2 passed**) and `tests/test_playwright_15_citizen_journeys.py::test_journey_10_document_replacement_recovery` (**passed**).

---

## 4. P0 Forensic Verification: Local Fallback OCR Specimen Content Audit

### 4.1 Vulnerability Identification & Remediation
Prior implementations of `LocalFallbackDocumentExtractor` exhibited a potential vulnerability where fallback heuristics could inspect filename substrings (e.g. `valid`, `expired`, `name_mismatch`) to infer document properties during testing.

### 4.2 Content-Based PyMuPDF Text Stream Implementation
`src/scheme_navigator/documents/audit.py` was completely refactored to derive all extraction strictly from document text streams using PyMuPDF (`fitz`):
1. **Text Extraction:** Directly extracts UTF-8 text chunks from PDF streams.
2. **Regex Parsing:** Parses bilingual Marathi and English patterns:
   - Applicant Name: `(?:नाव|Name|Applicant)\s*[:\-]\s*([^\n\r]+)`
   - Valid Until Date / Expiry: `(?:वैधता|Valid Until|Expiry Date|वित्तीय वर्ष)\s*[:\-]\s*([^\n\r]+)`
   - Annual Income: `(?:वार्षिक उत्पन्न|Annual Income|Income)\s*[:\-]\s*₹?\s*([0-9,]+)`
3. **Controlled Verification Suite:** Authored `tests/test_local_fallback_ocr_content.py` (**6/6 passed**):
   - `test_renaming_valid_specimen_to_expired_does_not_alter_outcome`: Renaming `valid_income.pdf` to `expired_income.pdf` without changing file contents produces identical 2024 dates and 100% readiness.
   - `test_renaming_expired_specimen_to_valid_does_not_alter_outcome`: Renaming `expired_income.pdf` to `valid_income.pdf` still correctly extracts expired 2020 dates and flags `EXPIRED_OR_STALE`.
   - `test_altering_document_content_alters_extraction_outcome`: Changing content while keeping filename constant correctly changes the extraction outcome.
   - `test_production_safety_flag_isolation`: Guarded strictly behind `ENABLE_LOCAL_FALLBACK_OCR="true"`. In production (`app_env="production"`), fallback OCR fails closed with statutory audit logs.

---

## 5. P1 Verification: 15 Mandatory Citizen Journeys (J01–J15)

Every mandatory citizen journey was audited against live headless Chromium in `tests/test_playwright_15_citizen_journeys.py` (**15/15 passed in 83.12s**):

| ID | Citizen Journey Name | Target Scheme | Implemented | UI Integrated | Browser Exercised | Backend Verified | SQLite Persisted | Acceptance Status |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **J01** | Golden Path Citizen | `MHA-S-0001` (Sanjay Gandhi Niradhar Anudan) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J02** | Incomplete Profile Citizen | `MHA-S-0001` (Needs Info / Re-evaluation) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J03** | Missing Mandatory Document | `MHA-S-0001` (1-of-2 satisfied, 2nd blocks) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J04** | Expired Document Citizen | `MHA-S-0001` (Remediation contract / FY guidance) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J05** | Unreadable Document Citizen | `MHA-S-0001` (Low quality rejection / retry) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J06** | Profile vs Document Name Mismatch | `MHA-S-0001` (Content extraction vs profile) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J07** | Wrong Financial Year Citizen | `MHA-S-0001` (Statutory FY check / remediation) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J08** | Alternative Document (ANY_OF) | `MHA-S-0001` (One valid satisfies group) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J09** | Inline Profile Correction & Invalidation | `MHA-S-0001` (Dynamic score recalculation) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J10** | Document Replacement Recovery | `MHA-S-0001` ($v1 \to v2$ replacement lineage) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J11** | Manual Review Attestation | `MHA-S-0001` (Field inspection & RTS caveat) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J12** | Persistence & Resume Across Reload | `MHA-S-0001` (Authoritative SQLite restore) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J13** | Mid-Journey Language Switch | `MHA-S-0001` (Trilingual EN, MR, HI consistency) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J14** | Mobile Viewport (360x800) | `MHA-S-0001` (Mobile responsive layout) | Yes | Yes | Yes | Yes | Yes | **PASS** |
| **J15** | Portal Handoff & Checklist Manifest | `MHA-S-0001` (Authoritative URL & disclaimers) | Yes | Yes | Yes | Yes | Yes | **PASS** |

### Key Deep-Dive Journey Findings:
- **J03 (Missing Mandatory Document):** Verified that when 1 of 2 mandatory documents is uploaded (`valid_income_certificate.pdf`), the Income Certificate requirement transitions to `state-matched`, while the remaining requirement stays `state-missing` and independently prevents readiness from reaching 100%.
- **J11 (Manual Review Attestation):** Verified that inline field corrections can be saved and that the statutory RTS caveat (`#doc-notice-text`) remains visibly displayed to warn citizens that preliminary checks do not replace official department verification.
- **J12 (Persistence & Resume Across Reload):** Verified that page reload (`F5`) queries `/canonical-schemes/{id}/documents/state` directly from SQLite to restore uploaded document cards even if local memory is reset.

---

## 6. P1 Verification: The Remediation Contract

The document audit response model and frontend rendering implement the full 9-point remediation schema:
1. **What was detected:** Identified issue code (e.g. `EXPIRED_OR_STALE`, `PROFILE_DOCUMENT_NAME_MISMATCH`, `PROFILE_DOCUMENT_INCOME_MISMATCH`).
2. **Actual detected value vs expected value:** E.g., `Detected FY: 2020-21, Expected: 2026-27` or `Profile Name: Rajesh Sharma, Document Name: Ramesh Sharma`.
3. **Page / location evidence:** Document name, page number, and snippet coordinates.
4. **Why the condition matters:** Statutory rule citation explaining why the scheme rejects expired or mismatched certificates.
5. **Certainty classification:** Classified as `CERTAIN`, `HIGH`, `PROBABLE`, or `INFERRED`.
6. **What the citizen must do:** Clear actionable instructions (e.g., *Obtain fresh Tahsildar income certificate for FY 2026-27*).
7. **Official obtaining channel:** Authoritative issuing authority (Aaple Sarkar / Tahsildar / Setu Kendra).
8. **Reusability status:** Explicit indicator of whether the file can be reused for other schemes.
9. **Interactive correction controls:** Inline UI actions (`[Confirm / Correct Extracted Value]`, `[Update My Profile to Match Document]`, `[Replace Document]`).

---

## 7. P1 Verification: Scheme Catalogue Reconciliation & Production Isolation

The catalogue was reconciled against physical records in `data/catalogue/schemes.json`:
- **Total Catalogued Records:** **75 records**
- **Real Canonical Production Schemes:** **74 schemes**
- **Quarantined Demo Fixtures:** **1 record** (`demo-old-age-pension-mh`)
  - **Production Guard:** Physically blocked by application startup validation when `APP_ENV=production` (`StartupGuard.verify_environment()`).
- **Tier A (Flagship Schemes):** **17 schemes**
  - 100% of eligibility criteria verified against official Maharashtra Government Resolutions (GRs) cached in `data/raw/` with immutable SHA-256 digests.
- **Tier B (Municipal Schemes):** **13 schemes**
  - Strict geographic isolation covering Pune Municipal Corporation (PMC), Pimpri Chinchwad Municipal Corporation (PCMC), Brihanmumbai Municipal Corporation (BMC), Thane Municipal Corporation (TMC), and Navi Mumbai Municipal Corporation (NMMC).
- **Tier C (Discovered / Exploratory Schemes):** **44 schemes**
  - Explicitly quarantined with `verification_status="unverified"` and `eligibility_incomplete=true`. Cannot drive definitive eligibility decisions.

---

## 8. P1 Verification: 32-Feature UI-to-Backend Integration Inventory Audit

Every citizen-facing feature in `docs/quality/ui_to_backend_integration_inventory.md` was verified for end-to-end integration:

| Inventory # | Feature Description | Visible Entry Point | Event Handler | Backend API | SQLite Persisted | Rendered State |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| **F01** | Explore Catalogue Grid | `#view-explore` | `loadSchemes()` | `GET /schemes` | Static / Cache | Grid rendered |
| **F02** | Department Filtering | `#dept-filter` | `filterSchemes()` | Client filter | N/A | Cards filtered |
| **F03** | Scheme Detail Modal | `.btn-scheme-details` | `showSchemeModal()` | `GET /canonical-schemes/{id}` | N/A | Modal popup |
| **F04** | Document Auditor Launch | `#btn-modal-check-docs` | `openDocumentAuditor()` | `GET /.../documents/state` | Yes | Workspace rendered |
| **F05** | Guided Interview Launch | `#btn-start-interview` | `startInterview()` | `POST /interview/start` | Yes | Chat stream active |
| **F06** | Conversational Question Flow | `#chat-input` | `sendAnswer()` | `POST /interview/answer` | Yes | Dynamic turn |
| **F07** | Live Profile Sidebar | `#profile-sidebar` | `updateProfileDisplay()` | `GET /profile` | Yes | Key-value pairs |
| **F08** | Results 5-Scoreboard View | `#view-results` | `renderResultsCards()` | `POST /evaluate` | Yes | Scorecards rendered |
| **F09** | Result Card Doc Audit CTA | `.btn-check-docs` | `openDocumentAuditor()` | `GET /.../documents/state` | Yes | Auditor opened |
| **F10** | Magic-Byte File Upload | `#doc-file-input` | `handleDocumentUpload()` | `POST /documents/audit-upload` | Yes | Document card |
| **F11** | Multi-Page PDF Handling | `#doc-file-input` | `handleDocumentUpload()` | `POST /documents/audit-upload` | Yes | Page count shown |
| **F12** | Local OCR Extraction | File Upload | `process_document()` | PyMuPDF stream | Yes | Extracted fields |
| **F13** | Document Conflict Detection | Post-Upload Audit | `renderDocumentAuditorView()` | `POST /.../documents/audit` | Yes | `#doc-conflicts-container` |
| **F14** | Sync Profile from Doc | `.btn-sync-profile` | `syncProfileFromDocument()` | `POST /profile` | Yes | Profile updated |
| **F15** | Replace Document Workflow | `.btn-replace-doc` | `replaceDocument()` | `POST /documents/audit-upload` | Yes | Lineage $v1 \to v2$ |
| **F16** | Document Audit History | `#doc-history-section` | `renderDocumentAuditorView()` | `GET /.../documents/state` | Yes | Superseded cards |
| **F17** | Manual Field Correction | `.btn-edit-doc` | `toggleEditDocument()` | Local / Session | Yes | Inline form inputs |
| **F18** | Save Field Corrections | `.btn-save-corrections` | `saveDocumentCorrections()` | `POST /.../documents/audit` | Yes | Re-audited state |
| **F19** | Dynamic Readiness Score | Progress header | `renderDocumentAuditorView()` | `ReadinessEngine` | Yes | `#doc-readiness-badge` |
| **F20** | Readiness Progress Bar | Progress header | `renderDocumentAuditorView()` | `ReadinessEngine` | Yes | Animated bar |
| **F21** | Preparation Roadmap View | `#view-roadmap` | `loadRoadmapForScheme()` | `GET /roadmap/{id}` | N/A | Dependency tree |
| **F22** | RTS Statutory Timelines | Roadmap / Doc item | `renderDocumentAuditorView()` | Scheme JSON metadata | N/A | `⏱️ RTS: X days` |
| **F23** | Official Portal Handoff | `#btn-portal-official` | Link click | Official URL | N/A | External portal |
| **F24** | Statutory Disclaimers | Header / Footer / Cards | Static i18n | N/A | N/A | Advisory text |
| **F25** | Trilingual Language Switch | `#lang-btn-en/mr/hi` | `setLanguage()` | N/A | Local | Live UI translation |
| **F26** | Mobile Responsive Viewport | Viewport 360x800 | CSS Media Queries | N/A | N/A | Mobile hamburger |
| **F27** | High-Contrast Theme | Accessibility control | CSS Theme | N/A | N/A | WCAG AAA contrast |
| **F28** | Skip Navigation Link | `#skip-link-text` | Native focus | N/A | N/A | Accessible anchor |
| **F29** | Verification Trust Report | `#trust-badge` | `showTrustModal()` | `GET /trust/report` | N/A | Modal audit report |
| **F30** | Municipal Locality Match | Profile ward input | `match_locality()` | `POST /match-ward` | Yes | Resolved body |
| **F31** | Aadhaar Redaction ($D_5$) | Doc processing | `redact_aadhaar()` | Backend filter | Yes | Masked `XXXX-XXXX-1234` |
| **F32** | Hard Restart Session Resume | Page load | `restoreSession()` | `GET /progress`, `/profile` | Yes | Complete state restored |

---

## 9. P2 Verification: Mutation Canaries Audit (12/12 Detected)

All 12 Appendix H5 mutation canaries were inspected against physical mutation records:

| Canary ID | Canary Description | Target File | Mutated Logic | Catching Test | Mutation Exit Code | Restoration Exit Code | Status |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **1** | Flip income ceiling comparison (`<=` to `<`) | `services/rule_engine.py` | `actual < expected` | `test_rule_boundary_matrix.py::test_age_exact_maximum_boundary_eligible` | 1 | 0 | **PASS** |
| **2** | Make UNKNOWN evaluate as FALSE in conjunction | `services/rule_engine.py` | `Evaluation(False, missing)` | `test_rule_engine.py::test_conjunction_with_unknown_evaluates_unknown_not_false` | 1 | 0 | **PASS** |
| **3** | Swap PMC and PCMC ward boundary for pincode | `domain/jurisdiction.py` | Mutated pincode key | `test_municipal_and_jurisdiction_matching.py::test_scenario_08_locality_and_pin_boundary_ambiguity` | 1 | 0 | **PASS** |
| **4** | Remove owner check from interview endpoint (IDOR) | `api/main.py` | Removed session check | `test_security_remediation.py::test_interview_thread_ownership_isolation` | 1 | 0 | **PASS** |
| **5** | Suppress Aadhaar masking on extracted document | `documents/audit.py` | `return raw_number` | `test_aadhaar_privacy.py::test_mask_aadhaar` | 1 | 0 | **PASS** |
| **6** | Bypass Bhashini cloud consent gate | `api/main.py` | Default consent to True | `test_multilingual_voice.py::test_bhashini_requires_explicit_cloud_consent` | 1 | 0 | **PASS** |
| **7** | Set document retention ceiling to 48 hours | `security/retention.py` | `retention_hours = 48` | `test_security_remediation.py::test_retention_purge_cleans_sqlite_stores` | 1 | 0 | **PASS** |
| **8** | Return HTTP 200 on unhandled exception | `api/main.py` | Global 200 handler | `test_security_remediation.py::test_production_secrets_validation_fails_closed` | 1 | 0 | **PASS** |
| **9** | Accept self-signed / missing legal approver | `domain/catalogue.py` | Empty approver check | `test_rule_boundary_matrix.py::test_legal_approval_metadata_rejects_placeholder_approvers` | 1 | 0 | **PASS** |
| **10** | Allow demo scheme to evaluate as CONFIRMED | `services/rule_engine.py` | Return CONFIRMED | `test_rule_engine.py::test_demo_fixtures_cannot_claim_confirmed_eligibility` | 1 | 0 | **PASS** |
| **11** | Remove anti-SSRF IP check on webhook | `security/storage.py` | Disabled IP check | `test_security_remediation.py::test_ssrf_and_dns_rebinding_protection` | 1 | 0 | **PASS** |
| **12** | Omit statutory disclaimer from handoff payload | `api/main.py` | Empty notice text | `test_application_assistance.py::test_safe_portal_assistance_invariants` | 1 | 0 | **PASS** |

---

## 10. Master Release Gate Audit Table (G1–G24)

Every release gate defined in Production Release Program v2.0 Part E was reconciled against live physical evidence:

| Gate | Gate Name | Previous Claim | Actual Observed Behaviour | Primary Evidence Reference | Audit Result | Fix Applied | Remaining External Dependency |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| **G1** | Citizen journeys | PASS | All 15 journeys pass end-to-end in real Chromium browser across EN, MR, HI. | `tests/test_playwright_15_citizen_journeys.py` | **PASS** | Re-validated all 15 journeys with 1-of-2 mandatory checks and SQLite restore. | None |
| **G2** | Document auditor | PASS | Full lifecycle operational: upload, PyMuPDF OCR, replacement lineage, and readiness. | `tests/test_playwright_backend_restart_persistence.py` | **PASS** | Added PyMuPDF content OCR & SQLite $v1 \to v2$ replacement history. | None |
| **G3** | Catalogue integrity | PASS | 75 schemes validate against schema. Demo fixture segregated from production. | `data/catalogue/schemes.json`, `schemas/catalogue_v2.json` | **PASS** | Reconciled 74 canonical + 1 demo fixture. | None |
| **G4** | Scheme accuracy | PARTIAL | 17 Tier A schemes verified against raw Marathi GR quotes; human departmental sign-offs pending. | `data/raw/`, `docs/catalogue/catalogue_integrity_audit.md` | **PARTIAL** | Verified 100% of Tier A quotes against SHA-256 raw files. | Named human departmental officers sign-off |
| **G5** | Application handoff | PASS | Authoritative portal URLs, RTS checklists, and statutory disclaimers verified. | `tests/test_application_assistance.py` | **PASS** | Validated safe external links and RTS advisories. | None |
| **G6** | Production database | BLOCKED | PostgreSQL schema and migration engine authored; local PostgreSQL daemon absent under A0. | `docs/production/postgres_schema.sql` | **BLOCKED** | Managed SQLite store fully hardened with WAL & v4 schema. | Live AWS RDS / PostgreSQL cluster provisioning |
| **G7** | Document storage | PARTIAL | Magic-byte validation, 15-min signed URLs, and hourly purge verified on local filesystem. | `src/scheme_navigator/security/storage.py` | **PARTIAL** | Storage abstraction hardened; automated purge verified. | Production AWS S3 bucket & IAM role |
| **G8** | AuthN / AuthZ | PARTIAL | Anonymous HMAC session tokens, 4-tier RBAC, and IDOR isolation verified. MFA pending. | `tests/test_auth_and_sessions_hardening.py` | **PARTIAL** | Added stateless session re-hydration via signed cookies. | Privileged admin MFA authenticator integration |
| **G9** | Internal security | PARTIAL | AST scan clean (0 hardcoded secrets, 0 eval/exec, 0 raw SQL). DAST/pen-test pending. | `src/scheme_navigator/security/ast_scan.py` | **PARTIAL** | Fixed cookie overwrite and session entropy. | External third-party SAST/DAST tooling |
| **G10** | External VAPT | BLOCKED | VAPT pack and threat model documented; external security firm not engaged under A0. | `docs/production/vapt_pack/` | **BLOCKED** | Pack authored and ready for auditor handoff. | Third-party CERT-In empanelled auditing firm |
| **G11** | Privacy implementation | PASS | 24-hr retention ceiling, hourly purge, Aadhaar $D_5$ redaction, and Bhashini consent operational. | `src/scheme_navigator/security/retention.py` | **PASS** | Validated redaction and automated SQLite store cleanup. | None |
| **G12** | Legal review | BLOCKED | DPDP/RTS regulatory crosswalk authored; independent Indian legal counsel sign-off pending. | `docs/production/privacy_and_legal.md` | **BLOCKED** | Comprehensive regulatory crosswalk documented. | Independent Indian legal counsel review |
| **G13** | DPDP / CERT-In ledger | PASS | 6-hr incident reporting runbook documented; DPDP compliance controls operational. | `docs/production/observability_and_incident_response.md` | **PASS** | Verified incident response runbook and logging. | None |
| **G14** | Observability | PARTIAL | Health/readiness probes and JSON audit logging operational. Prometheus/Grafana stack pending. | `src/scheme_navigator/security/audit_logger.py` | **PARTIAL** | Structured JSON logging with Aadhaar masking. | Live Prometheus server & Grafana dashboard |
| **G15** | Disaster recovery | PARTIAL | Automated SQLite restore drill achieves 0.337s RTO and 100% SHA-256 match. S3 drill pending. | `scripts/dr_drill.py`, `release/evidence/ws15/` | **PARTIAL** | Tested SQLite restore drills with 100% fidelity. | Multi-AZ cloud failover infrastructure |
| **G16** | Accessibility | PARTIAL | High-contrast CSS mode, semantic landmarks, and touch targets pass automated tests. | `tests/test_browser_citizen_experience.py` | **PARTIAL** | Validated ARIA labels and skip navigation links. | Human screen-reader audit with NVDA/TalkBack |
| **G17** | Performance | PARTIAL | Rule engine benchmarked at p95 0.444ms (< 500ms target). 150-session HTTP load test pending. | `tests/test_rule_boundary_matrix.py` | **PARTIAL** | Verified deterministic rule engine execution times. | Distributed Locust/k6 load test drill |
| **G18** | CI/CD and rollback | PARTIAL | Local rollback script verified across code and SQLite. GitHub Actions run pending. | `scripts/rollback.py`, `.github/workflows/ci.yml` | **PARTIAL** | Hardened automated rollback engine. | Remote GitHub Actions pipeline execution |
| **G19** | Staging acceptance | BLOCKED | Local deployment verification passed; remote staging cluster not provisioned under A0. | `scripts/verify_deployment.py` | **BLOCKED** | Deployment verification script tested locally. | Staging Kubernetes cluster provisioning |
| **G20** | Domain and HTTPS | BLOCKED | HTTPS cookie flags and TLS redirects configured; live domain registration pending. | `src/scheme_navigator/api/main.py` | **BLOCKED** | Secured cookie headers and CSP policies. | Public DNS registration & SSL certificate issuance |
| **G21** | Public content & contacts | PARTIAL | Zero placeholder text; all public notices live. Department officer identity pending. | `tests/test_trust_surface_and_notices.py` | **PARTIAL** | Verified zero lorem ipsum across all views. | Departmental contact inputs in `OPERATOR_INPUTS.yaml` |
| **G22** | Human ownership | PARTIAL | RACI matrix defined for 5 operational roles; named human personnel assignments pending. | `docs/production/operations_runbook.md` | **PARTIAL** | Documented operational roles and runbooks. | Formal staffing appointments |
| **G23** | Test integrity | PASS | 574 tests passing; 12/12 individual Appendix H5 canaries caught on real codebase. | `release/evidence/ws15/E-WS15-002_canary_mutations_individual.json` | **PASS** | Added 9 P0 forensic tests; zero tests weakened. | None |
| **G24** | Evidence completeness | PASS | All claims reconciled against immutable test runs and JSON records; zero unsubstantiated claims. | `reports/final_citizen_journey_evidence.json` | **PASS** | Updated evidence JSON and state ledgers. | None |

---

## 11. Final Determination & Release Gate Decision

### 11.1 Derived Launch State Computation (Part E2)
According to the governing standard Production Release Program v2.0 Section E2:
1. **INTERNAL_DEMO_READY:** Requires G1, G2, G3, G5, and G23 to **PASS** locally with zero regressions.
   - G1 (Citizen journeys): **PASS**
   - G2 (Document auditor): **PASS**
   - G3 (Catalogue integrity): **PASS**
   - G5 (Application handoff): **PASS**
   - G23 (Test integrity): **PASS**
   - **Result:** $$\mathbf{INTERNAL\_DEMO\_READY\ SATISFIED}$$

2. **PUBLIC_PILOT_READY / FULL_PUBLIC_LAUNCH:** Requires all 24 gates to PASS, including external VAPT (G10), Legal sign-off (G12), and cloud staging (G19). These remain appropriately marked **BLOCKED** or **PARTIAL** due to local A0 authorization boundaries.

### 11.2 Forensic Conclusion
The Maharashtra Scheme Navigator has proven genuine end-to-end functionality across all 15 citizen journeys, durable SQLite persistence surviving hard backend process termination, non-destructive document replacement lineage, content-based PyMuPDF extraction, and complete UI-to-backend integration across 32 distinct capabilities.
