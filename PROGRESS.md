# Progress Tracker: Verified Catalogue v2 & Document Review Overhaul (PROGRESS.md)
**Last Updated:** 2026-11-20T21:05:00+05:30  
**Active Phase:** TRIMURTI v3 — Milestone SC-M0 Complete, SC-G1 In Progress  
**Branch:** `feat/catalogue-v2`  
**Milestone Tags:** `rc4-accepted`, `sc-m0-accepted` (pending tag)

---

## 0. TRIMURTI v3 Scheme Universe Intelligence Ladder

| Milestone | Target Scope | Status | Audit Score / Evidence |
| :--- | :--- | :---: | :--- |
| **SC-M0** | Baseline, Safety & Overclaim Prevention | **PASS** | 64.8/100 Honest Baseline; 621 pytest tests, 19 Playwright tests, 12 canaries; Thin-rule lint & DB attestations active. |
| **SC-G1** | P0 High-Impact Scheme Depth | **IN PROGRESS** | Flagship social assistance, DBT, scholarships, and pension deep dossiers with verbatim quotes. |
| **SC-G2** | Complete Universe & Department Reconciliation | **PENDING** | 40+ departments, municipal bodies, and state portals inventory reconciliation. |
| **SC-G3** | P1 Depth, Document Graphs & Lifecycle | **PENDING** | Complete document requirement graph, renewal workflows, and Right to Services timelines. |
| **SC-G4** | Quality Instrumentation & Update Monitoring | **PENDING** | Automated daily GR scraper, diff engine, and change alert feed. |
| **SC-G5** | Independent Audit & Long-Tail Completion | **PENDING** | Final 9.5/10 quality target, independent human reviewer sign-off pack, and production handoff. |

---

---

## 1. Scheme Counts by Verification & Coverage Tier

| Metric | Target | Final Release Status | Gate Result |
| :--- | :--- | :--- | :--- |
| **Total Schemes Catalogued** | 75+ | **75 schemes (74 canonical + 1 demo fixture)** | **PASS** |
| **Tier A (Flagship / Full Verification)** | 15+ fully verified | **17 schemes (100% verified quotes)** | **PASS** |
| **Tier B (Municipal / Local Government)** | 10+ | **13 schemes (PMC, PCMC, BMC, TMC, NMMC)** | **PASS** |
| **Tier C (Discovered / Exploratory)** | Remainder | **44 schemes (explicitly unverified)** | **PASS** |
| **Schemes with Residency-Only Rules** | 0 in Tier A / B | **0 schemes** | **PASS** |
| **Schemes with < 2 Substantive Criteria** | 0 in Tier A / B | **0 schemes** | **PASS** |
| **Schemes with Verbatim Sourced Quotes** | 100% of Tier A | **100% of Tier A criteria verified against data/raw/** | **PASS** |
| **Document Consistency Checks** | Mismatch + Expiry | **Income mismatch, Caste mismatch, Expiry, Unreadable** | **PASS** |
| **Regression Test Invariance** | 0 Regressions | **613/613 Pytest + 47/47 Playwright Browser PASSED** | **PASS** |
| **Canary Mutation Detection** | 12/12 caught | **12/12 Individual Appendix H5 Canaries Caught** | **PASS** |

---

## 2. Phase Completion Status

- [x] **Phase 0: Read-Only Audit & Baseline Analysis** (Completed 2026-11-18)
  - Baseline pytest suite verified: 518 tests collected.
  - Criteria distribution mapped across all 75 canonical schemes.
  - Deliverables: `reports/audit.md`, `DECISIONS.md`, `PROGRESS.md`, `CHANGELOG.md`.

- [x] **Phase 1: Contract-First Data Model** (Completed 2026-11-18)
  - Canonical Profile Vocabulary registry (`profile_vocabulary.py`).
  - Pydantic v2 domain models (`SchemeV2`, `Criterion`, `DocRequirement`, `SourceEvidence`, `LegalBasis`, `BenefitDetails`).
  - JSON Schema export: `schemas/catalogue_v2.json`.
  - SQLite Migration 2 (`catalogue_v2_provenance_and_rules`) implemented and verified.

- [x] **Phase 2 & 3: Source Crawl, Cache & Verbatim Quote Verification** (Completed 2026-11-18)
  - Built raw source caching infrastructure (`raw_cache.py`) managing `data/raw/`.
  - Cached 17 raw Government Resolutions and central guidelines with SHA-256 digests.
  - Programmatic substring verification of original Marathi quotes against raw files.

- [x] **Phase 4: Structured Data Compilation & Audit Dossier** (Completed 2026-11-18)
  - Generated `data/catalogue/schemes.json`, `schemes.csv`, `schemes.xlsx`, `discovery_index.csv`.
  - Audited 75 schemes with geographic isolation in `docs/catalogue/catalogue_integrity_audit.md`.

- [x] **Phase 5: Document Review Overhaul & Readiness Engine Rebuild** (Completed 2026-11-18)
  - Rebuilt Document Auditor with multi-page PDF support, magic-byte validation, and local deterministic fallback.
  - Implemented 9 consistency & verification checks (`PROFILE_DOCUMENT_INCOME_MISMATCH`, `EXPIRED_OR_STALE`, etc.).
  - Added inline controls (`[Confirm / Correct Extracted Value]`, `[Update My Profile to Match Document]`, `[Replace Document]`).
  - Implemented mathematical `ReadinessEngine` with dynamic reactive invalidation.
  - Synthetic Fixture Generator: `tests/fixtures/generate_synthetic_documents.py` (9 watermarked specimens).

- [x] **Phase 6: 15 Mandatory End-to-End Playwright Browser Journeys** (Completed 2026-11-18)
  - Executed and passed all 15 journeys in `tests/test_playwright_15_citizen_journeys.py`.
  - Total browser tests: 46 passed (0 failed).

- [x] **Phase 7: RC2 Forensic Acceptance & Hard Restart Invariance** (Completed 2026-11-19)
  - SQLite Migration 4: durable document and audit history schema across hard server restarts.
  - Non-destructive document replacement lineage ($v1 \to v2$) with hash and reason tracking.
  - Tagged `rc2-forensic-accepted` at commit `f10a0a0`.

- [x] **Phase 8: RC3 Document Intelligence, Scheme Coverage & Citizen Trust Hardening** (Completed 2026-11-19)
  - Multimodal document processing distinguishing `SEARCHABLE_PDF`, `SCANNED_PDF`, `PHOTOGRAPH`, `IMAGE`.
  - Image quality rejection: resolution < 250px (`LOW_RESOLUTION_IMAGE`) and blur variance < 45.0 (`IMAGE_EXCESSIVE_BLUR`).
  - Devanagari numerals (`०-९`), currency, and FY extraction; separated OCR uncertainty from rule failures.
  - Multi-page missing page detection (`MISSING_PAGE_IN_SEQUENCE`).
  - Scheme-diverse document requirement coverage across 12 families (`docs/quality/scheme_diverse_document_coverage.md`).
  - SQLite Migration 5 triggers enforcing append-only immutability on document content, hashes, and audit history.
  - 24-hr retention ceiling purge with reactive readiness invalidation and localized re-upload notices in EN, MR, HI.
  - Normalized eligibility status `MEETS_VERIFIED_CRITERIA` with fail-closed protection for demo fixtures.
  - Exact trilingual symmetry across 112 keys in `static/index.html` verified via Playwright in Chromium.
  - Full test suite: **606/606 tests passing**, **12/12 canaries caught**.
  - Tagged `rc3-hardened`.

- [x] **Phase 9: RC4 Real-World Document Intelligence & Citizen Trust Acceptance** (Completed 2026-11-19)
  - Verified 6 document processing routes end-to-end: Searchable PDF, Scanned PDF (Tesseract OCR), Multi-page with gap detection, Mobile phone photo (EXIF orientation), Low-contrast official scan handling, and Trilingual extraction (EN, MR, HI).
  - Field-level ground truth accuracy: 64/64 fields matched across Marathi, Hindi, and English specimens with 0 false rejections on readable low-contrast scans.
  - Scheme-diverse document coverage: 12/12 scheme families executed end-to-end through discovery, requirements, upload, OCR, persistence, readiness, and official handoff (`reports/rc4_scheme_diverse_journey_evidence.json`).
  - Proportional readiness math: Verified monotonic, non-collapsing score adjustments ($N \to N-1$, 100% $\to$ 80% $\to$ 60%) upon purge of individual documents, with valid ANY_OF alternate requirements logic.
  - Staged DPDP commencement vs IT SPDI Rules 2011 distinction established across 7 data classes with concrete retention policies (`reports/rc4_retention_and_privacy_audit.md`).
  - Trilingual UI & notices: Full 112-key parity across English, Marathi, Hindi with Devanagari numeral conversions and localized expiry notifications.
  - Full regression test suite: **613/613 Pytest tests passing**, **47/47 Playwright browser tests passing**, **12/12 canaries caught**.
  - Milestone Tag: `rc4-accepted`.

- [x] **Phase 10: TRIMURTI Milestone SC-M0 — Baseline, Safety & Overclaim Prevention** (Completed 2026-11-20)
  - Enforced 7 hard architectural safeguards preventing overclaims and AI self-authorization.
  - Implemented Thin-Rule Protection (`thin_rule_lint.py`) failing closed schemes with < 2 substantive criteria or residency-only rules (Invariant I-07).
  - Built SQLite-backed Attestation Store (`attestation_store.py`) enforcing server-side human reviewer role check and binding approvals to rule set SHA-256 hashes (Invariants I-04, I-05, I-06).
  - Audited 64 official government links & GRs (`reports/source_link_health_report.md`).
  - Implemented 10-dimension auditable quality scorecard (`scorer.py`) deriving an honest baseline score of **64.8 / 100** (`reports/scheme_coverage_scorecard.md`).
  - Integrated public trilingual error reporting (`#modal-report-issue`) directly into citizen UI with immutable audit logging (`tests/test_playwright_scheme_issue_reporting.py`).
  - Authored comprehensive catalogue documentation: Universe Scope (`U-20261120`), Department Source Inventory (32 departments), Provenance Matrix, Lifecycle Register, Canonical Reconciliation, and Rule Completeness Register.
  - Test Suite: **621/621 Pytest tests passing**, **19/19 Playwright browser tests passing**, **12/12 canaries caught**.
  - Milestone Tag: `sc-m0-accepted`.
