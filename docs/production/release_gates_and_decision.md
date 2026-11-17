# MAHARASHTRA SCHEME NAVIGATOR — RELEASE GATES EVALUATION & LAUNCH DECISION

**Document Version:** 1.0.0  
**Evaluation Date:** 17 November 2026  
**Accountable Release Engineer:** Single Accountable Release Engineer  
**Branch:** `release/prod-hardening`  
**Latest Hardening Commit:** `aa8f560`  
**Governing Standard:** Protocol v2.0 (Part E Evidence Gates & Protocol B Invariants)  

---

## 1. Executive Summary & Derived Launch State

Maharashtra Scheme Navigator has completed all 15 production hardening workstreams (WS0 through WS15). Every release claim has been subjected to cryptographic verification, static AST analysis, automated integration tests, and disaster recovery drills.

### 1.1 Mechanically Computed Release Decision
In strict adherence to Protocol Part B (Invariants) and Part E (Release Gates), the launch state is computed mechanically from evidence rather than asserted subjectively:

$$\text{Launch State} = \mathbf{INTERNAL\_DEMO\_READY}$$

- **Status Determination Rationale:**
  - All core functional, security, session, privacy, accessibility, and governance gates (**G1, G2, G3, G5, G6, G7, G8, G9, G10, G11, G12, G13, G14, G15, G16, G17, G18, G19, G20, G21, G22, G23, G24**) have achieved **PASS**.
  - **Gate G4 (Production PostgreSQL 16+ Live Cluster)** is honestly recorded as **BLOCKED** based on diagnostic port scan evidence: no local PostgreSQL daemon is bound to `127.0.0.1:5432` and Docker engine is not provisioned on the host environment (Authorisation Level A0: local machine execution only).
  - Per Protocol Part E, when G4 is BLOCKED while all other core gates PASS, the maximum permissible release state is strictly capped at **`INTERNAL_DEMO_READY`**.
  - No claim of "production-ready", "DPDP-compliant", or "live public launch" is made (Protocol B12 compliance).

---

## 2. Release Gates Master Scorecard (G1 to G24)

| Gate ID | Release Gate Name | Associated WS | Evidence Reference | Gate Status | Verification Summary & Rationale |
|---|---|---|---|---|---|
| **G1** | Clean External Backup | WS0 | `E-WS0-001` | **PASS** | External backup at `_backups/msn-20261117T164517Z` verified (1,275 files, SHA-256 manifest, SQLite PRAGMA integrity PASS across 194 databases). |
| **G2** | Clean Test Suite Baseline | WS0 | `E-WS0-001` | **PASS** | Baseline test suite executed with zero skips, zero xfails: 400 unit tests passed (29.62s), 30 browser tests passed (83.81s). |
| **G3** | Canonical Truth Audit | WS1 | `E-WS1-001` | **PASS** | 71 API routes, 75 canonical schemes, and 319 document requirements audited with zero orphaned entries. |
| **G4** | Production PostgreSQL 16+ | WS4 | `E-WS4-001` | **BLOCKED** | Port 5432 scan confirmed no local daemon. Migration script (`scripts/migrate_sqlite_to_postgres.py`) and PostgreSQL DDL (`docs/production/postgres_schema.sql`) verified in dry-run. |
| **G5** | Private Object Storage | WS4 | `E-WS4-001` | **PASS** | Storage service enforces magic bytes (PDF/PNG/JPEG), private ACLs, AES-256 at-rest encryption, and 15-minute signed URL expiry. |
| **G6** | Hardened Identity & Sessions | WS5 | `E-WS5-001` | **PASS** | Citizen sessions HMAC-SHA256 signed with zero PII; role escalation blocked; IDOR thread cross-contamination prevented. |
| **G7** | Security Headers & C8 Guard | WS6 | `E-WS6-001` | **PASS** | Protocol C8 startup guard enforced in `lifespan`; OWASP security headers (`nosniff`, `X-Frame-Options: DENY`, `CSP`) active. |
| **G8** | Static Code Security Scan | WS6 | `E-WS6-002` | **PASS** | AST security scanner parsed 51 Python source files: 0 hardcoded secrets, 0 eval/exec, 0 shell injection findings. |
| **G9** | Hardened Container & Non-Root | WS9 | `E-WS9-001` | **PASS** | Multi-stage Dockerfile runs unprivileged non-root user `msnuser` (UID 10001); native `HEALTHCHECK` probe active. |
| **G10** | Deployment Verification | WS9 | `E-WS9-001` | **PASS** | `scripts/verify_deployment.py` confirms liveness, readiness, security headers, catalogue count, and anonymous sessions. |
| **G11** | CI/CD Quality Pipeline | WS10 | `E-WS10-001` | **PASS** | `.github/workflows/ci.yml` defines 3 stages (Lint/Security, Test Suite + G23, Container Verification). |
| **G12** | Automated Rollback Engine | WS10 | `E-WS10-001` | **PASS** | `scripts/rollback.py` supports code, catalogue, and database rollbacks with dry-run and health verification. |
| **G13** | Disaster Recovery Drill | WS11 | `E-WS11-001` | **PASS** | `scripts/dr_drill.py` restored sandbox with 100% SHA-256 match, 0 corrupt databases; RTO measured at **0.337s** (SLA < 15m). |
| **G14** | Accessibility & GIGW | WS12 | `E-WS12-001` | **PASS** | Static templates comply with WCAG 2.1 AA / GIGW: `<html lang="mr">`, landmark semantics, high contrast tokens. |
| **G15** | Trilingual Localisation | WS12 | `E-WS12-001` | **PASS** | Native Marathi (`mr`), Hindi (`hi`), English (`en`) support with `MultilingualText` dynamic fallback chain. |
| **G16** | Deterministic Evaluation SLA | WS12 | `E-WS12-001` | **PASS** | Rule engine evaluated 2,700 runs: p95 latency **0.444 ms** (SLA < 500 ms); throughput **5,500 evals/sec**. |
| **G17** | Citizen Trust Surface Notices | WS13 | `E-WS13-001` | **PASS** | Prominent top banner, pre-assessment, and footer disclaimers state platform is an independent advisory tool. |
| **G18** | Zero Placeholder Content | WS13 | `E-WS13-001` | **PASS** | Zero occurrences of `Lorem ipsum` or dummy mock text in citizen-facing HTML templates. |
| **G19** | Operations Handover Runbooks | WS14 | `E-WS14-001` | **PASS** | Comprehensive operational runbooks authored covering Deployments, Monitoring, Key Rotation, Incidents, and RACI. |
| **G20** | Invariant B3 Agent Ceiling | WS3 | `E-WS3-001` | **PASS** | Automated agent capability strictly capped at `EXTRACTED`; human review cannot be simulated or bypassed. |
| **G21** | Invariant B4 Deterministic Core | WS2 | `E-WS2-001` | **PASS** | Deterministic eligibility evaluates identically when `LLM_MODE=off`. |
| **G22** | SSRF Security Defense | WS3 | `E-WS3-001` | **PASS** | Blocks private/internal IPs, loopback, link-local metadata, non-HTTPS schemes, and untrusted hostnames. |
| **G23** | AST Non-Weakening Baseline | WS15 | `E-WS15-001` | **PASS** | Baseline: 398 tests, 1,902 assertions. Current: **468 tests (+70)**, **2,147 assertions (+245)**. Zero tests weakened. |
| **G24** | Canary Mutation Sensitivity | WS15 | `E-WS15-002` | **PASS** | Inverting assertion in `tests/test_dr_drill.py` caused pytest failure (code 1); revert restored clean pass (code 0). |

---

## 3. Operator Unblocking Action Packet

To promote the release state from **`INTERNAL_DEMO_READY`** to **`STAGING_READY`**, the designated human operators must execute the following concrete tasks:

### 3.1 Database Administrator Action (To Unblock Gate G4)
1. Provision a PostgreSQL 16+ instance accessible from the application host.
2. Configure `DATABASE_URL=postgresql://user:password@hostname:5432/scheme_navigator`.
3. Execute the validated migration script:
   ```bash
   python scripts/migrate_sqlite_to_postgres.py --postgres-url "$DATABASE_URL"
   ```
4. Verify all 10 tables are populated and run the test suite under PostgreSQL to flip Gate G4 to **PASS**.

### 3.2 Security Team Action (VAPT Execution)
1. Hand over the VAPT Readiness Pack (`docs/production/vapt_pack/`) to a CERT-In empanelled auditing firm.
2. Execute the penetration test within the defined Rules of Engagement (`roe.md`).
3. Remediate any external findings before public domain provisioning.

### 3.3 Legal & Translation Team Action
1. Conduct certified human legal translation review for Marathi (`privacy_notice_mr.json`) and Hindi (`privacy_notice_hi.json`) notices in `data/legal/`.
2. Flip `needs_human_translation_review: false` upon official legal sign-off.
