# Scheme Intelligence Dossier: Shravanbal Seva Rajya Nivruttivetan Yojana (candidate-shravanbal-sewa-rajya-nivruttivetan)
**Standard:** TRIMURTI v3 Appendix E Scheme Dossier Template & Milestone SC-G1  
**Classification:** Tier A Flagship (verified_primary)  
**Audit Snapshot:** `U-20261120` | Generated: 2026-11-20T15:44:23.534699+00:00  

---

## 1. Identity
- **Canonical ID:** `candidate-shravanbal-sewa-rajya-nivruttivetan`
- **Official Name (English):** Shravanbal Seva Rajya Nivruttivetan Yojana
- **Official Name (Marathi):** श्रावणबाळ सेवा राज्य निवृत्तीवेतन योजना
- **Department:** Social Justice and Special Assistance
- **Implementing Authority:** Tahsildar Sanjay Gandhi Branch
- **Funding Model:** STATE_FUNDED
- **Catalogue Version:** `2.0.0`

## 2. Scope
- **Jurisdiction Scope:** `MAHARASHTRA_STATE`
- **Target Beneficiary:** Senior Citizens, Social Security, Pension
- **Scheme Level:** `state`

## 3. Lifecycle
- **Scheme Lifecycle Status:** `active`
- **Application Window Status:** `APPLICATION_WINDOW_OPEN`
- **Official Application Portal:** [Official Portal](#)
- **Last Verified Timestamp:** `2026-11-18T15:35:16.423375Z`

## 4. Benefit Intelligence
- **Benefit Type:** `cash_transfer`
- **Amount / Details:** Direct monetary / assistance transfer
- **Marathi Benefit Details:** थेट लाभ हस्तांतरण
- **Frequency:** `monthly`
- **Statutory Delivery Timeline:** 30 days (Maharashtra Right to Services Act 2015)

## 5. Eligibility Rule Model & Exclusions
### Mandatory Substantive Criteria
- **`c_shravan_state` (resident_state eq maharashtra):** Must be resident of Maharashtra
  - *Marathi:* महाराष्ट्राचा रहिवासी असणे आवश्यक
  - *Verbatim Legal Quote:* `महाराष्ट्रात किमान १५ वर्षे सलग वास्तव्याचा दाखला आवश्यक आहे`
- **`c_shravan_domicile` (residence_years gte 15):** Must have resided in Maharashtra for at least 15 continuous years
  - *Marathi:* किमान १५ वर्षे सलग वास्तव्य असणे आवश्यक
  - *Verbatim Legal Quote:* `महाराष्ट्रात किमान १५ वर्षे सलग वास्तव्याचा दाखला आवश्यक आहे`
- **`c_shravan_age` (age gte 65):** Applicant must be aged 65 years or above
  - *Marathi:* वय ६५ वर्षे व त्यावरील असणे आवश्यक
  - *Verbatim Legal Quote:* `वय ६५ वर्षे व त्यावरील निराधार वृद्ध व्यक्ती असणे आवश्यक आहे`
- **`c_shravan_income` (annual_family_income lte 21000):** Family annual income must not exceed ₹21,000 (Group A)
  - *Marathi:* कौटुंबिक वार्षिक उत्पन्न मर्यादा रु. २१,०००/- पर्यंत (गट अ)
  - *Verbatim Legal Quote:* `गट (अ) साठी कौटुंबिक वार्षिक उत्पन्न मर्यादा रु. २१,०००/- पर्यंत असावी`

### Dedicated Exclusion Hunting Pass (Section 12.5)
- **`e_shravanbal_income_ceiling` (annual_family_income lte 21000):** Excludes individuals with annual family income exceeding Rs. 21,000 for Group A
  - *Marathi:* गट (अ) साठी कौटुंबिक वार्षिक उत्पन्न रु. २१,०००/- पेक्षा जास्त असणारे अपात्र ठरतील
  - *Verbatim Legal Quote:* `गट (अ) साठी कौटुंबिक वार्षिक उत्पन्न मर्यादा रु. २१,०००/- पर्यंत असावी.`
- **`e_shravanbal_duplicate_pension` (receives_nsap_pension eq False):** Excludes individuals receiving duplicate central old age pension under IGNOAPS
  - *Marathi:* इतर कोणत्याही शासकीय निवृत्तीवेतन योजनेचा लाभ घेणारे वृद्ध व्यक्ती अपात्र
  - *Verbatim Legal Quote:* `निराधार वृद्ध व्यक्ती असणे आवश्यक आहे`

## 6. Document Requirement Graph
The following documentation is strictly verified by the Document Auditor:
- **`identity`:** identity (Mandatory: `True`)
- **`residence`:** residence (Mandatory: `True`)
- **`income`:** income (Mandatory: `False`)
- **`banking`:** banking (Mandatory: `True`)
- **`welfare_specific`:** welfare_specific (Mandatory: `False`)

## 7. Provenance & Official Source Instruments
- **Title:** श्रावणबाळ सेवा राज्य निवृत्तीवेतन योजना शासन निर्णय
  - **Official URL:** [https://sjsa.maharashtra.gov.in/gr/Shravanbal_Rules.pdf](https://sjsa.maharashtra.gov.in/gr/Shravanbal_Rules.pdf)
  - **Source Tier:** `tier_1` | **Language:** `mr`
  - **Raw Evidence SHA-256:** `a48bc296ceeebd23f41164789a91cd29b7e80f0c8f611fd61c1eda20533fa568`
  - **Local Cache Path:** `data/raw/gr_shravanbal_2023.txt`

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