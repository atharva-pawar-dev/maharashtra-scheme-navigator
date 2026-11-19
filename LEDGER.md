# Release Gates Ledger (LEDGER.md)
**Project:** Maharashtra Scheme Navigator  
**Last Updated:** 2026-11-19T23:15:00+05:30  
**Governing Standard:** Production Release Program v2.0 (Part E1, E2)  
**Milestone:** RC4 — Real-World Document Intelligence & Citizen Trust Acceptance

---

## 1. Master Release Gate Status Table

| Gate ID | Gate Name | Classification | Primary Evidence Reference | Verification Date | Summary of Audit Finding |
| :---: | :--- | :---: | :--- | :---: | :--- |
| **G1** | Citizen journeys | **PASS** | `reports/final_citizen_journey_evidence.json`, `test_playwright_15_citizen_journeys.py`, `test_trilingual_parity.py` | 2026-11-19 | All 15 citizen journeys (J01–J15) pass end-to-end in real Chromium across EN, MR, HI, with 1-of-2 mandatory checks and SQLite persistence. |
| **G2** | Document auditor | **PASS** | `reports/rc4_document_intelligence_accuracy.md`, `tests/test_rc4_document_intelligence_accuracy.py`, `tests/test_ocr_and_document_intelligence.py` | 2026-11-19 | Complete Document Auditor lifecycle: 6 ingestion routes, 100% field-level accuracy (64/64 matches vs ground truth), image quality gates (blur/resolution/contrast), Devanagari numerals, and zero HTTP 500 crashes via resilient local fallback. |
| **G3** | Catalogue integrity | **PASS** | `data/catalogue/schemes.json`, `schemas/catalogue_v2.json`, `tests/test_catalogue_v2_contracts.py` | 2026-11-19 | 75 schemes validate against schema (74 canonical + 1 demo fixture). Demo fixture physically quarantined from production discovery. |
| **G4** | Scheme accuracy | **PARTIAL** | `data/raw/`, `docs/catalogue/catalogue_integrity_audit.md`, `docs/quality/scheme_diverse_document_coverage.md` | 2026-11-19 | All 17 Tier A schemes have 100% verified verbatim Marathi quotes matching official GRs. Agent ceiling is `EXTRACTED`; named departmental human sign-offs pending. |
| **G5** | Application handoff | **PASS** | `tests/test_application_assistance.py`, `tests/test_rc4_scheme_diverse_e2e_journeys.py`, `docs/application_channels.md` | 2026-11-19 | External official portal links verified across all 74 canonical schemes and 12 representative families; statutory advisory disclaimers displayed prominently. |
| **G6** | Production database | **BLOCKED** | `docs/production/postgres_schema.sql` | 2026-11-19 | PostgreSQL schema and migration engine authored; local PostgreSQL daemon absent on port 5432 under A0 authorization. |
| **G7** | Document storage | **PARTIAL** | `src/scheme_navigator/security/storage.py`, `tests/test_data_layer_and_storage.py` | 2026-11-19 | Storage abstraction enforces magic-byte validation, 15-minute signed URL expiry, and hourly purge. Local filesystem tested; live AWS S3 drill pending. |
| **G8** | AuthN / AuthZ | **PARTIAL** | `tests/test_auth_and_sessions_hardening.py` | 2026-11-19 | Anonymous HMAC-SHA256 session tokens, 4-tier RBAC, role escalation guards, and IDOR isolation verified. Privileged MFA not implemented. |
| **G9** | Internal security verification | **PARTIAL** | `src/scheme_navigator/security/ast_scan.py`, `tests/test_production_security.py` | 2026-11-19 | AST static scan clean (0 hardcoded credentials, 0 `eval`/`exec`, 0 dynamic SQL). Formal DAST, container scanning, and third-party SAST pending. |
| **G10** | External VAPT | **BLOCKED** | `docs/production/vapt_pack/` | 2026-11-19 | VAPT readiness pack and threat model documented. External certified pen-testing firm not engaged under local A0 environment. |
| **G11** | Privacy implementation | **PASS** | `reports/rc4_retention_and_privacy_audit.md`, `tests/test_rc4_retention_and_readiness_math.py`, `tests/test_document_retention_and_readiness.py` | 2026-11-19 | DPDP staged commencement facts clarified; 24-hr privacy retention ceiling governed under IT SPDI Rules 2011; 7 data classes defined; proportional readiness drops (4/5 = 80%). |
| **G12** | Legal review | **BLOCKED** | `docs/production/privacy_and_legal.md` | 2026-11-19 | Legal and regulatory crosswalk authored; independent Indian legal counsel sign-off pending. |
| **G13** | DPDP / CERT-In ledger | **PASS** | `tests/test_immutable_audit_history.py`, `docs/production/observability_and_incident_response.md` | 2026-11-19 | Append-only SQLite triggers prevent historical tampering; 6-hour CERT-In incident reporting runbook documented. |
| **G14** | Observability | **PARTIAL** | `src/scheme_navigator/security/audit_logger.py`, `tests/test_observability_and_incident_response.py` | 2026-11-19 | Health/readiness probes and structured JSON audit logging with Aadhaar redaction operational. Live Prometheus/Grafana stack pending. |
| **G15** | Disaster recovery | **PARTIAL** | `scripts/dr_drill.py`, `release/evidence/ws15/E-WS15-001_dr_drill_full.json` | 2026-11-19 | Automated SQLite restore drill achieves 0.337s RTO and 100% SHA-256 match. Live PostgreSQL/S3 cluster drill pending. |
| **G16** | Accessibility | **PARTIAL** | `tests/test_browser_citizen_experience.py` | 2026-11-19 | High-contrast CSS mode, semantic landmarks, ARIA attributes, and touch target minimums pass automated checks. Human screen-reader audit pending. |
| **G17** | Performance | **PARTIAL** | `tests/test_rule_boundary_matrix.py` | 2026-11-19 | Rule engine benchmarked at p95 0.444ms (< 500ms target). Full HTTP load test under 150 concurrent sessions pending. |
| **G18** | CI/CD and rollback | **PARTIAL** | `.github/workflows/ci.yml`, `scripts/rollback.py`, `tests/test_ci_cd_and_rollback.py` | 2026-11-19 | Local rollback script verified across code, catalogue, and SQLite databases. Remote GitHub Actions run pending. |
| **G19** | Staging acceptance | **BLOCKED** | `scripts/verify_deployment.py` | 2026-11-19 | Local deployment verification passed; remote staging environment not provisioned under A0 authorization. |
| **G20** | Domain and HTTPS | **BLOCKED** | `src/scheme_navigator/api/main.py` | 2026-11-19 | HTTPS cookie flags and TLS redirects configured; public domain registration and live DNS/CAA records pending. |
| **G21** | Public content and contacts | **PARTIAL** | `reports/rc4_multilingual_acceptance.md`, `tests/test_trilingual_parity.py` | 2026-11-19 | 112 translation keys verified across EN, MR, HI with zero English leakage and native Devanagari numerals. Department contact identity pending in `OPERATOR_INPUTS.yaml`. |
| **G22** | Human ownership | **PARTIAL** | `docs/production/operations_runbook.md` | 2026-11-19 | RACI matrix defined for 5 operational roles; named human personnel assignments pending. |
| **G23** | Test integrity | **PASS** | `release/evidence/ws15/E-WS15-002_canary_mutations_individual.json` | 2026-11-19 | Non-weakening test suite verified (**613 tests passing, 0 failed**); **12/12 individual Appendix H5 canaries caught on real codebase**. |
| **G24** | Evidence completeness | **PASS** | `reports/rc4_final_acceptance_report.md`, `reports/rc4_scheme_diverse_journey_evidence.json` | 2026-11-19 | All claims reconciled against immutable test runs and JSON records; zero unsubstantiated claims. |
