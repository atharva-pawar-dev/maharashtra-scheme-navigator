# Scheme Navigator — Statement of Capabilities & Operational Limitations

**Document Version:** 1.3.0 (Reality Audit Baseline)  
**Date:** November 13, 2026  
**Target Territory:** Maharashtra, India  
**Audience:** Government Leadership, External Auditors, Citizen Advocates  
**Publication Reality Invariant:** Active Published Production Schemes = 0 (ZERO) | Active Demo Fixtures = 2 | Quarantined Draft Candidates = 7  

---

## 1. Verified Software Capabilities (Release Path A — Operational Today)

The following capabilities have been engineered, automated, and verified across **299 passing automated tests** and **19 headless browser state captures**:

| Subsystem | Verified Functionality | Technical Evidence |
|---|---|---|
| **Deterministic Rule Engine** | Pure three-valued logic (`TRUE`, `FALSE`, `UNKNOWN`). Evaluates complex age, gender, income, caste, disability, and land conditions without AI hallucination. | 299 tests in `tests/test_rules.py`, `tests/test_three_citizen_journeys.py`, `tests/test_supreme_master_capabilities.py` |
| **Three Citizen Journeys** | Guided AI interview (`view-interview`), independent library search (`view-explore`), and application prep/resume (`view-prepare`). | Headless browser captures 01–19 in `artifacts/ui-redesign/` |
| **Comprehensive Source Registry** | 72 official sources indexed across all categories (35 state departments, 11 corporations, 6 central/joint, 8 core portals, 6 collectorates, 6 municipal corps). | Verified via `GET /source-registry/sources` and `data/source_registry/sources.json` |
| **Canonical Scheme Inventory** | 9 deduplicated canonical schemes (2 active demo fixtures + 7 draft candidates) mapped to 26 portal aliases and authoritative GR citations. | Verified via `GET /canonical-schemes` and `data/source_registry/canonical_schemes.json` |
| **Public Services Registry (RTS)** | Authoritative registry of 8 core certificates (Domicile, Income, Caste, NCL, UDID, 7/12, Ration Card, Senior Citizen) with statutory days and designated/appellate officers under Maharashtra RTS Act 2015. | Verified via `GET /public-services` and `data/source_registry/public_services.json` |
| **Application Channels Registry** | Mappings for schemes to their authentic portals (`DIRECT_OFFICIAL_PORTAL`, `OFFLINE_OFFICE_APPLICATION`). | Verified via `GET /channels` and `data/source_registry/application_channels.json` |
| **Citizen Application Tracking** | Tracks citizen progress with mandatory `is_citizen_reported: true` invariant. Never falsely claims official submission. | Verified via `POST /application/track` and `GET /application/track/{id}` |
| **Source Lifecycle Monitor** | Monitors source availability, content hashes (SHA-256), detects amendments, and supports publication suspension. | Verified via `GET /source-registry/monitor/status` |
| **Prerequisite DAG Roadmap** | Computes topological dependency graph of prerequisites with RTS days and critical path estimation. | Verified via `POST /plans/{scheme_id}` and NetworkX planner |
| **Document Pre-Audit Workspace** | Validates file security (magic bytes, size), extracts structured schemas, provides machine extraction disclaimer. | Verified via `POST /documents/audit-upload` |
| **Multilingual Integrity** | Pure monolingual separation in Marathi, Hindi, and English with Devanagari numerals (`०-९`) in Devanagari views. | Verified in `tests/test_multilingual_voice.py` |
| **Session Security & Privacy** | Stateless HMAC-SHA256 session ownership, zero plaintext Aadhaar storage, zero password collection, 24-hr ephemeral TTL. | Verified in `tests/test_security_remediation.py` |
| **Concurrent Load Benchmark** | Live load test on running server (250 requests across 10 threads) measured 131.35 RPS, 71.08 ms p50 latency, and 0 unhandled 500 errors. | Verified via `scratch/run_load_and_concurrency_test.py` |
| **Disaster Recovery Restore** | Live SQLite backup (47.01 ms) and restore (64.16 ms) benchmarked with post-restore `PRAGMA integrity_check` returning `['ok']`. | Verified via `scratch/run_dr_restoration_test.py` |

---

## 2. Explicit Operational Limitations & External Blockers

The following capabilities are **not currently available or authorized** and require formal external government authorization or infrastructure:

| Limitation / Feature | Current Truthful Status | Governance Rationale & Technical Boundary |
|---|:---:|---|
| **Official Government Partnership / Accreditation** | **NOT AUTHORIZED** | Scheme Navigator is an independent technology platform. It makes zero claim of official endorsement, CSC partnership, or government adoption. Software cannot grant itself authority. |
| **Demonstration Video (MP4)** | **VIDEO NOT PRODUCED — DEMONSTRATION MATERIALS PREPARED** | Demonstration package contains scripts, storyboard, captions, and slide briefing, but no binary MP4 video file has been rendered. |
| **PostgreSQL Database** | **NOT IMPLEMENTED / ARCHITECTURE SPECIFIED** | SQLite WAL mode is used for persistence (`data/interviews.sqlite3`). Multi-worker deployment requires provisioning an external PostgreSQL cluster. |
| **Distributed Rate Limiting (Redis)** | **NOT IMPLEMENTED / IN-MEMORY USED** | In-memory sliding window limiter is used; single worker `--workers 1` enforced. Multi-worker scaling requires external Redis cluster. |
| **Document Encryption At Rest** | **PARTIAL (IN-MEMORY & EPHEMERAL PURGE ONLY)** | Ephemeral byte processing and 24-hr TTL purge implemented. Persistent on-disk AES-256 volume encryption is NOT implemented. |
| **TLS / HTTPS** | **PARTIALLY IMPLEMENTED (REVERSE PROXY REQUIRED)** | HSTS/CSP headers verified on local HTTP. Production deployment requires external TLS-terminating reverse proxy (Nginx/Caddy). |
| **Independent Security Audit (VAPT)** | **PARTIALLY VERIFIED (SELF-ASSESSED)** | Self-assessed against OWASP ASVS 5.0 Level 2 controls. Independent third-party penetration testing by CERT-In auditor NOT performed. |
| **Live Docker Runtime Execution** | **NOT VERIFIED ON LOCAL HOST** | Host environment lacks Docker daemon (`docker` command unrecognized). Container manifests syntactically valid but live runtime execution is NOT VERIFIED. |
| **MahaSarathi / MahaONE SSO Integration** | **PENDING AUTHORIZATION** | Architectural adapter is prepared; live integration requires bilateral data-sharing agreement and OIDC client credentials from GAD/DIT. |
| **Automated Government Portal Submission** | **STRICTLY BLOCKED** | Neither MahaDBT nor Aaple Sarkar provides public REST APIs for submission. Bypassing CAPTCHA or headless scraping is illegal under IT Act 2000. Resolved via Safe Portal Hand-Off. |
| **Publication of 7 Candidate Schemes** | **QUARANTINED AS DRAFT** | All 7 candidate schemes in `data/candidates/` maintain `publication_authorized: false`. They cannot be published to the public catalog until signed by `CATALOGUE_RELEASE_SIGNING_KEY`. |
| **Ladki Bahin ₹2,100 Benefit Claim** | **ENFORCING OPERATIVE GR (₹1,500)**| Political announcements proposing ₹2,100 have not been gazetted on `gr.maharashtra.gov.in`. Candidate records strictly enforce the gazetted ₹1,500 benefit. |
| **Shravanbal Group A Pension Conflict** | **UNRESOLVED INQUIRY (`POL-SHRAVANBAL-01`)** | GR 20-08-2019 Para 4 excludes recipients of other pensions, yet Group A is defined as co-funding Central IGNOAPS. No unwritten exception is invented. |
| **OBC Scholarship Income Ceiling Conflict** | **UNRESOLVED INQUIRY (`POL-OBC-01`)** | MahaDBT portal accepts applications up to ₹2.5 Lakh, while base GR 14-10-2013 specifies ₹1.0 Lakh. Preserved as an open inquiry under `EXTRACTED_UNVERIFIED`. |
