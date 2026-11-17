# Claims Register
## Protocol C3 / B1 / B12 · Evidence-Gated Claim Tracking

---

| Claim ID | Claim Text | Evidence ID | Verdict | Notes |
|---|---|---|---|---|
| C-001 | Full external backup created outside source tree with SHA-256 manifest and SQLite PRAGMA integrity check | E-WS0-001 | CONFIRMED | Backed up to `_backups/msn-20261117T164517Z`, 1,275 files, 194 SQLite databases verified OK. |
| C-002 | Test inventory snapshot established via Python AST with zero skips and zero xfails | E-WS0-002 | CONFIRMED | AST snapshot recorded: 44 files, 398 test functions, 1,902 assertions. |
| C-003 | Full unit baseline suite passes with zero failures | E-WS0-003 | CONFIRMED | `release/evidence/baseline/pytest_unit_baseline.xml` records 400 passed in 29.62s. |
| C-004 | Full Playwright browser baseline suite passes with zero failures | E-WS0-004 | CONFIRMED | `release/evidence/baseline/pytest_browser_baseline.xml` records 30 passed in 83.81s. |
| C-005 | Reported 75 canonical schemes catalogued in source registry | E-WS1-001 | CONFIRMED | 75 schemes verified across canonical dataset with exact lifecycle states. |
| C-006 | Reported 319 document requirements catalogued | E-WS1-001 | CONFIRMED | 319 requirements (273 mandatory, 31 conditional, 15 optional) verified across 75 schemes with 0 orphaned entries. |
| C-007 | Native PostgreSQL support across entire test suite | PENDING_WS4 | UNVERIFIED | To be evaluated and verified in WS4. |
| C-008 | Real production deployment live on public domain | NONE | REFUTED | No public cloud domain authorized or deployed (A0 local only). |
