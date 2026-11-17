# Scheme Navigator — Final Independent Production Readiness Audit

**Audit Date:** 11 November 2026  
**Auditor:** Independent Principal Security & Systems Architect  
**Project Root:** `C:\Users\Admin\Downloads\scheme-navigator\scheme-navigator`  
**Automated Test Baseline:** 254 tests collected, 254 passed in 50.19 seconds (100% pass rate)  
**Audit Classification:** READ-ONLY Architectural, Policy, and Security Verification  

---

## 1. Executive Summary & Verdict

This independent audit conducted a comprehensive, read-only inspection of the Scheme Navigator codebase, candidate scheme records, automated test suites, and operational configurations following the Master Project Directive.

### Deployment Readiness Verdict

| Deployment Tier | Suitability Verdict | Key Conditions / Blockers |
|:---|:---:|:---|
| **Local Demo / Workshop** | **APPROVED (100% READY)** | Flawless local execution: deterministic 3-valued logic, pure multilingual explanations (English, Marathi, Hindi), prerequisite DAG planning, and safe portal guidance. All 254 automated tests pass cleanly. |
| **Controlled Intranet / Pilot** | **CONDITIONAL APPROVAL** | Permitted **only** under strict administrative supervision in a closed environment (e.g. supervised Gram Panchayat CSC kiosk), subject to: (1) overriding default HMAC secrets in `.env`, (2) disallowing arbitrary roles in `/auth/session`, and (3) configuring OS-level periodic invocation of `/admin/retention/purge`. |
| **Public Production Deployment** | **REJECTED (NOT PRODUCTION READY)** | **Critical blockers identified:**<br>1. **Privilege Escalation:** Trivial unauthenticated role escalation via `POST /auth/session?role=catalogue_admin`.<br>2. **Session Hijacking:** `/interview` endpoints lack session ownership checks, allowing cross-citizen thread tampering.<br>3. **Zero Active Rate Limiting:** Rate limiting dependency is not wired into any production FastAPI endpoints.<br>4. **DPDPA Non-Compliance:** Retention purge omits SQLite databases (`InterviewSessionStore` and `DocumentReviewStore`).<br>5. **Broken Container Config:** `docker-compose.yml` mounts `/app/data` as `:ro` (read-only), crashing all SQLite writes.<br>6. **Policy Incomplete:** All 7 Maharashtra candidate schemes remain draft with unresolved gazette discrepancies. |

---

## 2. Part 1 — Implementation Verification & Feature Classification

Every claimed capability was inspected in source code, cross-referenced with test coverage, and evaluated for architectural completeness.

### Detailed Feature Classification Table

| # | Feature / Capability | Primary Source Module | Automated Test File | Classification | Core Audit Findings |
|:---|:---|:---|:---|:---:|:---|
| 1 | **Multilingual Explanation Service** | `services/explanation.py` | `tests/test_explanation.py` (13 tests) | **IMPLEMENTED AND TESTED** | Pure 3-valued reasoning (`TRUE`, `FALSE`, `UNKNOWN`); static, reviewed bilingual dictionaries in EN, MR, and HI; zero LLM hallucination; attached to `/eligibility/evaluate` and `/schemes/{id}/explain`. |
| 2 | **Government-Source Ingestion** | `ingestion/store.py`, `ingestion/pipeline.py` | `tests/test_ingestion_architecture.py` (7 tests) | **IMPLEMENTED AND TESTED** | SQLite-backed `IngestionStore`, immutable SHA-256 snapshots, robots.txt compliance checking, and human review queue. External web fetches mocked/tested cleanly. |
| 3 | **Change Detection & Lineage** | `ingestion/store.py`, `ingestion/lineage.py`, `ingestion/dedup.py` | `tests/test_ingestion_architecture.py` | **IMPLEMENTED AND TESTED** | `DocumentChangeEvent` triggers on SHA-256 byte divergence; statutory lineage tracks base GRs, amendments, and superseded rules; alias deduplication prevents conflation of distinct scheme branches. |
| 4 | **Trust Status Display** | `services/trust.py`, `static/index.html` | `tests/test_trust_verification_ui.py` (4 tests) | **IMPLEMENTED AND TESTED** | 7-tier verification taxonomy (`draft_candidate` through `active`); responsive trust badges in EN, MR, HI; operative date bounds and GR paragraph citations. Explicitly disclaims government endorsement. |
| 5 | **Document Preparation** | `services/document_prep.py` | `tests/test_application_assistance.py` (6 tests) | **IMPLEMENTED AND TESTED** | Matches Maharashtra statutory alternatives (15-yr ration card, voter ID, school leaving cert for domicile; yellow/orange ration card for income); detects expiry dates and financial year mismatches. |
| 6 | **Dependency DAG Planner** | `planner/dag.py`, `domain/dag.py` | `tests/test_planner_retrieval_ingestion.py`, `test_application_assistance.py` | **IMPLEMENTED AND TESTED** | Topological sorting of prerequisite document dependencies with cycle detection; integrates statutory Maharashtra Right to Services (RTS) Act 2015 delivery timelines. |
| 7 | **Portal Application Assistance** | `services/portal_assistance.py` | `tests/test_application_assistance.py` | **IMPLEMENTED AND TESTED** | Form field mapping for MahaDBT and Aaple Sarkar; flags Aadhaar/OTP as `RESTRICTED_SECURITY_FIELD`; enforces pre-submission verification checklist; status stamped as `not_submitted_guidance_only`. |
| 8 | **Authentication & Session Ownership** | `security/auth.py`, `security/models.py` | `tests/test_production_security.py` | **PARTIALLY IMPLEMENTED** | `SessionManager` implements HMAC-SHA256 token signing and `authorize_thread_access()`. **Critical Defect:** `authorize_thread_access()` is **never called** in any `/interview` endpoint in `main.py`, allowing cross-citizen thread access. In multi-worker mode, session state is trapped in process memory. |
| 9 | **Role-Based Access Control (RBAC)** | `security/auth.py`, `api/main.py` | `tests/test_production_security.py` | **PARTIALLY IMPLEMENTED** | `require_role()` dependency protects `/admin/*` routes. **Critical Vulnerability:** `POST /auth/session` accepts arbitrary `role` from the client without authentication, allowing immediate privilege escalation to `catalogue_admin`. Reviewer UI (`/reviewer`) has zero role checks. |
| 10 | **Rate Limiting** | `security/rate_limiter.py` | `tests/test_production_security.py` | **PARTIALLY IMPLEMENTED** | `InMemoryRateLimiter` class and `rate_limit` dependency were written and tested in isolation. **Critical Defect:** `rate_limit` is **not attached** to any route in `api/main.py`. The entire production API is un-rate-limited. Process-local memory prevents multi-worker synchronization. |
| 11 | **SSRF Protection** | `security/ssrf.py`, `ingestion/pipeline.py` | `tests/test_production_security.py`, `test_ingestion_architecture.py` | **IMPLEMENTED BUT INCOMPLETELY TESTED** | HTTPS protocol and allowlist checking implemented. **Architectural Blindspots:** `validate_safe_url()` is never called in `ingestion/pipeline.py`; HTTP redirects are followed before URL re-checking; no DNS pre-resolution occurs to detect DNS rebinding or private IP aliasing. |
| 12 | **File Upload Validation** | `security/upload.py`, `api/main.py` | `tests/test_production_security.py`, `test_document_upload.py` | **IMPLEMENTED AND TESTED** | Magic-byte validation (`%PDF-`, PNG, JPEG, WEBP), filename sanitization, dangerous extension blocking, and size limits (15 MiB / 12 MiB) enforced on `/documents/audit-upload`. Audio upload (`/interview/voice`) lacks magic-byte inspection. |
| 13 | **Catalogue Release Signing** | `security/publication.py` | `tests/test_production_security.py` | **IMPLEMENTED AND TESTED** | Cryptographic SHA-256 catalogue digest computation, 100% legal approved evidence validation, fail-closed enforcement. Note: uses symmetric HMAC-SHA256 rather than asymmetric public-key cryptography. |
| 14 | **Audit Logging** | `security/audit_logger.py` | `tests/test_production_security.py` | **IMPLEMENTED AND TESTED** | Structured JSON security logging with PII/secret redaction. Note: in-memory event buffer is fragmented in multi-worker environments, and file rotation is not configured. |
| 15 | **Retention Management** | `security/retention.py` | `tests/test_production_security.py` | **PARTIALLY IMPLEMENTED** | `purge_expired_data()` purges memory sessions and temp files. **Critical Defects:** No background scheduler runs the purge; it only triggers on manual admin API call. Crucially, it **does not purge** `InterviewSessionStore` or `DocumentReviewStore` SQLite databases. |
| 16 | **Health & Readiness Probes** | `api/main.py` (`/healthz`, `/readyz`) | `tests/test_production_security.py` | **IMPLEMENTED AND TESTED** | `/healthz` provides standard liveness; `/readyz` validates catalogue readiness and operational settings. |

---

## 3. Part 2 — Policy Data Consistency & Legal Traceability

The 7 candidate scheme JSON records under `data/candidates/` were cross-checked against `docs/source-dossier.md`, `docs/unresolved_policy_questions.md`, `docs/missing_source_documents.md`, and `docs/validation_report.md`.

### Policy Investigation Findings

#### 1. Sanjay Gandhi Niradhar Anudan Yojana (SGNAY): 40% vs 80% Disability Conflation
- **Discrepancy Identified:**
  - In `data/candidates/sanjay-gandhi-niradhar-anudan.json` (lines 5, 8), the summary and benefits state that enhanced assistance of **₹2,500/month** is provided to beneficiaries with `>= 40% certified disability`.
  - In statutory reality and `docs/source-dossier.md` (Para 3.2, 4.2), **40% disability** is the baseline statutory threshold for entering the destitute disability track (under the RPwD Act 2016, with an income ceiling of ₹50,000).
  - The enhanced assistance of **₹2,500/month** (introduced via Government Resolution dated 15 September 2025) is restricted specifically to **severe disability ($\ge 80\%$)** or the Central Indira Gandhi National Disability Pension Scheme (IGNDPS) tier.
  - **AST Encoding Defect:** The candidate rule evaluates only `"field": "has_disability", "value": true` (a binary boolean). It contains no predicate checking `disability_percentage >= 40` or `disability_percentage >= 80`. Consequently, an applicant with a 40% disability is incorrectly promised the ₹2,500 severe disability benefit.

#### 2. Shravanbal Seva Rajya Nivruttivetan Yojana: Group A vs Group B
- **Audit Finding:** Correctly modeled and legally accurate.
  - **Group A:** Senior citizens (65+) whose family name appears in the Central Government BPL List (Rural BPL survey 2002 / Urban survey 2007). They receive a consolidated ₹1,500/month (joint funding: Central IGNOAPS ₹200 for ages 65–79 / ₹500 for age 80+, topped up by Maharashtra State funds). Inclusion in BPL list waives the requirement for a separate Tahsildar income certificate.
  - **Group B:** Senior citizens (65+) not on the BPL list, whose annual family income is $\le$ ₹21,000 (verified by Tahsildar income certificate). 100% funded by Maharashtra State (₹1,500/month).
  - Both branches enforce `age >= 65`, 15-year Maharashtra residence, and `receiving_other_pension == false`.

#### 3. OBC Scholarship Income Tiers: ₹1.0 Lakh / ₹1.5 Lakh vs ₹2.50 Lakh Gap
- **Audit Finding:** Unresolved administrative gap between base GR and portal operations.
  - The operative base State Government Resolution dated 14 October 2013 (`ईबीसी-२०१२/प्र.क्र.२२९/मावक-२`) set the parental income ceiling at **₹1,00,000/-**.
  - The active MahaDBT 2.0 portal enforces **₹2,50,000/-** to match the Central Government PM-YASASVI umbrella norms.
  - `data/candidates/post-matric-scholarship-obc.json` encodes `annual_family_income <= 250000` to reflect actual portal processing, but the evidence status is correctly flagged as `extracted_unverified` because no state GR increasing the ceiling to ₹2.5 lakh has been gazetted on `gr.maharashtra.gov.in`.

#### 4. Separation of the Three OBC Educational Schemes
- **Audit Finding:** Correctly isolated into three separate candidate files; conflation successfully prevented:
  1. `candidate-post-matric-obc.json`: Standard post-matric scholarship across all recognized post-matric courses. Parental income $\le$ ₹2.5L. Benefits: 100% fees (aided) / 50% (unaided) + **10 months monthly maintenance allowance**.
  2. `candidate-post-matric-obc-girls-professional.json`: OBC girls in approved professional degree/diploma courses. Parental income $\le$ ₹2.5L. Benefits: Tuition/exam fees + **monthly maintenance allowance**.
  3. `candidate-payment-tuition-examination-fees-obc-girls.json`: 100% Tuition & Exam Fee reimbursement under Higher & Technical Education Department GR dated 8 July 2024. Family income $\le$ **₹8,00,000/-** (backed by NCL certificate). Mandatory Centralized Admission Process (CAP) seat and 75% attendance. **Zero maintenance allowance**.

#### 5. Government of India Post-Matric Scholarship for SC Students: 2026–27 Cycle Transition
- **Audit Finding:** Correctly flagged as an unresolved policy boundary.
  - The Central Ministry of Social Justice and Empowerment (MoSJE) scheme guidelines covered the 15th Finance Commission 5-year block (2020-21 through 2025-26), formally expiring on 31 March 2026.
  - While MahaDBT accepts applications for AY 2026-27 under interim executive continuance directives, the formal 16th Finance Commission guidelines have not yet been gazetted in the Gazette of India. The candidate record remains draft pending official publication.
  - The scheme is properly distinguished from the *Top Class Education Scheme for SC Students* (which has an ₹8 lakh ceiling and is restricted to premier institutes like IITs/IIMs).

#### 6. Mukhyamantri Majhi Ladki Bahin Yojana: Benefit and Rule Amendments
- **Audit Finding:** Strictly adheres to gazetted Government Resolutions.
  - Base GR: 28 June 2024 (Age 21–60, ₹1,500/month, family income $\le$ ₹2.5 lakh, 15-year Maharashtra residence).
  - Shuddhipatra: 3 July 2024 (Age ceiling raised from 60 to 65; 15-year ration card, voter ID, or school leaving certificate accepted in lieu of separate domicile certificate).
  - Clarification: 12 July 2024 (Yellow and orange ration cards exempt families from obtaining separate Tahsildar income certificates).
  - **₹2,100 Benefit Proposal:** Maintained at ₹1,500. Refused to fabricate the politically announced ₹2,100 rate because no operative Government Resolution has been gazetted as of November 2026.
  - Expired historical deadlines (30 Sept / 15 Oct 2024) are omitted from prospective evaluation logic.

---

## 4. Part 3 — Security Adversarial Testing

Adversarial testing was performed against the live API and security modules to evaluate defensive robustness.

### 1. Privilege Escalation via Client-Supplied RBAC Roles (CONFIRMED CRITICAL)
- **Vulnerability:** `POST /auth/session` accepts `role: UserRole = UserRole.CITIZEN` directly from the client request.
- **Exploitation:**
  ```bash
  curl -X POST "http://localhost:8000/auth/session?role=catalogue_admin"
  ```
  Returns a cryptographically valid HMAC token with `role: "catalogue_admin"`.
- **Impact:** An unauthenticated external attacker can immediately mint administrative tokens and invoke protected endpoints:
  - `POST /admin/catalogue/sign-release` (signs unauthorized catalogue versions)
  - `POST /admin/retention/purge` (triggers data purging)
  - `GET /admin/audit-logs` (reads internal audit logs)

### 2. Session Ownership Bypass on Interview Threads (CONFIRMED HIGH)
- **Vulnerability:** While `SessionManager.authorize_thread_access()` was implemented and unit-tested in `auth.py`, it was **never integrated into the interview endpoints** in `src/scheme_navigator/api/main.py`.
- **Exploitation:**
  Calling `POST /interview/answer` or `POST /interview/start` with another citizen's `thread_id` succeeds without checking whether the session owns that thread. In development/local mode, `GET /interview/{thread_id}` allows reading arbitrary interview states.
- **Code Acknowledgment:** `main.py` explicitly notes: `"Interview state recovery is a local development prototype until session ownership protection is added."`

### 3. Missing Rate Limiting on Production Endpoints (CONFIRMED HIGH)
- **Vulnerability:** `InMemoryRateLimiter` was implemented in `security/rate_limiter.py`, but the `rate_limit` dependency was **not attached to any FastAPI router or endpoint** in `main.py`.
- **Impact:**
  - Unlimited file uploads on `/documents/audit-upload` can exhaust server memory and disk.
  - Unlimited voice uploads on `/interview/voice` can deplete API quotas and exhaust Gemini/Whisper processing capacity.
  - Unlimited profile evaluation queries can cause CPU denial-of-service.

### 4. SSRF Vulnerabilities via Redirects and Lack of DNS Resolution (CONFIRMED MEDIUM)
- **Vulnerability:**
  - `security/ssrf.py:validate_safe_url()` is never called in `ingestion/pipeline.py`.
  - In `ingestion/pipeline.py:ingest_public_source()`, `httpx.Client(follow_redirects=True)` follows HTTP redirects before `_check_url(str(response.url))` validates the final URL. If an allowlisted government server redirects to an internal endpoint (e.g. `http://169.254.169.254/latest/meta-data/`), the internal request is dispatched before rejection.
  - No DNS pre-resolution occurs, leaving the ingestion pipeline vulnerable to DNS rebinding attacks if non-allowlisted modes are used.

### 5. Reviewer Dashboard Unauthorized Access (CONFIRMED MEDIUM)
- **Vulnerability:**
  `GET /reviewer` in `src/scheme_navigator/api/reviewer_ui.py` serves `static/reviewer.html` with zero authentication, zero headers, and zero role checks.
- **Operational Divergence:** In local environments (`APP_ENV=local`), any caller can view and modify document review cases using unauthenticated caller-supplied `reviewer_id`. In `APP_ENV=production`, `_ensure_local_review_api()` completely blocks human review with HTTP 403 rather than authenticating reviewers via RBAC.

### 6. Data Retention and Deletion Failures (CONFIRMED MEDIUM)
- **Vulnerability:**
  - `purge_expired_data()` is not scheduled to run automatically; it requires manual invocation via `POST /admin/retention/purge`.
  - When invoked, `purge_expired_data()` only clears in-memory session dictionaries and files in `data/temp_uploads`.
  - It **fails to purge** `InterviewSessionStore` (the SQLite database holding interview transcripts and profile slots) and `DocumentReviewStore` (the SQLite database holding extracted citizen document fields).
- **DPDPA Reality Check:** The presence of security modules does not constitute DPDPA compliance. Without automated, end-to-end database record purging, citizen personal data remains indefinitely on disk in SQLite databases.

### 7. Hardcoded Fallback Secrets
- **Vulnerability:**
  - `SCHEME_NAVIGATOR_AUTH_SECRET` falls back to `"sn-prod-auth-secret-key-32-chars-long-minimum-safe-entropy"`.
  - `SCHEME_NAVIGATOR_RELEASE_KEY` falls back to `"sn-prod-catalogue-signing-key-high-entropy-64-bytes-sample-key"`.
- **Impact:** If deployed without environment overrides, an attacker can generate offline signed tokens and release signatures using public repository constants.

---

## 5. Part 4 — End-to-End Local Journey Execution

A complete 10-step citizen and administrator journey was exercised against the live application using `TestClient(app)` (scratch execution script `audit_journey.py`).

| Step | Journey Stage | Action Executed | HTTP Status | Observed Behavior & Audit Notes |
|:---:|:---|:---|:---:|:---|
| 1 & 2 | **Profile Discovery** | `POST /eligibility/evaluate?language=en` | `200 OK` | Evaluated 2 runtime demo schemes. Correctly returned 3-valued `needs_review` status with condition breakdown. |
| 3 | **Multilingual Explanations** | `POST /schemes/demo-majhi-ladki-bahin/explain?language={en,mr,hi}` | `200 OK` | Verified in all 3 languages. Returned 6 positive satisfied conditions. Translated titles (`Gender Requirement` / `लिंग अट` / `लिंग आवश्यकता`). Zero LLM hallucination. |
| 4 | **Interactive Interview** | `POST /interview/start` | `200 OK` | LangGraph state graph initialized. First interview question returned: *"Do you currently reside in Maharashtra?"*. |
| 5 | **Document Audit & Prep** | `POST /assistance/documents/audit-and-prepare` | `200 OK` | Evaluated scheme requirements against document bundle. Correctly reported `all_mandatory_satisfied: False` and identified 5 required documents. |
| 6 | **Dependency Planning (DAG)** | `POST /plans/demo-majhi-ladki-bahin` | `200 OK` | Topological sort generated 6 sequential plan steps. Maharashtra RTS statutory delivery days accurately returned (15 days for Domicile, 15 days for Income). |
| 7 | **Portal Application Guidance** | `POST /assistance/portal/guidance` | `200 OK` | Formulated guidance package for Aaple Sarkar. Status stamped: `not_submitted_guidance_only`. Aadhaar/OTP marked restricted. |
| 8 | **Reviewer UI Access** | `GET /reviewer` | `200 OK` | Dashboard served anonymously without authentication check. |
| 9 | **Candidate Isolation Gate** | `SchemeCatalog.from_json("data/candidates/candidate_schemes.json")` | `Success` | Loaded all 7 candidate schemes. Verified that `publication_authorized` is forced to `False` for all external records (`[False, False, False, False, False, False, False]`). |
| 10 | **Adversarial Escalation** | `POST /auth/session?role=catalogue_admin`<br>`GET /admin/audit-logs` | `200 OK`<br>`200 OK` | Minted `catalogue_admin` token without credentials; successfully read administrative audit logs. |

---

## 6. Part 5 — Operational Readiness & Infrastructure Review

1. **Environment Configuration (`.env`):**
   - Active configuration specifies `APP_ENV=local`.
   - `SCHEME_CATALOG_PATH` is unset, correctly defaulting to local demo fixtures.
   - `GEMINI_API_KEY` is present in plaintext in `.env`.
2. **Database Migrations:**
   - **Absence of Migration Framework:** SQLite databases (`ingestion.sqlite3`, `interview_sessions.sqlite3`, `document_reviews.sqlite3`) are initialized using raw `CREATE TABLE IF NOT EXISTS` queries in Python constructors.
   - There is no Alembic or schema versioning. Schema alterations in production will require manual SQLite table migrations.
3. **Multi-Worker Concurrency (`uvicorn ... --workers 4`):**
   - The project completion report recommends running with `--workers 4`.
   - **Process-Memory Isolation:** `SessionManager._sessions`, `InMemoryRateLimiter._requests`, and `SecurityAuditLogger._buffer` are stored in process-local Python dictionaries. In a multi-worker setup, sessions, rate-limit buckets, and audit event logs are not shared across workers, causing cache misses and split state.
   - **SQLite Concurrency:** SQLite under multi-worker write load can suffer from database locks (`sqlite3.OperationalError: database is locked`).
4. **Container & Deployment Configuration (`docker-compose.yml`):**
   - **FATAL DOCKER CONFIGURATION:** `docker-compose.yml` mounts `./data:/app/data:ro` as **read-only**.
   - Because `ingestion.sqlite3`, `interview_sessions.sqlite3`, and `security_audit.log` reside in `/app/data`, starting the application under the provided docker-compose file will immediately fail with filesystem write errors as soon as an interview, ingestion, or audit log event is triggered.
5. **Dependency Security (`pyproject.toml`):**
   - Dependencies are modern and pinned with upper bounds (`fastapi>=0.115,<1.0`, `pydantic>=2.8,<3.0`, `langgraph>=0.2.50,<2.0`).
   - `playwright` is restricted to local mock form testing in `workers/mock_form_worker.py` and strictly blocked from accessing external non-loopback domains.

---

## 7. Residual Risks & Production Blockers Register

| Risk ID | Severity | Category | Specific Vulnerability / Discrepancy | Required Remediation |
|:---|:---:|:---|:---|:---|
| **SEC-01** | **CRITICAL** | Security | Unauthenticated privilege escalation via `POST /auth/session?role=catalogue_admin` | Hardcode `role=UserRole.CITIZEN` in public session minting; require admin secret / API key for elevated roles. |
| **SEC-02** | **HIGH** | Security | Interview endpoints (`/interview/*`) do not verify session thread ownership | Add `session: UserSession = Depends(get_current_session)` and enforce `authorize_thread_access()` in `api/main.py`. |
| **SEC-03** | **HIGH** | Security | Rate limiting is completely disconnected from FastAPI endpoints | Attach `Depends(rate_limit(...))` to upload, voice, interview, and evaluation routes. |
| **SEC-04** | **HIGH** | Compliance | Data retention purge does not clean `InterviewSessionStore` or `DocumentReviewStore` databases | Add SQLite deletion queries in `purge_expired_data()` for records older than `retention_hours`. |
| **OPS-01** | **HIGH** | Deployment | `docker-compose.yml` mounts `./data` as `:ro` (read-only), breaking SQLite writes | Change volume mount from `:ro` to read-write (`:rw`) or use named volumes for writable databases. |
| **POL-01** | **HIGH** | Policy | SGNAY conflates 40% disability eligibility with 80% severe disability ₹2,500 benefit | Update `sanjay-gandhi-niradhar-anudan.json` AST to distinguish $\ge 40\%$ from $\ge 80\%$ severity tiers. |
| **SEC-05** | **MEDIUM** | Security | Ingestion pipeline follows HTTP redirects before re-checking government allowlist | Intercept redirects in `httpx` transport adapter or disable automatic redirect following. |
| **OPS-02** | **MEDIUM** | Operations | In-memory session, rate limit, and audit buffers fail across multiple Uvicorn workers | Migrate session and rate-limiting stores to Redis for multi-worker production deployments. |

---

## 8. Final Audit Sign-Off

- **Verified Code Integrity:** All 254 automated tests pass with zero regressions. The underlying 3-valued deterministic logic, condition evidence structures, multilingual explanations, and safe portal mappings represent outstanding domain engineering.
- **Production Status:** The platform is **APPROVED for local demonstrations, interactive workshops, and evaluated simulations**. It is **NOT APPROVED for live citizen public production deployment** until the critical privilege escalation, session ownership, active rate limiting, and Docker write blockers are resolved.
