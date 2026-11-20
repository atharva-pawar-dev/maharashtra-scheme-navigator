# Honest Claims Register (CLAIMS.md)
**Project:** Maharashtra Scheme Navigator  
**Last Updated:** 2026-11-19T23:15:00+05:30  
**Governing Standard:** Production Release Program v2.0 (Part E2, Appendix H4)  
**Rule:** Outcome is computed, not asserted. Any claim without direct, reproducible primary-source evidence is refuted.

---

## 1. Verified & Supported Claims (CONFIRMED)

| Claim ID | System Claim | Primary Evidence Reference | Status |
| :---: | :--- | :--- | :---: |
| **C-01** | The application serves 89 Maharashtra government schemes in registry (88 canonical + 1 demo fixture) and 88 canonical schemes in active catalogue. | `data/catalogue/schemes.json`, `data/source_registry/canonical_schemes.json`, `tests/test_universe_reconciliation.py` | **CONFIRMED** |
| **C-02** | 17 Tier A Flagship schemes have 100% verified verbatim Marathi quotes matching official GR documents. | `data/raw/`, `scripts/build_verified_catalogue_v2.py`, `tests/test_catalogue_v2_contracts.py` | **CONFIRMED** |
| **C-03** | 13 Tier B schemes implement strict municipal corporation isolation (PMC, PCMC, BMC, TMC, NMMC). | `src/scheme_navigator/domain/jurisdiction.py`, `tests/test_municipal_and_jurisdiction_matching.py` | **CONFIRMED** |
| **C-04** | All 44 Tier C schemes and 14 newly integrated candidates are explicitly marked `verification_status="unverified"` and `eligibility_incomplete=true` / `LIMITED_INFORMATION`. | `data/catalogue/schemes.json`, `tests/test_catalogue_v2_contracts.py`, `tests/test_universe_reconciliation.py` | **CONFIRMED** |
| **C-05** | Document Auditor handles full lifecycle: upload, magic-byte validation, OCR extraction, rule matching, findings, inline correction, and SQLite persistence. | `tests/test_playwright_backend_restart_persistence.py`, `tests/test_document_*.py` | **CONFIRMED** |
| **C-06** | The test suite is strictly non-weakening: 635+ unit/integration tests and 44 Playwright browser tests pass with zero regressions. | `pytest tests/` run output: 0 failed, exit code 0 | **CONFIRMED** |
| **C-07** | All 12/12 individual Appendix H5 canary mutations are caught by tests on the real codebase. | `release/evidence/ws15/E-WS15-002_canary_mutations_individual.json` | **CONFIRMED** |
| **C-08** | 17 Tier A P0 Flagship schemes have complete Appendix E 10-part markdown dossiers in `docs/dossiers/` and formal human review packets in `docs/catalogue/review_packets/`. | `docs/dossiers/`, `docs/catalogue/review_packets/` | **CONFIRMED** |
| **C-09** | Dedicated exclusion pass extracted verbatim statutory exclusion conditions for all 17 Tier A schemes into `data/catalogue/schemes.json`. | `data/catalogue/schemes.json`, `scripts/compile_p0_dossiers_and_exclusions.py` | **CONFIRMED** |
| **C-10** | The citizen UI visibly distinguishes Decision-Ready (`🟢 निर्णय-सज्ज`) from Limited-Information (`ℹ️ मर्यादित माहिती`) schemes with badges, trilingual multi-field search, and contextual advisory banners. | `static/index.html`, `tests/test_playwright_five_citizen_acceptance.py` | **CONFIRMED** |
| **C-11** | Governance human review queue (`/governance/review-queue`) and completeness attestation endpoint (`/governance/review-queue/{scheme_id}/attest`) enforce Invariant I-05 (no AI agent self-authorization; requires authenticated `LEGAL_REVIEWER` or `CATALOGUE_ADMIN`). | `src/scheme_navigator/api/main.py`, `tests/test_governance_review_queue.py` | **CONFIRMED** |
| **C-12** | All 5 citizen archetype journeys pass in real Chromium browser via Playwright (`tests/test_playwright_five_citizen_acceptance.py`). | `tests/test_playwright_five_citizen_acceptance.py` (6/6 passed) | **CONFIRMED** |
| **C-13** | Complete trilingual UI and document guidance across English, Marathi, and Hindi (112 keys with zero leakage). | `static/index.html`, `tests/test_trilingual_parity.py`, `reports/rc4_multilingual_acceptance.md` | **CONFIRMED** |
| **C-14** | SQLite database operations use WAL mode with immediate transaction isolation and strict restart durability. | `src/scheme_navigator/core/citizen_store.py`, `tests/test_sqlite_persistence_and_replacement.py` | **CONFIRMED** |
| **C-15** | Demo fixture `demo-majhi-ladki-bahin` is quarantined and cannot trigger verified eligibility in production. | `tests/test_fail_closed_activation.py`, `tests/test_browser_citizen_experience.py` | **CONFIRMED** |
| **C-16** | Unapproved rules or draft schemes fail closed to Caseworker Review (`NEEDS_REVIEW` / `LIMITED_INFORMATION`). | `tests/test_fail_closed_activation.py`, `src/scheme_navigator/domain/rules.py` | **CONFIRMED** |
| **C-17** | Right to Services (RTS) statutory delivery timelines are rendered on factsheets and document preparation modals. | `data/source_registry/canonical_schemes.json`, `static/index.html` | **CONFIRMED** |
| **C-18** | Verification Tier badges (`Tier A Verified`, `Tier B Verified`, `Tier C Under Review`) reflect authentic evidentiary status. | `static/index.html`, `tests/test_trust_verification_ui.py` | **CONFIRMED** |
| **C-19** | All 15 mandatory citizen journeys (J01–J15) pass in real Chromium via Playwright. | `reports/final_citizen_journey_evidence.json`, `tests/test_playwright_15_citizen_journeys.py` | **CONFIRMED** |
| **C-20** | Document replacement strictly tracks lineage ($v1 \to v2$) with immutable SQLite triggers protecting history. | `tests/test_immutable_audit_history.py`, `src/scheme_navigator/core/citizen_store.py` | **CONFIRMED** |
| **C-21** | Document medium is explicitly categorized (`SEARCHABLE_PDF`, `SCANNED_PDF`, `PHOTOGRAPH`, `IMAGE`). | `tests/test_ocr_and_document_intelligence.py`, `src/scheme_navigator/documents/audit.py` | **CONFIRMED** |
| **C-22** | Image quality gates mathematically detect blur (Laplacian $< 45.0$) and resolution ($< 250$px). | `tests/test_ocr_and_document_intelligence.py`, `src/scheme_navigator/documents/audit.py` | **CONFIRMED** |
| **C-23** | Devanagari numerals (`०-९`) and vernacular formats are accurately parsed into integers and ISO dates. | `tests/test_ocr_and_document_intelligence.py`, `src/scheme_navigator/documents/audit.py` | **CONFIRMED** |
| **C-24** | Document retention purge reactively invalidates downstream readiness proportionally (e.g. 4/5 = 80%, not 0%) with localized re-upload notices in EN, MR, HI. | `tests/test_rc4_retention_and_readiness_math.py`, `tests/test_document_retention_and_readiness.py` | **CONFIRMED** |
| **C-25** | Eligibility status is normalized to `MEETS_VERIFIED_CRITERIA` (`meets_verified_criteria`) with fail-closed protection for unapproved rules/demo fixtures. | `tests/test_eligibility_state_model_consistency.py`, `src/scheme_navigator/domain/models.py` | **CONFIRMED** |
| **C-26** | Field-level extraction matches ground truth with 100% precision (64/64 fields matched) across English, Marathi, Hindi specimens. | `reports/rc4_document_intelligence_accuracy.md`, `tests/test_rc4_document_intelligence_accuracy.py` | **CONFIRMED** |
| **C-27** | 12 representative scheme families validated end-to-end with real upload journeys logged to structured JSON evidence. | `reports/rc4_scheme_diverse_journey_evidence.json`, `tests/test_rc4_scheme_diverse_e2e_journeys.py` | **CONFIRMED** |
| **C-28** | Retention architecture reflects MeitY DPDP staged commencement facts and governs 7 distinct data classes under IT SPDI Rules 2011. | `reports/rc4_retention_and_privacy_audit.md`, `src/scheme_navigator/core/config.py` | **CONFIRMED** |
| **C-29** | Thin-Rule Protection fails closed to Caseworker Review / Limited Info any scheme with < 2 substantive criteria or residency-only rules (Invariant I-07). | `src/scheme_navigator/governance/thin_rule_lint.py`, `tests/invariants/test_trimurti_invariants.py` | **CONFIRMED** |
| **C-30** | Definitive eligibility verdicts strictly require authenticated server-side human completeness attestations bound to rule set SHA-256 hashes; AI cannot self-attest (Invariants I-04, I-05, I-06). | `src/scheme_navigator/governance/attestation_store.py`, `tests/invariants/test_trimurti_invariants.py` | **CONFIRMED** |
| **C-31** | Public error and feedback reporting modal (`#modal-report-issue`) is integrated across English, Marathi, Hindi with ticket creation and immutable JSONL audit ledger. | `static/index.html`, `tests/test_playwright_scheme_issue_reporting.py`, `data/citizen_reports.jsonl` | **CONFIRMED** |
| **C-32** | SC-G2 Official Scheme Universe Snapshot (`data/research/universe/U-20261120.json`) maps 137 authoritative bodies across 5 tiers: 40 State departments & directorates, 18 statutory corporations, 14 central ministries, 29 Municipal Corporations, and 36 District Collectorates. | `data/research/universe/U-20261120.json`, `docs/catalogue/universe_snapshot.md`, `tests/test_universe_reconciliation.py` | **CONFIRMED** |
| **C-33** | Master Candidate Register (`docs/catalogue/scheme_discovery_master_register.csv` and `reports/final_candidate_reconciliation.csv`) reconciles 142 candidates across all 9 required dispositions: 17 `IN_CATALOGUE_VERIFIED`, 71 `IN_CATALOGUE_LIMITED`, 18 `NEEDS_RESEARCH`, 6 `BLOCKED_SOURCE`, 9 `DUPLICATE_OF`, 6 `SUB_SCHEME_OF`, 5 `HISTORICAL`, 7 `EXCLUDED_NOT_INDIVIDUAL_BENEFIT`, 3 `EXCLUDED_OUT_OF_GEOGRAPHIC_SCOPE`. | `reports/final_candidate_reconciliation.csv`, `reports/final_candidate_reconciliation.json`, `tests/test_universe_reconciliation.py` | **CONFIRMED** |
| **C-34** | Source Link Health Audit (`reports/final_source_health.csv`) verified 135 unique official government and portal URLs with real HTTP status codes, latency measurements, and error classifications (57 Working, 26 Dead, 46 Temporarily Unavailable, 6 Unknown). | `reports/final_source_health.csv`, `reports/final_source_remediation.csv`, `docs/governance/final_evidence_quality.md` | **CONFIRMED** |
| **C-35** | Administrative Governance APIs (`/governance/research-summary`, `/governance/candidates`, `/governance/authorities`) and Reviewer UI Universe Dashboard (`static/reviewer.html`) provide interactive real-time candidate search, department filtering, and disposition auditing. | `src/scheme_navigator/api/main.py`, `static/reviewer.html`, `tests/test_playwright_sc_g2_reconciliation.py` | **CONFIRMED** |
| **C-36** | Frozen Scorer v1 (`1.0.0-sc-g1`) mechanically evaluated with zero weight, denominator, or formula tampering, yielding a composite score of **76.65/100** (up from SC-G1 baseline of 69.74/100). | `reports/final_scorecard.json`, `reports/final_scorecard.md`, `reports/final_score_reconciliation.md` | **CONFIRMED** |
| **C-37** | 19 Playwright real-browser workflows covering all 18 Section 18 workflows and Reviewer tab pass in real Chromium browser (`tests/test_playwright_sc_g2_reconciliation.py`). | `tests/test_playwright_sc_g2_reconciliation.py` (19/19 passed) | **CONFIRMED** |
| **C-38** | All 10 Citizen Journeys (A to J) and all 10 synthetic citizen personas pass end-to-end in real Chromium browser via Playwright (`tests/test_playwright_trimurti_v4_acceptance.py`). | `tests/test_playwright_trimurti_v4_acceptance.py` (20/20 passed) | **CONFIRMED** |
| **C-39** | Final requirements register (`docs/project/final_requirements_register.md`) achieves 100.0% accepted software project completion across all 55 frozen atomic requirements. | `docs/project/final_requirements_register.md`, `reports/final_project_completion_report.md` | **CONFIRMED** |
| **C-40** | Local Government Directory (LGD) mapping codified for all 36 districts and all 29 Municipal Corporations of Maharashtra with official portal endpoints. | `reports/final_lgd_reconciliation.csv`, `docs/catalogue/local_scheme_coverage.md` | **CONFIRMED** |

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
