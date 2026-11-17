# Maharashtra Scheme Navigator (महाराष्ट्र योजना मार्गदर्शक)
### Independent Citizen Guidance Platform for Government Welfare Schemes

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3114/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.10+-e92063.svg)](https://docs.pydantic.dev)
[![Tests Passing](https://img.shields.io/badge/tests-441%20passed-brightgreen.svg)](docs/citizen_journey_acceptance.md)
[![Playwright](https://img.shields.io/badge/Playwright-30%20passed-green.svg)](docs/citizen_journey_acceptance.md)
[![Schemes Catalogued](https://img.shields.io/badge/canonical%20schemes-75%20covered-blue.svg)](docs/scheme_knowledge_base.md)
[![Coverage](https://img.shields.io/badge/document%20requirements-100%25-success.svg)](docs/scheme_research_coverage.md)

---

## 1. Product Overview & Core Mission
**Maharashtra Scheme Navigator** is an independent, source-grounded citizen guidance platform designed to help residents of Maharashtra:
1. **Discover Welfare Schemes**: Explore Central Government, Maharashtra State, District, and Urban Local Body (ULB) schemes across all 36 districts and 29 Municipal Corporations.
2. **Evaluate Eligibility Deterministically**: Three-valued logic (`ELIGIBLE`, `PARTIAL`, `NEEDS_INFORMATION`, `INELIGIBLE`, `NEEDS_REVIEW`) backed by an immutable Rule AST.
3. **Understand Requirements**: Transparent breakdowns showing matched conditions, failed thresholds, missing fields, and operative Government Resolutions (GRs).
4. **Intelligent Document Auditor & Preparation**: Step-by-step readiness checklists, 13-state requirement lifecycle machine, approved Maharashtra alternative documents (e.g. 15-year Ration Card for Domicile), OCR extraction auditing, and real-time readiness scoring.
5. **Scheme Factsheets & Privacy-Safe Sharing**: Instant factsheets containing verified criteria, GR references, and trilingual FAQs (English, Marathi, Hindi) without leaking citizen personal data or PII.
6. **Navigate Official Channels**: Direct routing to verified official government portals (MahaDBT, Aaple Sarkar, Ladki Bahin Portal) or designated offline civic offices (Setu Suvidha Kendra, Ward Prabhag Karyalaya, Tahsildar Office).
7. **Track Preparation Progress**: Honest personal tracking (`is_citizen_reported = True`) that preserves citizen milestones without falsely claiming official government confirmation.

> **Statutory Notice & Operational Boundary:**
> Scheme Navigator is an **independent citizen guidance platform**. It does **not** grant benefits, guarantee statutory approval, collect government portal passwords/OTPs, or represent itself as an official Government of Maharashtra agency. All formal applications must be submitted directly to the competent government authorities.

---

## 2. Definitive Release Metrics & Coverage Inventory
- **Canonical Welfare Schemes**: **75** verified records in `data/source_registry/canonical_schemes.json` (100% complete coverage with trilingual FAQs in English, Marathi, and Hindi).
- **Scheme Document Requirements**: **319** requirements catalogued across all 75 schemes in `data/source_registry/scheme_document_requirements.json` (273 mandatory, 28 conditional, 18 optional, with issuing authorities and RTS statutory limits).
- **Official Sources Tracked**: **72** authoritative sources in `data/source_registry/sources.json` with active URLs, SHA-256 digests, and retrieval timestamps.
- **Application Channel Coverage**: **75 / 75 (100%)** of schemes have verified application channels in `data/source_registry/application_channels.json`.
- **Local Government Reconciliation**:
  - **29 Municipal Corporations** (all 29 with individual ward directories).
  - **245 Municipal Councils** (214 verified Census baseline councils + 31 upgraded Class C councils post-2014 under Section 3 of the 1965 Act).
  - **150 Nagar Panchayats** (transitional urban local bodies under Section 341A).
  - **424 Total Urban Local Bodies (ULBs)** across all 36 districts.
  - **7 Central Cantonment Boards** (Ministry of Defence, Cantonments Act, 2006).
  - **34 Zilla Parishads** (all rural districts under the 1961 Act; Mumbai City & Suburban are 100% urban).
- **Automated Test Suite**: **441 passed tests** (0 failed, 0 errors, 0 skipped), including **411 unit/API tests** and **30 Playwright end-to-end browser tests**.

---

## 3. Quickstart: Local Development Setup

### 3.1 Prerequisites
- Windows 10/11, Linux, or macOS
- Python 3.11 (tested on Python 3.11.4)
- Git

### 3.2 Installation & Virtual Environment Setup
```powershell
# Navigate to the project directory
Set-Location -Path "C:\Users\Admin\Downloads\scheme-navigator\scheme-navigator"

# Activate the existing virtual environment (or create a new one)
..\.venv\Scripts\Activate.ps1

# Verify compilation
..\.venv\Scripts\python.exe -m compileall -q src tests
```

### 3.3 Running the Development Server
```powershell
..\.venv\Scripts\python.exe -m uvicorn scheme_navigator.api.main:app --host 127.0.0.1 --port 8000 --reload
```
Access the application:
- **Citizen Portal**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Explore Schemes**: [http://127.0.0.1:8000/explore](http://127.0.0.1:8000/explore)
- **Find Schemes for Me (Discovery Interview)**: [http://127.0.0.1:8000/interview](http://127.0.0.1:8000/interview)
- **Document Auditor Workspace**: [http://127.0.0.1:8000/workspace/candidate-majhi-ladki-bahin/documents](http://127.0.0.1:8000/workspace/candidate-majhi-ladki-bahin/documents)
- **Reviewer Portal**: [http://127.0.0.1:8000/reviewer.html](http://127.0.0.1:8000/reviewer.html)
- **Administrative Scheme Coverage Report**: [http://127.0.0.1:8000/admin/scheme-coverage](http://127.0.0.1:8000/admin/scheme-coverage)
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 4. Running the Verification Test Suite

### 4.1 Full Pytest Regression Suite (411 Unit & Integration Tests)
```powershell
..\.venv\Scripts\python.exe -m pytest -q --ignore=tests/test_browser_citizen_experience.py --ignore=tests/test_browser_municipal_citizen_journey.py --ignore=tests/test_browser_document_auditor_journey.py
```
Expected output:
```text
411 passed in ~40s
```

### 4.2 Browser Acceptance Tests (30 Playwright Tests)
```powershell
..\.venv\Scripts\python.exe -m pytest tests/test_browser_document_auditor_journey.py tests/test_browser_citizen_experience.py tests/test_browser_municipal_citizen_journey.py -v
```
Expected output:
```text
30 passed in ~95s
```

### 4.3 Document Requirements & Factsheets API Suite (11 Tests)
```powershell
..\.venv\Scripts\python.exe -m pytest tests/test_document_requirements_api.py -v
```

---

## 5. Key Architecture & Documentation Reference
- [Document Auditor Restoration & Citizen Journey](docs/document_auditor_restoration.md)
- [Canonical Scheme Knowledge Base](docs/scheme_knowledge_base.md)
- [Scheme Research Coverage Matrix](docs/scheme_research_coverage.md)
- [Document Requirements Inventory](docs/document_requirements_inventory.md)
- [Document Audit Workflow & State Machine](docs/document_audit_workflow.md)
- [Scheme Information Maintenance & Governance](docs/scheme_information_maintenance.md)
- [Citizen Journey Acceptance & Test Report](docs/citizen_journey_acceptance.md)
- [Local Jurisdiction Architecture](docs/local_jurisdiction_architecture.md)

---

## 6. License & Statutory Compliance
Released under the MIT License. Designed in compliance with the Maharashtra Right to Public Services Act, 2015 (RTS Act) and Digital Personal Data Protection (DPDP) Act, 2023.
