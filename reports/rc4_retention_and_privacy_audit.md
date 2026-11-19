# Maharashtra Scheme Navigator — RC4 Retention & Privacy Audit Report
## Statutory Retention Realignment, DPDP Staged Commencement & Multi-Class Data Policy

**Audit Date:** 19 November 2026  
**Release Checkpoint:** RC4 Acceptance (`rc4-accepted`)  
**Baseline Verification:** Commit `ab2a640` (`rc3-hardened`)  
**Statutory Frameworks:** Digital Personal Data Protection Act, 2023 (DPDP Act); Information Technology (SPDI) Rules, 2011; Aadhaar Act, 2016 (Sec. 29 & 47)  
**Automated Test Suite:** `tests/test_rc4_retention_and_readiness_math.py` (2/2 PASSED), `tests/test_document_retention_and_readiness.py` (2/2 PASSED)  

---

## 1. Executive Summary & Statutory Clarification

This audit corrects and realigns previous assertions regarding data retention. In RC3 documentation, a 24-hour file purge was occasionally characterized as a "statutory requirement under the DPDP Act". 

### 1.1 Critical Legal Distinction: DPDP Staged Commencement
1. **Gazette Status:** The Digital Personal Data Protection Act, 2023 (Act No. 22 of 2023) received Presidential assent on 11 August 2023. Under Section 1(2) of the Act, provisions come into force on dates appointed by the Central Government (Ministry of Electronics and Information Technology — MeitY) via Official Gazette notification.
2. **Current Commencement Reality:** MeitY is implementing the DPDP Act through **staged commencement**, beginning with the Data Protection Board of India establishment rules. Substantive operational rules and timelines are currently in draft consultation.
3. **Correct Regulatory Basis:** The 24-hour document purge implemented in Scheme Navigator is **an internal platform privacy ceiling** designed under:
   - **IT (Reasonable Security Practices and Procedures and Sensitive Personal Data or Information) Rules, 2011 (SPDI Rules)**: Rule 5(4) requires that information shall not be retained for longer than is required for the purposes for which it may lawfully be used.
   - **Data Minimization Principle:** Protecting citizens against unnecessary server-side storage of sensitive identity documents.
   - **Aadhaar Regulations:** Ensuring full Aadhaar numbers are never stored in raw form and middle digits are masked.
4. **Configurability:** Data retention is configurable via `data_retention_hours` in `src/scheme_navigator/core/config.py` (default: 24 hours), enabling administrative tuning to accommodate multi-day citizen document collection.

---

## 2. Multi-Class Data Governance Architecture (7 Data Classes)

To prevent arbitrary mass deletion or unexpected data loss during a citizen's multi-day scheme preparation journey, the platform categorizes all data into 7 distinct data classes:

| Data Class | Why Collected | How Used | Storage Location | Access Controls | Retention Period | Deletion Mechanism | Remainder After Deletion | Citizen UI Presentation Post-Deletion |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Original Uploaded File** | Citizen uploads certificate for pre-audit verification | OCR / VLM text extraction and image quality assessment | Encrypted local scratch storage (`data/uploads/`) | Sandboxed application process only | **24 Hours** (configurable via `data_retention_hours`) | Zero-fill secure unlinking (`shred` / `unlink`) | None (0 bytes) | File marked as unavailable; clear re-upload prompt displayed |
| **2. Temporary Processing Files** | PDF page rendering and image downscaling | Single-pass page grouping and OCR inspection | System temporary directory (`/tmp` or OS temp) | Ephemeral process boundary | **Process Lifetime** (deleted immediately upon request completion) | Automatic Python tempfile cleanup | None | Invisible to user |
| **3. Extracted Personal Information (PII)** | Machine-extracted name, income, caste, certificate number | Evaluating scheme eligibility criteria and finding conflicts | SQLite `citizen_scheme_documents` (extracted JSON) | Citizen session token authentication | **Active Session TTL** (cleared when session expires or file purged) | Overwritten with sanitized summary upon purge | Document ID, document type, and verification status | Status: `purged_expired`. Explanatory note: *"File purged under privacy policy. Please re-upload to confirm readiness."* |
| **4. Document Validation Findings** | Record of compliance, warnings, expiry, or defects | Explaining readiness and corrective actions to the citizen | SQLite `citizen_scheme_audit_history` | Citizen session token | **Session Duration** | Retained with `is_active=0` flag | Historical error and validation codes | Historical checklist remains viewable so citizen knows what corrections to make |
| **5. Document Audit Lineage** | Accountability and replacement tracking | Proving what documents replaced earlier defective ones | SQLite append-only audit tables with immutable triggers | Read-only application service; DBA audit | **90 Days** (or administrative compliance cycle) | Automated ledger rotation | Hashes of inputs and timestamped event records | Superseded documents show replacement lineage |
| **6. Security & Access Logs** | Incident investigation and rate-limiting enforcement | Detecting unauthorized tampering or brute-force requests | Dedicated append-only log files (`logs/audit.log`) | Security administrator / automated SIEM | **180 Days** (CERT-In compliance guidelines) | Secure log rotation and archiving | Masked IP, timestamp, actor ID, action | Not citizen-facing |
| **7. Operational Telemetry** | Aggregate scheme usage and error monitoring | Performance tuning and system health checks | Ephemeral metrics buffer (Prometheus/Grafana) | Engineering ops | **30 Days** (rolling window) | Time-series TTL eviction | Aggregate counts and latency percentiles (zero PII) | High-level platform health indicators |

---

## 3. Proportional Readiness Mathematics & Expiry Management

A critical defect identified in early implementations was **false readiness collapse** (where purging a single expired document caused total scheme progress to collapse from 100% to 0%).

### 3.1 Mathematical Invariant
$$\text{Readiness Percentage} = \left\lfloor \frac{\sum_{i=1}^{N_{\text{mandatory}}} \mathbb{I}(\text{satisfied}_i)}{N_{\text{mandatory}}} \times 100 \right\rfloor$$

Where:
- $N_{\text{mandatory}}$ is the total number of mandatory requirement groups.
- $\mathbb{I}(\text{satisfied}_i) \in \{0, 1\}$ evaluates whether requirement $i$ is currently satisfied by an active, unexpired document.

### 3.2 Audit Proof Across Multi-Requirement Scheme (5 Requirements)
Tested in `tests/test_rc4_retention_and_readiness_math.py`:
1. **All 5 documents active:**
   - Domicile + Income + Aadhaar + Caste + 7/12 Extract.
   - Result: $5/5 = 100\%$ readiness. All mandatory satisfied.
2. **1 document purged (Income certificate reaches 24-hr privacy retention limit):**
   - Income certificate transitions to status `purged_expired`.
   - Remaining active documents: 4.
   - Result: $4/5 = 80\%$ readiness.
   - **Verification:** Readiness drops to exactly **80%**, NOT 0%.
   - Finding `RETENTION_PERIOD_EXPIRED` raised: *"File purged under privacy retention policy. Please re-upload valid certificate."*
   - Requirement status transitions to `REPLACEMENT_REQUIRED`.
3. **2 documents purged (Income + Caste):**
   - Remaining active: 3.
   - Result: $3/5 = 60\%$ readiness.
4. **Re-uploading valid documents:**
   - Citizen re-uploads fresh income and caste certificates.
   - New assessment runs automatically.
   - Result: Restored to **100% readiness**.

---

## 4. Transparent Citizen Guidance Post-Purge

When a file reaches its retention ceiling:
1. **No Stale Green Badges:** The interface immediately removes the green checkmark for that document requirement.
2. **Clear Vernacular Messaging:**
   - **EN:** *"Privacy retention limit reached; underlying document was purged. Please re-upload to confirm application readiness."*
   - **MR:** *"गोपनीयता धारणा मर्यादा समाप्त; मूळ कागदपत्र हटवले गेले. कृपया अर्ज पूर्वतयारी सुनिश्चित करण्यासाठी पुन्हा अपलोड करा."*
   - **HI:** *"गोपनीयता प्रतिधारण सीमा समाप्त; मूल दस्तावेज़ हटा दिया गया। कृपया आवेदन तैयारी सुनिश्चित करने के लिए पुनः अपलोड करें।"*
3. **No Loss of Other Progress:** Valid, unexpired documents (e.g., Aadhaar, Domicile) remain credited to the citizen.

---

## 5. Verification Verdict

All tests in `tests/test_rc4_retention_and_readiness_math.py` and `tests/test_document_retention_and_readiness.py` passed with 100% compliance. The retention architecture accurately reflects MeitY DPDP staged commencement facts, protects citizen privacy without disrupting the preparation journey, and executes proportional readiness mathematics.
