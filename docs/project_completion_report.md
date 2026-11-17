# Scheme Navigator — Master Project Completion Report

**Project Root:** `C:\Users\Admin\Downloads\scheme-navigator\scheme-navigator`  
**Date of Completion:** 12 November 2026  
**Status:** Complete & Deployment-Ready Verified Baseline  
**Automated Tests:** 287 passing automated tests (0 failures, 0 regressions from initial 217 baseline)  
**Target Region:** Maharashtra, India  
**Languages Supported:** English (en), Marathi (mr), Hindi (hi)  

---

## 1. Executive Summary

Scheme Navigator is an evidence-backed, citizen-first assistance platform designed to navigate social welfare, pension, and scholarship schemes offered by the Government of Maharashtra and the Government of India.

The platform addresses a critical gap in citizen service delivery: citizens frequently struggle to understand complex Government Resolutions (GRs), navigate overlapping scheme aliases, understand condition-level eligibility criteria, prepare prerequisite documents, and safely interact with state application portals (such as MahaDBT and Aaple Sarkar).

Under this Master Project Directive, Scheme Navigator has been developed from its research and draft baseline into a production-hardened platform adhering strictly to:
1. **Three-Valued Deterministic Logic:** Explicit distinction between `TRUE` (satisfied), `FALSE` (unmet), and `UNKNOWN` (missing information requiring interview collection).
2. **Fail-Closed Verification Gate:** All newly researched and draft candidate records remain strictly isolated with `publication_authorized=false`, preventing unauthorized or unverified claims of government entitlement.
3. **Pure Multilingual Explanations:** Citizen explanations in English, Marathi, and Hindi derived from deterministic condition breakdowns, free of raw JSON Logic or unverified LLM translations.
4. **Official Source Ingestion Architecture:** SHA-256 byte-level snapshotting, automatic document change detection, duplicate alias resolution, and statutory GR lineage tracking.
5. **Citizen-Facing Trust & Verification Interface:** Prominent verification badges across 7 distinct states (`draft_candidate`, `under_review`, `source_verified`, `internally_reviewed`, `publication_authorized`, `active`, `expired_or_superseded`), operative date ranges, official GR links, and explicit non-endorsement notices.
6. **Intelligent Document Preparation:** Classification, approved alternative document matching (e.g. 15-year ration card for domicile, yellow/orange ration card for income), expiry detection, FY validity checks, cross-certificate conflict detection, and human reviewer audit escalation.
7. **Prerequisite DAG Dependency Planner:** Directed acyclic graph planning with cycle detection, identifying document acquisition sequences and statutory Maharashtra Right to Services (RTS) Act 2015 notified delivery timelines.
8. **Safe Portal Application Guidance:** Structured field mapping for MahaDBT and Aaple Sarkar, review-before-submission verification, zero storage of passwords/OTPs, zero CAPTCHA bypass, and clear manual portal fallback instructions.
9. **Production Security & Operations:** HMAC-SHA256 authenticated sessions, session ownership enforcement, Role-Based Access Control (RBAC), SSRF protection on official government domains, magic-byte upload validation, rate limiting, structured audit logging, and automated retention purging.

---

## 2. Chronological Phase Implementation Log

### Phase 4.1 & 4.1.1 — Evidence & Condition Models
- Established condition-level `RuleEvidence` models with explicit fields for `source_title`, `official_reference`, `official_source_url`, `effective_from`, `effective_until`, `verbatim_excerpt`, `translated_excerpt`, and cryptographic `source_document_sha256`.
- Implemented fail-closed publication gate in `Scheme.active_rule_needs_audit_trail()`: active production schemes require full reviewer approval, approval reference, verification timestamp, and 100% `legal_approved` evidence coverage.

### Phase 4.2 & 4.2.2 — Maharashtra Scheme Candidate Dossier & Policy Reconciliation
- Isolated 7 draft Maharashtra candidate records under `data/candidates/`:
  1. Mukhyamantri Majhi Ladki Bahin Yojana (`candidate-majhi-ladki-bahin`)
  2. Sanjay Gandhi Niradhar Anudan Yojana (`candidate-sanjay-gandhi-niradhar`)
  3. Shravanbal Seva Rajya Nivruttivetan Yojana (`candidate-shravanbal-nivruttivetan`)
  4. Government of India Post-Matric Scholarship for SC Students (`candidate-post-matric-sc`)
  5. Standard Post-Matric Scholarship to OBC Students (`candidate-post-matric-obc`)
  6. Post Matric Scholarship to OBC Girls in Professional Courses (`candidate-post-matric-obc-girls-professional`)
  7. Payment of Tuition & Examination Fees to OBC Girls in Professional Courses (`candidate-tuition-fees-obc-girls`)
- Policy reconciliation achievements:
  - Reconciled standard OBC scholarship (parental income up to ₹1.5L/₹2.5L) vs OBC Girls Professional Courses vs 100% Tuition/Exam fee reimbursement under GR dated 8 July 2024.
  - Maintained operative ₹1,500 monthly benefit for Majhi Ladki Bahin based on operative GRs 28 June 2024, 3 July 2024, and 12 July 2024, refusing to fabricate ₹2,100 without an official gazetted notification.
  - Separated Sanjay Gandhi Niradhar Anudan Yojana and Shravanbal Seva Yojana income thresholds (₹21,000 for non-disabled vs ₹50,000 for disabled beneficiaries) and consolidated assistance enhancements (₹1,500 from 5 July 2023; ₹2,500 for severe disability from 15 September 2025).

### Phase 4.3 — Intelligent Multilingual Eligibility Explanation Engine
- Implemented `src/scheme_navigator/services/explanation.py` with pure three-valued reasoning:
  - `TRUE`: requirement appears satisfied.
  - `FALSE`: requirement unmet, citing actual vs required values safely.
  - `UNKNOWN`: information missing, guiding citizen on what profile data or documents are required.
- Static, reviewed translations across English, Marathi, and Hindi for legal and policy terminology.
- Explicit provenance separation: `SELF_REPORTED`, `DOCUMENT_EXTRACTED`, `REVIEWER_VERIFIED`, and `MISSING`.
- Attached explanations to API endpoints `/eligibility/evaluate` and `/schemes/{scheme_id}/explain`.
- Verified with 13 automated tests in `tests/test_explanation.py`.

### Phase 4.4 — Official Government-Source Ingestion Architecture
- Built `src/scheme_navigator/ingestion/` architecture:
  - Persistent SQLite store `IngestionStore` tracking snapshots, SHA-256 byte digests, and automatic change detection (`DocumentChangeEvent`).
  - Human-review queue (`IngestionReviewItem`) requiring analyst signoff before candidate generation.
  - Maharashtra scheme alias and duplicate detection registry (`dedup.py`) preventing improper merger of distinct statutory branches.
  - Legislative and executive lineage tracking (`lineage.py`) recording base GRs, amendments, clarifications, and superseded rules.
- Exposed REST routes in `src/scheme_navigator/api/ingestion_routes.py`.
- Verified with 7 automated tests in `tests/test_ingestion_architecture.py`.

### Phase 4.5 — Citizen-Facing Trust and Verification Interface
- Created `src/scheme_navigator/services/trust.py` defining 7 distinct verification statuses:
  - `draft_candidate`: Preliminary draft record under compilation.
  - `under_review`: Active policy analysis and departmental verification underway.
  - `source_verified`: Primary GR identified, excerpted, and cryptographic hash verified.
  - `internally_reviewed`: Internal team policy review complete; awaiting publication signoff.
  - `publication_authorized`: Release signed by catalogue administrator.
  - `active`: Operative rule active for eligibility evaluation.
  - `expired_or_superseded`: Rule superseded or financial year ended.
- Updated `static/index.html` with responsive trust badges, operative date ranges, official GR links with section numbers, verification status filters, and non-endorsement warnings in EN, MR, and HI.
- Exposed `/schemes/{scheme_id}/trust` and `/schemes/trust/all` endpoints.
- Verified with 4 automated tests in `tests/test_trust_verification_ui.py`.

### Phase 5.1 — Intelligent Document Preparation
- Created `src/scheme_navigator/services/document_prep.py`:
  - Matches uploaded certificates against scheme required documents.
  - Identifies officially permitted alternative documents (e.g. 15-year ration card, voter ID, school leaving certificate for Domicile; yellow/orange ration card for Income).
  - Expiry date detection against reference calendar dates.
  - Financial year mismatch detection (e.g. FY 2024-25 certificate presented for FY 2026-27).
  - Duplicate document detection via SHA-256 byte hashes and certificate IDs.
  - Missing document explanations with issuing authority and statutory Maharashtra RTS delivery days.
  - Automatic escalation of low confidence (<0.75) extractions to `DocumentReviewStore`.

### Phase 5.2 — Prerequisite Dependency Planner
- Verified topological sorting and cycle detection in `src/scheme_navigator/planner/dag.py`.
- Enriched application steps with statutory Maharashtra Right to Services (RTS) Act 2015 delivery timelines (e.g. 15 days for Domicile/Income certificates, 21 days for Caste/Non-Creamy Layer certificates).
- Exposed `/plans/{scheme_id}` and integrated into consolidated applicant assessment.

### Phase 5.3 — Safe Portal Application Guidance
- Created `src/scheme_navigator/services/portal_assistance.py`:
  - Supports MahaDBT (`https://mahadbt.maharashtra.gov.in`) and Aaple Sarkar (`https://aaplesarkar.mahaonline.gov.in`).
  - Form field mapping table providing suggested values from verified documents and profiles.
  - Strict security restrictions: Aadhaar OTP, biometric data, and passwords are never stored, handled, or autofilled.
  - Pre-submission safety checklist requiring citizen personal verification before applying.
  - Clear manual portal fallback instructions; never falsely asserts application submission.
- Integrated into `build_applicant_assessment` and `static/index.html`.
- Verified with 6 automated tests in `tests/test_application_assistance.py`.

### Phase 6.0 — Production Security and Operations
- Implemented `src/scheme_navigator/security/`:
  - `auth.py`: HMAC-SHA256 session token generation, cryptographic validation, session ownership enforcement (preventing cross-citizen thread access), and role-based access control.
  - `rate_limiter.py`: Sliding-window in-memory rate limiter per IP/session returning HTTP 429 with `Retry-After`.
  - `ssrf.py`: Strict URL validation requiring HTTPS, blocking private IP ranges (127.0.0.1, 10.0.0.0/8, 192.168.0.0/16, 169.254.169.254), blocking internal ports, and enforcing official `.gov.in`/`.nic.in` domain allowlists.
  - `upload.py`: Magic-byte inspection for PDFs (`%PDF-`), PNG, JPEG, WEBP; filename sanitization blocking path traversal; rejection of dangerous executable extensions (`.exe`, `.svg`, `.sh`, `.php`); size limits (15 MiB PDF, 12 MiB image).
  - `publication.py`: Cryptographic catalogue release signing by `CATALOGUE_ADMIN`, canonical manifest SHA-256 hashing, provenance disclaimers, and fail-closed gate preservation.
  - `audit_logger.py`: Structured JSON security logging with PII/secret redaction.
  - `retention.py`: Automated purging of expired sessions and temporary files.
  - Monitoring endpoints `/healthz` and `/readyz`.
- Verified with 7 automated tests in `tests/test_production_security.py`.

### Phase 6.1 — Critical Security Remediation
- Fixed critical vulnerabilities identified in the independent production audit:
  1. **Privilege Escalation Prevention:** `POST /auth/session` restricted strictly to issuing `CITIZEN` role. Privileged accounts (`CATALOGUE_ADMIN`, `ANALYST`, `REVIEWER`) require secure provisioning via `/admin/auth/provision` with `ADMIN_BOOTSTRAP_KEY`.
  2. **Session Ownership Enforcement:** Attached `authorize_thread_access()` and `bind_thread_to_session()` across all `/interview/*` endpoints, stopping cross-citizen thread hijacking.
  3. **Universal Rate Limiting:** Attached `rate_limit` dependencies across all public and privileged FastAPI routes.
  4. **DPDPA Retention Engine Hardening:** Extended `purge_expired_data()` to clean orphaned records inside SQLite databases (`InterviewSessionStore` and `DocumentReviewStore`).
  5. **Audio Magic-Byte Inspection:** Added `validate_uploaded_audio_security()` verifying RIFF/WAV, ID3/MP3, OggS, fLaC, and WebM magic headers.
  6. **Reviewer UI Access Gate:** Restricted `/reviewer` and document correction endpoints to authenticated reviewers.
  7. **Docker Read-Write Volume Mount:** Replaced `:ro` mount with read-write named volume to allow SQLite WAL mode operations.
- Verified with 11 automated tests in `tests/test_security_remediation.py`.

### Phase 6.1.1 — Final Security Hardening
- Hardened bootstrap provisioning and SSRF defense:
  1. **One-Time Bootstrap Provisioning:** Admin bootstrap key can only be used once to provision the initial `CATALOGUE_ADMIN`. Once provisioned, bootstrap is permanently disabled until explicit in-process reset. Subsequent users must be provisioned via `/admin/auth/provision-user` by an authenticated admin.
  2. **Short Privileged Session Lifetimes:** Privileged sessions are bounded to 1 hour (configurable via `PRIVILEGED_SESSION_TTL_HOURS`) compared to citizen session lifespans.
  3. **SSRF DNS Rebinding & IP Pinning:** Implemented `SSRFSafeSyncBackend` and `SSRFSafeTransport` pinning DNS pre-resolution to the exact socket connection, blocking IPv4/IPv6 private ranges and localhost aliasing, while preserving SNI TLS verification.
- Verified with 11 automated tests in `tests/test_final_security_hardening.py`.

### Stages 0–8 — Ultimate Master Project Completion
- Advanced Scheme Navigator through comprehensive operational maturity:
  1. **Document Review Session Ownership:** Added `_review_owners` mapping, `bind_review_to_session()`, and `authorize_review_access()`. Citizens who create a document review session retain exclusive access to assess their documents against scheme criteria, preventing cross-tenant information exposure while allowing authorized reviewers.
  2. **SQLite Database Migration Engine (`core/migrations.py`):** Implemented schema version tracking (`schema_migrations`), WAL mode configuration, live crash-consistent SQLite backup (`backup_database` using `sqlite3.Connection.backup()`), database restoration (`restore_database`), and integrity verification (`check_database_integrity` via `PRAGMA integrity_check`). Attached migrations to application startup lifespan.
  3. **Air-Gapped Government Source Ingestion:** Added `POST /ingestion/upload-source` for offline ingestion of Government Resolutions with SHA-256 calculation, text extraction, snapshot persistence, and review queue enrollment. Added `GET /ingestion/compare` to calculate unified text diffs and similarity metrics between successive statutory amendments.
  4. **Single-Worker Invariant Enforced:** Documented and enforced single-worker runtime configuration (`--workers 1`) in Docker Compose and operational procedures, ensuring process memory consistency for rate limiting, session management, and SQLite single-writer guarantees.
  5. **End-to-End Synthetic Citizen Journeys (Journeys A through F):** Verified complete citizen lifecycles across 6 rigorous automated tests in `tests/test_end_to_end_citizen_journeys.py`.
- Verified with 11 automated tests in `tests/test_end_to_end_citizen_journeys.py` and `tests/test_migrations_and_manual_ingestion.py`.

---

## 3. Verified Automated Test Progression

| Milestone | Passing Tests | Failures | Notes |
|:---|:---:|:---:|:---|
| Initial Baseline | 217 | 0 | Starting point of Phase 4.3 |
| Phase 4.3 (Explanation Engine) | 230 | 0 | +13 multilingual explanation tests |
| Phase 4.4 (Ingestion Architecture) | 237 | 0 | +7 snapshot, lineage & dedup tests |
| Phase 4.5 (Trust & Verification UI) | 241 | 0 | +4 trust status & API tests |
| Phase 5.0 (Application Assistance) | 247 | 0 | +6 document prep & portal assistance tests |
| Phase 6.0 (Security & Operations) | 254 | 0 | +7 auth, RBAC, SSRF, upload, & rate limiting tests |
| Phase 6.1 (Critical Security Remediation) | 265 | 0 | +11 security remediation tests |
| Phase 6.1.1 (Final Security Hardening) | 276 | 0 | +11 admin bootstrap, SSRF pinning & TTL tests |
| Stages 0–8 (Ultimate Master Completion) | **287** | **0** | +6 E2E citizen journey tests + 5 migration & ingestion tests |

All 287 automated tests pass with 0 failures in approximately 60 seconds on Python 3.11 with zero external network dependencies.

---

## 4. End-to-End Citizen Journey Walkthrough

The platform successfully demonstrates the complete end-to-end citizen experience across 6 synthetic journey suites:

- **Journey A: Discovery, Trust Badges, and Multilingual Explanations:**
  Anonymous citizen lands on the portal, discovers available schemes, inspects verification badges across active fixtures and draft candidates, and evaluates eligibility in English, Marathi, and Hindi. Ineligible results clearly state unmet conditions (e.g. age requirements) and relevant GR clauses.
- **Journey B: Guided Multilingual AI Interview & Session Ownership:**
  Citizen begins a guided interview for Majhi Ladki Bahin in Marathi, submits sequential answers, simulates browser refresh, resumes conversation state seamlessly, and verifies that cross-citizen interview tampering is rejected with HTTP 403 Forbidden.
- **Journey C: Document Pre-Audit & Session-Bound Assessment:**
  Citizen uploads supporting certificates (Income, Domicile, Ration Card), triggers synthetic document extraction, inspects document groups and conflict warnings, and verifies eligibility assessment bound to their authenticated session.
- **Journey D: Prerequisite DAG Roadmap & Safe Portal Guidance:**
  Citizen requests application plan, generates topological dependency graph, prunes already-held certificates, calculates critical path statutory RTS delivery timelines, and inspects safe field mapping tables for MahaDBT and Aaple Sarkar portals.
- **Journey E: Reviewer UI Inspection, Field Correction & Audit Logging:**
  Authorized reviewer logs into `/reviewer`, inspects flagged document findings, performs human-in-the-loop field correction, validates audit trail event recording, and completes review verification.
- **Journey F: Adversarial Security & Invariant Validation:**
  Rigorous penetration tests verifying rejection of role escalation attacks, rejection of private IP SSRF requests, preservation of fail-closed publication gate for unapproved candidate records, and SQLite database integrity verification.

---

## 5. Deployment and Operations Procedure

### 5.1 Environment Prerequisites
- Python 3.11+
- Virtual environment with dependencies from `pyproject.toml`
- Optional local Ollama / Whisper instances for local offline inference
- Optional Gemini API key (`GEMINI_API_KEY`) for assisted document extraction

### 5.2 Configuration Settings (`.env`)
```bash
APP_NAME="Scheme Navigator"
APP_ENV="production"                      # Set to "production" to disable demo fixtures
LOG_LEVEL="INFO"
DATA_RETENTION_HOURS=24                   # Auto-purge expired session data after 24 hours
SCHEME_CATALOG_PATH=""                    # Path to signed production catalogue JSON
GEMINI_API_KEY="your-api-key"
SCHEME_NAVIGATOR_AUTH_SECRET="secure-hmac-secret-min-32-chars-entropy"
ADMIN_BOOTSTRAP_KEY="secure-bootstrap-key-min-32-chars-entropy"
CATALOGUE_RELEASE_SIGNING_KEY="secure-catalogue-signing-key"
PRIVILEGED_SESSION_TTL_HOURS=1           # Short lifetime for administrative sessions
```

### 5.3 Launch Commands

> [!IMPORTANT]
> **Single-Worker & Localhost Invariant:** Scheme Navigator must be run with `--workers 1` and bound to `127.0.0.1` by default. The platform relies on single-process memory state for sliding-window rate limiting, active session revocation, and safe SQLite single-writer operations.
>
> **Conditions for Network Exposure (`0.0.0.0`):**
> Network exposure (`0.0.0.0`) must **only** be configured behind an authenticated, TLS-terminating reverse proxy (e.g., Nginx, Envoy, or AWS ALB) with strict network firewall / VPC ingress rules, Web Application Firewall (WAF), and citizen rate-limiting. Directly binding to `0.0.0.0` on an untrusted or public network exposes unencrypted HTTP traffic, administrative provisioning endpoints, and internal SQLite databases to unauthorized LAN/WAN access.

```bash
# Start backend server in single-worker mode bound to localhost
uvicorn scheme_navigator.api.main:app --host 127.0.0.1 --port 8000 --workers 1

# Or run using Docker Compose (host ports bound to 127.0.0.1)
docker-compose up -d --build

# Run complete automated test suite (287 passing tests)
python -m pytest -q

# Execute database migration manually (catalogue_admin role required)
curl -X POST http://localhost:8000/admin/db/migrate -H "Authorization: Bearer <admin-token>"

# Execute live database backup (catalogue_admin role required)
curl -X POST http://localhost:8000/admin/db/backup -H "Authorization: Bearer <admin-token>"

# Execute data retention purge (catalogue_admin role required)
curl -X POST http://localhost:8000/admin/retention/purge -H "Authorization: Bearer <admin-token>"
```

### 5.4 Health & Readiness Probes
- Liveness Probe: `GET http://localhost:8000/healthz` -> `{"status": "ok"}`
- Readiness Probe: `GET http://localhost:8000/readyz` -> `{"status": "ready", "schemes_loaded": 2, ...}`
- Database Status Probe: `GET http://localhost:8000/admin/db/status` -> `{"interviews": {"status": "healthy"}, ...}`
