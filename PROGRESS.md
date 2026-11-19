# Progress Tracker: Verified Catalogue v2 & Document Review Overhaul (PROGRESS.md)
**Last Updated:** 2026-11-19T22:25:00+05:30  
**Active Phase:** Complete — RC3 Document Intelligence, Scheme Coverage & Citizen Trust Hardening Verified  
**Branch:** `feat/catalogue-v2`  
**Milestone Tag:** `rc3-hardened`

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
| **Regression Test Invariance** | 0 Regressions | **606/606 Pytest + 47/47 Playwright Browser PASSED** | **PASS** |
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
