# Scheme Intelligence Dossier: Bhausaheb Fundkar Phalbag Lagwad Yojana (scheme-bhausaheb-fundkar-phalbag)
**Standard:** TRIMURTI v3 Appendix E Scheme Dossier Template & Milestone SC-G1  
**Classification:** Tier A Flagship (verified_primary)  
**Audit Snapshot:** `U-20261120` | Generated: 2026-11-20T15:44:23.572066+00:00  

---

## 1. Identity
- **Canonical ID:** `scheme-bhausaheb-fundkar-phalbag`
- **Official Name (English):** Bhausaheb Fundkar Phalbag Lagwad Yojana
- **Official Name (Marathi):** भाऊसाहेब फुंडकर फळबाग लागवड योजना
- **Department:** Agriculture Department
- **Implementing Authority:** Directorate of Horticulture, Maharashtra
- **Funding Model:** STATE_FUNDED
- **Catalogue Version:** `2.0.0`

## 2. Scope
- **Jurisdiction Scope:** `MAHARASHTRA_STATE`
- **Target Beneficiary:** Agriculture, Horticulture, Subsidy
- **Scheme Level:** `state`

## 3. Lifecycle
- **Scheme Lifecycle Status:** `active`
- **Application Window Status:** `APPLICATION_WINDOW_OPEN`
- **Official Application Portal:** [Official Portal](#)
- **Last Verified Timestamp:** `2026-11-18T15:35:16.528224Z`

## 4. Benefit Intelligence
- **Benefit Type:** `subsidy`
- **Amount / Details:** Direct monetary / assistance transfer
- **Marathi Benefit Details:** थेट लाभ हस्तांतरण
- **Frequency:** `one_time`
- **Statutory Delivery Timeline:** 30 days (Maharashtra Right to Services Act 2015)

## 5. Eligibility Rule Model & Exclusions
### Mandatory Substantive Criteria
- **`c_bfp_state` (resident_state eq maharashtra):** Resident farmer of Maharashtra
  - *Marathi:* शेतकरी महाराष्ट्र राज्याचा रहिवासी असावा
  - *Verbatim Legal Quote:* `शेतकरी महाराष्ट्र राज्याचा रहिवासी असावा.`
- **`c_bfp_farmer` (has_land eq True):** Must be a landowner farmer
  - *Marathi:* शेतकरी जमीनधारक असणे आवश्यक
  - *Verbatim Legal Quote:* `शेतकऱ्याकडे स्वतःच्या नावावर किमान ०.२० हेक्टर ते कमाल ६.०० हेक्टरपर्यंत शेतीजमीन असणे आवश्यक.`
- **`c_bfp_land_min` (landholding_hectares gte 0.2):** Minimum cultivable landholding of 0.20 hectares
  - *Marathi:* किमान ०.२० हेक्टर शेतीजमीन असणे आवश्यक
  - *Verbatim Legal Quote:* `शेतकऱ्याकडे स्वतःच्या नावावर किमान ०.२० हेक्टर ते कमाल ६.०० हेक्टरपर्यंत शेतीजमीन असणे आवश्यक.`
- **`c_bfp_land_max` (landholding_hectares lte 6.0):** Maximum landholding limit of 6.00 hectares
  - *Marathi:* कमाल ६.०० हेक्टरपर्यंत शेतीजमीन
  - *Verbatim Legal Quote:* `शेतकऱ्याकडे स्वतःच्या नावावर किमान ०.२० हेक्टर ते कमाल ६.०० हेक्टरपर्यंत शेतीजमीन असणे आवश्यक.`

### Dedicated Exclusion Hunting Pass (Section 12.5)
- **`e_fundkar_land_ceiling` (agricultural_land_hectares lte 6.0):** Excludes landholders owning more than 6.00 hectares of cultivable land
  - *Marathi:* ६.०० हेक्टरपेक्षा जास्त शेतीजमीन असणारे शेतकरी अपात्र
  - *Verbatim Legal Quote:* `किमान ०.२० हेक्टर ते कमाल ६.०० हेक्टरपर्यंत शेतीजमीन असणे आवश्यक.`

## 6. Document Requirement Graph
The following documentation is strictly verified by the Document Auditor:
- **`land_agriculture`:** land_agriculture (Mandatory: `True`)
- **`land_agriculture`:** land_agriculture (Mandatory: `True`)
- **`identity`:** identity (Mandatory: `True`)
- **`banking`:** banking (Mandatory: `True`)
- **`welfare_specific`:** welfare_specific (Mandatory: `False`)

## 7. Provenance & Official Source Instruments
- **Title:** भाऊसाहेब फुंडकर फळबाग लागवड योजना शासन निर्णय
  - **Official URL:** [https://krishi.maharashtra.gov.in/gr/Bhausaheb_Fundkar_Phalbag.pdf](https://krishi.maharashtra.gov.in/gr/Bhausaheb_Fundkar_Phalbag.pdf)
  - **Source Tier:** `tier_1` | **Language:** `mr`
  - **Raw Evidence SHA-256:** `4f9a900759a66c3cdb7b7c008687ae52d755efbe4f5ed43f2d20fc939e541f87`
  - **Local Cache Path:** `data/raw/gr_bhausaheb_fundkar.txt`

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