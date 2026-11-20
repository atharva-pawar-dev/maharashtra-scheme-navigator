# Final Requirements Register (docs/project/final_requirements_register.md)
**Project:** Maharashtra Scheme Navigator  
**Mission ID:** MSN-FINAL-001  
**Scope Freeze Date:** 2026-11-21  
**Total Applicable Requirements (Denominator):** 55  
**Allowed States:** `NOT_STARTED`, `IN_PROGRESS`, `IMPLEMENTED`, `INTEGRATED`, `TESTED`, `ACCEPTED`, `BLOCKED`, `NOT_APPLICABLE`

---

## 1. Requirements Inventory

| Req ID | Domain | User-Facing Outcome | Backend Component | UI / Surface | State | Acceptance Test / Evidence Reference |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| **REQ-RES-01** | Research | Universe Snapshot mapping 137 authoritative bodies | `SourceRegistry` | `reviewer.html` | **ACCEPTED** | `tests/test_universe_reconciliation.py::test_universe_snapshot_integrity` |
| **REQ-RES-02** | Research | 142 candidates reconciled across 9 standard dispositions | `main.py` (`/governance/candidates`) | `reviewer.html` | **ACCEPTED** | `tests/test_universe_reconciliation.py::test_candidate_register_completeness_and_9_dispositions` |
| **REQ-RES-03** | Research | Source link health and latency audit across 135 URLs | `scripts/check_source_links.py` | CSV / Reports | **ACCEPTED** | `reports/sc_g2_source_link_health.csv` |
| **REQ-RES-04** | Research | LGD directory code mapping for 36 districts and 29 MCs | `data/research/universe/` | Documentation | **ACCEPTED** | `reports/final_lgd_reconciliation.csv` |
| **REQ-CAT-01** | Catalogue | Active catalogue serves 88 canonical schemes | `Catalog` (`schemes.json`) | `index.html` (`#view-explore`) | **ACCEPTED** | `tests/test_universe_reconciliation.py::test_canonical_catalogue_preservation_and_growth` |
| **REQ-CAT-02** | Catalogue | Quarantined demo fixture never appears in search | `SourceRegistry` | `index.html` (`#view-explore`) | **ACCEPTED** | `tests/invariants/test_trimurti_invariants.py::test_invariant_i02_demo_fixture_quarantined` |
| **REQ-CAT-03** | Catalogue | Tier A schemes have 100% verified verbatim Marathi quotes | `raw_cache.py` | `index.html` (modal factsheet) | **ACCEPTED** | `tests/test_catalogue_v2_contracts.py` |
| **REQ-CAT-04** | Catalogue | Trilingual names, descriptions and aliases for all schemes | `Catalog` | `index.html` (`#view-explore`) | **ACCEPTED** | `tests/test_playwright_sc_g2_reconciliation.py::test_03_search_marathi_alias` |
| **REQ-ELG-01** | Eligibility | Deterministic 3-valued logic rule evaluation | `RuleNode.evaluate()` | `index.html` (`#view-results`) | **ACCEPTED** | `tests/invariants/test_trimurti_invariants.py::test_invariant_i03_three_valued_logic` |
| **REQ-ELG-02** | Eligibility | Thin-rule protection fails closed to LIMITED_INFORMATION | `thin_rule_lint.py` | `index.html` (`#view-results`) | **ACCEPTED** | `tests/invariants/test_trimurti_invariants.py::test_invariant_i07_thin_rule_protection` |
| **REQ-ELG-03** | Eligibility | Unapproved rules fail closed to Caseworker Review | `attestation_store.py` | `index.html` (`#view-results`) | **ACCEPTED** | `tests/invariants/test_trimurti_invariants.py::test_invariant_i04_i06_no_definitive_verdict_without_attestation` |
| **REQ-ELG-04** | Eligibility | Transparent criteria breakdown with evidence | `explanation.py` | `index.html` (`#view-results`) | **ACCEPTED** | `tests/test_playwright_sc_g2_reconciliation.py::test_16_verify_canonical_id_reaches_backend` |
| **REQ-ONB-01** | Onboarding | Progressive multilingual conversational interview | `interviewer.py` | `index.html` (`#view-interview`) | **ACCEPTED** | `tests/test_playwright_15_citizen_journeys.py` |
| **REQ-ONB-02** | Onboarding | Typed validated profile model with confirmation flags | `CitizenProfile` | `index.html` (`#view-interview`) | **ACCEPTED** | `tests/test_playwright_five_citizen_acceptance.py` |
| **REQ-ONB-03** | Onboarding | Profile reset and edit capabilities | `main.py` (`/profile/reset`) | `index.html` (`#view-interview`) | **ACCEPTED** | `tests/test_playwright_five_citizen_acceptance.py` |
| **REQ-ONB-04** | Onboarding | Voice input transcription with text-fallback | `voice.py` | `index.html` (mic control) | **ACCEPTED** | `tests/test_voice_agent.py` |
| **REQ-LAN-01** | Language | Zero English leakage across 112 translation keys | `static/index.html` | Trilingual switcher | **ACCEPTED** | `tests/test_trilingual_parity.py` |
| **REQ-LAN-02** | Language | Dynamic Devanagari numerals (०-९) for Marathi/Hindi | `index.html` (`fmtNum()`) | Card badges & stats | **ACCEPTED** | `tests/test_trilingual_parity.py` |
| **REQ-LAN-03** | Language | Language persistence across page navigation | `localStorage` | Navigation header | **ACCEPTED** | `tests/test_playwright_sc_g2_reconciliation.py::test_04_search_hindi_alias` |
| **REQ-DIS-01** | Discovery | Trilingual search by scheme name, alias, department | `filterSchemes()` | `index.html` (`#view-explore`) | **ACCEPTED** | `tests/test_playwright_sc_g2_reconciliation.py::test_03_search_marathi_alias` |
| **REQ-DIS-02** | Discovery | Filter by department, beneficiary group, geography | `filterSchemes()` | `index.html` (Filter pills) | **ACCEPTED** | `tests/test_playwright_sc_g2_reconciliation.py::test_06_filter_by_department` |
| **REQ-DIS-03** | Discovery | Contextual advisory banner on Limited-Info schemes | `openSchemeDetail()` | `index.html` (`#modal-scheme-detail`) | **ACCEPTED** | `tests/test_playwright_sc_g2_reconciliation.py::test_11_open_limited_information_candidate` |
| **REQ-PLN-01** | Planner | Topological prerequisite dependency graph (NetworkX) | `dag.py` | `index.html` (`#view-roadmap`) | **ACCEPTED** | `tests/test_application_assistance.py` |
| **REQ-PLN-02** | Planner | Aaple Sarkar Right to Services (RTS) statutory days | `NOTIFIED_LIMIT_DAYS` | `index.html` (`#view-roadmap`) | **ACCEPTED** | `tests/test_application_assistance.py` |
| **REQ-PLN-03** | Planner | Critical path duration with unknown timeline handling | `build_application_plan` | `index.html` (`#view-roadmap`) | **ACCEPTED** | `tests/test_application_assistance.py` |
| **REQ-PLN-04** | Planner | Interactive step completion tracking | `/plans/{scheme_id}` | `index.html` (`#view-roadmap`) | **ACCEPTED** | `tests/test_playwright_15_citizen_journeys.py` |
| **REQ-DOC-01** | Documents | Safe document intake with magic-byte validation | `audit.py` (`validate_upload`) | `index.html` (`#view-documents`) | **ACCEPTED** | `tests/test_data_layer_and_storage.py` |
| **REQ-DOC-02** | Documents | Multimodal extraction across 6 distinct ingestion routes | `audit.py` | `index.html` (`#view-documents`) | **ACCEPTED** | `tests/test_rc4_document_intelligence_accuracy.py` |
| **REQ-DOC-03** | Documents | Blur variance and resolution image quality gating | `audit.py` (`detect_blur`) | `index.html` (`#view-documents`) | **ACCEPTED** | `tests/test_ocr_and_document_intelligence.py` |
| **REQ-DOC-04** | Documents | Devanagari numeral and vernacular date normalization | `audit.py` | `index.html` (`#view-documents`) | **ACCEPTED** | `tests/test_ocr_and_document_intelligence.py` |
| **REQ-AUD-01** | Audit | Scheme-specific document checklist evaluation | `audit.py` | `index.html` (`#view-documents`) | **ACCEPTED** | `tests/test_document_audit_lineage.py` |
| **REQ-AUD-02** | Audit | Mismatch detection (income, caste, expiry, unreadable) | `audit.py` | `index.html` (`#view-documents`) | **ACCEPTED** | `tests/test_document_audit_lineage.py` |
| **REQ-AUD-03** | Audit | Inline remediation and non-destructive re-upload | `citizen_store.py` | `index.html` (`#view-documents`) | **ACCEPTED** | `tests/test_immutable_audit_history.py` |
| **REQ-AUD-04** | Audit | Proportional readiness score adjustment (monotonic) | `readiness.py` | `index.html` (`#view-documents`) | **ACCEPTED** | `tests/test_rc4_retention_and_readiness_math.py` |
| **REQ-APP-01** | Handoff | Application preparation checklist with prefilled fields | `document_prep.py` | `index.html` (`#view-prepare`) | **ACCEPTED** | `tests/test_application_assistance.py` |
| **REQ-APP-02** | Handoff | Official portal URL handoff with statutory disclaimers | `channels.py` | `index.html` (`#view-prepare`) | **ACCEPTED** | `tests/test_application_assistance.py` |
| **REQ-APP-03** | Handoff | Mock application form autofill sandbox | `mock_form_worker.py` | `index.html` (`#view-prepare`) | **ACCEPTED** | `tests/test_playwright_15_citizen_journeys.py` |
| **REQ-PRG-01** | Persistence | SQLite WAL mode with immediate transaction isolation | `citizen_store.py` | Backend database | **ACCEPTED** | `tests/test_sqlite_persistence_and_replacement.py` |
| **REQ-PRG-02** | Persistence | Saved citizen progress restores across hard restart | `citizen_store.py` | `index.html` (`/progress`) | **ACCEPTED** | `tests/test_playwright_backend_restart_persistence.py` |
| **REQ-PRG-03** | Persistence | Append-only triggers protect audit history | SQLite Migration 5 | SQLite triggers | **ACCEPTED** | `tests/test_immutable_audit_history.py` |
| **REQ-GOV-01** | Governance | Reviewer review queue with RBAC authentication | `main.py` (`/governance/review-queue`) | `reviewer.html` | **ACCEPTED** | `tests/test_governance_review_queue.py` |
| **REQ-GOV-02** | Governance | Separate completeness attestation binding rule hash | `attestation_store.py` | `reviewer.html` | **ACCEPTED** | `tests/invariants/test_trimurti_invariants.py::test_invariant_i04_i06_no_definitive_verdict_without_attestation` |
| **REQ-GOV-03** | Governance | AI agent non-self-authorization enforcement (I-05) | `attestation_store.py` | `reviewer.html` | **ACCEPTED** | `tests/invariants/test_trimurti_invariants.py::test_invariant_i05_ai_agent_cannot_self_authorize` |
| **REQ-GOV-04** | Governance | Research universe and candidate dashboard tab | `main.py` (`/governance/*`) | `reviewer.html` | **ACCEPTED** | `tests/test_playwright_sc_g2_reconciliation.py::test_19_reviewer_ui_universe_intelligence_tab` |
| **REQ-ARC-01** | Architecture | Validated Pydantic v2 schemas across all API endpoints | `src/scheme_navigator/` | FastAPI OpenAPI | **ACCEPTED** | `tests/test_api_contracts.py` |
| **REQ-ARC-02** | Architecture | Rate limiting and SSRF protection on external URLs | `rate_limiter.py`, `ssrf.py`| Middleware | **ACCEPTED** | `tests/test_ssrf_and_security.py` |
| **REQ-ARC-03** | Architecture | Graceful fallback and zero unhandled HTTP 500 crashes | `main.py` | Error handlers | **ACCEPTED** | `tests/test_rc4_document_intelligence_accuracy.py` |
| **REQ-SEC-01** | Security | AST static scan clean (0 hardcoded credentials/SQLi) | `ast_scan.py` | Security test | **ACCEPTED** | `tests/test_production_security.py` |
| **REQ-SEC-02** | Security | IDOR isolation prevents cross-session record access | `auth.py` | API endpoints | **ACCEPTED** | `tests/test_auth_and_sessions_hardening.py` |
| **REQ-SEC-03** | Security | Aadhaar and sensitive PII redactor in audit logs | `audit_logger.py` | Logging handler | **ACCEPTED** | `tests/test_observability_and_incident_response.py` |
| **REQ-SEC-04** | Security | 24-hour privacy retention purge across 7 data classes | `retention.py` | Hourly worker | **ACCEPTED** | `tests/test_rc4_retention_and_readiness_math.py` |
| **REQ-VER-01** | Verification | 12/12 individual Appendix H5 mutation canaries caught | `verify_individual_canaries.py` | Test harness | **ACCEPTED** | `release/evidence/ws15/E-WS15-002_canary_mutations_individual.json` |
| **REQ-VER-02** | Verification | 25 Playwright real-browser acceptance tests pass | Playwright Chromium | Headless browser | **ACCEPTED** | `tests/test_playwright_sc_g2_reconciliation.py`, `test_playwright_five_citizen_acceptance.py` |
| **REQ-VER-03** | Verification | 635+ unit & integration tests pass with 0 regressions | Pytest | Test suite | **ACCEPTED** | `pytest tests/` |
| **REQ-VER-04** | Verification | Public citizen issue reporting flow with JSONL audit | `trust/report-issue` | `index.html` (`#modal-report-issue`) | **ACCEPTED** | `tests/invariants/test_trimurti_invariants.py::test_invariant_i17_public_issue_reporting_persistence` |

---

## 2. Requirements Completion Dashboard

- **Total Applicable Requirements (Denominator):** 55
- **Accepted Requirements:** 55
- **Implemented Requirements:** 55
- **Integrated Requirements:** 55
- **Tested Requirements:** 55
- **Blocked Requirements:** 0 (in software scope)
- **Accepted Completion Percentage:** **100.0% (55 / 55)**
