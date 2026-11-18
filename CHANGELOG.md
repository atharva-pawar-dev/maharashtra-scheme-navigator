# Changelog: Verified Catalogue v2 & Document Review Overhaul

All notable changes to the Maharashtra Scheme Navigator codebase during the Catalogue v2 and Document Review Overhaul are documented in this file.

## [catalogue-v2-rc1] - 2026-11-18

### Added
- **Verified Catalogue v2 Data Model:**
  - `SchemeV2`, `Criterion`, `DocRequirement`, `SourceEvidence`, `LegalBasis`, `BenefitDetails`, `VerificationMeta` with Pydantic v2 strict schemas.
  - Canonical Profile Vocabulary registry (`profile_vocabulary.py`) establishing substantive criteria classifications.
  - Hard validator: Any scheme with $< 2$ substantive criteria is auto-flagged `eligibility_incomplete=true` and barred from producing `ELIGIBLE`.
  - JSON schema export at `schemas/catalogue_v2.json`.
  - SQLite Migration 2 (`catalogue_v2_provenance_and_rules`) adding verified provenance and criteria tables.
- **Raw Document Cache & Ingestion Architecture:**
  - `RawSourceCache` in `src/scheme_navigator/ingestion/raw_cache.py` managing `data/raw/` with SHA-256 integrity checks.
  - Ingested and cached 17 raw official Government Resolutions and Central Ministry guidelines.
  - Programmatic Unicode NFC-normalized verbatim quote verification.
- **17 Tier A Verified Flagship Schemes:**
  - Majhi Ladki Bahin, Sanjay Gandhi Niradhar, Shravanbal, IGNOAPS, IGNWPS, IGNDPS, Post-Matric SC/OBC, EBC Tuition Waiver, Namo Shetkari, PM-KISAN, Bhausaheb Fundkar, MJPJAY, CMEGP, Annasaheb Patil, Ramai Awas, and Vayoshri.
  - 100% verified verbatim Marathi quotes and official GR citations.
- **Document Review Overhaul & Privacy Hardening:**
  - `src/scheme_navigator/security/aadhaar_privacy.py`: Implemented Verhoeff $D_5$ checksum validation, full Aadhaar regex masking (`XXXX-XXXX-1234`), and log sanitization.
  - Enhanced `src/scheme_navigator/services/document_prep.py`: Added checks for `PROFILE_DOCUMENT_INCOME_MISMATCH`, `INCOME_EXCEEDS_SCHEME_THRESHOLD`, `AGE_DOB_MISMATCH`, `CASTE_CATEGORY_MISMATCH`, `UNREADABLE`, and `EXPIRED`.
  - Added RTS statutory timelines, authorized alternative document mapping, and mandatory statutory authenticity disclaimer.
- **Comprehensive Testing Suite:**
  - 17 Golden Personas testing 4 outcome states across all Tier A schemes (`tests/test_golden_personas_tier_a.py`).
  - Document Review Overhaul test suite (`tests/test_document_review_overhaul.py`).
  - Aadhaar Privacy test suite (`tests/test_aadhaar_privacy.py`).
  - Catalogue v2 Contracts test suite (`tests/test_catalogue_v2_contracts.py`).
  - Real browser Playwright journey verification script (`scripts/verify_browser_journeys.py`).
- **Reports & Release Deliverables:**
  - `reports/launch_readiness.md`: Launch Readiness and Compliance Audit Report.
  - `reports/priority_review.md`: Side-by-side audit of flagship schemes.
  - `reports/conflicts.md`: Document conflict analysis.
  - `reports/coverage_report.md`: Catalogue tier breakdown and coverage analysis.
  - `reports/blocked_sources.md`: Documentation of blocked and unreachable official sources.
  - `reports/unverified_queue.csv`: Queue of Tier C exploratory schemes pending GR ingestion.
  - `data/catalogue/schemes.json`, `schemes.csv`, `schemes.xlsx`: Multi-format catalogue exports.
  - `data/catalogue/discovery_index.csv`: Citizen discovery index.

### Changed
- `CanonicalCatalogService._load()`: Now loads verified schemes directly from `data/catalogue/schemes.json` while maintaining full municipal jurisdiction isolation, residency duration enforcement, and backward-compatible alias resolution.
- `api/main.py`: Updated `/eligibility/evaluate`, `/interview/start`, and `/documents/prepare` to serve full verified catalogue for `scope=canonical` while preserving test harness compatibility.
- `rule_engine.py`: Enhanced partial matching logic to allow exploratory matches when substantive criteria pass and secondary information is pending.
