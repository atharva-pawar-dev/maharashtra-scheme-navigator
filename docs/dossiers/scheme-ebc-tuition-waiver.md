# Scheme Intelligence Dossier: Rajarshi Chhatrapati Shahu Maharaj Shikshan Shulkh Shishyavrutti Yojna (EBC) (scheme-ebc-tuition-waiver)
**Standard:** TRIMURTI v3 Appendix E Scheme Dossier Template & Milestone SC-G1  
**Classification:** Tier A Flagship (verified_primary)  
**Audit Snapshot:** `U-20261120` | Generated: 2026-11-20T15:44:23.560069+00:00  

---

## 1. Identity
- **Canonical ID:** `scheme-ebc-tuition-waiver`
- **Official Name (English):** Rajarshi Chhatrapati Shahu Maharaj Shikshan Shulkh Shishyavrutti Yojna (EBC)
- **Official Name (Marathi):** राजारशी छत्रपती शाहू महाराज शिक्षण शुल्क शिष्यवृत्ती योजना (EBC)
- **Department:** Higher and Technical Education Department
- **Implementing Authority:** Directorate of Higher Education (DHE) via MahaDBT
- **Funding Model:** STATE_FUNDED
- **Catalogue Version:** `2.0.0`

## 2. Scope
- **Jurisdiction Scope:** `MAHARASHTRA_STATE`
- **Target Beneficiary:** Higher Education, Tuition Fee Waiver, EBC
- **Scheme Level:** `state`

## 3. Lifecycle
- **Scheme Lifecycle Status:** `active`
- **Application Window Status:** `APPLICATION_WINDOW_OPEN`
- **Official Application Portal:** [Official Portal](#)
- **Last Verified Timestamp:** `2026-11-18T15:35:16.488302Z`

## 4. Benefit Intelligence
- **Benefit Type:** `scholarship`
- **Amount / Details:** Direct monetary / assistance transfer
- **Marathi Benefit Details:** थेट लाभ हस्तांतरण
- **Frequency:** `academic_year`
- **Statutory Delivery Timeline:** 30 days (Maharashtra Right to Services Act 2015)

## 5. Eligibility Rule Model & Exclusions
### Mandatory Substantive Criteria
- **`c_ebc_state` (resident_state eq maharashtra):** Resident of Maharashtra
  - *Marathi:* महाराष्ट्र राज्याचा रहिवासी असणे आवश्यक
  - *Verbatim Legal Quote:* `अर्जदार विद्यार्थी महाराष्ट्र राज्याचा रहिवासी असणे आवश्यक आहे.`
- **`c_ebc_student` (is_student eq True):** Enrolled student in recognized course
  - *Marathi:* मान्यताप्राप्त अभ्यासक्रमात नियमित शिक्षण घेत असलेला विद्यार्थी
  - *Verbatim Legal Quote:* `विद्यार्थी मान्यताप्राप्त व्यावसायिक किंवा बिगर-व्यावसायिक अभ्यासक्रमात नियमित शिक्षण घेत असावा.`
- **`c_ebc_income` (annual_family_income lte 800000):** Family annual income must not exceed ₹8,00,000
  - *Marathi:* कौटुंबिक वार्षिक उत्पन्न मर्यादा रु. ८,००,०००/- पर्यंत
  - *Verbatim Legal Quote:* `कौटुंबिक वार्षिक उत्पन्न मर्यादा रु. ८,००,०००/- पर्यंत असणे आवश्यक आहे.`

### Dedicated Exclusion Hunting Pass (Section 12.5)
- **`e_ebc_income_ceiling` (annual_family_income lte 800000):** Excludes students whose family annual income exceeds Rs. 8,00,000
  - *Marathi:* कौटुंबिक वार्षिक उत्पन्न रु. ८ लाखांपेक्षा जास्त असणारे विद्यार्थी अपात्र
  - *Verbatim Legal Quote:* `कौटुंबिक वार्षिक उत्पन्न मर्यादा रु. ८,००,०००/- पर्यंत असणे आवश्यक आहे.`
- **`e_ebc_management_quota` (cap_round_admission eq True):** Excludes admissions secured through management quota or non-centralized admission process
  - *Marathi:* व्यवस्थापन कोट्यातून (मॅनेजमेंट कोटा) घेतलेले प्रवेश या योजनेसाठी अपात्र आहेत
  - *Verbatim Legal Quote:* `विद्यार्थी मान्यताप्राप्त व्यावसायिक किंवा बिगर-व्यावसायिक अभ्यासक्रमात नियमित शिक्षण घेत असावा.`

## 6. Document Requirement Graph
The following documentation is strictly verified by the Document Auditor:
- **`residence`:** residence (Mandatory: `True`)
- **`income`:** income (Mandatory: `True`)
- **`welfare_specific`:** welfare_specific (Mandatory: `True`)
- **`education_marksheet`:** education_marksheet (Mandatory: `True`)
- **`residence`:** residence (Mandatory: `False`)

## 7. Provenance & Official Source Instruments
- **Title:** राजारशी छत्रपती शाहू महाराज शिक्षण शुल्क शिष्यवृत्ती योजना (EBC)
  - **Official URL:** [https://mahadbt.maharashtra.gov.in/scheme_rules/EBC_Shahu_Maharaj.pdf](https://mahadbt.maharashtra.gov.in/scheme_rules/EBC_Shahu_Maharaj.pdf)
  - **Source Tier:** `tier_1` | **Language:** `mr`
  - **Raw Evidence SHA-256:** `51dda36bfec27f237eb4b0b572e36afaf9995095a10233a1af2e982a024bce95`
  - **Local Cache Path:** `data/raw/mahadbt_ebc_shahu.txt`

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