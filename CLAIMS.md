# Honest Claims Register (CLAIMS.md)
**Project:** Maharashtra Scheme Navigator  
**Last Updated:** 2026-11-19T23:15:00+05:30  
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
| **C-05** | Document Auditor handles full lifecycle: upload, magic-byte validation, OCR extraction, rule matching, findings, inline correction, and SQLite persistence. | `tests/test_playwright_backend_restart_persistence.py`, `tests/test_document_*.py` | **CONFIRMED** |
| **C-06** | The test suite is strictly non-weakening: **613 tests pass with zero regressions** (including 47 Playwright browser tests). | `pytest tests/` run output: 613 passed, exit code 0 | **CONFIRMED** |
| **C-07** | All 12/12 individual Appendix H5 canary mutations are caught by tests on the real codebase. | `release/evidence/ws15/E-WS15-002_canary_mutations_individual.json` | **CONFIRMED** |
| **C-08** | Complete trilingual UI and document guidance across English, Marathi, and Hindi (112 keys with zero leakage). | `static/index.html`, `tests/test_trilingual_parity.py`, `reports/rc4_multilingual_acceptance.md` | **CONFIRMED** |
| **C-09** | SQLite database operations use WAL mode with immediate transaction isolation and strict restart durability. | `src/scheme_navigator/core/citizen_store.py`, `tests/test_sqlite_persistence_and_replacement.py` | **CONFIRMED** |
| **C-10** | Demo fixture `demo-majhi-ladki-bahin` is quarantined and cannot trigger verified eligibility in production. | `tests/test_fail_closed_activation.py`, `tests/test_browser_citizen_experience.py` | **CONFIRMED** |
| **C-11** | Unapproved rules or draft schemes fail closed to Caseworker Review (`NEEDS_REVIEW`). | `tests/test_fail_closed_activation.py`, `src/scheme_navigator/domain/rules.py` | **CONFIRMED** |
| **C-12** | Right to Services (RTS) statutory delivery timelines are rendered on factsheets and document preparation modals. | `data/source_registry/canonical_schemes.json`, `static/index.html` | **CONFIRMED** |
| **C-13** | Verification Tier badges (`Tier A Verified`, `Tier B Verified`, `Tier C Under Review`) reflect authentic evidentiary status. | `static/index.html`, `tests/test_trust_verification_ui.py` | **CONFIRMED** |
| **C-14** | All 15 mandatory citizen journeys (J01–J15) pass in real Chromium via Playwright. | `reports/final_citizen_journey_evidence.json`, `tests/test_playwright_15_citizen_journeys.py` | **CONFIRMED** |
| **C-15** | Document replacement strictly tracks lineage ($v1 \to v2$) with immutable SQLite triggers protecting history. | `tests/test_immutable_audit_history.py`, `src/scheme_navigator/core/citizen_store.py` | **CONFIRMED** |
| **C-16** | Document medium is explicitly categorized (`SEARCHABLE_PDF`, `SCANNED_PDF`, `PHOTOGRAPH`, `IMAGE`). | `tests/test_ocr_and_document_intelligence.py`, `src/scheme_navigator/documents/audit.py` | **CONFIRMED** |
| **C-17** | Image quality gates mathematically detect blur (Laplacian $< 45.0$) and resolution ($< 250$px). | `tests/test_ocr_and_document_intelligence.py`, `src/scheme_navigator/documents/audit.py` | **CONFIRMED** |
| **C-18** | Devanagari numerals (`०-९`) and vernacular formats are accurately parsed into integers and ISO dates. | `tests/test_ocr_and_document_intelligence.py`, `src/scheme_navigator/documents/audit.py` | **CONFIRMED** |
| **C-19** | Document retention purge reactively invalidates downstream readiness proportionally (e.g. 4/5 = 80%, not 0%) with localized re-upload notices in EN, MR, HI. | `tests/test_rc4_retention_and_readiness_math.py`, `tests/test_document_retention_and_readiness.py` | **CONFIRMED** |
| **C-20** | Eligibility status is normalized to `MEETS_VERIFIED_CRITERIA` (`meets_verified_criteria`) with fail-closed protection for unapproved rules/demo fixtures. | `tests/test_eligibility_state_model_consistency.py`, `src/scheme_navigator/domain/models.py` | **CONFIRMED** |
| **C-21** | Field-level extraction matches ground truth with 100% precision (64/64 fields matched) across English, Marathi, Hindi specimens. | `reports/rc4_document_intelligence_accuracy.md`, `tests/test_rc4_document_intelligence_accuracy.py` | **CONFIRMED** |
| **C-22** | 12 representative scheme families validated end-to-end with real upload journeys logged to structured JSON evidence. | `reports/rc4_scheme_diverse_journey_evidence.json`, `tests/test_rc4_scheme_diverse_e2e_journeys.py` | **CONFIRMED** |
| **C-23** | Retention architecture reflects MeitY DPDP staged commencement facts and governs 7 distinct data classes under IT SPDI Rules 2011. | `reports/rc4_retention_and_privacy_audit.md`, `src/scheme_navigator/core/config.py` | **CONFIRMED** |

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
| **CR-03** | "The 24-hour document purge is a universal statutory deadline under the DPDP Act." | The DPDP Act is in staged commencement by MeitY; the 24-hr purge is a platform privacy ceiling under IT SPDI Rules 2011 and data minimization. | **REFUTED** |
