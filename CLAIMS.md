# Honest Claims Register (CLAIMS.md)
**Project:** Maharashtra Scheme Navigator  
**Last Updated:** 2026-11-19T21:05:00+05:30  
**Governing Standard:** Production Release Program v2.0 (Part E2, Appendix H4)  
**Rule:** Outcome is computed, not asserted. Any claim without direct, reproducible primary-source evidence is refuted.

---

## 1. Verified & Supported Claims (CONFIRMED)

| Claim ID | System Claim | Primary Evidence Reference | Status |
| :---: | :--- | :--- | :---: |
| **C-01** | The application serves 75 canonical Maharashtra government schemes (74 canonical + 1 demo fixture). | `data/catalogue/schemes.json`, `tests/test_catalogue_v2_contracts.py` | **CONFIRMED** |
| **C-02** | 17 Tier A Flagship schemes have 100% verified verbatim Marathi quotes matching official GR documents. | `data/raw/`, `scripts/build_verified_catalogue_v2.py`, `tests/test_catalogue_v2_contracts.py` | **CONFIRMED** |
| **C-03** | 13 Tier B schemes implement strict municipal corporation isolation (PMC, PCMC, BMC, TMC, NMMC). | `src/scheme_navigator/domain/jurisdiction.py`, `tests/test_municipal_and_jurisdiction_matching.py` | **CONFIRMED** |
| **C-04** | All 44 Tier C schemes are explicitly marked `verification_status="unverified"` and `eligibility_incomplete=true`. | `data/catalogue/schemes.json`, `tests/test_catalogue_v2_contracts.py` | **CONFIRMED** |
| **C-05** | Document Auditor handles full lifecycle: upload, magic-byte validation, PyMuPDF OCR extraction, rule matching, findings, inline correction, and SQLite persistence. | `tests/test_playwright_backend_restart_persistence.py`, `tests/test_document_*.py` | **CONFIRMED** |
| **C-06** | The test suite is strictly non-weakening: 574 tests pass with zero regressions (including 46 Playwright browser tests). | `pytest tests/` run output: 574 passed in 201.46s, exit code 0 | **CONFIRMED** |
| **C-07** | All 12/12 individual Appendix H5 canary mutations are caught by tests on the real codebase. | `release/evidence/ws15/E-WS15-002_canary_mutations_individual.json` | **CONFIRMED** |
| **C-08** | Sensitive Aadhaar numbers are verified via Verhoeff $D_5$ algorithm and masked to `XXXX-XXXX-1234`. | `src/scheme_navigator/security/aadhaar_privacy.py`, `tests/test_aadhaar_privacy.py` | **CONFIRMED** |
| **C-09** | Public factsheets contain zero citizen PII and provide official Government Resolution citations. | `src/scheme_navigator/services/catalog.py`, `tests/test_browser_document_auditor_journey.py` | **CONFIRMED** |
| **C-10** | Document consistency engine detects income mismatches, caste mismatches, unreadable scans, and expired documents. | `src/scheme_navigator/services/document_prep.py`, `tests/test_document_review_overhaul.py` | **CONFIRMED** |
| **C-11** | Local SQLite disaster recovery drill restores database with 100% checksum match in 0.337 seconds. | `scripts/dr_drill.py`, `release/evidence/ws15/E-WS15-001_dr_drill_full.json` | **CONFIRMED** |
| **C-12** | Trilingual UI (English, Marathi, Hindi) renders with zero missing translation keys or raw backend identifiers. | `tests/test_browser_citizen_experience.py`, `tests/test_browser_document_auditor_journey.py` | **CONFIRMED** |
| **C-13** | SQLite persistence is authoritative across hard backend process restarts (Migration v4 schema). | `tests/test_playwright_backend_restart_persistence.py`, `reports/evidence_screenshots/` | **CONFIRMED** |
| **C-14** | Document replacement implements non-destructive lineage ($v1 \to v2$) with immutable audit history preserved in SQLite. | `tests/test_sqlite_persistence_and_replacement.py`, `src/scheme_navigator/core/citizen_store.py` | **CONFIRMED** |
| **C-15** | Local fallback OCR extracts from PyMuPDF document text streams with zero filename heuristics. | `tests/test_local_fallback_ocr_content.py`, `src/scheme_navigator/documents/audit.py` | **CONFIRMED** |

---

## 2. Partial Claims (PARTIAL)

| Claim ID | System Claim | Limitation & Boundary | Status |
| :---: | :--- | :--- | :---: |
| **CP-01** | Privileged authentication with Multi-Factor Authentication (MFA). | RBAC, session isolation, and token hashing are active; TOTP/MFA is not implemented. | **PARTIAL** |
| **CP-02** | Document storage in encrypted cloud S3 buckets. | S3 abstraction and signed URLs are verified; currently runs against local filesystem. | **PARTIAL** |
| **CP-03** | End-to-end observability stack. | Liveness/readiness probes and redaction logging work; live Prometheus/Grafana stack unconfigured. | **PARTIAL** |
| **CP-04** | Web Content Accessibility Guidelines (WCAG) 2.1 AA compliance. | Automated DOM checks and high-contrast CSS pass; human screen-reader audit pending. | **PARTIAL** |
| **CP-05** | Production performance benchmark. | In-memory rule engine is sub-millisecond (0.444ms); full HTTP load test at 150 sessions pending. | **PARTIAL** |

---

## 3. Blocked Claims (BLOCKED)

| Claim ID | System Claim | Reason for Block (Authorization Level A0) | Status |
| :---: | :--- | :--- | :---: |
| **CB-01** | Production PostgreSQL 15+ database execution. | No PostgreSQL daemon or Docker engine available on host machine under local A0 execution. | **BLOCKED** |
| **CB-02** | External certified VAPT (Penetration Testing). | Local machine scope does not permit third-party security firm engagement. | **BLOCKED** |
| **CB-03** | Independent Indian legal counsel review. | Legal review requires qualified external legal counsel sign-off. | **BLOCKED** |
| **CB-04** | Staging server cluster deployment. | External staging environment is not provisioned or reachable from local developer machine. | **BLOCKED** |
| **CB-05** | Public government domain registration and CAA/TLS records. | Public DNS registration is outside local execution authority. | **BLOCKED** |

---

## 4. Refuted & Prohibited Claims (REFUTED)

| Claim ID | False Claim | Truth Statement | Status |
| :---: | :--- | :--- | :---: |
| **CR-01** | "The application has passed 23/24 release gates and is production ready." | Mechanically derived state is `INTERNAL_DEMO_READY` (8 PASS, 11 PARTIAL, 5 BLOCKED). | **REFUTED** |
| **CR-02** | "Local OCR pre-check guarantees 100% government application approval." | Local pre-checks only verify document readability and consistency; official departments make final eligibility determinations. | **REFUTED** |
| **CR-03** | "Tier C schemes have full eligibility rule coverage." | Tier C schemes are explicitly unverified exploratory records with incomplete eligibility criteria. | **REFUTED** |
| **CR-04** | "Browser sessionStorage is authoritative for durable citizen data." | SQLite is the sole authoritative store; sessionStorage is purely a transient UI rendering cache. | **REFUTED** |
| **CR-05** | "Document replacement overwrites or erases earlier audit records." | Prior document records are preserved as immutable superseded records in SQLite. | **REFUTED** |
