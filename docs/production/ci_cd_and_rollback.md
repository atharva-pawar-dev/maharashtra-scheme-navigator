# MAHARASHTRA SCHEME NAVIGATOR — CI/CD PIPELINE & ROLLBACK STRATEGY

**Document Version:** 1.0.0  
**Effective Date:** 17 November 2026  
**Status:** Approved for Production Hardening  

---

## 1. CI/CD Architecture & Quality Gates

The Maharashtra Scheme Navigator CI/CD pipeline (`.github/workflows/ci.yml`) establishes an automated, evidence-backed quality barrier that prevents regressions, security vulnerabilities, or weakening of tests from entering production branches (`main`, `release/*`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CI/CD Execution Pipeline                        │
├──────────────────┬──────────────────────┬──────────────────────────────┤
│ 1. Security &    │ 2. Test Execution    │ 3. Container & Deployment    │
│    AST Linting   │    & Gate G23 Check  │    Verification              │
├──────────────────┼──────────────────────┼──────────────────────────────┤
│ • Ruff linter    │ • Gate G23 Baseline  │ • Docker multi-stage build   │
│ • AST Security   │   AST check (asserts │ • Non-root UID 10001 check   │
│   scanner        │   must never drop)   │ • Container HEALTHCHECK      │
│ • Zero secrets   │ • Unit & Integration │ • `scripts/verify_deployment │
│   policy         │   test suite         │   .py --in-process`          │
└──────────────────┴──────────────────────┴──────────────────────────────┘
```

### 1.1 Gate G23 Enforcement (AST Invariant Baseline)
The pipeline strictly enforces Protocol B6 and Gate G23:
- Tests must never be deleted, commented out, or weakened.
- The Python AST test counter evaluates current test definitions and assertions against `release/evidence/baseline/test_inventory.json` (398 test definitions, 1,902 assertions).
- Any pull request that reduces total assertions or test counts fails the pipeline immediately.

### 1.2 Hermetic Security Scanning
- AST scanner `scripts/security_audit_scanner.py` parses all Python source files.
- Detects dynamic code evaluation (`eval`, `exec`), unescaped shell commands (`shell=True`), insecure deserialization (`pickle`), and hardcoded cryptographic secrets.

---

## 2. Automated Rollback Strategy (`scripts/rollback.py`)

A reliable deployment pipeline requires deterministic rollback automation. The `scripts/rollback.py` utility supports atomic rollbacks across code, scheme catalogues, and persistence layers.

### 2.1 Rollback Scenarios & Commands

#### Scenario A: Faulty Application Code Release
Trigger: Elevated 5xx error rate, latency spike, or runtime regression post-deployment.
Action: Revert application code to the prior known-good Git commit or release tag.
Command:
```bash
# 1. Dry run simulation
python scripts/rollback.py --target code --commit pre-hardening-20261117T164413Z --dry-run

# 2. Execute rollback and verify health
python scripts/rollback.py --target code --commit pre-hardening-20261117T164413Z --verify
```

#### Scenario B: Corrupted or Malformed Scheme Catalogue Release
Trigger: Discrepancy detected in canonical scheme criteria or missing document requirements.
Action: Revert `data/source_registry/` and `data/candidates/` from a certified backup or previous commit.
Command:
```bash
# 1. Dry run simulation
python scripts/rollback.py --target catalogue --commit HEAD~1 --dry-run

# 2. Execute rollback and verify health
python scripts/rollback.py --target catalogue --commit HEAD~1 --verify
```

#### Scenario C: Database Data Inconsistency or Corrupt State
Trigger: Erroneous batch update or database integrity check failure.
Action: Restore SQLite/PostgreSQL database from verified point-in-time backup.
Command:
```bash
# 1. Dry run simulation
python scripts/rollback.py --target database --backup-file _backups/msn-20261117T164517Z/data/citizen_profiles.sqlite3 --dry-run

# 2. Execute rollback and verify health
python scripts/rollback.py --target database --backup-file _backups/msn-20261117T164517Z/data/citizen_profiles.sqlite3 --verify
```

### 2.2 Pre-Rollback State Preservation
Before overwriting any active database file, `scripts/rollback.py` creates a pre-rollback snapshot (e.g. `citizen_profiles.sqlite3.pre_rollback_<timestamp>`) to prevent unrecoverable data loss during incident recovery.

### 2.3 Mean Time to Rollback (MTTR) SLA
- Automated code rollback target: < 2 minutes.
- Automated catalogue rollback target: < 1 minute.
- Automated database restoration target: < 5 minutes.
- System health verification: < 15 seconds.
