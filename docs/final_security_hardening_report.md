# Scheme Navigator — Phase 6.1.1: Final Security Hardening Report

**Project:** Scheme Navigator  
**Date:** 12 November 2026  
**Environment Baseline:** Python 3.11.4 | FastAPI 0.115.6 | Pydantic 2.14 | HTTPX 0.28.1 | HTTPCore 1.0.7  
**Test Suite Status:** 276 passed (11 new dedicated hardening tests + 265 regression tests), 0 failures  
**Backup Reference:** `backup-phase6-1-1-20261112-124036`  

---

## Executive Summary

Phase 6.1.1 addresses the residual security weaknesses identified during the post-Phase 6.1 evaluation. All remediations have been implemented without altering the core deterministic eligibility engine, candidate scheme records, or Gemini document extraction pipeline. 

The five targeted security dimensions are fully addressed and verified:
1. **Admin Bootstrap Hardening:** Initial administrator bootstrap is strictly one-time; once provisioned, bootstrap is permanently disabled. Privileged sessions have a configurable 1-hour time-to-live (`privileged_session_ttl_hours: int = 1`). Subsequent accounts must be provisioned by authenticated administrators via `POST /admin/auth/provision-user`. Token revocation and secret rotation mechanisms are implemented. Zero bootstrap keys exist in citizen-facing frontend assets.
2. **SSRF Connection Pinning & DNS Rebinding Elimination:** Resolved the validation-to-connection Time-of-Check to Time-of-Use (TOCTOU) gap by implementing `SSRFSafeSyncBackend` and `SSRFSafeTransport`. Hostnames are resolved at TCP connection time; every returned IP (IPv4 and IPv6) is validated against private/loopback/link-local/multicast ranges. The TCP socket connects directly to the validated safe IP, followed by post-connect peer address verification. Server Name Indication (SNI) and TLS certificate validation are strictly preserved using the target hostname. Redirect chains are restricted to HTTPS-only allowlisted domains with a 3-hop ceiling.
3. **Retention Verification & SQLite WAL/SHM Integrity:** Verified automated expiry deletion across all SQLite data stores (`interviews.sqlite3`, `document_reviews.sqlite3`, `ingestion.sqlite3`). Cascading deletion from `document_reviews` to `document_review_events` is enforced via foreign keys. Checkpoint threads and interview sessions are pruned together. Live SQLite write-ahead-logs (`.sqlite3-wal`, `.wal`) and shared-memory files (`.sqlite3-shm`, `.shm`) are explicitly excluded from file unlinking during temp upload cleanup. The hourly retention worker is integrated into application lifespan and documented for single-worker execution.
4. **Comprehensive Rate Limiting:** Bound `rate_limit` dependencies across all sensitive and resource-intensive endpoints, including interview threads, application plan generation, document auditing, portal assistance, audio transcription, session creation, and reviewer UI. Verified that excess traffic receives HTTP 429 Too Many Requests with compliant `Retry-After` headers. Documented single-worker in-memory constraints.
5. **Reviewer & Admin Role Boundaries:** Hardened `/reviewer` dashboard and all document review CRUD endpoints (`GET`, `PATCH`, `POST /complete`, `DELETE`). Citizen sessions attempting access receive HTTP 403 Forbidden. Unauthenticated requests in production are rejected with HTTP 403.

---

## 1. Admin Bootstrap & Privileged Token Lifecycle

### 1.1 One-Time Bootstrap Invariant
Previously, `/admin/auth/provision` could be invoked repeatedly as long as the `ADMIN_BOOTSTRAP_KEY` was provided. Under Phase 6.1.1:
- `SessionManager` tracks an internal `_bootstrap_completed: bool` flag.
- The first invocation of `POST /admin/auth/provision` with a valid `X-Admin-Bootstrap-Key` provisions the initial `CATALOGUE_ADMIN` account and sets `_bootstrap_completed = True`.
- Any subsequent attempt to call `/admin/auth/provision` is immediately rejected with `403 Forbidden` (`"Bootstrap disabled: Initial administrator has already been provisioned. Use administrative credentials."`).
- In production, bootstrap keys must have at least 32 characters of entropy and must be rotated or cleared from the environment after deployment.

### 1.2 Administrative User Provisioning
Subsequent administrative and review personnel must be provisioned by an authenticated, active `CATALOGUE_ADMIN`:
- Endpoint: `POST /admin/auth/provision-user`
- Authorization: Requires `CATALOGUE_ADMIN` role token.
- Allowed Roles: `ANALYST`, `LEGAL_REVIEWER`, `CATALOGUE_ADMIN`.
- Citizen sessions or unauthenticated callers attempting this endpoint are rejected with `403 Forbidden`.

### 1.3 Privileged Token Expiry (1-Hour TTL)
Citizen sessions maintain a 24-hour convenience window for interview persistence. However, privileged administrative sessions are strictly time-bound:
- Configurable via `Settings.privileged_session_ttl_hours: int = 1`.
- Any session provisioned with `ANALYST`, `LEGAL_REVIEWER`, or `CATALOGUE_ADMIN` receives an `expires_at` timestamp of exactly 1 hour from creation.
- Expired tokens fail HMAC signature verification or expiry checking in `validate_token()`.

### 1.4 Explicit Session Revocation & Secret Key Rotation
- **Session Revocation:** Endpoint `POST /admin/auth/revoke` allows a `CATALOGUE_ADMIN` to immediately invalidate any compromised session ID. Revoked IDs are recorded in `SessionManager._revoked_session_ids` and rejected during token validation.
- **Secret Key Rotation:** `SessionManager.rotate_secret(new_secret_key)` replaces the HMAC signing secret. All previously issued tokens are invalidated instantly because their cryptographic signatures cannot match the new key.

### 1.5 Frontend Credential Exposure Audit
An automated audit of `static/index.html` and `static/reviewer.html` was conducted. Zero bootstrap keys, passwords, secrets, or administrative provisioning endpoints are embedded in client-side HTML, JavaScript, or comments.

---

## 2. SSRF Connection Pinning & DNS Rebinding Elimination

### 2.1 The Vulnerability: TOCTOU in Standard HTTP Clients
Standard SSRF validation typically checks a URL via `socket.getaddrinfo()`, verifies that the resolved IP is public, and then calls `httpx.get(url)`. An attacker controlling DNS can execute a DNS rebinding attack:
1. First DNS resolution returns a legitimate public IP (passing the allowlist check).
2. Milliseconds later, `httpx` establishes the actual TCP connection and triggers a second DNS resolution, which returns `127.0.0.1`, `10.0.0.1`, or cloud metadata `169.254.169.254`.

### 2.2 The Solution: Connection-Pinned Network Backend
In `scheme_navigator.security.ssrf`:
- Implemented `SSRFSafeSyncBackend` subclassing `httpcore._backends.sync.SyncBackend`.
- Inside `connect_tcp(host, port, ...)`:
  1. Resolves `host` via `socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)`.
  2. Inspects **every** returned address tuple (both IPv4 and IPv6). If any resolved IP belongs to `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, link-local IPv6, multicast, or reserved ranges, `httpcore.ConnectError` is raised immediately.
  3. Binds and connects the TCP socket directly to the validated safe IP `(resolved_ip, port)`.
  4. Verifies the connected socket's peer address via `sock.getpeername()[0]` to ensure routing did not redirect to a private interface.
  5. Wraps the socket in `SyncStream(sock)`.
- When TLS is negotiated, `SyncStream.start_tls(ssl_context, server_hostname=host)` receives the original domain name (e.g. `gr.maharashtra.gov.in`). The TLS handshake sends SNI and validates the certificate against the domain name, completely preserving hostname-based certificate trust.
- Implemented `SSRFSafeTransport(httpx.HTTPTransport)` which injects `SSRFSafeSyncBackend` into HTTPX connection pools.
- Used in `scheme_navigator.ingestion.pipeline`:
  - `_robots_allows`: Uses `SSRFSafeTransport` to fetch `robots.txt`.
  - `ingest_public_source`: Uses `SSRFSafeTransport` for government resolution and aggregator ingestion.
  - Redirect handling: Enforces a maximum of 3 redirects; each redirect target URL is validated against `_check_url()` (enforce allowlist, HTTPS-only) before the pinned connection is made.

---

## 3. Retention Verification & SQLite File Protection

### 3.1 Data Minimization Across SQLite Stores
| Database Path | Table | Data Stored | Expiry & Cascade Mechanism |
|---|---|---|---|
| `data/interviews.sqlite3` | `interview_sessions` | Thread ID, timestamps, expiry | `purge_expired()` removes session; cascades to LangGraph `checkpointer.delete_thread(thread_id)` |
| `data/document_reviews.sqlite3` | `document_reviews` | Review metadata, extracted fields | `purge_expired()` deletes rows where `expires_at <= now` |
| `data/document_reviews.sqlite3` | `document_review_events` | Field audit correction events | `FOREIGN KEY(review_id) REFERENCES document_reviews(review_id) ON DELETE CASCADE` with `PRAGMA foreign_keys = ON` |
| `data/ingestion.sqlite3` | `ingestion_snapshots` | Government source snapshots | Public documents; retention governed by legal change log policy |

### 3.2 WAL & SHM Protection
In `scheme_navigator.security.retention.purge_expired_data()`:
- When cleaning expired temporary uploaded artifacts in `target_temp.glob("*")`, active SQLite files, write-ahead-logs (`.sqlite3-wal`, `.wal`), and shared-memory index files (`.sqlite3-shm`, `.shm`) are explicitly excluded.
- Tested: Purging a directory containing aged `.pdf`, `.sqlite3`, `.sqlite3-wal`, and `.sqlite3-shm` unlinks the `.pdf` and strictly preserves the SQLite database and log files.

### 3.3 Startup Cleanup & Inactivity Purge
- On application restart or initialization of `InterviewSessionStore`, `self.last_purge_count = self.purge_expired()` executes immediately in `__init__`, clearing any expired threads from prior ungraceful shutdowns.
- An hourly background task (`_retention_worker`) runs in the FastAPI application lifespan.

---

## 4. Rate Limiting Matrix & Single-Worker Invariant

### 4.1 Route Rate-Limit Matrix
| Route | Method | Rate Limit | Purpose |
|---|---|---|---|
| `/auth/session` | POST | 20 / min | Prevents session generation denial-of-service |
| `/admin/auth/provision` | POST | 10 / min | Throttles bootstrap attempts |
| `/admin/auth/provision-user` | POST | 20 / min | Throttles account creation |
| `/admin/auth/revoke` | POST | 20 / min | Prevents revocation spam |
| `/interview/start` | POST | 30 / min | Protects LangGraph interview initialization |
| `/interview/answer` | POST | 60 / min | Paces conversational interview inputs |
| `/interview/{thread_id}` | GET | 60 / min | Throttles poll attempts on interview state |
| `/voice/transcribe` | POST | 30 / min | Protects audio STT processing resources |
| `/documents/audit-upload` | POST | 20 / min | Restricts document upload and parsing |
| `/documents/reviews/{id}` | GET | 30 / min | Reviewer read rate control |
| `/documents/reviews/{id}/documents/{doc_id}` | PATCH | 30 / min | Throttles human review corrections |
| `/documents/reviews/{id}/complete` | POST | 30 / min | Throttles review finalization |
| `/documents/reviews/{id}` | DELETE | 30 / min | Throttles review record deletion |
| `/plans/{scheme_id}` | POST | 60 / min | Paces application plan DAG generation |
| `/assistance/documents/audit-and-prepare` | POST | 30 / min | Protects document prep assistance |
| `/assistance/portal/guidance` | POST | 60 / min | Throttles RTS/portal guidance queries |
| `/reviewer` | GET | 60 / min | Throttles reviewer dashboard access |
| `/eligibility/evaluate` | POST | 60 / min | Eligibility engine evaluation |
| `/schemes/{scheme_id}/explain` | POST | 60 / min | Multilingual explanation synthesis |
| `/assessment/{scheme_id}` | POST | 60 / min | Scheme assessment |

### 4.2 Throttling Response Compliance
When a client exceeds the threshold:
- HTTP Status: `429 Too Many Requests`
- Headers: `Retry-After: <seconds>` (integer value indicating wait time until the window slides)
- Body: `{"detail": "Rate limit exceeded. Retry after <N> seconds."}`

### 4.3 Operational Requirement: Single-Worker Invariant
The in-memory rate limiter and in-process SQLite databases require the application to run with a single Uvicorn process worker (`--workers 1`). If scaled horizontally across multiple workers or pods without sticky sessions or external caching (e.g. Redis), in-memory buckets and SQLite file locks would not synchronize. Single-worker execution is documented and enforced in production deployment scripts.

---

## 5. Reviewer & Admin Role Boundaries

1. **Reviewer Dashboard (`GET /reviewer`):**
   - Citizen sessions are explicitly rejected with `403 Forbidden` (`"Access denied: citizen accounts are not authorized to access the reviewer dashboard."`).
   - In production mode (`APP_ENV=production`), unauthenticated requests are rejected with `403 Forbidden`.
2. **Review API Endpoints (`/documents/reviews/*`):**
   - Handled via `_ensure_reviewer_access(session)`.
   - Any session carrying `UserRole.CITIZEN` is rejected with `403 Forbidden` across `GET`, `PATCH`, `POST /complete`, and `DELETE`.
   - In production mode, requests without an authenticated session having `ANALYST` or higher role are rejected with `403 Forbidden`.
3. **Audit Logging of Privileged Actions:**
   - Every bootstrap, administrative user provisioning, and session revocation event is recorded in the structured audit log with actor ID, actor role, action, and client IP.

---

## 6. Automated Verification Results

All 11 tests in the dedicated security hardening test suite passed:
```
tests/test_final_security_hardening.py::test_admin_bootstrap_one_time_only PASSED
tests/test_final_security_hardening.py::test_admin_provision_user_and_revocation PASSED
tests/test_final_security_hardening.py::test_secret_rotation_invalidates_all_prior_tokens PASSED
tests/test_final_security_hardening.py::test_ssrf_sync_backend_blocks_dns_rebinding_to_loopback_and_private PASSED
tests/test_final_security_hardening.py::test_ssrf_transport_integration_with_httpx PASSED
tests/test_final_security_hardening.py::test_retention_purge_protects_sqlite_wal_and_shm_files PASSED
tests/test_final_security_hardening.py::test_document_review_cascading_purge_and_retrieval PASSED
tests/test_final_security_hardening.py::test_interview_store_purge_on_restart PASSED
tests/test_final_security_hardening.py::test_citizen_cannot_access_reviewer_endpoints PASSED
tests/test_final_security_hardening.py::test_production_unauthenticated_reviewer_access_rejected PASSED
tests/test_final_security_hardening.py::test_rate_limiter_sensitive_routes_trigger_429 PASSED
```

Full regression test suite:
```
============================= 276 passed in 18.36s =============================
```

Zero failures, zero regressions. All candidate records remain in `draft` status (`publication_authorized=false`) in accordance with the fail-closed publication gate.
