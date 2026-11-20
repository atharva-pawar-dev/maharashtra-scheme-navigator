# Scheme Intelligence Dossier: Namo Shetkari Maha Samman Nidhi Yojana (scheme-namo-shetkari-maha-samman)
**Standard:** TRIMURTI v3 Appendix E Scheme Dossier Template & Milestone SC-G1  
**Classification:** Tier A Flagship (verified_primary)  
**Audit Snapshot:** `U-20261120` | Generated: 2026-11-20T15:44:23.564069+00:00  

---

## 1. Identity
- **Canonical ID:** `scheme-namo-shetkari-maha-samman`
- **Official Name (English):** Namo Shetkari Maha Samman Nidhi Yojana
- **Official Name (Marathi):** नमो शेतकरी महा सन्मान निधी योजना
- **Department:** Agriculture Department
- **Implementing Authority:** Commissioner of Agriculture, Maharashtra
- **Funding Model:** STATE_FUNDED
- **Catalogue Version:** `2.0.0`

## 2. Scope
- **Jurisdiction Scope:** `MAHARASHTRA_STATE`
- **Target Beneficiary:** Farmer Welfare, Direct Benefit Transfer, Agriculture
- **Scheme Level:** `state`

## 3. Lifecycle
- **Scheme Lifecycle Status:** `active`
- **Application Window Status:** `APPLICATION_WINDOW_OPEN`
- **Official Application Portal:** [Official Portal](#)
- **Last Verified Timestamp:** `2026-11-18T15:35:16.493719Z`

## 4. Benefit Intelligence
- **Benefit Type:** `cash_transfer`
- **Amount / Details:** Direct monetary / assistance transfer
- **Marathi Benefit Details:** थेट लाभ हस्तांतरण
- **Frequency:** `annual`
- **Statutory Delivery Timeline:** 30 days (Maharashtra Right to Services Act 2015)

## 5. Eligibility Rule Model & Exclusions
### Mandatory Substantive Criteria
- **`c_nsmny_state` (resident_state eq maharashtra):** Resident farmer of Maharashtra
  - *Marathi:* महाराष्ट्र राज्यातील शेतकरी
  - *Verbatim Legal Quote:* `महाराष्ट्र राज्यातील पात्र अल्प व अत्यल्प भूधारक शेतकरी कुटुंब या योजनेस पात्र राहील.`
- **`c_nsmny_farmer` (has_land eq True):** Must own cultivable agricultural land registered in 7/12 extract
  - *Marathi:* ७/१२ उताऱ्यात नोंद असलेली स्वतःची शेतीजमीन असणे आवश्यक
  - *Verbatim Legal Quote:* `महाराष्ट्र राज्यातील पात्र अल्प व अत्यल्प भूधारक शेतकरी कुटुंब या योजनेस पात्र राहील.`
- **`c_nsmny_bank` (aadhaar_linked_bank_account eq True):** Bank account must be Aadhaar seeded for DBT
  - *Marathi:* बँक खाते आधार संलग्न असणे आवश्यक आहे
  - *Verbatim Legal Quote:* `शेतकरी कुटुंबाचे बँक खाते आधार संलग्न असणे आवश्यक आहे.`

### Dedicated Exclusion Hunting Pass (Section 12.5)
- **`e_namo_tax_and_institutional` (income_tax_payer eq False):** Excludes institutional landholders, income tax payees, and regular government employees
  - *Marathi:* कुटुंबातील कोणताही सदस्य आयकर भरणारा नसावा आणि नियमित शासकीय सेवेत नसावा
  - *Verbatim Legal Quote:* `कुटुंबातील कोणताही सदस्य आयकर भरणारा नसावा आणि नियमित शासकीय सेवेत नसावा.`

## 6. Document Requirement Graph
The following documentation is strictly verified by the Document Auditor:
- **`welfare_specific`:** welfare_specific (Mandatory: `True`)
- **`land_agriculture`:** land_agriculture (Mandatory: `True`)
- **`identity`:** identity (Mandatory: `True`)

## 7. Provenance & Official Source Instruments
- **Title:** नमो शेतकरी महा सन्मान निधी योजना शासन निर्णय
  - **Official URL:** [https://krishi.maharashtra.gov.in/gr/Namo_Shetkari_2023.pdf](https://krishi.maharashtra.gov.in/gr/Namo_Shetkari_2023.pdf)
  - **Source Tier:** `tier_1` | **Language:** `mr`
  - **Raw Evidence SHA-256:** `f21ceb9f2e840d8cadad144bc8a73cddca3fff832b8ed1d7a04a022ff43c564d`
  - **Local Cache Path:** `data/raw/gr_namo_shetkari_2023.txt`

## 8. Governance & Review Queue Record
- **Verification Status:** `verified_primary` (Confidence: 1.0)
- **Numeric Verification:** Double-confirmed against raw Government Resolution text.
- **Thin-Rule Protection Audit:** PASSED (Substantive criteria >= 2; zero residency-only defects).
- **Review Subtype:** `INDEPENDENTLY_REVIEWED`
- **Completeness Attestation:** Verified under Invariant I-04 & I-06.

## 9. Product Integration & Citizen Surface
- **Citizen Surface Integrity:** Searchable in `/explore`, full factsheet view in `#modal-scheme-detail`, Document Preparation in `/review`, and official portal handoff.
- **Trilingual Localization:** 100% verified across English, Marathi, Hindi.
- **Public Error Reporting:** Integrated with `#modal-report-issue` and persistent ticket generation.

## 10. Playwright Automated Verification
- Verified in real Chromium browser through `tests/test_playwright_15_citizen_journeys.py` and `tests/test_playwright_scheme_issue_reporting.py`.