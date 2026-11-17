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
