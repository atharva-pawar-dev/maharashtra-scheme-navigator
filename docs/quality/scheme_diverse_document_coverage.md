# Scheme-Diverse Document Requirement Coverage & Readiness Architecture
## Forensic Coverage Matrix Across 12 Canonical Maharashtra Scheme Families

**Status:** AUDITED & VERIFIED  
**Release Target:** RC3 Hardening (`rc3-hardened`)  
**Specification Reference:** Production Release Program v2.0 (Part 2 — Scheme-Diverse Document Coverage)  
**Authoritative Source Baseline:** `data/source_registry/scheme_document_requirements.json`, `data/source_registry/canonical_schemes.json`

---

## 1. Executive Summary

This deliverable establishes that document preparation, validation, and readiness in Maharashtra Scheme Navigator extend across a comprehensive cross-section of schemes beyond `MHA-S-0001`. The document architecture supports 12 representative scheme families covering pensions, scholarships, agriculture, housing, healthcare, assistive devices, and self-employment loans.

Every scheme in this cross-section is mapped through dual identifiers:
1. **Alphanumeric Canonical Alias:** `MHA-S-0001` through `MHA-S-0018`.
2. **Statutory Canonical Identifier:** e.g., `candidate-sanjay-gandhi-niradhar-anudan`, `scheme-bhausaheb-fundkar-phalbag`.

The engine dynamically evaluates mandatory, conditional, and optional document requirements, accommodates approved statutory alternative documents (ANY_OF groups), assesses source freshness, detects unreadable or expired certificates, and persists citizen attachments across backend restarts in SQLite.

---

## 2. Representative 12 Scheme Families Matrix

| Alphanumeric Alias | Canonical ID | Scheme Family & Title | Department | Primary Required Documents | Conditional & Alternative Logic |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MHA-S-0001** | `candidate-sanjay-gandhi-niradhar-anudan` | Income-tested Pension (SGNAY) | Social Justice & Special Assistance | 1. Maharashtra Domicile / 15-Yr Residence<br>2. Tahsildar Income Certificate (<= ₹21,000 / ₹50,000)<br>3. Age Proof (School Leaving / Birth Cert)<br>4. Aadhaar Card | **Conditional:** Medical Disability Certificate (Civil Surgeon, 40%+) if claiming under Divyang category.<br>**Optional:** PDS Ration Card. |
| **MHA-S-0002** | `demo-indira-gandhi-old-age-pension` | National Old Age Pension (IGNOAPS) | Social Justice & Special Assistance | 1. Age Proof (60+ Years)<br>2. BPL Ration Card / BPL Survey Inclusion<br>3. Aadhaar Card<br>4. Bank Account Passbook | **ANY_OF:** BPL survey inclusion or valid Yellow BPL Ration Card satisfies poverty criterion. |
| **MHA-S-0003** | `candidate-majhi-ladki-bahin` | Women Direct Benefit Transfer (MMLBY) | Women & Child Development | 1. Aadhaar Card<br>2. Maharashtra Domicile Certificate<br>3. Income Certificate (<= ₹2.5L)<br>4. Aadhaar-Seeded Bank Passbook | **ANY_OF Approved Alternatives:**<br>- Domicile: 15-Yr Ration Card, Voter ID, Birth Cert, or School Leaving Cert (GR 3 July 2024).<br>- Income: Yellow/Orange Ration Card exempts separate income certificate. |
| **MHA-S-0004** | `candidate-shravanbal-sewa-rajya-nivruttivetan` | State Senior Citizen Pension | Social Justice & Special Assistance | 1. Maharashtra Domicile (15+ Years)<br>2. Age Proof (65+ Years)<br>3. Tahsil Income Certificate (<= ₹21,000)<br>4. Aadhaar-Linked Bank Passbook | **Conditional:** Category A requires BPL survey inclusion; Category B accepts Tahsildar income certificate. |
| **MHA-S-0006** | `scheme-igndps-disability-pension` | Severe Disability Pension (IGNDPS) | Social Justice & Special Assistance | 1. Disability Certificate (80%+ or Multiple Disabilities)<br>2. BPL Certificate / Family BPL List<br>3. Age Proof (18-79 Years)<br>4. Aadhaar Card | **Conditional:** Disability certificate must be issued by District Medical Board or verified via Swavlamban UDID portal. |
| **MHA-S-0007** | `scheme-divyang-motorized-tricycle` | Disability Assistive Devices | Social Justice & Special Assistance | 1. UDID / Civil Surgeon Disability Certificate (40%+)<br>2. Maharashtra Domicile Certificate<br>3. Income Certificate (<= ₹5,00,000)<br>4. Aadhaar Card | **Conditional:** Orthopedic disability affecting lower limbs required; certificate must specify locomotor impairment. |
| **MHA-S-0008** | `candidate-post-matric-sc` | Post-Matric Scholarship (SC) | Social Justice & Special Assistance | 1. Caste Certificate (SC Category)<br>2. Tahsildar Income Certificate (<= ₹2.5L)<br>3. Maharashtra Domicile Certificate<br>4. Previous Year Marksheet<br>5. College Fee Receipt | **Conditional:** Caste Validity Certificate required for degree/professional courses (Maharashtra Act XXIII of 2001). |
| **MHA-S-0010** | `scheme-ebc-tuition-waiver` | Higher Education Fee Waiver (RCSM EBC) | Higher & Technical Education | 1. Tahsildar Income Certificate (<= ₹8.0L)<br>2. Maharashtra Domicile Certificate<br>3. CAP Admission Allotment Letter<br>4. College Fee Receipt<br>5. Self-Declaration (Hamipatra) | **Conditional:** Only for non-reserved (General / SEBC / Open) categories whose family income is <= ₹8 Lakhs. |
| **MHA-S-0015** | `scheme-bhausaheb-fundkar-phalbag` | Farmer Landholding Support (Phalbag) | Agriculture Department | 1. Mahabhulekh 7/12 Land Extract<br>2. 8-A Land Extract (Khate Utara)<br>3. Aadhaar Card<br>4. Aadhaar-Linked Bank Account<br>5. Soil & Water Test Report | **Mandatory Landholding:** 7/12 extract must reflect farmer ownership in Maharashtra (minimum 0.20 Ha up to 6.0 Ha). |
| **MHA-S-0016** | `scheme-ramai-awas-yojana` | Housing Assistance (Ramai Gharkul) | Social Justice & Special Assistance | 1. Caste Certificate (SC / Neo-Buddhist)<br>2. Maharashtra Domicile Certificate<br>3. BPL Card or Income Proof (<= ₹1.0L rural / ₹3.0L urban)<br>4. Own Land / Kutcha House Ownership Document | **Conditional:** Self-declaration of not owning any pucca house in Maharashtra under any other government housing scheme. |
| **MHA-S-0017** | `scheme-mjpjay-ayushman-bharat` | Universal Health Insurance (MJPJAY) | Public Health Department | 1. Valid Ration Card (Yellow, Orange, or White)<br>2. Aadhaar Card | **ANY_OF:** Ayushman Bharat PM-JAY Golden Card or Maharashtra Ration Card provides automatic cashless empaneled coverage. |
| **MHA-S-0018** | `scheme-annasaheb-patil-ir2` | Self-Employment Loan Scheme (IR-II) | Skill Development & Entrepreneurship | 1. Aadhaar Card<br>2. Maharashtra Domicile Certificate<br>3. Bank Loan Sanction Letter<br>4. Business Project Report / Udyam Aadhar<br>5. Age Proof (18-45 Years Male, 18-50 Female) | **Conditional:** Applicable to Maratha / economically weaker non-reserved entrepreneurs with bank-sanctioned enterprise loans up to ₹15 Lakhs. |

---

## 3. Statutory Alternative Document (ANY_OF) Architecture

The application implements the statutory alternative document rules defined in Maharashtra Government Resolutions:

```
                            [ Statutory Requirement: Domicile ]
                                           |
         +---------------------------------+---------------------------------+
         |                                 |                                 |
   [ Direct Match ]               [ Statutory Alternative ]       [ Statutory Alternative ]
Maharashtra Domicile             15-Year PDS Ration Card              Voter Identity Card
    Certificate                 (GR Sankirna-2024/CR137)           (GR 3 July 2024 Amendment)
         |                                 |                                 |
   State: MATCHED              State: ALTERNATIVE_MATCHED        State: ALTERNATIVE_MATCHED
```

When a citizen lacks a primary certificate, uploading an approved alternative automatically satisfies the requirement, annotating the audit report with statutory basis (`statutory_basis`) and issuing authority details.

---

## 4. Verification & Testing Evidence

All 12 scheme families were systematically audited via automated regression tests:
- **Suite:** `tests/test_scheme_diverse_document_requirements.py`
- **Results:**
  - `test_representative_12_scheme_families_exist_in_registry`: **PASSED** (Dual ID lookup and metadata verified)
  - `test_readiness_computation_for_all_12_schemes`: **PASSED** (Baseline 0% missing states verified)
  - `test_any_of_alternative_document_satisfaction`: **PASSED** (15-yr Ration Card satisfies Domicile)
  - `test_farmer_scheme_landholding_document_requirement`: **PASSED** (7/12 Mahabhulekh extract verified)
  - `test_sqlite_persistence_across_multiple_schemes`: **PASSED** (Cross-scheme attachments survive restart)

---

## 5. Architectural Invariants Preserved
1. **No Hardcoded Single-Scheme Logic:** Document requirements are loaded from canonical registry records (`scheme_document_requirements.json`).
2. **Dual-Key Lookup:** Both canonical string IDs and `MHA-S-xxxx` aliases resolve reliably.
3. **Statutory Integrity:** Requirements cite issuing authorities, Right to Services (RTS) statutory deadlines, and Government Resolutions.
4. **Append-Only SQLite Persistence:** Attachments are persisted to `citizen_scheme_documents` without data loss across process termination.
