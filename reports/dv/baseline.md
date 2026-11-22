# MSN-DV-001: Baseline Audit & Environment Truth Report

**Mission ID:** `MSN-DV-001` — "Your Papers, Ready" (Document Readiness Engine)  
**Baseline Date & Time:** 2026-11-22T23:35:00+05:30 (UTC: 2026-11-22T18:05:00Z)  
**Repository:** `C:\Users\Admin\Downloads\scheme-navigator\scheme-navigator`  
**Branch:** `feat/dv-001`  
**Baseline Commit:** `6d4495d`  
**Baseline Tag:** `dv-baseline`  
**Historical Tag Preserved:** `project-final-accepted` (at commit `7adb0f93074f4fc6e4cbc69c1ba172b0cb73eb04`)  
**Operating System:** Windows (PowerShell, UTF-8 environment enforced)  

---

## 1. Baseline Backup & Restore Proof

In accordance with §5.7 Item 2:
- **Backup Directory:** `backups/dv-baseline-20261122_175947/`
- **Total Files Backed Up:** 661 files covering `data/` and `docs/catalogue/`
- **Integrity Manifest:** `backups/dv-baseline-20261122_175947/SHA256SUMS.txt`
- **Restore Verification:** Restored completely into `scratch/restore_verification/`. All 661 file SHA-256 hashes matched 100% against the manifest.

---

## 2. Environment Truth

| Component | Status / Version | Notes |
| :--- | :--- | :--- |
| **Python** | 3.11.4 (`MSC v.1934 64 bit (AMD64)`) | Standard runtime |
| **OpenCV (`cv2`)** | `4.14.0` | Image processing, blur detection, bounds heuristic |
| **PyMuPDF (`fitz`)** | `1.28.2` | High-fidelity PDF rendering, text extraction, page parsing |
| **Playwright** | `Installed` (Python bindings + Chromium) | Browser journey automation and touch emulation |
| **Pydantic** | `2.14.1` | Strict schema validation |
| **FastAPI** | `0.162.0` | Backend API framework |
| **Tesseract OCR** | `NOT_INSTALLED_IN_PATH` | CLI binary absent on host PATH; local PyMuPDF text layer and CV preprocessing operational; external VLM fallback available |
| **OpenAI API Key** | `PRESENT` in `os.environ` | Available for optional VLM fallback under explicit citizen consent |
| **Other AI Keys** | `ABSENT` (`ANTHROPIC`, `GEMINI`, `GOOGLE`, `AZURE`, `MISTRAL`) | Accurately recorded per Law L12 |

---

## 3. Pre-Existing Test Suite Baseline

Prior to starting implementation, all existing suites were verified on branch `feat/dv-001`:

| Suite Category | Tests Run | Passed | Failed | Exit Code | Baseline Integrity |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Full Pytest Regression** | 682 | 682 | 0 | **0** | Verified clean baseline |
| **Browser Suites (Playwright)** | 94 | 94 | 0 | **0** | All 94 unique test node IDs passing |
| **Core Invariants (I-01 - I-20)** | 7 | 7 | 0 | **0** | Invariant tripwires active |
| **Canary Mutation Sensitivity** | 12 | 12 caught | 0 | **0** | All 12 Appendix H5 bugs detected |
| **AST Codebase Syntax Check** | 636 tests | Clean | 0 | **0** | Zero syntax errors |

---

## 4. Catalogue Fingerprint

- **Normalised `schemes.json` SHA-256:** `b1a9d64303213df304dbc372ce401aedacc6887e2992e895954d84ba8ea2208b`
- **Total Canonical Schemes:** 88 in `schemes.json`; 89 in `SourceRegistry`
- **Active Canonical Schemes:** 87
- **Quarantined Demo Fixtures:** 2 (`demo-majhi-ladki-bahin`, `demo-indira-gandhi-old-age-pension`)
- **Total Candidates in Universe:** 142 across 9 dispositions
- **Evidence Baseline:** 31 schemes with source references; 15 valid non-demo attestation records; 0 synthetic approvals

---

## 5. Existing Capabilities Classification (23 Areas)

| # | Capability Area | Classification | Architectural Location & Status |
|---|:---|:---:|:---|
| 1 | Document Requirement Discovery | `WORKING_AND_TESTED` | `SourceRegistry`, `data/research/universe/`, 75 schemes with document requirements |
| 2 | Two-Layer Slot Architecture | `MISSING` | To be implemented in S1 (`DocTypeProfile` + `RequirementSlot`) |
| 3 | Requirement Evidence Tiers | `PARTIALLY_INTEGRATED` | Exists in research CSVs; needs formal schema and UI representation |
| 4 | Secure Intake & Magic-Byte Sniffing | `WORKING_AND_TESTED` | `src/scheme_navigator/documents/audit.py` (`validate_upload`), tests pass |
| 5 | Camera Capture & Quality Guidance | `MISSING` | Live client-side blur/glare/bounds guidance to be implemented in S0/S2 |
| 6 | Multi-Format Ingestion (PDF/IMG) | `WORKING_AND_TESTED` | Handles PDF, PNG, JPEG with page caps |
| 7 | PDF Sanitization & Bomb Protection | `WORKING_AND_TESTED` | PyMuPDF page bounds, decompression limits enforced |
| 8 | Coherence-Checked Text Layer | `WORKING_NOT_FULLY_TESTED`| PyMuPDF text extraction exists; needs legacy Devanagari font coherence check |
| 9 | Local OCR Engine | `BLOCKED_EXTERNAL_DEPENDENCY` | Tesseract binary not on PATH; fallback routes must be explicit |
| 10| Optional VLM Cascade | `PARTIALLY_INTEGRATED` | Structured field extraction exists; needs strict consent gate and system prompt guard |
| 11| Extracted Value Normalisation | `WORKING_AND_TESTED` | Dates, amounts, names normalised in `audit.py` |
| 12| Maharashtra Name Matching | `WORKING_AND_TESTED` | Order hypotheses and transliteration in `audit.py`; marriage hypothesis to add |
| 13| Confirm-with-Crop Interface | `MISSING` | Bounding-box crop extraction exists; side-by-side UI to build in S3 |
| 14| Deterministic Single-Doc Checks | `WORKING_AND_TESTED` | Income ceiling, validity period, issuing authority checks in `audit.py` |
| 15| Cross-Document Consistency Engine | `WORKING_AND_TESTED` | Name/DOB/Income cross-checks in `grouping.py` and `audit.py` |
| 16| Plain-Language Trilingual Remediation| `PARTIALLY_INTEGRATED` | Issue reporting exists; needs strict grade-6 template catalogue |
| 17| Re-upload & Selective Invalidation | `PARTIALLY_INTEGRATED` | Full re-audit works; dependency-based selective invalidation to build in S5 |
| 18| Persistence & Restart Recovery | `WORKING_AND_TESTED` | SQLite WAL persistence verified across restart |
| 19| Privacy Masking & Deletion Verification | `WORKING_AND_TESTED` | 24-hr purge and masked storage verified in security suite |
| 20| Authenticity Adapters | `MOCK_ONLY` | QR payload parsing exists; Level-3 issuer adapters start `NOT_CONFIGURED` |
| 21| Readiness & Next-Step Engine | `PARTIALLY_INTEGRATED` | Document status reported; needs 7-dimension non-composite checklist UI |
| 22| Reviewer Governance Queue | `WORKING_AND_TESTED` | `static/reviewer.html` and review endpoints operational |
| 23| Application Preparation & Portal Handoff| `WORKING_AND_TESTED` | Tracking and mock autofill operational; printable slip to add in S6 |

---

## 6. The Aaji Walkthrough Baseline (UX & Ergonomics Audit)

Walking the existing application interface as Aaji (Marathi, touch-only, 200% text, Slow-3G):
1. **Text Sizing:** No persistent A/A+/A++ text resizing widget; relying on browser zoom at 200% causes card overflow on narrow mobile viewports (<360px).
2. **Read-Aloud:** Completely absent on current document upload and audit screens.
3. **Touch Targets:** Some action links and dismiss badges are 24-32px, failing the 48x48px touch-target floor.
4. **Devanagari Typography:** Current CSS uses `line-height: 1.4-1.5`, which clips top vowel marks (matras) and conjuncts in Devanagari. Needs `line-height: 1.7` floor.
5. **Feedback on Blurry Photo:** Currently, uploading a blurry document displays an OCR score failure or generic text alert instead of kind, actionable guidance: *"फोटो थोडा अस्पष्ट आहे. कृपया चांगल्या उजेडात पुन्हा फोटो काढा."*
6. **Confirmation Step:** Citizens cannot see extracted values side-by-side with original document crops.

---

## 7. Pilot Scheme Selection & Frequency Analysis

From empirical analysis of all 92 canonical scheme dossiers, the Top 5 most frequent document types are:
1. `DOC-INCOME-CERT`: Income Certificate (उत्पन्नाचा दाखला)
2. `DOC-DOMICILE-CERT`: Domicile / 15-Year Residence Certificate (अधिवास दाखला)
3. `DOC-RATION-CARD`: Ration Card (शिधापत्रिका)
4. `DOC-BANK-PASSBOOK`: Bank Account Passbook (बँक पासबुक)
5. `DOC-AADHAAR-CARD`: Aadhaar Card (आधार कार्ड)

Ten pilot schemes were formally selected covering smallholder farmers, students, senior citizens, widows, divyang, and youth entrepreneurs. Detailed in [dv-001-pilot-scheme-selection-and-doctype-hierarchy.md](file:///C:/Users/Admin/Downloads/scheme-navigator/scheme-navigator/docs/adr/dv-001-pilot-scheme-selection-and-doctype-hierarchy.md).

---

## 8. Transition to Slice 0

With the baseline established, backups verified, catalogue fingerprinted, and ADR dv-001 recorded, the mission proceeds directly into **Slice 0 (S0): Baseline, Law Tripwires, and Age-Inclusive Design Kit**.
