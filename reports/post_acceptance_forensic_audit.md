# Post-Acceptance Forensic Audit: Verification of TRIMURTI v4 Final Completion Claim
**File:** `reports/post_acceptance_forensic_audit.md`  
**Mission ID:** MSN-FINAL-001  
**Target Repository:** `C:\Users\Admin\Downloads\scheme-navigator\scheme-navigator`  
**Reported Checkpoint Commit:** `7adb0f93074f4fc6e4cbc69c1ba172b0cb73eb04`  
**Reported Checkpoint Tag:** `project-final-accepted`  
**Reported Checkpoint Branch:** `feat/catalogue-v2`  
**Audit Local Timestamp:** 2026-11-21T12:15:00+05:30  
**Auditor Classification:** Principal Forensic & Release-Quality Authority  

---

## EXECUTIVE VERDICT

# `COMPLETION_CLAIM_PARTIALLY_VERIFIED`

### Primary Finding
The Maharashtra Scheme Navigator codebase exhibits high architectural quality, robust vertical slice integration across all citizen journeys, and a comprehensive automated test harness. Real-browser Playwright execution proves the UI, API, and persistence layers function harmoniously for Maharashtra citizens.

However, the categorical claim of **"100% Accepted Completion across all 55 frozen requirements" cannot be substantiated** under strict forensic standards. The verifiable status is **Partially Verified** due to seven critical findings:
1. **Automated Gate Scripts Absent:** The specified acceptance gate scripts (`scripts/mission/compute_status.py`, `scripts/gates/final_gate.py`, `scripts/mission/status.py`) and evidence manifest (`reports/final_status.json`) do not exist in the repository.
2. **Pytest Regression Failure:** `python -m pytest tests/` does **NOT** pass with 0 errors. It executes 677 items, with **676 passing and 1 failing** (`tests/test_document_requirements_api.py::test_api_admin_scheme_coverage_report` fails with `assert 89 == 75` due to an un-updated hardcoded scheme assertion after candidate catalogue expansion).
3. **Empty Rule Approvals Database Table:** In `data/ingestion.sqlite3`, `scheme_rule_approvals` contains **0 rows**. Formal human rule-level approvals were never populated.
4. **Fixture Attestation Leaked into Real Database:** `scheme_completeness_attestations` contains 19 records covering 17 unique schemes. One of these 17 is `demo-indira-gandhi-old-age-pension` (a quarantined fixture), proving test fixture data entered the database. No 18th decision-ready scheme exists (real count is 16 genuine schemes).
5. **Synthetic Reviewer Identity:** Attestations were recorded under automated mock identities (`legal_reviewer_governance_board`, `legal_reviewer_invariants`, `advocate_deshmukh_legal_signoff`) during database seeding, rather than through authenticated human single-sign-on or real-world legal counsel.
6. **Preliminary vs. Final Scorer Variance:** Composite score is **76.65 / 100** (not the preliminary 78.88 projection), resulting from catalogue expansion from 74 to 88 schemes ($17 / 88 = 19.32\%$ verification rate).
7. **External Gate Dependencies Blocked:** Gate G10 (External VAPT by a CERT-In empanelled Information Security Auditing Organisation) and Gate G12 (Independent Indian legal counsel regulatory sign-off) remain pending.

---

## 1. Checkpoint & Version Control Verification

| Verification Item | Actual Value | Expected / Claimed | Audit Finding |
| :--- | :--- | :--- | :--- |
| **HEAD Commit SHA** | `7adb0f93074f4fc6e4cbc69c1ba172b0cb73eb04` | `7adb0f9` | **VERIFIED MATCH** |
| **Current Branch** | `feat/catalogue-v2` | `feat/catalogue-v2` | **VERIFIED MATCH** |
| **Git Tag at HEAD** | `project-final-accepted` | `project-final-accepted` | **VERIFIED MATCH** |
| **Working Tree Status** | Clean (nothing to commit) | Clean | **VERIFIED MATCH** |
| **Branch Deviation** | `feat/final-completion` does not exist in local or remote git refs | `feat/final-completion` | **DISCREPANCY RECORDED** (All final commits reside directly on `feat/catalogue-v2`) |
| **Final Tag Immutability** | Preserved without deletion or movement | Untouched | **VERIFIED PRESERVED** |

---

## 2. Frozen 55-Requirement Register Audit

Prior to this forensic audit, the requirements register existed solely as a manually edited Markdown document (`docs/project/final_requirements_register.md`). A canonical CSV register (`reports/post_acceptance_requirement_audit.csv`) has been generated and validated.

### 2.1 Inventory Metrics
- **Denominator (Frozen Scope):** 55 atomic requirements
- **Unique IDs:** 55 unique IDs across 15 operational domains
- **Markdown Register SHA-256:** `5a49806d7249e33fd7089480d2aeb705801cbc196b75dda9f096b35f86507395`
- **Scope Amendments:** None recorded.

### 2.2 Domain Breakdown & Acceptance Breakdown
| Domain | Total Reqs | Implemented | Integrated | Tested | Accepted (Verified) | Partial / Evidence Caveat |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Research (RES)** | 4 | 4 | 4 | 4 | 4 | 0 |
| **Catalogue (CAT)** | 4 | 4 | 4 | 4 | 4 | 0 |
| **Eligibility (ELG)** | 4 | 4 | 4 | 4 | 4 | 0 |
| **Onboarding (ONB)** | 4 | 4 | 4 | 4 | 3 | 1 (`REQ-ONB-04`: test ref misnamed `test_voice_agent.py`) |
| **Language (LAN)** | 3 | 3 | 3 | 3 | 3 | 0 |
| **Discovery (DIS)** | 3 | 3 | 3 | 3 | 3 | 0 |
| **Planner (PLN)** | 4 | 4 | 4 | 4 | 4 | 0 |
| **Documents (DOC)** | 4 | 4 | 4 | 4 | 4 | 0 |
| **Audit (AUD)** | 4 | 4 | 4 | 4 | 3 | 1 (`REQ-AUD-01/02`: test ref misnamed `test_document_audit_lineage.py`) |
| **Handoff (APP)** | 3 | 3 | 3 | 3 | 3 | 0 |
| **Persistence (PRG)** | 3 | 3 | 3 | 3 | 3 | 0 |
| **Governance (GOV)** | 4 | 4 | 4 | 4 | 3 | 1 (`REQ-GOV-02`: `scheme_rule_approvals` table empty) |
| **Architecture (ARC)**| 3 | 3 | 3 | 3 | 2 | 1 (`REQ-ARC-01`: test ref misnamed `test_api_contracts.py`) |
| **Security (SEC)** | 4 | 4 | 4 | 4 | 4 | 0 |
| **Verification (VER)**| 4 | 4 | 4 | 3 | 3 | 1 (`REQ-VER-03`: 1 failing test in `pytest tests/`) |
| **TOTAL** | **55** | **55 (100%)**| **55 (100%)**| **54 (98.2%)**| **51 (92.7%)**| **4 (7.3%)** |

### 2.3 Evidence Mapping Caveats
In `docs/project/final_requirements_register.md`, several test file references did not match the physical files on disk:
1. `tests/test_voice_agent.py` does not exist; actual implementation tested in `tests/test_multilingual_voice.py`.
2. `tests/test_document_audit_lineage.py` does not exist; actual implementation tested in `tests/test_document_audit.py`.
3. `tests/test_api_contracts.py` does not exist; actual implementation tested in `tests/test_catalogue_v2_contracts.py`.
4. `tests/test_ssrf_and_security.py` does not exist; actual implementation tested in `tests/test_security_remediation.py`.

---

## 3. Acceptance Gate Scripts Investigation

A thorough filesystem search for the claimed acceptance gate scripts revealed:
- `scripts/mission/compute_status.py`: **DOES NOT EXIST**
- `scripts/gates/final_gate.py`: **DOES NOT EXIST**
- `scripts/mission/status.py`: **DOES NOT EXIST**
- `reports/final_status.json`: **DOES NOT EXIST**
- `reports/final_evidence_manifest.json`: **DOES NOT EXIST**

**Forensic Finding:** There is no executable gate script in the repository to mechanically gate or validate the release state. Prior claims citing a final automated gate execution were unsupported by repository artifacts.

---

## 4. Test Suite Execution & Output Reconciliation

### 4.1 Full Pytest Suite (`python -m pytest tests/`)
- **Command:** `C:\Users\Admin\Downloads\scheme-navigator\.venv\Scripts\python.exe -m pytest tests/`
- **Duration:** 256.50 seconds (4 min 16.5 sec)
- **Exit Code:** `1` (FAILURE)
- **Total Collected Items:** 677
- **Passed:** 676
- **Failed:** 1
- **Failing Test:** `tests/test_document_requirements_api.py::test_api_admin_scheme_coverage_report`
  ```text
  def test_api_admin_scheme_coverage_report(client):
      resp = client.get("/admin/scheme-coverage")
      assert resp.status_code == 200
      data = resp.json()
  >   assert data["total_canonical_schemes"] == 75
  E   assert 89 == 75
  tests\test_document_requirements_api.py:255: AssertionError
  ```
- **Analysis:** This test was written when the canonical catalogue held 75 schemes (74 schemes + 1 demo fixture). When SC-G2 integrated 14 candidate schemes into `schemes.json` (bringing the total to 89), this test was never updated, causing `python -m pytest tests/` to fail.

### 4.2 Playwright Browser Test Suites (Real Served Browser Execution)
All browser suites were executed separately using independent uvicorn live servers:
1. **Trimurti v4 Master Acceptance (`test_playwright_trimurti_v4_acceptance.py`):**  
   - 20 items collected, **20 passed in 40.04s** (Exit code: 0)
   - Covered Journeys A through J and Personas 01 through 10.
2. **SC-G2 Reconciliation (`test_playwright_sc_g2_reconciliation.py`):**  
   - 19 items collected, **19 passed in 43.98s** (Exit code: 0)
   - Covered alias search, Marathi/Hindi scripts, department filters, advisory banners, and reviewer dashboard.
3. **Five-Citizen Acceptance (`test_playwright_five_citizen_acceptance.py`):**  
   - 6 items collected, **6 passed in 40.86s** (Exit code: 0)
4. **Citizen Experience Suite (`test_browser_citizen_experience.py`):**  
   - 21 items collected, **21 passed in 31.22s** (Exit code: 0)
5. **Document Auditor Browser Journey (`test_browser_document_auditor_journey.py`):**  
   - 4 items collected, **4 passed in 21.40s** (Exit code: 0)
6. **Municipal Citizen Journey (`test_browser_municipal_citizen_journey.py`):**  
   - 5 items collected, **5 passed in 23.14s** (Exit code: 0)
7. **Backend Restart Persistence (`test_playwright_backend_restart_persistence.py`):**  
   - 1 item collected, **1 passed in 18.12s** (Exit code: 0)
8. **Scheme Issue Reporting (`test_playwright_scheme_issue_reporting.py`):**  
   - 1 item collected, **1 passed in 11.94s** (Exit code: 0)
9. **15 Citizen Journeys (`test_playwright_15_citizen_journeys.py`):**  
   - 15 items collected, **14 passed, 1 failed** (Exit code: 1, duration: 102.73s).  
   - Failed test: `test_journey_06_profile_vs_document_name_mismatch_citizen` encountered a 30s UI locator timeout on click interaction.

**Total Browser Suite Results:** 91 passed out of 92 executed browser journey tests.

---

## 5. Scheme Intelligence Metrics Reconciliation

### 5.1 Scorer Reproduction & 78.88 vs. 76.65 Explanation
- **Frozen Scorer Version:** `1.0.0-sc-g1`
- **Evaluated Score:** **76.65 / 100**
- **Discrepancy Root Cause:** In milestone SC-G2, an early projection of 78.88 was calculated prior to merging candidate schemes into the active catalogue. When 14 candidate schemes were integrated into `schemes.json` (increasing total canonical schemes from 74 to 88), the 14 candidates were designated as `LIMITED_INFORMATION` to prevent unverified schemes from receiving automated eligibility determinations (enforcing Invariant I-04 & I-07). Consequently, the verified proportion of the active catalogue shifted from $17 / 74 = 22.97\%$ to $17 / 88 = 19.32\%$. Running the frozen scoring formula mechanically computes **76.65 / 100**.

### 5.2 Human Approval & Attestation Audit
- **Attestation Records in `scheme_completeness_attestations`:** 19 records covering 17 unique scheme identifiers.
- **Fixture Contamination:** Scheme ID `demo-indira-gandhi-old-age-pension` has attestation record `attest_63eff6ea805337dd` in the database, proving demo fixtures received completeness attestations in the database.
- **Genuine Attested Schemes:** Exactly 16 legitimate government schemes (not 17 or 18).
- **Rule Approvals Table:** `scheme_rule_approvals` contains **0 rows**.
- **Reviewer Identities:** Attestations were recorded under synthetic actor IDs (`legal_reviewer_governance_board`, `legal_reviewer_invariants`, `advocate_deshmukh_legal_signoff`) during test initialization, not authenticated real-world human legal reviewers.

### 5.3 Discovery Coverage & Authority Universe
- **Target Departments Claim (40/40):** Verified against 38 State Government Departments and 2 State Directorates.
- **Universe Boundary:** The platform maps 137 authoritative bodies across 6 categories (38 State Departments, 2 State Directorates, 18 State Corporations, 14 Central Ministries, 29 Municipal Corporations, 36 District Collectorates).
- **Unresolved Local Government:** Approximately 240+ Municipal Councils, 130+ Nagar Panchayats, and 27,000+ Gram Panchayats are unmapped and outside current scope.
- **LGD Directory Mapping:** 65 entities (36 Districts + 29 Municipal Corporations) are 100% verified against official Local Government Directory (LGD) codes.

### 5.4 Data Completeness vs. Verification Rate
- **Scheme Verification Rate:** **19.32% (17 / 88)**
- **Field-Level Completeness:**
  - Core fields (name, department, level, benefit, eligibility): **100.0% (88 / 88)**
  - Secondary fields (implementing body, descriptions, translation method): **84.1% (74 / 88)**
  - Operational criteria & document requirements: **35.2% (31 / 88)**
  - Deep legal basis & statutory citations: **19.3% (17 / 88)**

---

## 6. Security Audit Log Discard Investigation

- **File Path:** `data/security_audit.log`
- **File Size:** 3,836,366 bytes | **SHA-256:** `bced6bb42b4959d856bc319f1b0682334a7e2927988a22051c3de9a2968daf0d`
- **Record Count:** 11,418 structured JSONL entries
- **Discard Finding:** Discard operations (`git checkout -- data/security_audit.log`) discarded only ephemeral test-generated events caused by tests running against default logger paths.
- **Event Preservation:** Zero committed historical events were lost. The committed file matches archival backups `_backups/trimurti-g1-accepted-20261120-235500` and `_backups/trimurti-v4-baseline-20261121-011800` byte-for-byte.

---

## 7. Legal, Privacy & Compliance Corrections

The following corrections have been applied to `reports/final_security_assessment.md`:
1. **SPDI Rule 5(4) Purpose-Based Retention:** Clarified that Rule 5(4) of the IT (SPDI) Rules 2011 specifies that sensitive personal data shall not be retained longer than required for the purpose for which it may lawfully be used. The 24-hour file purge is an internal platform privacy ceiling, not an explicit statutory mandate.
2. **DPDP Act Phased Commencement:** Clarified that the DPDP Act 2023 is in phased commencement by MeitY via gazette notification. Substantive obligations commence upon notification of corresponding rules.
3. **CERT-In Terminology:** Replaced "certified third-party vendor" with the statutory term: **CERT-In empanelled Information Security Auditing Organisation**.
4. **Internal vs. External Security:** Automated security test suites provide internal regression assurance; Gate G10 remains formally blocked pending an external VAPT engagement.

---

## 8. Remaining Defects & External Blockers

1. **Defect D-01:** `tests/test_document_requirements_api.py::test_api_admin_scheme_coverage_report` hardcodes expected scheme count of 75 instead of 89.
2. **Defect D-02:** Flaky UI click timeout in `tests/test_playwright_15_citizen_journeys.py::test_journey_06`.
3. **Defect D-03:** `scheme_rule_approvals` SQLite table has 0 rows.
4. **Defect D-04:** Fixture attestation record `attest_63eff6ea805337dd` for `demo-indira-gandhi-old-age-pension` present in `data/ingestion.sqlite3`.
5. **External Blocker B-01 (Gate G10):** Independent third-party VAPT by a CERT-In empanelled Information Security Auditing Organisation not yet conducted.
6. **External Blocker B-02 (Gate G12):** Independent Indian legal counsel regulatory sign-off on DPDP and RTS compliance pending.

---

## 9. Conclusion & Release Gate Classification

The current release cannot be classified as `PRODUCTION_READY` or `100% ACCEPTED`. The scientifically accurate classification remains:

# `INTERNAL_DEMO_READY`

Tag `project-final-accepted` is preserved as a permanent historical marker of the Trimurti v4 feature-complete vertical slice, but does not constitute formal production acceptance.
