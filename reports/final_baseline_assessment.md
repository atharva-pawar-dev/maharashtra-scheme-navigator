# Final Baseline Assessment (reports/final_baseline_assessment.md)
**Project:** Maharashtra Scheme Navigator  
**Mission ID:** MSN-FINAL-001  
**Generated:** 2026-11-21T01:25:00+05:30  
**Governing Standard:** TRIMURTI v4 Project Completion & Production Readiness Specification  
**Current Baseline Commit:** `9d14a2f` (Tag: `sc-g2-accepted`)  
**Active Branch:** `feat/catalogue-v2`  
**Execution Authorization:** Level A0 (Local Developer Sandbox, Python 3.11, SQLite 3.x, Headless Chromium)

---

## 1. Executive Baseline Summary

Maharashtra Scheme Navigator has progressed through releases RC1 to RC4 and TRIMURTI milestones SC-M0, SC-G1, and SC-G2.
The core software architecture comprises:
- **Backend Application:** FastAPI (`src/scheme_navigator/api/main.py`) serving citizen APIs, document auditor, eligibility engine, planner, and reviewer governance endpoints.
- **Frontend Application:** Modern vanilla HTML5/ES6 application (`static/index.html`) serving 7 operational views (`view-home`, `view-explore`, `view-interview`, `view-results`, `view-documents`, `view-roadmap`, `view-prepare`) and 5 interactive modals (`modal-scheme-detail`, `modal-scheme-factsheet`, `modal-report-issue`, `modal-confirm`, `modal-content`).
- **Reviewer Dashboard:** Dedicated governance portal (`static/reviewer.html`) providing review queues, evidence audit, candidate reconciliation, and official authority browsing.
- **Persistence Layer:** SQLite 3 WAL-mode database (`data/ingestion.sqlite3`) with schema migrations 1–5, append-only triggers, immutable audit tables, and hard-restart durability.
- **Deterministic Rule Engine:** JSON Logic / typed AST evaluation (`src/scheme_navigator/domain/rules.py` and `rule_engine.py`) with 3-valued logic (`TRUE`, `FALSE`, `UNKNOWN`), Thin-Rule protection (Invariant I-07), and fail-closed gate enforcement (Invariants I-04 & I-05).
- **Document Intelligence:** Multi-route extraction (Searchable PDF, Scanned PDF, Mobile Photo, Image Scan) with Tesseract OCR, Laplacian blur detection, resolution minimums, Devanagari numeral normalization, and proportional readiness math.
- **Prerequisite Planner:** Directed Acyclic Graph (`src/scheme_navigator/planner/dag.py`) computing topological order, critical path timelines, and statutory Aaple Sarkar RTS notification limits.
- **Application Preparation & Handoff:** Mock application form worker (`src/scheme_navigator/workers/mock_form_worker.py`) demonstrating safe autofill without unauthorized automated submission.

---

## 2. Technical Layer Forensics & Feature Classification

| Capability / Subsystem | Primary Code Location | Frontend Integration | Persistence & State | Verification Status | Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Multilingual Citizen Onboarding** | `src/scheme_navigator/agents/interviewer.py` | `static/index.html` (`#view-interview`) | SQLite `citizen_profiles`, `interview_sessions` | 25 Playwright tests, 613 unit tests | **Implemented & Working** |
| **Trilingual Scheme Discovery** | `src/scheme_navigator/services/catalog.py` | `static/index.html` (`#view-explore`) | `data/catalogue/schemes.json` (88 schemes) | Tested in Chromium (EN, MR, HI) | **Implemented & Working** |
| **Deterministic Eligibility Engine** | `src/scheme_navigator/domain/rules.py` | `static/index.html` (`#view-results`) | In-memory evaluation + SQLite session | Invariant tests I-02, I-03, I-04, I-07 | **Implemented & Working** |
| **Prerequisite & Dependency Planner** | `src/scheme_navigator/planner/dag.py` | `static/index.html` (`#view-roadmap`) | NetworkX DAG + `/plans/{id}` API | API verified, DAG cycle tests pass | **Implemented & Working** |
| **Document Intake, OCR & Audit** | `src/scheme_navigator/documents/audit.py` | `static/index.html` (`#view-documents`) | SQLite `stored_documents`, `document_audit_lineage` | 64/64 field ground truth test, 6 routes | **Implemented & Working** |
| **Remediation & Proportional Readiness** | `src/scheme_navigator/documents/readiness.py`| `static/index.html` (`#view-documents`) | Dynamic score calculation ($N \to N-1$) | Mathematical tests pass (100% $\to$ 80%) | **Implemented & Working** |
| **Application Preparation & Mock Handoff** | `src/scheme_navigator/workers/mock_form_worker.py` | `static/index.html` (`#view-prepare`) | Profile prefill + mock portal endpoint | Playwright handoff tests | **Implemented & Working** |
| **Saved Progress & Resume** | `src/scheme_navigator/core/citizen_store.py` | `static/index.html` (`/progress`) | SQLite WAL transactions | Backend restart persistence tests pass | **Implemented & Working** |
| **Reviewer Governance & Queue** | `src/scheme_navigator/governance/attestation_store.py` | `static/reviewer.html` | SQLite `scheme_completeness_attestations` | RBAC and non-self-authorization tested | **Implemented & Working** |
| **Public Citizen Issue Reporting** | `src/scheme_navigator/api/main.py` (`/trust/report-issue`) | `static/index.html` (`#modal-report-issue`) | JSONL ledger `data/citizen_reports.jsonl` | Playwright trilingual report submission test | **Implemented & Working** |
| **Universe Snapshot & Authority Inventory** | `src/scheme_navigator/source_registry/` | `static/reviewer.html` (Universe Tab) | `data/research/universe/U-20261120.json` | 7 unit tests (`test_universe_reconciliation.py`) | **Implemented & Working** |
| **Bhashini / Whisper Voice Integration** | `src/scheme_navigator/agents/voice.py` | `static/index.html` (Mic button) | Ephemeral audio stream | Mock provider tests pass; Live provider unconfigured | **Tested with Mocks (Fallback Working)** |
| **External Live Portal Autofill** | `src/scheme_navigator/workers/mock_form_worker.py` | `static/index.html` (`#view-prepare`) | External MahaDBT / Aaple Sarkar | Sandbox mock verified; live portals gated by OTP/CAPTCHA | **Tested with Mocks (Safe Boundary)** |
| **Production PostgreSQL 15+ Execution**| `docs/production/postgres_schema.sql` | N/A (Backend DB adapter) | SQLite used locally (Level A0) | SQLite verified; PostgreSQL daemon absent locally | **Blocked (Authorization Level A0)** |
| **External Certified VAPT** | `docs/production/vapt_pack/` | N/A (Operational security) | Threat model documented | Static AST scan clean; external audit pending | **Blocked (Authorization Level A0)** |
| **Independent Legal Counsel Sign-off** | `docs/production/privacy_and_legal.md` | N/A (Compliance) | Crosswalk documented | Requires Bar-certified Indian legal counsel | **Blocked (External Human Sign-off)** |

---

## 3. Findings & Identified Gaps for Resolution in TRIMURTI v4

1. **Candidate Accounting Discrepancy:**
   - Previous human text reported 141 sum (17+71+18+6+8+6+5+7+3).
   - Forensic physical row analysis proves 142 total candidates: `DUPLICATE_OF` contains 9 records (`CAND-075` demo fixture + 8 duplicate portal records), not 8.
   - Complete reconciliation register and documentation must formalize this truthful 142 count.
2. **Frozen Score Reproduction:**
   - Frozen Scorer v1 (`1.0.0-sc-g1`) evaluates the 88 canonical schemes against 40 target departments to **76.65 / 100**.
   - An earlier report cited 78.88 based on preliminary unadjusted denominators before the 14 candidates expanded dimensions 4 and 5.
   - The discrepancy must be documented openly and truthfully without altering frozen scorer weights or formulas.
3. **Local Government Directory (LGD) Codification:**
   - The 29 Municipal Corporations and 36 District Collectorates in Snapshot `U-20261120.json` require explicit reconciliation against official MoHUA / LGD directory standards (`reports/final_lgd_reconciliation.csv`).
4. **End-to-End Persona Journey Suite:**
   - Build comprehensive Playwright acceptance covering all 10 synthetic citizen personas (Farmer, Student, Senior Citizen, Woman, Divyang, Urban, Rural, Incomplete, Conflicting, Ineligible) across Journeys A through J.
