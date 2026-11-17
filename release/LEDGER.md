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
