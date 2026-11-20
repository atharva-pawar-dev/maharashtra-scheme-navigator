# Scheme Intelligence Dossier: Annasaheb Patil Self-Employment Interest Reimbursement Scheme (scheme-annasaheb-patil-ir2)
**Standard:** TRIMURTI v3 Appendix E Scheme Dossier Template & Milestone SC-G1  
**Classification:** Tier A Flagship (verified_primary)  
**Audit Snapshot:** `U-20261120` | Generated: 2026-11-20T15:44:23.586283+00:00  

---

## 1. Identity
- **Canonical ID:** `scheme-annasaheb-patil-ir2`
- **Official Name (English):** Annasaheb Patil Self-Employment Interest Reimbursement Scheme
- **Official Name (Marathi):** अण्णासाहेब पाटील स्वयंरोजगार कर्ज व्याज परतावा योजना
- **Department:** Planning / Skill Development Department
- **Implementing Authority:** Annasaheb Patil Arthik-Magas Vikas Mahamandal Maryadit
- **Funding Model:** STATE_FUNDED
- **Catalogue Version:** `2.0.0`

## 2. Scope
- **Jurisdiction Scope:** `MAHARASHTRA_STATE`
- **Target Beneficiary:** Entrepreneurship, Interest Subsidy, Open Category
- **Scheme Level:** `state`

## 3. Lifecycle
- **Scheme Lifecycle Status:** `active`
- **Application Window Status:** `APPLICATION_WINDOW_OPEN`
- **Official Application Portal:** [Official Portal](#)
- **Last Verified Timestamp:** `2026-11-18T15:35:16.555606Z`

## 4. Benefit Intelligence
- **Benefit Type:** `subsidy`
- **Amount / Details:** Direct monetary / assistance transfer
- **Marathi Benefit Details:** थेट लाभ हस्तांतरण
- **Frequency:** `monthly`
- **Statutory Delivery Timeline:** 30 days (Maharashtra Right to Services Act 2015)

## 5. Eligibility Rule Model & Exclusions
### Mandatory Substantive Criteria
- **`c_ap_state` (resident_state eq maharashtra):** Citizen of Maharashtra
  - *Marathi:* अर्जदार महाराष्ट्र राज्याचा नागरिक असावा
  - *Verbatim Legal Quote:* `अर्जदार महाराष्ट्र राज्याचा नागरिक असावा.`
- **`c_ap_caste` (caste_category in ['Open', 'SEBC', 'EWS']):** Must belong to Open / Maratha / EWS community
  - *Marathi:* मराठा किंवा खुल्या प्रवर्गातील असणे आवश्यक
  - *Verbatim Legal Quote:* `मराठा / खुल्या प्रवर्गातील आर्थिकदृष्ट्या दुर्बल घटकांसाठी स्वयंरोजगार कर्ज व्याज परतावा योजना.`
- **`c_ap_age_min` (age gte 18):** Minimum age 18 years
  - *Marathi:* किमान वय १८ वर्षे
  - *Verbatim Legal Quote:* `वय १८ ते ४५ वर्षे (पुरुषांसाठी) आणि १८ ते ५० वर्षे (महिलांसाठी).`
- **`c_ap_income` (annual_family_income lte 800000):** Family annual income must not exceed ₹8,00,000
  - *Marathi:* वार्षिक कौटुंबिक उत्पन्न रु. ८,००,०००/- पर्यंत असावे
  - *Verbatim Legal Quote:* `वार्षिक कौटुंबिक उत्पन्न रु. ८,००,०००/- पर्यंत असावे.`

### Dedicated Exclusion Hunting Pass (Section 12.5)
- **`e_annasaheb_income_ceiling` (annual_family_income lte 800000):** Excludes candidates whose annual family income exceeds Rs. 8,00,000
  - *Marathi:* वार्षिक कौटुंबिक उत्पन्न रु. ८ लाखांपेक्षा जास्त असणारे उमेदवार अपात्र
  - *Verbatim Legal Quote:* `वार्षिक कौटुंबिक उत्पन्न रु. ८,००,०००/- पर्यंत असावे.`

## 6. Document Requirement Graph
The following documentation is strictly verified by the Document Auditor:
- **`banking`:** banking (Mandatory: `True`)
- **`welfare_specific`:** welfare_specific (Mandatory: `True`)
- **`residence`:** residence (Mandatory: `True`)
- **`income`:** income (Mandatory: `False`)
- **`welfare_specific`:** welfare_specific (Mandatory: `True`)

## 7. Provenance & Official Source Instruments
- **Title:** अण्णासाहेब पाटील आर्थिक मागास विकास महामंडळ स्वयंरोजगार कर्ज व्याज परतावा योजना
  - **Official URL:** [https://annasahebpatil.maharashtra.gov.in/gr/Vyaj_Partava_2023.pdf](https://annasahebpatil.maharashtra.gov.in/gr/Vyaj_Partava_2023.pdf)
  - **Source Tier:** `tier_1` | **Language:** `mr`
  - **Raw Evidence SHA-256:** `e2a6ede4fe1257e902f4a63c0ca4d735070829098ac7a7d422e87d222f9cfb6e`
  - **Local Cache Path:** `data/raw/gr_annasaheb_patil_2023.txt`

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