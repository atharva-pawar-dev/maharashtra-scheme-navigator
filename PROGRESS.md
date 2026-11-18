# Progress Tracker: Verified Catalogue v2 & Document Review Overhaul (PROGRESS.md)
**Last Updated:** 2026-11-18T21:20:00+05:30  
**Active Phase:** Complete — Tagged `catalogue-v2-rc1`  
**Branch:** `feat/catalogue-v2`  

---

## 1. Scheme Counts by Verification & Coverage Tier

| Metric | Target | Final Release Status | Gate Result |
| :--- | :--- | :--- | :--- |
| **Total Schemes Catalogued** | 75+ | **75 schemes** | **PASS** |
| **Tier A (Flagship / Full Verification)** | 15+ fully verified | **17 schemes (100% verified quotes)** | **PASS** |
| **Tier B (Municipal / Local Government)** | 10+ | **13 schemes (PMC, PCMC, BMC, TMC, NMMC)** | **PASS** |
| **Tier C (Discovered / Exploratory)** | Remainder | **44 schemes (explicitly unverified)** | **PASS** |
| **Schemes with Residency-Only Rules** | 0 in Tier A / B | **0 schemes** | **PASS** |
| **Schemes with < 2 Substantive Criteria** | 0 in Tier A / B | **0 schemes** | **PASS** |
| **Schemes with Verbatim Sourced Quotes** | 100% of Tier A | **100% of Tier A criteria verified against data/raw/** | **PASS** |
| **Document Consistency Checks** | Mismatch + Expiry | **Income mismatch, Caste mismatch, Expiry, Unreadable** | **PASS** |
| **Regression Test Invariance** | 0 Regressions | **520/520 Pytest + 30/30 Playwright Browser PASSED** | **PASS** |

---

## 2. Phase Completion Status

- [x] **Phase 0: Read-Only Audit & Baseline Analysis** (Completed 2026-11-18)
  - Baseline pytest suite verified: 518 tests collected.
  - Criteria distribution mapped across all 75 canonical schemes.
  - Root cause of lone-residency identified in `CanonicalCatalogService._load()`.
  - Deliverables: `reports/audit.md`, `DECISIONS.md`, `PROGRESS.md`, `CHANGELOG.md`.

- [x] **Phase 1: Contract-First Data Model** (Completed 2026-11-18)
  - Canonical Profile Vocabulary registry (`profile_vocabulary.py`).
  - Pydantic v2 domain models (`SchemeV2`, `Criterion`, `DocRequirement`, `SourceEvidence`, `LegalBasis`, `BenefitDetails`).
  - Hard validator: `< 2 substantive criteria` -> auto `eligibility_incomplete=true`.
  - CI guard test preventing verified schemes with only residency rules (`test_catalogue_v2_contracts.py`).
  - JSON Schema export: `schemas/catalogue_v2.json`.
  - SQLite Migration 2 (`catalogue_v2_provenance_and_rules`) implemented and verified.

- [x] **Phase 2 & 3: Source Crawl, Cache & Verbatim Quote Verification** (Completed 2026-11-18)
  - Built raw source caching infrastructure (`raw_cache.py`) managing `data/raw/`.
  - Cached 17 raw Government Resolutions and central guidelines with SHA-256 digests.
  - Programmatic substring verification of original Marathi quotes against raw files.

- [x] **Phase 4: Structured Data Compilation & Audit Dossier** (Completed 2026-11-18)
  - Executed `scripts/build_verified_catalogue_v2.py`.
  - Generated:
    - `data/catalogue/schemes.json`, `schemes.csv`, `schemes.xlsx`
    - `data/catalogue/discovery_index.csv`
    - `reports/priority_review.md`
    - `reports/conflicts.md`
    - `reports/coverage_report.md`
    - `reports/blocked_sources.md`
    - `reports/unverified_queue.csv`

- [x] **Phase 5: Rule Engine & Results UX Integration** (Completed 2026-11-18)
  - Integrated `CanonicalCatalogService._load()` to serve Catalogue v2 with full jurisdiction isolation and metadata.
  - Preserved backward compatibility for test harnesses (`catalog.all()`) while serving full 75 canonical schemes to `/results` and `scope=canonical`.
  - Maintained single canonical scheme ID and version across all journeys.

- [x] **Phase 6: Document Review Overhaul & Privacy Enforcement** (Completed 2026-11-18)
  - Built `aadhaar_privacy.py` with Verhoeff $D_5$ checksum validation and `XXXX-XXXX-1234` masking.
  - Upgraded `document_prep.py` with:
    - `PROFILE_DOCUMENT_INCOME_MISMATCH`
    - `INCOME_EXCEEDS_SCHEME_THRESHOLD`
    - `AGE_DOB_MISMATCH`
    - `CASTE_CATEGORY_MISMATCH`
    - `UNREADABLE` / blurry document detection
    - `EXPIRED` certificate detection
    - RTS notified statutory days and authorized alternative document suggestions.
    - Statutory disclaimer: "Pre-check only; the official department verifies authenticity upon application."

- [x] **Phase 7: Comprehensive Testing Suite & Real Browser Verification** (Completed 2026-11-18)
  - 17 Golden Personas verified across Eligible, Borderline, Ineligible, and Needs Info (`test_golden_personas_tier_a.py`).
  - Document Review Overhaul test fixture suite (`test_document_review_overhaul.py`).
  - Aadhaar Privacy test suite (`test_aadhaar_privacy.py`).
  - 520 non-browser pytest regression tests PASSED (0 failures).
  - 30 Playwright browser tests PASSED (0 failures).
  - Real browser verification of all 4 primary journeys (DISCOVER, UNDERSTAND, PREPARE, APPLY) across Desktop & Mobile, English & Marathi with 16 screenshots (`verify_browser_journeys.py`).

- [x] **Phase 8: Launch Gates, Final Exports & RC Tagging** (Completed 2026-11-18)
  - Generated `reports/launch_readiness.md`.
  - Updated `PROGRESS.md`, `CHANGELOG.md`, `DECISIONS.md`.
  - Tagged release candidate `catalogue-v2-rc1`.
