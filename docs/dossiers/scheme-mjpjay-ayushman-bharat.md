# Scheme Intelligence Dossier: Mahatma Jyotirao Phule Jan Arogya Yojana (MJPJAY) (scheme-mjpjay-ayushman-bharat)
**Standard:** TRIMURTI v3 Appendix E Scheme Dossier Template & Milestone SC-G1  
**Classification:** Tier A Flagship (verified_primary)  
**Audit Snapshot:** `U-20261120` | Generated: 2026-11-20T15:44:23.576088+00:00  

---

## 1. Identity
- **Canonical ID:** `scheme-mjpjay-ayushman-bharat`
- **Official Name (English):** Mahatma Jyotirao Phule Jan Arogya Yojana (MJPJAY)
- **Official Name (Marathi):** महात्मा ज्योतिराव फुले जन आरोग्य योजना (MJPJAY)
- **Department:** Public Health Department
- **Implementing Authority:** State Health Assurance Society (SHAS)
- **Funding Model:** STATE_FUNDED
- **Catalogue Version:** `2.0.0`

## 2. Scope
- **Jurisdiction Scope:** `MAHARASHTRA_STATE`
- **Target Beneficiary:** Health Insurance, Universal Healthcare, Hospitalization
- **Scheme Level:** `state`

## 3. Lifecycle
- **Scheme Lifecycle Status:** `active`
- **Application Window Status:** `APPLICATION_WINDOW_OPEN`
- **Official Application Portal:** [Official Portal](#)
- **Last Verified Timestamp:** `2026-11-18T15:35:16.533197Z`

## 4. Benefit Intelligence
- **Benefit Type:** `insurance`
- **Amount / Details:** Direct monetary / assistance transfer
- **Marathi Benefit Details:** थेट लाभ हस्तांतरण
- **Frequency:** `annual`
- **Statutory Delivery Timeline:** 30 days (Maharashtra Right to Services Act 2015)

## 5. Eligibility Rule Model & Exclusions
### Mandatory Substantive Criteria
- **`c_mjpjay_state` (resident_state eq maharashtra):** Resident of Maharashtra
  - *Marathi:* महाराष्ट्र राज्यातील रहिवासी
  - *Verbatim Legal Quote:* `महाराष्ट्र राज्यातील सर्व शिधापत्रिकाधारक कुटुंबे पात्र आहेत.`
- **`c_mjpjay_ration` (ration_card_type in ['aay', 'bpl_yellow', 'apl_orange', 'white']):** Possess valid ration card (Yellow, Orange, White, or Antyodaya)
  - *Marathi:* वैध शिधापत्रिका (पिवळी, केशरी, पांढरी किंवा अंत्योदय) असणे आवश्यक
  - *Verbatim Legal Quote:* `अंत्योदय, पिवळी, केशरी व पांढरी शिधापत्रिकाधारक कुटुंब या योजनेअंतर्गत वार्षिक रु. ५,००,०००/- पर्यंत मोफत वैद्यकीय उपचार मिळण्यास पात्र आहेत.`
- **`c_mjpjay_domicile` (residence_years gte 15):** At least 15 years domicile or residence in Maharashtra
  - *Marathi:* महाराष्ट्रात किमान १५ वर्षे वास्तव्य असणे आवश्यक
  - *Verbatim Legal Quote:* `लाभार्थी कुटुंबाकडे महाराष्ट्रात किमान १५ वर्षे वास्तव्याचा अधिवास दाखला किंवा वैध शिधापत्रिका असणे आवश्यक आहे.`

### Dedicated Exclusion Hunting Pass (Section 12.5)
- **`e_mjpjay_ration_card_required` (has_valid_ration_card eq True):** Excludes households not possessing a valid Maharashtra Ration Card or Domicile Certificate
  - *Marathi:* महाराष्ट्र राज्यातील वैध शिधापत्रिका किंवा अधिवास नसलेली कुटुंबे अपात्र
  - *Verbatim Legal Quote:* `लाभार्थी कुटुंबाकडे महाराष्ट्रात किमान १५ वर्षे वास्तव्याचा अधिवास दाखला किंवा वैध शिधापत्रिका असणे आवश्यक आहे.`

## 6. Document Requirement Graph
The following documentation is strictly verified by the Document Auditor:
- **`identity`:** identity (Mandatory: `True`)
- **`residence`:** residence (Mandatory: `False`)

## 7. Provenance & Official Source Instruments
- **Title:** महात्मा ज्योतिराव फुले जन आरोग्य योजना (MJPJAY) सर्वसमावेशक सुधारित मार्गदर्शक सूचना
  - **Official URL:** [https://jeevandayee.gov.in/gr/MJPJAY_Universal_2023.pdf](https://jeevandayee.gov.in/gr/MJPJAY_Universal_2023.pdf)
  - **Source Tier:** `tier_1` | **Language:** `mr`
  - **Raw Evidence SHA-256:** `7dfdecf8e932f762cabc09e6e1a8055280dd9ad0218d923241a2b0b760a53270`
  - **Local Cache Path:** `data/raw/gr_mjpjay_2023.txt`

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