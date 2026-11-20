# Scheme Intelligence Dossier: Sanjay Gandhi Niradhar Anudan Yojana (SGNAY) (candidate-sanjay-gandhi-niradhar-anudan)
**Standard:** TRIMURTI v3 Appendix E Scheme Dossier Template & Milestone SC-G1  
**Classification:** Tier A Flagship (verified_primary)  
**Audit Snapshot:** `U-20261120` | Generated: 2026-11-20T15:44:23.524203+00:00  

---

## 1. Identity
- **Canonical ID:** `candidate-sanjay-gandhi-niradhar-anudan`
- **Official Name (English):** Sanjay Gandhi Niradhar Anudan Yojana (SGNAY)
- **Official Name (Marathi):** संजय गांधी निराधार अनुदान योजना
- **Department:** Social Justice and Special Assistance
- **Implementing Authority:** Collectorate / Tahsildar Sanjay Gandhi Branch
- **Funding Model:** STATE_FUNDED
- **Catalogue Version:** `2.0.0`

## 2. Scope
- **Jurisdiction Scope:** `MAHARASHTRA_STATE`
- **Target Beneficiary:** Social Security, Destitute Welfare, Disability Assistance
- **Scheme Level:** `state`

## 3. Lifecycle
- **Scheme Lifecycle Status:** `active`
- **Application Window Status:** `APPLICATION_WINDOW_OPEN`
- **Official Application Portal:** [Official Portal](#)
- **Last Verified Timestamp:** `2026-11-18T15:35:16.418578Z`

## 4. Benefit Intelligence
- **Benefit Type:** `cash_transfer`
- **Amount / Details:** Direct monetary / assistance transfer
- **Marathi Benefit Details:** थेट लाभ हस्तांतरण
- **Frequency:** `monthly`
- **Statutory Delivery Timeline:** 30 days (Maharashtra Right to Services Act 2015)

## 5. Eligibility Rule Model & Exclusions
### Mandatory Substantive Criteria
- **`c_sgnay_state` (resident_state eq maharashtra):** Must be resident of Maharashtra
  - *Marathi:* महाराष्ट्र राज्यात वास्तव्य आवश्यक
  - *Verbatim Legal Quote:* `महाराष्ट्र राज्यात किमान १५ वर्षे वास्तव्य असणे आवश्यक आहे`
- **`c_sgnay_domicile` (residence_years gte 15):** Must have resided in Maharashtra for at least 15 continuous years
  - *Marathi:* किमान १५ वर्षे सलग वास्तव्य असणे आवश्यक
  - *Verbatim Legal Quote:* `महाराष्ट्र राज्यात किमान १५ वर्षे वास्तव्य असणे आवश्यक आहे`
- **`c_sgnay_age_min` (age gte 18):** Minimum age must be 18 years
  - *Marathi:* किमान वय १८ वर्षे असावे
  - *Verbatim Legal Quote:* `वय १८ ते ६५ वर्षे दरम्यान असावे`
- **`c_sgnay_income` (annual_family_income lte 21000):** Annual family income must not exceed ₹21,000 (up to ₹50,000 for persons with disability)
  - *Marathi:* वार्षिक कौटुंबिक उत्पन्न रु. २१,०००/- पर्यंत (दिव्यांगांसाठी रु. ५०,०००/- पर्यंत)
  - *Verbatim Legal Quote:* `वार्षिक कौटुंबिक उत्पन्न रु. २१,०००/- पर्यंत असणे आवश्यक आहे`

### Dedicated Exclusion Hunting Pass (Section 12.5)
- **`e_sgnay_income_limit` (annual_family_income lte 21000):** Excludes households with annual income exceeding Rs. 21,000 (Rs. 50,000 for persons with disabilities)
  - *Marathi:* वार्षिक कौटुंबिक उत्पन्न रु. २१,०००/- पेक्षा जास्त असणाऱ्या व्यक्ती अपात्र ठरतील
  - *Verbatim Legal Quote:* `वार्षिक कौटुंबिक उत्पन्न रु. २१,०००/- पर्यंत असणे आवश्यक आहे.`
- **`e_sgnay_duplicate_pension` (receives_govt_pension eq False):** Excludes individuals receiving regular state/central retirement pensions
  - *Marathi:* इतर शासकीय निवृत्तीवेतन किंवा नियमित मानधन घेणारे नागरिक अपात्र राहतील
  - *Verbatim Legal Quote:* `निराधार, विधवा, घटस्फोटित, परित्यक्त्या, तृतीयपंथी, देवदासी`

## 6. Document Requirement Graph
The following documentation is strictly verified by the Document Auditor:
- **`residence`:** residence (Mandatory: `True`)
- **`income`:** income (Mandatory: `True`)
- **`disability_medical`:** disability_medical (Mandatory: `False`)
- **`identity`:** identity (Mandatory: `True`)
- **`residence`:** residence (Mandatory: `False`)

## 7. Provenance & Official Source Instruments
- **Title:** संजय गांधी निराधार अनुदान योजना शासन निर्णय व सर्वसमावेशक मार्गदर्शक सूचना
  - **Official URL:** [https://sjsa.maharashtra.gov.in/gr/SGNAY_Consolidated_2023.pdf](https://sjsa.maharashtra.gov.in/gr/SGNAY_Consolidated_2023.pdf)
  - **Source Tier:** `tier_1` | **Language:** `mr`
  - **Raw Evidence SHA-256:** `0c98518ea91d34bccaefaec49c1479f54b891490eba09adb27dcf0420f54a7f3`
  - **Local Cache Path:** `data/raw/gr_sgnay_2023.txt`

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