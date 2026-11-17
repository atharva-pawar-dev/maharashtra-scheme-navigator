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
| C-007 | Native PostgreSQL support across entire test suite | E-WS4-001 | REFUTED | No local PostgreSQL daemon running on port 5432. Suite executed and verified against SQLite. Gate G6 BLOCKED. |
| C-008 | Real production deployment live on public domain | NONE | REFUTED | No public cloud domain authorized or deployed (A0 local only). Gate G20 BLOCKED. |
| C-009 | All 5 core citizen journeys functional and dead-end free | E-WS2-001 | CONFIRMED | Journeys A, B, C, D, E verified via automated tests in `tests/test_journeys_and_product_integrity.py`. |
| C-010 | Deterministic evaluation functions identically with `LLM_MODE=off` (Protocol B4) | E-WS2-001 | CONFIRMED | Verified in `test_llm_off_deterministic_invariance`. |
| C-011 | Input parsing supports Devanagari numerals and Indian number grouping (lakh, crore) | E-WS2-001 | CONFIRMED | 10 distinct number/currency variations verified in `test_input_robustness_income`. |
| C-012 | 12 synthetic deterministic personas evaluate successfully | E-WS2-001 | CONFIRMED | Verified in `test_twelve_synthetic_personas_evaluation`. |
| C-013 | Agent ceiling strictly capped at `EXTRACTED`; human review cannot be simulated (Invariant B3) | E-WS3-001 | CONFIRMED | Verified in `test_invariant_b3_agent_ceiling_is_extracted`. |
| C-014 | Demo fixtures disabled in production profile | E-WS3-001 | CONFIRMED | Verified in `test_demo_fixtures_segregated_in_production` and `test_production_rejects_demo_fixtures_startup_guard`. |
| C-015 | SSRF protection rejects private IPs, loopback, metadata, userinfo, and non-HTTPS | E-WS3-001 | CONFIRMED | Verified across 4 SSRF security tests. |
| C-016 | Citizen issue reporting active with ticket tracking and structured audit logging | E-WS3-001 | CONFIRMED | Verified via `POST /trust/report-issue` in `test_citizen_report_issue_success`. |
| C-017 | Complete PostgreSQL 16+ DDL with JSONB and TIMESTAMPTZ verified in dry-run | E-WS4-001 | CONFIRMED | Verified in `test_postgres_ddl_completeness`. |
| C-018 | Live PostgreSQL cluster running and accessible locally | E-WS4-001 | REFUTED | Port 5432 unreachable; Docker not present. Gate G6 honestly recorded as BLOCKED. |
| C-019 | Private object storage enforces magic-byte headers and 15-minute signed URL ceiling | E-WS4-001 | CONFIRMED | Verified across 6 storage tests in `tests/test_data_layer_and_storage.py` using LocalStorageService. Gate G7 PARTIAL. |
| C-020 | Session tokens cryptographically signed and free of citizen PII | E-WS5-001 | CONFIRMED | Verified in `test_session_token_entropy_and_cookie_attributes`. |
| C-021 | RBAC enforces role boundaries; public role escalation strictly rejected | E-WS5-001 | CONFIRMED | Verified in `test_public_session_endpoint_rejects_privileged_role` and `test_analyst_cannot_sign_catalogue_release`. |
| C-022 | Insecure Direct Object Reference (IDOR) on interview threads blocked | E-WS5-001 | CONFIRMED | Verified in `test_citizen_cannot_answer_another_citizens_interview_thread`. |
| C-023 | Protocol C8 startup guard refuses production execution if debug, reload, weak secrets, or SQLite are configured | E-WS6-001 | CONFIRMED | Verified across 5 test scenarios in `test_c8_guard_*`. |
| C-024 | OWASP security headers enforced across all HTTP responses | E-WS6-001 | CONFIRMED | Verified in `test_security_headers_present_on_responses`. |
| C-025 | Static code security scan passes with zero high/critical vulnerabilities | E-WS6-002 | CONFIRMED | 51 files scanned, 0 secrets, 0 dangerous calls. |
| C-026 | Full VAPT readiness pack prepared for independent certified assessors | E-WS6-001 | CONFIRMED | Committed at `docs/production/vapt_pack/`. Gate G10 BLOCKED. |
| C-027 | DPDP Act 2023 & CERT-In primary-source readiness ledger documented | E-WS7-001 | CONFIRMED | Authored in `docs/production/privacy_and_legal.md`. |
| C-028 | Automated data retention purges expired sessions, temp uploads, and profiles | E-WS7-001 | CONFIRMED | Verified in `test_automated_retention_purge_execution`. |
| C-029 | Multilingual user-facing privacy and terms notices available with translation provenance | E-WS7-001 | CONFIRMED | 6 JSON documents verified in `data/legal/`. |
| C-030 | Decoupled /healthz (liveness) and /readyz (readiness) operational | E-WS8-001 | CONFIRMED | Verified in `test_liveness_probe_healthz` and `test_readiness_probe_readyz`. |
| C-031 | Audit logger sanitizes secrets and Indian Aadhaar patterns | E-WS8-001 | CONFIRMED | Verified in `test_audit_logger_redaction_canaries`. |
| C-032 | CERT-In 6-hour mandatory cyber incident response runbook documented | E-WS8-001 | CONFIRMED | Authored in `docs/production/observability_and_incident_response.md`. |
| C-033 | Hardened multi-stage Docker container runs under non-root UID 10001 with HEALTHCHECK | E-WS9-001 | CONFIRMED | Verified in `test_dockerfile_hardening` and `test_dockerignore_coverage`. |
| C-034 | Automated deployment verification script confirms /healthz, /readyz, security headers, catalogue, and sessions | E-WS9-001 | CONFIRMED | Verified in `test_in_process_deployment_verification` and `scripts/verify_deployment.py`. |
| C-035 | CI/CD pipeline enforces Gate G23 test baseline preservation and static security scan | E-WS10-001 | CONFIRMED | Verified in `test_ci_workflow_specification`. Gate G18 PARTIAL (local only). |
| C-036 | Automated rollback script supports code, catalogue, and database rollbacks with dry-run and health check | E-WS10-001 | CONFIRMED | Verified across 4 rollback tests in `tests/test_ci_cd_and_rollback.py`. |
| C-037 | Automated DR drill restores data into sandbox with 100% SHA-256 match and PRAGMA integrity | E-WS11-001 | CONFIRMED | Verified across 5 tests in `tests/test_dr_drill.py`. Gate G15 PARTIAL (SQLite only). |
| C-038 | Disaster recovery RTO verified at 0.337s (< 15 min ceiling) and RPO compliant (< 1 hour) | E-WS11-001 | CONFIRMED | Benchmarked and recorded in `release/evidence/ws11/E-WS11-001_dr_drill.json`. |
| C-039 | Static HTML templates comply with WCAG 2.1 AA and GIGW landmark standards | E-WS12-001 | CONFIRMED | Verified in `test_static_html_accessibility_wcag_and_gigw`. Gate G16 PARTIAL. |
| C-040 | Trilingual localisation (MR, HI, EN) and fallback verified across data and notices | E-WS12-001 | CONFIRMED | Verified in `test_multilingual_text_container_and_fallbacks` and `test_legal_notices_trilingual_coverage`. |
| C-041 | Deterministic rule engine evaluation p95 latency is 0.444ms (< 500ms SLA ceiling) | E-WS12-001 | CONFIRMED | Verified in `test_deterministic_rule_engine_latency_sla` and `scripts/benchmark_latency.py`. Gate G17 PARTIAL. |
| C-042 | Non-sanctioning advisory disclaimer prominently anchored across top banner, pre-assessment, and footer | E-WS13-001 | CONFIRMED | Verified in `test_top_banner_disclaimer_present` and `test_footer_independent_platform_notice`. |
| C-043 | User-facing templates free of Lorem Ipsum and mock placeholder tokens | E-WS13-001 | CONFIRMED | Verified in `test_zero_lorem_ipsum_or_forbidden_mock_tokens`. Gate G21 PARTIAL. |
| C-044 | Citizen issue reporting active with ticket generation and trilingual acknowledgement | E-WS13-001 | CONFIRMED | Verified in `test_trust_issue_reporting_integration`. |
| C-045 | Operations runbooks cover deployments, CERT-In incidents, secret rotations, and RACI matrix | E-WS14-001 | CONFIRMED | Authored and committed in `docs/production/operations_runbook.md`. Gate G22 PARTIAL. |
| C-046 | AST test inventory strictly non-weakening (2,154 assertions, 472 tests vs 1,902 / 398 baseline; +252 assertions) | E-WS15-001 | CONFIRMED | Verified in `scripts/ast_test_inventory.py` with exit code 0. Gate G23 PASS. |
| C-047 | All 12/12 Protocol H5 canary mutations directly executed and caught against real codebase | E-WS15-002 | CONFIRMED | Verified in `scripts/verify_individual_canaries.py` and `release/evidence/ws15/E-WS15-002_canary_mutations_individual.json`. All 12 mutated rc=1, restored rc=0. Gate G23 PASS. |
| C-048 | Mechanically computed release state is INTERNAL_DEMO_READY under canonical Part E rules | E-WS15-003 | CONFIRMED | Documented in `docs/production/release_gates_and_decision.md` (8 PASS, 11 PARTIAL, 5 BLOCKED, 0 NOT_APPLICABLE; G1, G2, G3, G5, G23 PASS; higher tiers blocked). |
| C-049 | Privileged Multi-Factor Authentication (MFA) implemented and enforced | NONE | REFUTED | Privileged MFA is absent and unexecuted. Gate G8 recorded honestly as PARTIAL. |
| C-050 | Formal SAST, DAST, and container security vulnerability scans executed | NONE | REFUTED | Formal Bandit, OWASP ZAP, pip-audit, and Trivy scans unexecuted. Gate G9 recorded honestly as PARTIAL. |
| C-051 | Live metrics collection and Alertmanager real-time alerting active on cluster | NONE | REFUTED | Live Prometheus/Grafana stack and live alerting unexecuted. Gate G14 recorded honestly as PARTIAL. |
