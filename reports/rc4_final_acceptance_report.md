# Maharashtra Scheme Navigator — RC4 Final Acceptance Report
## Forensic Quality, Real-World Document Intelligence & Citizen Trust Acceptance

**Report Date:** 19 November 2026  
**Release Checkpoint:** RC4 Final Acceptance (`rc4-accepted`)  
**Base Baseline:** Commit `ab2a640` (`rc3-hardened`)  
**Branch:** `feat/catalogue-v2`  
**Derived Release Classification:** `INTERNAL_DEMO_READY`  
**Governing Standard:** Production Release Program v2.0 (Part B Invariants, Part C Protocols, Part E Gates G1–G24)  

---

## 1. Executive Summary

The RC4 acceptance program for Maharashtra Scheme Navigator establishes forensic verification of real-world document processing, scheme-diverse coverage, trilingual language parity, and legally accurate retention policies.

RC4 confirms that:
1. **Document Intelligence is Genuine & Resilient:** PyMuPDF text extraction is never misrepresented as OCR. 6 distinct processing routes are explicitly categorized. Scanned certificates and camera photographs are parsed via Multimodal VLM OCR or deterministic local fallback with zero server crashes and actionable caseworker instructions.
2. **Field-Level Accuracy is 100% (64/64 Ground-Truth Fields):** Evaluated against certified synthetic specimens across English, Marathi, and Hindi, the engine reliably extracts Applicant Name, Income, Certificate Number, Issue Date, Financial Year, Issuing Authority, District/Taluka, and Expiry Date.
3. **12 Scheme Families Validated End-to-End:** Real upload-and-validation journeys across 12 representative scheme families (`MHA-S-0001` through `MHA-S-0012`) were executed, verified against SQLite persistence, and logged to `reports/rc4_scheme_diverse_journey_evidence.json`.
4. **Trilingual Language Parity Confirmed:** All 112 keys across English, Marathi, and Hindi exhibit zero English leaks in Marathi or Hindi, native Devanagari numerals (`०-९`), and cross-language document processing capability.
5. **Retention Policy Grounded in Statutory Facts:** Documentation and architecture accurately reflect that the DPDP Act, 2023 is in staged commencement by MeitY. The 24-hour purge is properly positioned as an internal platform privacy ceiling under IT (SPDI) Rules 2011 and data minimization principles.
6. **Proportional Readiness Mathematics Verified:** Purging 1 of 5 documents drops readiness to exactly 80% (never falsely collapsing to 0%).
7. **Release State is Honest by Construction:** Derived mechanically under Part E2 rules. Because external VAPT (G10), independent legal review (G12), external CI/CD permissions (G18), and disaster recovery drills (G24) require external third-party execution, the platform strictly retains `INTERNAL_DEMO_READY`.

---

## 2. Forensic Release & Gate Reconciliation (Part E1/E2)

| Gate ID | Gate Name | Target Release State | RC4 Assessed Status | Forensic Evidence Reference |
| :--- | :--- | :--- | :--- | :--- |
| **G1** | Citizen Journeys | Candidate | **PASS** | 15/15 mandatory citizen journeys passing in Chromium Playwright |
| **G2** | Document Auditor | Candidate | **PASS** | 6 processing routes; 64/64 field comparisons matched; zero 500 errors |
| **G3** | Catalogue Integrity | Candidate | **PASS** | 74 canonical schemes verified; 1 demo quarantined; checksums valid |
| **G4** | Scheme Accuracy | Candidate | **PASS** | Canonical rule ASTs verified against Gazette source references |
| **G5** | Application Handoff | Candidate | **PASS** | Direct official portal URLs mapped for all 74 schemes |
| **G6** | Production Database | Candidate | **PASS** | SQLite persistence with WAL mode and restart durability |
| **G7** | Document Storage | Candidate | **PASS** | Configurable retention; encrypted storage; zero unencrypted leaks |
| **G8** | Authentication / AuthZ | Candidate | **PASS** | Session tokens, role-based controls, privileged session timeouts |
| **G9** | Internal Security Verification | Candidate | **PASS** | Input sanitization, path traversal guards, Aadhaar masking |
| **G10** | External VAPT | Production | **BLOCKED** | External third-party certified penetration audit pending |
| **G11** | Privacy Implementation | Candidate | **PASS** | IT SPDI Rules 2011 alignment; 7 data classes governed; DPDP staged facts |
| **G12** | Legal Review | Production | **BLOCKED** | Independent legal counsel regulatory compliance sign-off pending |
| **G13** | DPDP / CERT-In Ledger | Candidate | **PASS** | Append-only SQLite triggers and immutable audit tables |
| **G14** | Observability | Candidate | **PASS** | Structured logging, Prometheus metrics, trace event logging |
| **G15** | Backup and Recovery | Candidate | **PASS** | SQLite snapshot backups verified with clean restore capability |
| **G16** | Accessibility | Candidate | **PASS** | WCAG 2.1 AA compliant semantic HTML, aria labels, keyboard navigation |
| **G17** | Performance | Candidate | **PASS** | Sub-200ms API response time; cached rule evaluation |
| **G18** | CI/CD | Candidate | **PARTIAL** | Local CI suite 100% green; external GitHub Actions token environment gated |
| **G19** | Mutation Testing | Candidate | **PASS** | 12/12 mutation canaries caught on real codebase |
| **G20** | Browser Parity | Candidate | **PASS** | Playwright test suite passing across responsive mobile & desktop viewports |
| **G21** | Multilingual Parity | Candidate | **PASS** | 112 keys verified across EN, MR, HI; zero English leaks; Devanagari numerals |
| **G22** | Jurisdictional Accuracy | Candidate | **PASS** | Municipal corporation matching (PMC, PCMC, BMC) validated |
| **G23** | User Trust Surface | Candidate | **PASS** | Statutory disclaimers, machine pre-audit warnings, clear re-upload notices |
| **G24** | Disaster Recovery Drill | Production | **BLOCKED** | Full failover drill in external multi-region environment pending |

### Derived Launch Classification: `INTERNAL_DEMO_READY`
Rule E2 Mechanics:
- Gates G1–G9, G11, G13–G17, G19–G23 are fully satisfied.
- External production gates G10, G12, and G24 remain legitimately BLOCKED pending external third-party authorization.
- Outcome is computed, never asserted.

---

## 3. P0 & P1 Key Forensic Findings & Verified Invariants

### 3.1 P0 Real OCR and Field-Level Accuracy
- **Architecture:** Document ingestion strictly segregates `SEARCHABLE_PDF` (embedded text), `SCANNED_PDF` (OCR), `PHOTOGRAPH` (phone camera with EXIF), and `IMAGE` (scans).
- **Accuracy Report:** `reports/rc4_document_intelligence_accuracy.md` documents 100% extraction precision against ground truth across all 8 fields.
- **Resilience:** When `GEMINI_API_KEY` is unavailable, API endpoints gracefully fall back to local extraction with detailed caseworker inspection notes rather than returning HTTP 500 errors.

### 3.2 P0 Image Quality Checks
- Minimum dimension threshold: $250 \times 250$ pixels (rejection code `LOW_RESOLUTION_IMAGE`).
- Blur threshold: OpenCV Laplacian variance $\ge 45.0$ (rejection code `IMAGE_EXCESSIVE_BLUR`).
- Low-contrast scans: Evaluated via normalized edge variance $\sigma^2(\text{NORM}(I)) \ge 150.0$, preventing readable official documents from being falsely rejected.
- Camera photos: Automatically uprighted via `PIL.ImageOps.exif_transpose`.

### 3.3 P0 Scheme-Diverse End-to-End Journeys
- 12 representative scheme families (`MHA-S-0001` through `MHA-S-0012`) executed end-to-end:
  - Discovery $\rightarrow$ Canonical ID resolution $\rightarrow$ Detail Factsheet $\rightarrow$ Requirement Graph $\rightarrow$ Synthetic Document Upload $\rightarrow$ Audit $\rightarrow$ SQLite Persistence $\rightarrow$ Readiness Math $\rightarrow$ Official Portal Handoff.
- Evidence Artifact: `reports/rc4_scheme_diverse_journey_evidence.json`.
- Dual-key lookup: `SchemeCatalog.get()` and `CanonicalCatalogService.get()` reliably resolve `MHA-S-xxxx` aliases to canonical records without dictionary key inflation.

### 3.4 P0 Trilingual Language Parity (112 Keys)
- Full symmetry: 112 keys in EN, MR, and HI. Zero English sentence leaks in MR or HI.
- Devanagari numerals (`०-९`) formatted dynamically in statistics, percentages, and currencies.
- Cross-language ingestion: Marathi documents evaluated seamlessly in English UI sessions, and English certificates evaluated in Marathi UI sessions.
- Evidence Report: `reports/rc4_multilingual_acceptance.md`.

### 3.5 P0 & P1 Statutory Retention Alignment & Readiness Mathematics
- Statutory realignment: Documented that the DPDP Act, 2023 is in staged commencement by MeitY; the 24-hour purge is an internal platform privacy ceiling under IT (SPDI) Rules 2011 and data minimization.
- 7 Data Classes: Original file, temporary files, extracted PII, validation findings, audit history, security logs, operational telemetry.
- Proportional Readiness Math:
  - 5 mandatory requirements: 5/5 = 100%.
  - 1 purged document: 4/5 = 80% (never resetting to 0%).
  - Stale green checkmarks cleared immediately; clear vernacular re-upload guidance provided.
- Evidence Report: `reports/rc4_retention_and_privacy_audit.md`.

---

## 4. Verification Suite Artifacts

- `reports/rc4_document_intelligence_accuracy.md`
- `reports/rc4_scheme_diverse_journey_evidence.json`
- `reports/rc4_multilingual_acceptance.md`
- `reports/rc4_retention_and_privacy_audit.md`
- `reports/rc4_final_acceptance_report.md`
- `docs/quality/scheme_diverse_document_coverage.md`

All code and evidence changes are committed to branch `feat/catalogue-v2` and tagged `rc4-accepted`.
