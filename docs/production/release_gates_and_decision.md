# MAHARASHTRA SCHEME NAVIGATOR — RELEASE GATES EVALUATION & LAUNCH DECISION
## Rigorous Part E Compliance Audit & Evidence-Gated Evaluation

**Document Version:** 2.1.0 (Final Reconciliation)  
**Evaluation Date:** 18 November 2026  
**Accountable Role:** Single Accountable Release Engineer  
**Branch:** `release/prod-hardening`  
**Governing Standard:** Original Master Execution Program v2.0 (Part E1, E2 & Appendix H5)  
**Authorisation Level:** A0 (Local Machine Execution Only)  

---

## 1. Executive Summary & Derived Launch State

Following an exhaustive compliance and evidence reconciliation against the original Production Release Program v2.0, the release gate scorecard has been completely audited and aligned with primary source evidence, executable test results, and actual environment boundaries. Stale or inflated claims (such as "23/24 PASS") have been permanently removed.

### 1.1 Reconciled Release Gate Counts

$$\mathbf{Total\ Gates:\ 24}$$
$$\mathbf{PASS:\ 8\ \ \ |\ \ \ PARTIAL:\ 11\ \ \ |\ \ \ BLOCKED:\ 5\ \ \ |\ \ \ NOT\_APPLICABLE:\ 0}$$

- **PASS (8 Gates):** G1 (Citizen journeys), G2 (Document auditor), G3 (Catalogue integrity), G5 (Application handoff), G11 (Privacy implementation), G13 (DPDP / CERT-In ledger), G23 (Test integrity), G24 (Evidence completeness).
- **PARTIAL (11 Gates):** G4 (Scheme accuracy), G7 (Document storage), G8 (AuthN/AuthZ), G9 (Internal security verification), G14 (Observability), G15 (Disaster recovery), G16 (Accessibility), G17 (Performance), G18 (CI/CD and rollback), G21 (Public content and contacts), G22 (Human ownership).
- **BLOCKED (5 Gates):** G6 (Production database), G10 (External VAPT), G12 (Legal review), G19 (Staging acceptance), G20 (Domain and HTTPS).
- **NOT_APPLICABLE (0 Gates):** Zero gates are marked N/A. (G20 is classified as BLOCKED because authorization level A0 explains why it cannot be completed locally, but does not waive the gate requirement).

---

### 1.2 Mechanically Computed Release Decision (Section E2)

$$\mathbf{Launch\ State = INTERNAL\_DEMO\_READY}$$

- **Mechanical Derivation Formula (Part E2):**
  - **`INTERNAL_DEMO_READY`** requires: **G1, G2, G3, G5, and G23 PASS locally**.
    - **G1 (Citizen journeys):** **PASS** (Journeys A, B, C pass end-to-end in 3 languages × 2 viewports, no dead ends; 30 browser acceptance tests + 21 journey integrity tests verified green).
    - **G2 (Document auditor):** **PASS** (Full lifecycle verified: upload → OCR extraction → requirement matching → missing docs detection → user correction → session persistence → resume).
    - **G3 (Catalogue integrity):** **PASS** (75 canonical schemes validate; demo data physically segregated; production C8 startup guard strictly enforced).
    - **G5 (Application handoff):** **PASS** (Official external government portal links verified; prominent statutory non-sanctioning advisory disclaimers active across all entry points).
    - **G23 (Test integrity):** **PASS** (AST test inventory strictly non-weakening: 56 files, 472 tests, 2,154 assertions vs 44 files, 398 tests, 1,902 assertions baseline; **all 12/12 Appendix H5 canary mutations executed and caught against the real codebase**).
  - **Why higher release tiers cannot be claimed:**
    - **`STAGING_READY`** requires all above PLUS **G6, G7, G8, G9, G18, G19, G24 PASS**:
      - G6 (Production database) is **BLOCKED** (no PostgreSQL daemon on port 5432; Docker engine absent).
      - G7 (Document storage) is **PARTIAL** (storage abstraction and TTL verified locally; live cloud S3 drill unexecuted).
      - G8 (AuthN/AuthZ) is **PARTIAL** (privileged-user MFA is absent and unexecuted).
      - G9 (Internal security) is **PARTIAL** (DAST, SAST, dependency, and container scanning unexecuted).
      - G18 (CI/CD) is **PARTIAL** (remote GitHub Actions run unexecuted).
      - G19 (Staging acceptance) is **BLOCKED** (no external staging environment provisioned).
    - **`PILOT_READY`** requires G10, G11, G12, G14, G15, G16, G17, G20 PASS (G10, G12, G20 are BLOCKED; G14, G15, G16, G17 are PARTIAL).
    - **`GENERAL_AVAILABILITY`** requires all 24 gates PASS.
  - Therefore, the application is derived mechanically and honestly as **`INTERNAL_DEMO_READY`**.

---

## 2. Reassessment of Specific Gates

### G8 — Authentication and Authorization: PARTIAL
- **Implemented & Verified:** Citizen anonymous session minting, HMAC-SHA256 cookie security (`__Host-sn_session`, `HttpOnly`, `SameSite=Lax`, `Secure` in prod), session revocation, idle timeout expiry, 4-tier Role-Based Access Control (`citizen`, `analyst`, `reviewer`, `catalogue_admin`), role escalation guards, and interview thread IDOR isolation (`test_citizen_cannot_answer_another_citizens_interview_thread`).
- **Missing / Gap:** Privileged-user Multi-Factor Authentication (MFA) via TOTP, SMS OTP, or WebAuthn/FIDO2 is **not implemented** in the application and **not tested**. RBAC cannot substitute for MFA.
- **Verdict:** **PARTIAL**.

### G9 — Internal Security Verification: PARTIAL
- **Implemented & Verified:** Custom AST static security scanner (`scripts/ast_test_inventory.py` and `src/scheme_navigator/security/ast_scan.py`) executed across 56 files (0 hardcoded secrets, 0 `eval`/`exec`, 0 dynamic SQL queries); OWASP ASVS Level 2 design matrix documented with 35 verified controls.
- **Missing / Gap:** Security categories must be formally distinguished:
  1. *AST Analysis:* **EXECUTED & PASSED** locally.
  2. *SAST (Static Application Security Testing):* **UNEXECUTED** (no formal Bandit/Semgrep run).
  3. *Dependency Scanning:* **UNEXECUTED** (no `pip-audit` or CVE database check).
  4. *Container Scanning:* **UNEXECUTED** (no Trivy or Grype scan of container image).
  5. *API Security Testing:* **PARTIALLY EXECUTED** (unit/integration tests cover auth and rate limiting).
  6. *DAST (Dynamic Application Security Testing):* **UNEXECUTED** (no OWASP ZAP or Burp Suite scan against live endpoints).
- **Verdict:** **PARTIAL**.

### G14 — Observability: PARTIAL
- **Implemented & Verified:** Liveness probe (`/healthz`) and readiness probe (`/readyz`) operational; structured JSON security audit logger (`SecurityAuditLogger`) with real-time value-level regex redaction for 12-digit Indian Aadhaar patterns and sensitive credential keys (`test_audit_logger_redaction_canaries`).
- **Missing / Gap:** No active Prometheus metrics scraper is deployed on live infrastructure; no Grafana dashboards are streaming real-time metrics; no Alertmanager alerting pipeline is configured; and no live alert firing was triggered under synthetic fault conditions against an external notification endpoint.
- **Verdict:** **PARTIAL**.

### G15 — Disaster Recovery: PARTIAL
- **Implemented & Verified:** Automated disaster recovery drill (`scripts/dr_drill.py`) executed against SQLite development databases and local file storage, achieving 0.337s restore RTO, 100% SHA-256 checksum match, and `PRAGMA integrity_check = ok` (`release/evidence/ws15/E-WS15-001_dr_drill_full.json`).
- **Missing / Gap:** Full restore drills have **not** been executed against a real PostgreSQL 15+ database cluster or cloud S3-compatible object storage (e.g., AWS S3, MinIO) due to local A0 environment boundaries.
- **Verdict:** **PARTIAL**.

### G18 — CI/CD and Rollback: PARTIAL
- **Implemented & Verified:** GitHub Actions workflow definition (`.github/workflows/ci.yml`) authored with 3-stage validation, automated rollback triggers, and git-tag semantic releases; local rollback script (`scripts/rollback.py`) verified with code, catalogue, and database rollbacks and dry-run execution (`tests/test_ci_cd_and_rollback.py`).
- **Missing / Gap:** The CI/CD pipeline has **not** executed in a remote GitHub repository runner, and automated deployment rollback has **not** been demonstrated on a live deployment cluster.
- **Verdict:** **PARTIAL**.

### G20 — Domain and HTTPS: BLOCKED
- **Implemented & Verified:** Security middleware enforces HSTS, TLS requirements, and HTTPS redirects in production mode (`secure=True` cookie attributes).
- **Missing / Gap:** No public domain is registered (e.g. `schemes.maharashtra.gov.in`); DNS CAA records and Let's Encrypt / commercial TLS certificates are not provisioned. Authorization level A0 explains why this cannot be completed locally, but does not waive the gate requirement.
- **Verdict:** **BLOCKED**.

---

## 3. Canonical Release Gates Master Scorecard (Original Part E1)

| Gate ID | Canonical Gate Name | Original Part E Definition | Evidence Reference | Actual Status | Primary Verification & Reality Assessment |
|---|---|---|---|:---:|---|
| **G1** | Citizen journeys | A, B, C pass end to end in 3 languages × 2 viewports, no dead ends | `E-WS2-001`, `pytest_final_unit.xml`, Playwright baseline | **PASS** | 30 Playwright browser tests + 21 journey integrity tests pass across mobile (390x844) and desktop (1280x800) viewports in MR, HI, EN. Dead ends eliminated. |
| **G2** | Document auditor | Upload → extraction → matching → missing docs → correction → save → refresh → resume | `E-WS0-001`, `pytest_final_unit.xml`, `test_browser_document_auditor_journey.py` | **PASS** | Complete document auditor lifecycle verified: upload, OCR extraction findings, conflict resolution, manual user correction, and session persistence across 39 unit/browser tests. |
| **G3** | Catalogue integrity | Records validate; demo data physically separated; production guard enforced | `E-WS1-001`, `E-WS3-001`, `E-WS6-001` | **PASS** | 75 canonical scheme records validate; `data/demo/` physically separated; `demo_fixtures_enabled=False` in production; C8 startup guard active. |
| **G4** | Scheme accuracy | Every *published* claim has source evidence and a named human approval | `E-WS1-001`, `E-WS3-001` | **PARTIAL** | All 75 schemes have GR source citations and SHA-256 evidence. Per Invariant B3, agent ceiling is `EXTRACTED`; named human departmental approvals pending. |
| **G5** | Application handoff | Verified official channel; no false submission claims | `E-WS13-001`, `pytest_final_unit.xml`, `test_application_assistance.py` | **PASS** | External links to Aaple Sarkar, MahaDBT, and state portals verified. Top banner, cards, and footer prominently disclaim executive sanctioning authority. |
| **G6** | Production database | Entire suite green on real PostgreSQL; migration parity proven | `E-WS4-001` | **BLOCKED** | Migration engine and PostgreSQL DDL complete. Port 5432 scan confirmed no daemon; Docker absent on host. Zero tests run on real PostgreSQL. |
| **G7** | Document storage | Private, encrypted, scanned, signed-URL-only, retention enforced | `E-WS4-001`, `pytest_final_unit.xml` | **PARTIAL** | Storage abstraction enforces magic bytes, 15-min signed URL TTL, and retention purge. Tested against local filesystem/mock, not live S3 server. |
| **G8** | AuthN/AuthZ | Session security, RBAC, MFA, IDOR/escalation suites green | `E-WS5-001`, `pytest_final_unit.xml` | **PARTIAL** | Anonymous HMAC-SHA256 sessions, zero PII, HttpOnly/SameSite cookies, 4-tier RBAC, role escalation blocked, IDOR thread isolation verified. Privileged MFA not implemented. |
| **G9** | Internal security verification | ASVS L2 matrix, scans, DAST, zero unaccepted critical/high | `E-WS6-001`, `E-WS6-002` | **PARTIAL** | AST static scan executed with 0 secrets and 0 dangerous calls. Formal SAST, dependency scanning, container scanning, and DAST unexecuted. |
| **G10** | External VAPT | Independent report attached; criticals/highs remediated and retested | `docs/production/vapt_pack/` | **BLOCKED** | VAPT Readiness Pack prepared. Independent certified penetration testing firm not yet engaged under local A0 authorization. |
| **G11** | Privacy implementation | Inventory, retention jobs, rights workflows, notices, provider register | `E-WS7-001`, `pytest_final_unit.xml` | **PASS** | 24-hour retention ceiling with automated hourly purge worker verified; Bhashini cloud consent gate enforced (HTTP 400 when unconsented). |
| **G12** | Legal review | Qualified counsel review evidenced; resulting changes implemented | `docs/production/privacy_and_legal.md` | **BLOCKED** | Primary-source legal ledger complete. Multilingual notices flagged `needs_human_translation_review: true`. External counsel sign-off pending. |
| **G13** | DPDP / CERT-In ledger | Primary-source ledger complete; later tranche design tracked; incident/log controls implemented | `E-WS7-001`, `E-WS8-001` | **PASS** | DPDP Act 2023 / CERT-In Directions crosswalk complete; 6-hour incident runbook documented; audit logger redacts Aadhaar and secrets. |
| **G14** | Observability | Logs, metrics, alerts, redaction canaries, tabletop exercise | `E-WS8-001`, `pytest_final_unit.xml` | **PARTIAL** | Decoupled `/healthz` (liveness) and `/readyz` (readiness) operational; redaction canaries verified; live Prometheus/Alertmanager stack and live alert firing unexecuted. |
| **G15** | Disaster recovery | Restore drill completed; RPO/RTO measured | `E-WS11-001`, `pytest_final_unit.xml` | **PARTIAL** | Restore drill from SHA-256 backup verified: 100% checksum match, 0 corrupt DBs, PRAGMA integrity OK; local restore RTO 0.337s; full PostgreSQL/S3 drill unexecuted. |
| **G16** | Accessibility | Automated suite clean; human screen-reader attestation | `E-WS12-001` | **PARTIAL** | Automated static template checks pass (`<html lang="mr">`, landmarks, contrast, touch targets). Human screen-reader attestation pending. |
| **G17** | Performance | Measured results at declared envelope and above | `E-WS12-001` | **PARTIAL** | Rule engine benchmarked across 2,700 evals: p95 0.444ms (< 500ms). Full HTTP load test at declared envelope (150 sessions, 40 req/s) pending. |
| **G18** | CI/CD and rollback | Pipeline works; rollback demonstrated | `E-WS10-001`, `pytest_final_unit.xml` | **PARTIAL** | CI workflow defined; local rollback script verified across code, catalogue, and DB. Remote GitHub Actions execution and remote deployment rollback unexecuted. |
| **G19** | Staging acceptance | Full acceptance passed on a reachable staging environment | `E-WS9-001` | **BLOCKED** | In-process deployment verification passed. No external reachable staging environment provisioned under A0 authorization. |
| **G20** | Domain and HTTPS | Live external verification script passes at the real domain | `CLAIMS.md` | **BLOCKED** | Under local A0 authorization, public domain registration and live DNS/TLS verification are out of scope. Classified BLOCKED, not N/A. |
| **G21** | Public content and contacts | Real operator identity and contacts; no placeholders | `E-WS13-001` | **PARTIAL** | Public disclaimers and portal links live with zero `Lorem ipsum`. Operator legal identity and public contacts in `OPERATOR_INPUTS.yaml` pending. |
| **G22** | Human ownership | Named owners for all six areas | `docs/production/operations_runbook.md` | **PARTIAL** | RACI operations ownership matrix documented across 5 operational roles. Specific named individuals not assigned in `OPERATOR_INPUTS.yaml`. |
| **G23** | Test integrity | Baseline diff justified; all canaries caught | `E-WS15-001`, `E-WS15-002` | **PASS** | AST inventory non-weakening PASS (+74 tests, +252 assertions vs baseline); **all 12/12 Appendix H5 canary mutations caught by automated tests on real codebase**. |
| **G24** | Evidence completeness | Zero `UNSUPPORTED` claims in the final report | `release/CLAIMS.md` | **PASS** | All claims in Claims Register cite immutable JSON evidence records; unsupported infrastructure claims marked `REFUTED` or `BLOCKED`. |

---

## 4. Canary Mutation Verification Matrix (Appendix H5)

All 12 Appendix H5 canary mutations were directly executed against the real codebase via `scripts/verify_individual_canaries.py`. Each canary injected a defect into the production source file, executed the targeted pytest command, verified failure with exit code 1, restored the original code byte-for-byte, and verified passing with exit code 0.

$$\mathbf{Result:\ 12/12\ CANARIES\ CAUGHT\ (100\%)\ -\ EXIT\ CODE\ 0}$$

| ID | Canary Name | Target File | Mutated Code Snippet | Catching Test & Command | Mutated RC | Restored RC | Failure Detected by Test | Status |
|:---:|---|---|---|---|:---:|:---:|---|:---:|
| **01** | Flip income ceiling comparison (<= to <) | `src/scheme_navigator/services/rule_engine.py` | `elif node.op == "lte":\n    value = actual < expected` | `pytest tests/test_rule_boundary_matrix.py -k test_age_exact_maximum_boundary_eligible` | **1** | **0** | `assert evaluate_node(rule, profile_65).value is True` failed (`False != True`) | **PASS (CAUGHT)** |
| **02** | Make UNKNOWN evaluate as FALSE in conjunction | `src/scheme_navigator/services/rule_engine.py` | `if any(result.value is None for result in results):\n    return Evaluation(False, missing)` | `pytest tests/test_rule_engine.py -k test_conjunction_with_unknown_evaluates_unknown_not_false` | **1** | **0** | `assert result.value is None` failed (`False != None`) | **PASS (CAUGHT)** |
| **03** | Swap PMC/PCMC ward boundary membership | `src/scheme_navigator/domain/jurisdiction.py` | `"411027_MUTATED": [\n    {"corporation_id": "mc-pimpri-chinchwad", ...` | `pytest tests/test_municipal_and_jurisdiction_matching.py -k test_scenario_08_locality_and_pin_boundary_ambiguity` | **1** | **0** | `assert data["status"] == "LOCATION_REQUIRES_CONFIRMATION"` failed | **PASS (CAUGHT)** |
| **04** | Remove owner check from interview endpoint (IDOR) | `src/scheme_navigator/api/main.py` | `if False and not session_manager.authorize_thread_access(effective_session, payload.thread_id):` | `pytest tests/test_auth_and_sessions_hardening.py -k test_citizen_cannot_answer_another_citizens_interview_thread` | **1** | **0** | `assert answer_resp.status_code == 403` failed (got 200) | **PASS (CAUGHT)** |
| **05** | Let production profile load a fixture scheme | `src/scheme_navigator/core/config.py` | `if False and self.demo_fixtures_enabled:\n    raise RuntimeError(...)` | `pytest tests/test_content_governance.py -k test_production_rejects_demo_fixtures_startup_guard` | **1** | **0** | `Failed: DID NOT RAISE <class 'RuntimeError'>` | **PASS (CAUGHT)** |
| **06** | Allow published claim with no source ID / incomplete evidence | `src/scheme_navigator/domain/evidence.py` | `is_valid = (\n    True\n    and len(orphan_evidence) == 0` | `pytest tests/test_rule_boundary_matrix.py -k test_active_scheme_with_incomplete_evidence_raises` | **1** | **0** | `Failed: DID NOT RAISE <class 'ValueError'>` | **PASS (CAUGHT)** |
| **07** | Drop Secure flag from session cookie in production | `src/scheme_navigator/api/main.py` | `secure=False, samesite="lax", max_age=24*3600` | `pytest tests/test_auth_and_sessions_hardening.py -k test_production_session_cookie_has_secure_flag` | **1** | **0** | `assert "secure" in set_cookie` failed | **PASS (CAUGHT)** |
| **08** | Serve signed URL with expiry of days instead of minutes | `src/scheme_navigator/security/storage.py` | `effective_ttl = expires_in_seconds  # Expiry ceiling bypassed` | `pytest tests/test_data_layer_and_storage.py -k test_presigned_url_max_ttl_ceiling` | **1** | **0** | `assert (expiry_ts - now) <= 902` failed (`604800 > 902`) | **PASS (CAUGHT)** |
| **09** | Skip magic-byte check on upload | `src/scheme_navigator/security/storage.py` | `detected_mime = content_type or "application/octet-stream"` | `pytest tests/test_data_layer_and_storage.py -k test_storage_rejects_malicious_or_forged_headers` | **1** | **0** | `Failed: DID NOT RAISE StorageValidationError` | **PASS (CAUGHT)** |
| **10** | Log raw session token unredacted | `src/scheme_navigator/security/audit_logger.py` | `if False and any(s in k_lower for s in ("password", "secret", "token", ...)):` | `pytest tests/test_observability_and_incident_response.py -k test_audit_logger_redaction_canaries` | **1** | **0** | `assert event.details["auth_password"] == "[REDACTED]"` failed | **PASS (CAUGHT)** |
| **11** | Permit author to approve own publication | `src/scheme_navigator/api/main.py` | `session: UserSession = Depends(require_role(UserRole.ANALYST))` | `pytest tests/test_auth_and_sessions_hardening.py -k test_analyst_cannot_sign_catalogue_release` | **1** | **0** | `assert resp.status_code == 403` failed (got 200) | **PASS (CAUGHT)** |
| **12** | Cache personalised response under shared key | `src/scheme_navigator/api/main.py` | `citizen_store.save_profile("shared_cache_key", ...)\ncitizen_store.get_profile_with_provenance("shared_cache_key")` | `pytest tests/test_auth_and_sessions_hardening.py -k test_cross_session_profile_isolation` | **1** | **0** | `assert b_profile.get("age_years") is None` failed (`45 is not None`) | **PASS (CAUGHT)** |

*Artifact Reference:* `release/evidence/ws15/E-WS15-002_canary_mutations_individual.json`.

---

## 5. Evidence Register & Traceability

| Gate | Claim / Subsystem | Evidence ID | Primary Output Artifact | Verification Mechanism | Status |
|---|---|---|---|---|:---:|
| **G1** | Citizen journeys | `E-WS2-001`, `E-WS0-004` | `release/evidence/baseline/pytest_browser_baseline.xml` | 30 Playwright tests in Chromium headless + 21 journey integrity tests | **CONFIRMED** |
| **G2** | Document auditor | `E-WS0-001`, `E-WS15-003` | `tests/test_browser_document_auditor_journey.py` | 4 Playwright browser tests + 35 unit/integration tests in `test_document_*.py` | **CONFIRMED** |
| **G3** | Catalogue integrity | `E-WS1-001`, `E-WS3-001` | `release/evidence/ws1/E-WS1-001_truth_inventory.json` | 75 schemes validated, JSON schema check, demo fixtures segregated | **CONFIRMED** |
| **G4** | Scheme accuracy | `E-WS3-001` | `docs/production/content_governance.md` | All schemes cite official GRs; agent ceiling `EXTRACTED` enforced | **PARTIAL** |
| **G5** | Application handoff | `E-WS13-001` | `tests/test_application_assistance.py` | External portal link tests, disclaimer presence tests across all viewports | **CONFIRMED** |
| **G6** | Production database | `E-WS4-001` | `docs/production/postgres_schema.sql` | DDL ready, migration script ready; live daemon unreachable | **BLOCKED** |
| **G7** | Document storage | `E-WS4-001` | `tests/test_data_layer_and_storage.py` | Magic bytes, 15m presigned URL TTL, retention purge tested on local store | **PARTIAL** |
| **G8** | AuthN/AuthZ | `E-WS5-001` | `tests/test_auth_and_sessions_hardening.py` | 9 automated tests passing; privileged MFA absent | **PARTIAL** |
| **G9** | Internal security | `E-WS6-001`, `E-WS6-002` | `release/evidence/ws6/E-WS6-002_security_scan.json` | AST scanner executed (0 secrets, 0 eval); SAST/DAST unexecuted | **PARTIAL** |
| **G10** | External VAPT | N/A | `docs/production/vapt_pack/` | VAPT pack prepared; independent assessor not engaged | **BLOCKED** |
| **G11** | Privacy implementation | `E-WS7-001` | `tests/test_privacy_and_legal.py` | Retention purge worker, Bhashini consent gate, 0 telemetry verified | **CONFIRMED** |
| **G12** | Legal review | N/A | `docs/production/privacy_and_legal.md` | Primary-source ledger authored; legal counsel review pending | **BLOCKED** |
| **G13** | DPDP / CERT-In ledger | `E-WS7-001`, `E-WS8-001` | `docs/production/observability_and_incident_response.md` | CERT-In 6h runbook, Aadhaar regex sanitizer active | **CONFIRMED** |
| **G14** | Observability | `E-WS8-001` | `tests/test_observability_and_incident_response.py` | Health probes active, Aadhaar redaction verified; live metrics stack pending | **PARTIAL** |
| **G15** | Disaster recovery | `E-WS11-001` | `release/evidence/ws15/E-WS15-001_dr_drill_full.json` | Local restore RTO 0.337s; PostgreSQL/S3 restore drills pending | **PARTIAL** |
| **G16** | Accessibility | `E-WS12-001` | `tests/test_static_html_accessibility_wcag_and_gigw` | Structural HTML checks pass; screen-reader human attestation pending | **PARTIAL** |
| **G17** | Performance | `E-WS12-001` | `release/evidence/ws12/E-WS12-001_quality.json` | Rule engine p95 0.444ms (< 500ms); full HTTP load test pending | **PARTIAL** |
| **G18** | CI/CD and rollback | `E-WS10-001` | `tests/test_ci_cd_and_rollback.py` | Local rollback script verified; remote GitHub Actions execution pending | **PARTIAL** |
| **G19** | Staging acceptance | `E-WS9-001` | `scripts/verify_deployment.py` | In-process verification passed; external staging server pending | **BLOCKED** |
| **G20** | Domain and HTTPS | N/A | `release/CLAIMS.md` | Local A0 authorization limit; public domain not registered | **BLOCKED** |
| **G21** | Public content | `E-WS13-001` | `tests/test_trust_surface.py` | Disclaimers verified; operator legal entity pending in inputs | **PARTIAL** |
| **G22** | Human ownership | N/A | `docs/production/operations_runbook.md` | RACI matrix documented; named individuals pending in inputs | **PARTIAL** |
| **G23** | Test integrity | `E-WS15-001`, `E-WS15-002` | `release/evidence/ws15/E-WS15-002_canary_mutations_individual.json` | AST inventory non-weakening (+74 tests, +252 asserts); 12/12 canaries caught | **CONFIRMED** |
| **G24** | Evidence completeness | `release/CLAIMS.md` | `release/CLAIMS.md` | All 48 claims reconciled with immutable JSON evidence; zero unsubstantiated claims | **CONFIRMED** |

---

## 6. Action Packets for Human Operators

To advance Maharashtra Scheme Navigator from `INTERNAL_DEMO_READY` toward higher release tiers, the human operator must execute the following specific action packets:

### Action Packet 1: Unblock Gate G6 (Production Database)
- **Target:** Advance toward `STAGING_READY`.
- **Action:**
  1. Provision a managed PostgreSQL 15+ instance (e.g. AWS RDS, Azure Database for PostgreSQL, or local Docker daemon).
  2. Set `DATABASE_URL=postgresql://user:password@host:5432/scheme_navigator` in environment.
  3. Execute `python scripts/migrate_sqlite_to_postgres.py` to create schema and migrate data.
  4. Run `pytest tests/test_data_layer_and_storage.py` against live PostgreSQL.

### Action Packet 2: Unblock Gate G8 (Privileged MFA) & G9 (SAST/DAST)
- **Target:** Advance toward `STAGING_READY`.
- **Action:**
  1. Implement TOTP/WebAuthn two-factor authentication for `ANALYST`, `REVIEWER`, and `CATALOGUE_ADMIN` roles.
  2. Execute formal SAST tool (`bandit -r src/`) and dependency scanner (`pip-audit`).
  3. Run container vulnerability scan (`trivy image scheme-navigator:latest`).
  4. Run OWASP ZAP baseline scan against staging endpoints.

### Action Packet 3: Unblock Gate G10 (External VAPT) & G12 (Legal Counsel)
- **Target:** Advance toward `PILOT_READY`.
- **Action:**
  1. Transmit `docs/production/vapt_pack/` to a CERT-In empanelled security auditing firm.
  2. Receive independent penetration test report; remediate any high/critical findings.
  3. Engage qualified Indian legal counsel to review `docs/production/privacy_and_legal.md` and multilingual notices in `data/legal/`.

### Action Packet 4: Unblock Gate G19 (Staging Acceptance) & G20 (Domain and HTTPS)
- **Target:** Advance toward `PILOT_READY`.
- **Action:**
  1. Register official state government domain (e.g., `schemes.maharashtra.gov.in`).
  2. Configure DNS records, publish DNS CAA records, and install DigiCert/Let's Encrypt TLS certificates.
  3. Deploy container to isolated staging cluster and run `scripts/verify_deployment.py https://staging.schemes.maharashtra.gov.in`.
