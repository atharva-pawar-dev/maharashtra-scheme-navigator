# Scheme Navigator — Phase 6.1 Critical Security Remediation Report

**Date:** 11 November 2026  
**Auditor Finding Baseline:** `docs/final_independent_audit.md`  
**Test Suite Verification:** 265 Automated Tests Passing (254 Baseline + 11 Adversarial Security Integration Tests)  
**Backup Baseline:** `backup-security-remediation-20261111-173900/`  

---

## 1. Executive Summary

Following the comprehensive production readiness audit (`docs/final_independent_audit.md`), ten critical, high, and medium vulnerabilities were identified across authentication, session boundaries, rate limiting, file validation, retention policies, and scheme data accuracy.

Phase 6.1 remediated all 10 priority issues without degrading existing functionality. All 254 existing automated regression tests continue to pass seamlessly, alongside 11 newly engineered adversarial security integration tests covering every attack vector identified in the audit.

---

## 2. Priority-by-Priority Remediation Matrix

| Priority | Risk Area | Original Finding / Vulnerability | Remediation Applied | Files Modified | Verification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Priority 1** | **Auth & Role Escalation** | Client-supplied role parameter in `POST /auth/session` allowed unauthenticated privilege escalation to `catalogue_admin` or `analyst`. | Removed client-controlled role assignment. Public session creation strictly issues `CITIZEN` role. Privileged administrative roles require `POST /admin/auth/provision` protected by constant-time verification of `ADMIN_BOOTSTRAP_KEY` ($\ge 32$ chars). Fails closed (HTTP 503) if unconfigured. Attempted privilege escalation via public endpoint returns HTTP 403. | `src/scheme_navigator/security/auth.py`<br>`src/scheme_navigator/api/main.py` | `test_public_session_creation_rejects_privileged_roles`<br>`test_admin_auth_provisioning_requires_valid_bootstrap_key`<br>`test_admin_auth_provisioning_fails_closed_when_unconfigured` |
| **Priority 2** | **Session Ownership** | `POST /interview/answer` and `GET /interview/{thread_id}` did not verify thread ownership. Malicious actors could answer or read other citizens' interview state by guessing thread IDs. | Implemented explicit session-to-thread binding and ownership authorization in `SessionManager`. Authenticated citizen sessions can only answer and access their own threads. Unauthenticated or foreign citizen sessions attempting cross-thread access are rejected with HTTP 403 Forbidden. | `src/scheme_navigator/security/auth.py`<br>`src/scheme_navigator/api/main.py` | `test_interview_thread_ownership_isolation` |
| **Priority 3** | **Rate Limiting** | Rate limiting dependencies were unattached to FastAPI route definitions, leaving sensitive endpoints vulnerable to DoS/brute force. | Attached `Depends(rate_limit(...))` to: `/auth/session` (20/min), `/admin/auth/provision` (10/min), `/voice/transcribe` (10/min), `/documents/audit-upload` (10/min), `/interview/start` (30/min), `/interview/answer` (30/min), `/eligibility/evaluate` (60/min), `/schemes/{id}/explain` (60/min), `/assessment/{id}` (60/min), `/documents/reviews/*` (10-60/min). | `src/scheme_navigator/api/main.py` | `test_rate_limiting_enforcement` |
| **Priority 4** | **Reviewer RBAC** | `GET /reviewer` and document review endpoints lacked session checks, permitting citizen and anonymous access to reviewer UI and data. | Added strict role-based access control. Explicit citizen sessions are rejected with HTTP 403 Forbidden across all review endpoints (`GET /reviewer`, `/documents/reviews/*`). Production mode strictly rejects unauthenticated callers. Only `ANALYST`, `LEGAL_REVIEWER`, and `CATALOGUE_ADMIN` roles are permitted. | `src/scheme_navigator/api/reviewer_ui.py`<br>`src/scheme_navigator/api/main.py` | `test_reviewer_dashboard_and_review_endpoints_rbac` |
| **Priority 5** | **Data Retention** | `purge_expired_data()` only cleared in-memory dictionaries; SQLite database tables (`interview_sessions`, `document_reviews`) grew unbounded. | Extended `purge_expired_data()` to initialize and trigger deletion queries on SQLite `interview_sessions` and `document_reviews` (cascading to `review_events`), purging expired records beyond `retention_hours`. Scheduled hourly background retention task in FastAPI lifespan. | `src/scheme_navigator/security/retention.py`<br>`src/scheme_navigator/agents/interview_store.py`<br>`src/scheme_navigator/api/main.py` | `test_retention_purge_cleans_sqlite_stores` |
| **Priority 6** | **SSRF & Redirection** | Ingestion pipeline automatically followed HTTP redirects (`follow_redirects=True`), risking internal network scanning and bypass of government allowlists. | Disabled automatic redirect following. Implemented manual redirect inspection loop verifying each target URL against official allowlists and private IP ranges. Added DNS pre-resolution via `socket.getaddrinfo()` to block DNS rebinding to loopback, private, and cloud metadata (169.254.169.254) addresses. | `src/scheme_navigator/security/ssrf.py`<br>`src/scheme_navigator/ingestion/pipeline.py` | `test_ssrf_and_dns_rebinding_protection` |
| **Priority 7** | **Secret Management** | Hardcoded default secrets existed in codebase. Missing or weak secrets did not prevent production startup. | Added `validate_production_secrets()` executing on application startup. Requires `SCHEME_NAVIGATOR_AUTH_SECRET` and `SCHEME_NAVIGATOR_RELEASE_KEY` to have $\ge 32$ characters, non-default entropy, and distinct cryptographic keys in production. Fails closed with `RuntimeError` if invalid. | `src/scheme_navigator/core/config.py`<br>`src/scheme_navigator/security/auth.py`<br>`src/scheme_navigator/security/publication.py`<br>`src/scheme_navigator/api/main.py` | `test_production_secrets_validation_fails_closed` |
| **Priority 8** | **Audio Validation** | `/voice/transcribe` relied solely on `Content-Type` header without inspecting binary headers or magic bytes. | Added `validate_uploaded_audio_security()` validating magic container headers for WAV (`RIFF....WAVE`), MP3 (`ID3` or sync words `\xff\xfb`), OGG (`OggS`), FLAC (`fLaC`), and WebM (`\x1a\x45\xdf\xa3`). Rejects spoofed binaries and oversized payloads with HTTP 400 Bad Request. | `src/scheme_navigator/security/upload.py`<br>`src/scheme_navigator/api/main.py` | `test_audio_magic_byte_validation` |
| **Priority 9** | **Docker & Deployment** | `docker-compose.yml` mounted `./data` as `:ro`, crashing SQLite writes. Multiple Uvicorn workers caused cache inconsistency for in-memory session/rate limiter state. | Changed volume mount in `docker-compose.yml` from `./data:/app/data:ro` to read-write `./data:/app/data`. Explicitly pinned `--workers 1` in `Dockerfile` and `docker-compose.yml` to preserve memory state integrity until distributed Redis backend is deployed. | `docker-compose.yml`<br>`Dockerfile` | Verified Docker configuration files |
| **Priority 10** | **SGNAY Policy Data** | `sanjay-gandhi-niradhar-anudan.json` conflated $\ge 40\%$ disability eligibility with the $\ge 80\%$ severe disability enhanced benefit (₹2,500/mo). | Clarified AST and candidate schemas: baseline eligibility for destitute disability track requires certified disability $\ge 40\%$ and annual family income $\le$ ₹50,000 (providing base assistance of ₹1,500/month); enhanced ₹2,500/month assistance is restricted specifically to severe disability ($\ge 80\%$) under 15 September 2025 amendment. Candidate remains strictly in `draft` with `publication_authorized=false`. | `data/candidates/sanjay-gandhi-niradhar-anudan.json`<br>`data/candidates/candidate_schemes.json` | `test_sgnay_policy_disability_tier_distinction` |

---

## 3. Test Verification and Pass Rate

The complete test suite was executed against the remediated codebase:

```bash
..\.venv\Scripts\python.exe -m pytest -q
........................................................................ [ 27%]
........................................................................ [ 54%]
........................................................................ [ 81%]
.................................................                        [100%]
265 passed in 39.07s
```

### Breakdown of Test Coverage:
- **Baseline Automated Tests:** 254 tests passing.
- **Phase 6.1 Adversarial Security Integration Tests (`tests/test_security_remediation.py`):** 11 tests passing:
  1. `test_public_session_creation_rejects_privileged_roles`
  2. `test_admin_auth_provisioning_requires_valid_bootstrap_key`
  3. `test_admin_auth_provisioning_fails_closed_when_unconfigured`
  4. `test_interview_thread_ownership_isolation`
  5. `test_reviewer_dashboard_and_review_endpoints_rbac`
  6. `test_rate_limiting_enforcement`
  7. `test_retention_purge_cleans_sqlite_stores`
  8. `test_ssrf_and_dns_rebinding_protection`
  9. `test_audio_magic_byte_validation`
  10. `test_production_secrets_validation_fails_closed`
  11. `test_sgnay_policy_disability_tier_distinction`
- **Total Test Count:** 265 passed, 0 failed, 0 errors.

---

## 4. Architectural Boundaries and Residual Considerations

1. **Single-Worker Invariant (OPS-01):**
   The application strictly runs with `--workers 1` in container and production configurations. The in-memory session manager, rate limiter sliding windows, and audit ring buffer are process-local. Distributed deployment across multiple Uvicorn workers requires a Redis-backed session and token store.
2. **Citizen Privacy and DPDPA Compliance:**
   Citizen interview answers and extracted documents are stored in local SQLite databases protected by retention windows (default 24 hours). The automated purge scheduler enforces data minimization. DPDPA statutory compliance requires production deployment behind end-to-end TLS termination and dedicated database encryption at rest.
3. **Candidate Scheme Publication Boundary:**
   All 7 Maharashtra candidate schemes remain strictly in `draft` or `needs_review` status with `publication_authorized=false`. The fail-closed publication gate is active and tested.
