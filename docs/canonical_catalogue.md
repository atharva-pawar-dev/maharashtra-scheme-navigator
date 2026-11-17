# Canonical Scheme Catalogue Architecture & Publication Governance

## 1. Executive Summary & Authoritative Role
The **Canonical Scheme Catalogue** (`data/source_registry/canonical_schemes.json`) is the single authoritative source of truth for all citizen journeys across the Maharashtra Scheme Navigator. It powers:
- **Explore Schemes**: Statewide and local municipal scheme discovery, filtering, and search.
- **Find Schemes for Me**: Adaptive AI and rule-driven citizen interviews.
- **Focused Scheme Assessment**: Dedicated scheme eligibility checks and prerequisite analysis.
- **Results**: Scoreboard-driven evaluation outcomes (`ELIGIBLE`, `PARTIAL`, `NEEDS_INFORMATION`, `INELIGIBLE`, `NEEDS_REVIEW`).
- **My Progress**: Application document preparation checklists, task tracking, and milestone logging.
- **Application Channel Navigation**: Authoritative routing to official government portals and designated offline offices.

Every scheme record is governed by strict schema validation, referential integrity, and verifiable statutory provenance.

---

## 2. Canonical Scheme Schema (`CanonicalSchemeRecord`)
All canonical scheme records conform to the Pydantic v2 domain model (`scheme_navigator.source_registry.models.CanonicalSchemeRecord`).

### Key Fields & Statutory Attributes:
| Attribute | Type | Description |
|---|---|---|
| `canonical_scheme_id` | `str` | Unique, permanent scheme identifier (e.g., `scheme-pm-svanidhi`, `candidate-majhi-ladki-bahin`, `pmc-shahari-garib-arogya`). |
| `official_scheme_name` | `str` | Authoritative official name as published in Government Resolutions (GR) or Gazettes. |
| `english_name` | `str` | Standardized English nomenclature. |
| `marathi_name` | `str` | Official Marathi name (देवनागरी). |
| `hindi_name` | `str` | Official Hindi name. |
| `responsible_department` | `str` | Administering Government of Maharashtra or Central Ministry department. |
| `implementing_authority` | `str` | Operational agency, directorate, or local body responsible for scheme execution. |
| `funding_type` | `str` | `CENTRAL_FUNDED`, `STATE_FUNDED`, `MUNICIPAL_FUNDED`, or `JOINT_STATE_CENTRAL`. |
| `jurisdiction_scope` | `str` | Statutory geographic level (`CENTRAL`, `MAHARASHTRA_STATE`, `DIVISION`, `DISTRICT`, `MUNICIPAL_CORPORATION`, `MUNICIPAL_COUNCIL`, `NAGAR_PANCHAYAT`, `GRAM_PANCHAYAT`, `ZILLA_PARISHAD`, `WARD`, `SPECIAL_AREA`, `CANTONMENT_BOARD`). |
| `jurisdiction_ids` | `list[str]` | Canonical jurisdiction tokens defining statutory eligibility scope (e.g., `["jurisdiction:mc:mc-pune"]`). |
| `included_local_bodies` | `list[str]` | Explicit list of eligible local bodies or districts. |
| `excluded_local_bodies` | `list[str]` | Explicit list of excluded local bodies or districts. |
| `required_residency_years` | `int \| None` | Statutory minimum continuous residence required within the administering local body (e.g., 3 years for PMC, 3 years for PCMC). |
| `publication_status` | `str` | Verification status (`VERIFIED_FOR_INFORMATION`, `PUBLISHED`, `REVIEW_REQUIRED`, `POLICY_UNRESOLVED`, `ACTIVE_DEMO_FIXTURE`). |
| `lifecycle_status` | `str` | Lifecycle phase (`VERIFIED_FOR_INFORMATION`, `DEMO_ONLY`, `REVIEW_REQUIRED`, `POLICY_UNRESOLVED`). |
| `rule_version` | `str` | Semantic rule version (e.g., `1.0.0`). |
| `required_documents` | `list[str]` | Statutory checklist of mandatory documents backed by operative GRs. |
| `optional_documents` | `list[str]` | Supplementary or alternative documents. |
| `government_source_references` | `list[str]` | Operative GR computer codes, official gazette numbers, and primary portal URLs. |

---

## 3. Scheme Inventory & Classification Breakdown
As of the current release candidate, the Canonical Catalogue contains **75 verified schemes**:

### 3.1 Breakdown by Geographic Jurisdiction Scope
| Jurisdiction Scope | Count | Representative Examples |
|---|---|---|
| `MAHARASHTRA_STATE` | 55 | Mukhyamantri Majhi Ladki Bahin, Sanjay Gandhi Niradhar Anudan, Shravanbal Seva, MJPJAY, Post-Matric SC/OBC Scholarships, Dr. Punjabrao Deshmukh Hostel Allowance |
| `MUNICIPAL_CORPORATION` | 13 | PMC Shahari Garib Arogya, PMC Maulana Azad Scholarship, PCMC Free Bicycle, PCMC MS-CIT Women, BMC Anand Dighe Divyang, TMC Divyang Kalyan, NMMC Divyang Grant |
| `CENTRAL` (All-Maharashtra Applicable) | 5 | PM SVANidhi (Street Vendors), PM Surya Ghar Muft Bijli, PM Vishwakarma, PM-KISAN, Ayushman Bharat PM-JAY |
| `MUNICIPAL_COUNCIL` | 1 | Swachh Maharashtra Urban Sanitation & Livelihood Scheme |
| `GRAM_PANCHAYAT` | 1 | Zilla Parishad Shetkari Sheti Shala & Farmer Field School Grant |
| **Total** | **75** | **100% Validated against Canonical Scheme Record Schema** |

### 3.2 Breakdown by Publication & Lifecycle Status
| Publication Status | Count | Description & Handling |
|---|---|---|
| `VERIFIED_FOR_INFORMATION` | 51 | Primary government source acquired, rules extracted and verified against operative notifications. Available in Explore, Discovery, and Results. |
| `PUBLISHED` | 15 | Formally authorized schemes with complete evidence and non-demo approval metadata. |
| `REVIEW_REQUIRED` | 5 | Newly extracted candidate schemes pending secondary human legal verification (e.g., tuition fee reimbursement revisions). |
| `POLICY_UNRESOLVED` | 2 | Schemes with pending policy questions (e.g., income threshold reconciliation between Group A and Group B in Shravanbal). |
| `ACTIVE_DEMO_FIXTURE` | 2 | Explicitly labeled development fixtures (`demo-majhi-ladki-bahin`, `demo-indira-gandhi-old-age-pension`). Strictly isolated from production publication. |
| **Total** | **75** | |

---

## 4. Separation of Concepts
To prevent data contamination, Scheme Navigator enforces strict boundary separation across related public administration concepts:
1. **Schemes vs. Public Services**: Public services (such as obtaining an Income Certificate or Domicile Certificate from Aaple Sarkar RTS) are modeled separately in `data/source_registry/public_services.json` as **prerequisites**, never as independent welfare schemes.
2. **Schemes vs. Application Channels**: Application portals (e.g., MahaDBT, Aaple Sarkar, PCMC Sarathi) are tracked in `data/source_registry/application_channels.json`, ensuring clear decoupling between statutory eligibility rules and submission mechanics.
3. **Schemes vs. Civic Services**: Routine civic municipal services (water connections, property tax payments, birth certificates) are excluded from the welfare scheme catalogue.

---

## 5. Production vs. Demo Isolation
Scheme Navigator guarantees that demo fixtures cannot contaminate production workflows:
1. **Fail-Closed Production Gate**: When `APP_ENV=production`:
   - Demo fixtures (`demo-*`) return `status="NEEDS_REVIEW"` with the explicit reason: *"This rule is a demo fixture or lacks non-demo approval metadata. Eligibility cannot be confirmed."*
   - Untrusted external catalogue files without valid digital signatures are rejected (`CatalogLoadError`).
   - If the catalogue is missing or inaccessible, the application fails closed with HTTP 503 (`Catalogue unavailable`), never falling back silently to demo fixtures.
2. **Explicit Labeling**: In local development (`APP_ENV=local`), demo records are explicitly marked with `ACTIVE_DEMO_FIXTURE` badges on the frontend and API responses.
3. **Cryptographic Release Signing**: Catalogue releases can be signed using `POST /admin/catalogue/sign-release` with a 64-byte HMAC key, verifying tamper-proof integrity before deployment.

---

## 6. Cross-Journey Consistency Invariant
The same canonical record powers all citizen interactions:
- When a user views a scheme in **Explore Schemes** (`GET /canonical-schemes/{id}`),
- When the scheme is evaluated during **Find Schemes for Me** (`POST /interview/answer`),
- When tested under **Focused Assessment** (`POST /interview/start` with `mode="FOCUSED_SCHEME"`),
- When displayed on the **Results Scoreboard** (`POST /eligibility/evaluate`), and
- When tracked in **Prepare My Application** (`GET /channels/{id}`),

it references the exact same canonical ID, eligibility AST, document checklist, and source provenance. Automated consistency tests (`test_canonical_catalog_cross_journey_consistency`) verify this invariant continuously.
