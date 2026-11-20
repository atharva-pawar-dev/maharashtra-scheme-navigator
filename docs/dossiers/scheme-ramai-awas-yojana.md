# Scheme Intelligence Dossier: Ramai Awas Gharkul Yojana (scheme-ramai-awas-yojana)
**Standard:** TRIMURTI v3 Appendix E Scheme Dossier Template & Milestone SC-G1  
**Classification:** Tier A Flagship (verified_primary)  
**Audit Snapshot:** `U-20261120` | Generated: 2026-11-20T15:44:23.589283+00:00  

---

## 1. Identity
- **Canonical ID:** `scheme-ramai-awas-yojana`
- **Official Name (English):** Ramai Awas Gharkul Yojana
- **Official Name (Marathi):** रमाई आवास घरकुल योजना
- **Department:** Social Justice and Special Assistance
- **Implementing Authority:** Social Welfare / Zilla Parishad Rural Housing
- **Funding Model:** STATE_FUNDED
- **Catalogue Version:** `2.0.0`

## 2. Scope
- **Jurisdiction Scope:** `MAHARASHTRA_STATE`
- **Target Beneficiary:** Housing, SC Welfare, Rural Development
- **Scheme Level:** `state`

## 3. Lifecycle
- **Scheme Lifecycle Status:** `active`
- **Application Window Status:** `APPLICATION_WINDOW_OPEN`
- **Official Application Portal:** [Official Portal](#)
- **Last Verified Timestamp:** `2026-11-18T15:35:16.576782Z`

## 4. Benefit Intelligence
- **Benefit Type:** `subsidy`
- **Amount / Details:** Direct monetary / assistance transfer
- **Marathi Benefit Details:** थेट लाभ हस्तांतरण
- **Frequency:** `one_time`
- **Statutory Delivery Timeline:** 30 days (Maharashtra Right to Services Act 2015)

## 5. Eligibility Rule Model & Exclusions
### Mandatory Substantive Criteria
- **`c_ramai_state` (resident_state eq maharashtra):** Resident of Maharashtra for at least 15 years
  - *Marathi:* किमान १५ वर्षे वास्तव्य असणारा महाराष्ट्राचा रहिवासी
  - *Verbatim Legal Quote:* `अर्जदार महाराष्ट्र राज्यातील किमान १५ वर्षे वास्तव्य असणारा रहिवासी असावा.`
- **`c_ramai_domicile` (residence_years gte 15):** 15 years residence in Maharashtra
  - *Marathi:* किमान १५ वर्षे वास्तव्य
  - *Verbatim Legal Quote:* `अर्जदार महाराष्ट्र राज्यातील किमान १५ वर्षे वास्तव्य असणारा रहिवासी असावा.`
- **`c_ramai_caste` (caste_category eq SC):** Must belong to Scheduled Caste (SC) category
  - *Marathi:* अनुसूचित जाती किंवा नवबौद्ध प्रवर्गातील असणे आवश्यक
  - *Verbatim Legal Quote:* `अनुसूचित जाती व नवबौद्ध प्रवर्गातील बेघर व कच्चे घर असणारे कुटुंब पात्र राहील.`
- **`c_ramai_income` (annual_family_income lte 100000):** Annual family income up to ₹1,00,000 (rural areas)
  - *Marathi:* वार्षिक कौटुंबिक उत्पन्न ग्रामीण भागासाठी रु. १,००,०००/- पर्यंत
  - *Verbatim Legal Quote:* `वार्षिक कौटुंबिक उत्पन्न ग्रामीण भागासाठी रु. १,००,०००/- व नागरी भागासाठी रु. ३,००,०००/- पर्यंत असणे आवश्यक आहे.`

### Dedicated Exclusion Hunting Pass (Section 12.5)
- **`e_ramai_pucca_house` (owns_pucca_house eq False):** Excludes applicants who already possess a pucca house in their own or family's name
  - *Marathi:* स्वतःच्या किंवा कुटुंबाच्या नावावर पक्के घर असणारे नागरिक अपात्र
  - *Verbatim Legal Quote:* `स्वतःची जागा किंवा कच्चे घर असणे आवश्यक असून पक्के घर नसावे.`

## 6. Document Requirement Graph
The following documentation is strictly verified by the Document Auditor:
- **`caste_social`:** caste_social (Mandatory: `True`)
- **`income`:** income (Mandatory: `True`)
- **`land_agriculture`:** land_agriculture (Mandatory: `False`)
- **`welfare_specific`:** welfare_specific (Mandatory: `True`)

## 7. Provenance & Official Source Instruments
- **Title:** रमाई आवास घरकुल योजना शासन निर्णय व निकष
  - **Official URL:** [https://sjsa.maharashtra.gov.in/gr/Ramai_Gharkul_Guidelines.pdf](https://sjsa.maharashtra.gov.in/gr/Ramai_Gharkul_Guidelines.pdf)
  - **Source Tier:** `tier_1` | **Language:** `mr`
  - **Raw Evidence SHA-256:** `171c5b680196307f0c5e52cade482e4ca59b1a9c6d0a9f8e1223fd5e8603c20e`
  - **Local Cache Path:** `data/raw/gr_ramai_gharkul.txt`

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