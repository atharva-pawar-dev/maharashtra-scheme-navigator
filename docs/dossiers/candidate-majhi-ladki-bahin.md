# Scheme Intelligence Dossier: Mukhyamantri Majhi Ladki Bahin Yojana (candidate-majhi-ladki-bahin)
**Standard:** TRIMURTI v3 Appendix E Scheme Dossier Template & Milestone SC-G1  
**Classification:** Tier A Flagship (verified_primary)  
**Audit Snapshot:** `U-20261120` | Generated: 2026-11-20T15:44:23.522194+00:00  

---

## 1. Identity
- **Canonical ID:** `candidate-majhi-ladki-bahin`
- **Official Name (English):** Mukhyamantri Majhi Ladki Bahin Yojana
- **Official Name (Marathi):** मुख्यमंत्री माझी लाडकी बहीण योजना
- **Department:** Women and Child Development Department
- **Implementing Authority:** Directorate of Women and Child Development
- **Funding Model:** STATE_FUNDED
- **Catalogue Version:** `2.0.0`

## 2. Scope
- **Jurisdiction Scope:** `MAHARASHTRA_STATE`
- **Target Beneficiary:** Women Empowerment, Direct Benefit Transfer, Financial Assistance
- **Scheme Level:** `state`

## 3. Lifecycle
- **Scheme Lifecycle Status:** `active`
- **Application Window Status:** `APPLICATION_WINDOW_OPEN`
- **Official Application Portal:** [Official Portal](#)
- **Last Verified Timestamp:** `2026-11-18T15:35:16.413183Z`

## 4. Benefit Intelligence
- **Benefit Type:** `cash_transfer`
- **Amount / Details:** Direct monetary / assistance transfer
- **Marathi Benefit Details:** थेट लाभ हस्तांतरण
- **Frequency:** `monthly`
- **Statutory Delivery Timeline:** 30 days (Maharashtra Right to Services Act 2015)

## 5. Eligibility Rule Model & Exclusions
### Mandatory Substantive Criteria
- **`c_mmlby_state` (resident_state eq maharashtra):** Must be a permanent resident of Maharashtra
  - *Marathi:* महिला महाराष्ट्र राज्याची रहिवासी असणे आवश्यक आहे
  - *Verbatim Legal Quote:* `महिला महाराष्ट्र राज्याची रहिवासी असणे आवश्यक आहे`
- **`c_mmlby_gender` (gender eq female):** Must be a female applicant
  - *Marathi:* अर्जदार महिला असणे आवश्यक आहे
  - *Verbatim Legal Quote:* `२१ ते ६५ वयोगटातील विवाहित, विधवा, घटस्फोटित, परित्यक्त्या आणि निराधार महिला`
- **`c_mmlby_age_min` (age gte 21):** Minimum age must be 21 years
  - *Marathi:* किमान वय २१ वर्षे पूर्ण असावे
  - *Verbatim Legal Quote:* `२१ ते ६५ वयोगटातील विवाहित, विधवा, घटस्फोटित, परित्यक्त्या आणि निराधार महिला`
- **`c_mmlby_age_max` (age lte 65):** Maximum age must be 65 years
  - *Marathi:* कमाल वय ६५ वर्षांपर्यंत असावे
  - *Verbatim Legal Quote:* `२१ ते ६५ वयोगटातील विवाहित, विधवा, घटस्फोटित, परित्यक्त्या आणि निराधार महिला`
- **`c_mmlby_income` (annual_family_income lte 250000):** Annual family income must not exceed ₹2,50,000
  - *Marathi:* कुटुंबाचे वार्षिक उत्पन्न रु. २.५० लाखांपेक्षा जास्त नसावे
  - *Verbatim Legal Quote:* `सदर योजनेच्या लाभासाठी कुटुंबाचे वार्षिक उत्पन्न रु. २.५० लाखांपेक्षा जास्त नसावे`
- **`c_mmlby_bank` (aadhaar_linked_bank_account eq True):** Bank account must be Aadhaar-seeded for DBT payments
  - *Marathi:* बँक खाते आधार लिंक असणे आवश्यक आहे
  - *Verbatim Legal Quote:* `लाभार्थी महिलेचे बँक खाते आधार लिंक असणे आवश्यक आहे`

### Dedicated Exclusion Hunting Pass (Section 12.5)
- **`e_mmlby_tax` (income_tax_payer eq False):** No family member should be an income tax payer
  - *Marathi:* कुटुंबातील सदस्य आयकरदाता नसावा
  - *Verbatim Legal Quote:* `कुटुंबातील सदस्य आयकरदाता नसावा`
- **`e_mmlby_govt_job` (govt_employee_in_family eq False):** No family member should be a regular government employee or pensioner
  - *Marathi:* कुटुंबातील सदस्य नियमित/कायम कर्मचारी म्हणून शासकीय विभाग/उपक्रम यामध्ये कार्यरत नसावा
  - *Verbatim Legal Quote:* `कुटुंबातील सदस्य नियमित/कायम कर्मचारी म्हणून शासकीय विभाग/उपक्रम यामध्ये कार्यरत नसावा`
- **`e_mmlby_vehicle` (owns_four_wheeler eq False):** Family must not own a four-wheeler vehicle (tractor excluded)
  - *Marathi:* कुटुंबातील सदस्यांच्या नावावर चारचाकी वाहन (ट्रॅक्टर वगळून) नसावे
  - *Verbatim Legal Quote:* `कुटुंबातील सदस्यांच्या नावावर चारचाकी वाहन (ट्रॅक्टर वगळून) नसावे`
- **`e_mmlby_duplicate_benefit` (receives_other_monthly_dbt_ge_1500 eq False):** Must not receive monthly financial assistance of Rs. 1,500 or more from other government schemes
  - *Marathi:* इतर कोणत्याही योजनेतून दरमहा रु. १५००/- किंवा त्यापेक्षा जास्त आर्थिक लाभ घेत नसावा
  - *Verbatim Legal Quote:* `ज्या कुटुंबातील महिला इतर कोणत्याही योजनेतून दरमहा रु. १५००/- किंवा त्यापेक्षा जास्त आर्थिक लाभ घेत असतील त्या अपात्र ठरतील.`

## 6. Document Requirement Graph
The following documentation is strictly verified by the Document Auditor:
- **`identity`:** identity (Mandatory: `True`)
- **`residence`:** residence (Mandatory: `True`)
- **`income`:** income (Mandatory: `True`)
- **`banking`:** banking (Mandatory: `True`)
- **`residence`:** residence (Mandatory: `False`)

## 7. Provenance & Official Source Instruments
- **Title:** शासन निर्णय क्र. संकीर्ण-२०२४/प्र.क्र.१३७/कार्या-०२ (मुख्यमंत्री माझी लाडकी बहीण योजना)
  - **Official URL:** [https://ladkibahin.maharashtra.gov.in/gr/GR_28_06_2024.pdf](https://ladkibahin.maharashtra.gov.in/gr/GR_28_06_2024.pdf)
  - **Source Tier:** `tier_1` | **Language:** `mr`
  - **Raw Evidence SHA-256:** `423c3e902af9cca1e5e54057d4cb9aa4793f35825b868a93e653c809e2691948`
  - **Local Cache Path:** `data/raw/gr_mmlby_2024.txt`

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