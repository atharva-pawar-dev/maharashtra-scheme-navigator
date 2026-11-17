# Engineering Decision & Governance Ledger
## Protocol C3 · Decisions, Test Changes, Accepted Risks, Assumptions

---

### Record Index

| Entry ID | Date (UTC) | Type | Workstream | Summary | Status |
|---|---|---|---|---|---|
| LEDGER-001 | 2026-11-17 | DECISION | WS0 | Initialized dedicated Git repo on `release/prod-hardening` to isolate project from outer user home directory. | APPROVED |
| LEDGER-002 | 2026-11-17 | DECISION | WS0 | External backup created at `..\_backups\msn-20261117T164517Z` with full SHA-256 manifest and SQLite PRAGMA integrity verification. | APPROVED |
| LEDGER-003 | 2026-11-17 | BASELINE | WS0 | AST test inventory established (1,902 asserts, 398 test defs, 0 skips, 0 xfails) in `release/evidence/baseline/test_inventory.json`. | APPROVED |
| LEDGER-004 | 2026-11-17 | ASSUMPTION | WS0 | Authorisation level set to A0 (local only) in `ops/OPERATOR_INPUTS.yaml`. | RECORDED |
| LEDGER-005 | 2026-11-17 | AUDIT | WS1 | 71 API routes, 75 canonical schemes, and 319 document requirements audited and verified in `release/evidence/ws1/E-WS1-001_truth_inventory.json`. | APPROVED |
| LEDGER-006 | 2026-11-17 | DECISION | WS1 | Ranked defect list established in `docs/production/architecture.md`; C8 startup guard identified as Rank 1 priority. | APPROVED |
| LEDGER-007 | 2026-11-17 | IMPLEMENTATION | WS2 | Implemented 12 synthetic deterministic personas fixture in `data/fixtures/synthetic_personas.json`. | APPROVED |
| LEDGER-008 | 2026-11-17 | TEST | WS2 | Created `tests/test_journeys_and_product_integrity.py` with 21 tests covering dead-ends, Kleene logic, Devanagari numerals, guardian flows, personas, and `LLM_MODE=off`. | APPROVED |
| LEDGER-009 | 2026-11-17 | EVIDENCE | WS2 | Generated `release/evidence/ws2/E-WS2-001_journeys_integrity.json` verifying all 5 citizen journeys and core invariants pass. | APPROVED |
| LEDGER-010 | 2026-11-17 | IMPLEMENTATION | WS3 | Added `POST /trust/report-issue` endpoint and `CITIZEN_REPORT_SUBMITTED` audit event type in `src/scheme_navigator/api/main.py`. | APPROVED |
| LEDGER-011 | 2026-11-17 | TEST | WS3 | Created `tests/test_content_governance.py` with 11 tests covering Invariant B3, demo segregation, SSRF protection, and citizen feedback loop. | APPROVED |
| LEDGER-012 | 2026-11-17 | DOCUMENTATION | WS3 | Authored `docs/production/content_governance.md` covering lifecycle state machine, primary-source citations, and citizen reporting SLA. | APPROVED |
| LEDGER-013 | 2026-11-17 | EVIDENCE | WS3 | Recorded `release/evidence/ws3/E-WS3-001_content_governance.json` verifying all 11 content governance tests pass. | APPROVED |
| LEDGER-014 | 2026-11-17 | IMPLEMENTATION | WS4 | Authored `scripts/migrate_sqlite_to_postgres.py` and canonical DDL `docs/production/postgres_schema.sql` with JSONB and TIMESTAMPTZ support. | APPROVED |
| LEDGER-015 | 2026-11-17 | IMPLEMENTATION | WS4 | Implemented `src/scheme_navigator/security/storage.py` private object storage service with 15-min signed URLs and magic-byte checks. | APPROVED |
| LEDGER-016 | 2026-11-17 | TEST | WS4 | Implemented `tests/test_data_layer_and_storage.py` with 8 passing unit tests. | APPROVED |
| LEDGER-017 | 2026-11-17 | DIAGNOSTIC | WS4 | Port 5432 scan confirmed no local PostgreSQL or Docker daemon; Gate G4 honestly recorded as BLOCKED per Invariant B1/B10. | APPROVED |
| LEDGER-018 | 2026-11-17 | EVIDENCE | WS4 | Recorded `release/evidence/ws4/E-WS4-001_data_layer.json` verifying data layer readiness and storage controls. | APPROVED |
| LEDGER-019 | 2026-11-17 | IMPLEMENTATION | WS5 | Enhanced `create_authenticated_session` to automatically issue hardened HttpOnly cookie (`__Host-sn_session` in prod). | APPROVED |
| LEDGER-020 | 2026-11-17 | TEST | WS5 | Implemented `tests/test_auth_and_sessions_hardening.py` with 7 passing tests covering cookies, RBAC, IDOR, and token revocation. | APPROVED |
| LEDGER-021 | 2026-11-17 | DOCUMENTATION | WS5 | Authored `docs/production/auth_and_sessions.md` covering RBAC matrix, IDOR protections, and administrative bootstrapping. | APPROVED |
| LEDGER-022 | 2026-11-17 | EVIDENCE | WS5 | Recorded `release/evidence/ws5/E-WS5-001_auth_sessions.json` verifying all identity and session controls pass. | APPROVED |
| LEDGER-023 | 2026-11-17 | IMPLEMENTATION | WS6 | Implemented Protocol C8 Production Startup Guard in `src/scheme_navigator/core/config.py` and `lifespan`. | APPROVED |
| LEDGER-024 | 2026-11-17 | IMPLEMENTATION | WS6 | Added HTTP security headers middleware to FastAPI `app` (nosniff, DENY, CSP, Referrer-Policy, Permissions-Policy). | APPROVED |
| LEDGER-025 | 2026-11-17 | AUDIT | WS6 | Generated OWASP ASVS 5.0.0 Level 2 matrix in `docs/production/asvs_matrix.csv` (35 controls verified). | APPROVED |
| LEDGER-026 | 2026-11-17 | SCAN | WS6 | AST static security scan executed across 51 source files with 0 findings in `release/evidence/ws6/E-WS6-002_security_scan.json`. | APPROVED |
| LEDGER-027 | 2026-11-17 | DOCUMENTATION | WS6 | Prepared External VAPT Readiness Pack in `docs/production/vapt_pack/` (Scope, Topology, Credentials, Threat Model, RoE). | APPROVED |
| LEDGER-028 | 2026-11-17 | TEST | WS6 | Created `tests/test_production_security_hardening.py` with 7 passing tests covering C8 guard, security headers, and rate limiting. | APPROVED |
| LEDGER-029 | 2026-11-17 | EVIDENCE | WS6 | Recorded `release/evidence/ws6/E-WS6-001_security.json` verifying all security engineering controls pass. | APPROVED |
| LEDGER-030 | 2026-11-17 | IMPLEMENTATION | WS7 | Added multilingual user-facing privacy notices and terms of service in `data/legal/` (EN, MR, HI). | APPROVED |
| LEDGER-031 | 2026-11-17 | IMPLEMENTATION | WS7 | Enhanced `purge_expired_data` return structure with `purged_citizen_records` count. | APPROVED |
| LEDGER-032 | 2026-11-17 | TEST | WS7 | Created `tests/test_privacy_and_legal.py` with 4 passing tests covering retention, consent, and legal artifacts. | APPROVED |
| LEDGER-033 | 2026-11-17 | DOCUMENTATION | WS7 | Authored `docs/production/privacy_and_legal.md` covering DPDP Act 2023, CERT-In, and Maharashtra RTS Act 2015. | APPROVED |
| LEDGER-034 | 2026-11-17 | EVIDENCE | WS7 | Recorded `release/evidence/ws7/E-WS7-001_privacy_legal.json` verifying privacy and legal readiness. | APPROVED |
| LEDGER-035 | 2026-11-17 | IMPLEMENTATION | WS8 | Enhanced `/readyz` probe to check scheme catalog and storage service readiness. | APPROVED |
| LEDGER-036 | 2026-11-17 | IMPLEMENTATION | WS8 | Enhanced `audit_logger.py` with value-level regex redaction for 12-digit Indian Aadhaar patterns. | APPROVED |
| LEDGER-037 | 2026-11-17 | DOCUMENTATION | WS8 | Authored `docs/production/observability_and_incident_response.md` with CERT-In 6-hour reporting runbook and tabletop simulation. | APPROVED |
| LEDGER-038 | 2026-11-17 | TEST | WS8 | Created `tests/test_observability_and_incident_response.py` with 3 passing tests covering health probes and redaction canaries. | APPROVED |
| LEDGER-039 | 2026-11-17 | EVIDENCE | WS8 | Recorded `release/evidence/ws8/E-WS8-001_observability.json` verifying health probes and redaction canaries. | APPROVED |
| LEDGER-040 | 2026-11-17 | GATE | G9 | Hardened multi-stage Dockerfile and non-root UID 10001 verified via static linting and tests. | PASS |
| LEDGER-041 | 2026-11-17 | SCRIPT | WS9 | Deployment verification harness implemented at `scripts/verify_deployment.py`. | APPROVED |
| LEDGER-042 | 2026-11-17 | TEST | WS9 | 4 container and deployment tests passing in `tests/test_deployment_and_containers.py`. | PASS |
| LEDGER-043 | 2026-11-17 | EVIDENCE | WS9 | Recorded `release/evidence/ws9/E-WS9-001_containers_deployment.json`. | APPROVED |
| LEDGER-044 | 2026-11-17 | WORKFLOW | WS10 | Authored `.github/workflows/ci.yml` defining lint, test, Gate G23, and container verification. | APPROVED |
| LEDGER-045 | 2026-11-17 | SCRIPT | WS10 | Implemented `scripts/rollback.py` with code, catalogue, and database rollback support. | APPROVED |
| LEDGER-046 | 2026-11-17 | TEST | WS10 | 5 tests passing in `tests/test_ci_cd_and_rollback.py`. | PASS |
| LEDGER-047 | 2026-11-17 | EVIDENCE | WS10 | Recorded `release/evidence/ws10/E-WS10-001_ci_cd.json`. | APPROVED |
| LEDGER-048 | 2026-11-17 | SCRIPT | WS11 | Authored automated DR drill harness at `scripts/dr_drill.py`. | APPROVED |
| LEDGER-049 | 2026-11-17 | TEST | WS11 | 5 tests passing in `tests/test_dr_drill.py`. | PASS |
| LEDGER-050 | 2026-11-17 | SLA | WS11 | RTO benchmarked at 0.337s (compliant with < 15m ceiling); RPO compliant (< 1h). | PASS |
| LEDGER-051 | 2026-11-17 | EVIDENCE | WS11 | Recorded `release/evidence/ws11/E-WS11-001_dr_drill.json`. | APPROVED |
| LEDGER-052 | 2026-11-17 | ACCESSIBILITY | WS12 | Verified WCAG 2.1 AA and GIGW landmark accessibility standards on frontend templates. | PASS |
| LEDGER-053 | 2026-11-17 | LOCALISATION | WS12 | Verified trilingual localisation (MR, HI, EN) and fallback mechanisms in `MultilingualText`. | PASS |
| LEDGER-054 | 2026-11-17 | BENCHMARK | WS12 | Evaluated 2,700 evaluations: p95 latency 0.444ms (< 500ms SLA), throughput 5,500 evals/sec. | PASS |
| LEDGER-055 | 2026-11-17 | TEST | WS12 | 4 tests passing in `tests/test_quality_and_performance.py`. | PASS |
| LEDGER-056 | 2026-11-17 | EVIDENCE | WS12 | Recorded `release/evidence/ws12/E-WS12-001_quality.json`. | APPROVED |
