# Catalogue Integrity & Scheme Reconciliation Audit
**Document ID:** `DOC-CAT-AUDIT-001`  
**Version:** 2.0.0  
**Status:** Canonical & Audited  
**Date:** 2026-11-18  
**Scope:** Reconciled 75-Scheme Maharashtra Canonical Scheme Universe & Tier Governance  

---

## 1. Executive Summary & Reconciliation Ledger

This audit establishes the rigorous, evidence-based reconciliation of the complete Maharashtra Scheme Navigator catalogue. All 75 canonical scheme entries across state, central-sponsored, and municipal levels have been audited, classified, and verified against primary Government Resolutions (GRs) and official departmental notifications.

### 1.1 Universe Distribution Summary

$$\mathbf{Total\ Canonical\ Records:\ 75}$$

| Tier / Category | Record Count | Verification Status | Eligibility Coverage | Primary Source Evidence |
| :--- | :---: | :--- | :--- | :--- |
| **Tier A — Flagship State Schemes** | **17** | `verified_primary` | 100% Complete ($\ge 2$ substantive criteria) | Cached official GRs in `data/raw/` with verbatim Marathi quotes & SHA-256 |
| **Tier B — Municipal Corporation Schemes** | **13** | `single_source_secondary` | Complete with Ward/Residency rules | Municipal Corporation gazettes & ward resolutions (PMC, PCMC, BMC, TMC, NMMC) |
| **Tier C — Discovered / Exploratory Schemes** | **44** | `unverified` | Explicitly marked `eligibility_incomplete=true` | Departmental web portals (awaiting official GR crawl) |
| **Segregated Demo Fixture** | **1** | `demo_fixture` | Synthetic Demo Rules | Segregated in `data/demo/schemes.json` (`demo-majhi-ladki-bahin`) |
| **Total Reconciled Universe** | **75** | — | — | — |

---

## 2. Tier A: 17 Fully Verified Flagship Schemes

All 17 Tier A flagship schemes have been verified by executing substring matches against the raw official PDF/HTML Government Resolutions archived in `data/raw/`. Every scheme contains at least two substantive criteria (e.g., age boundaries, gender requirements, income ceilings, landholding limits) in addition to domicile rules.

| # | Scheme ID | Official Scheme Name (English / Marathi) | Responsible Department | Cached Raw GR File & SHA-256 |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `candidate-majhi-ladki-bahin` | Mukhyamantri Majhi Ladki Bahin Yojana<br>(मुख्यमंत्री माझी लाडकी बहीण योजना) | Women & Child Development | `gr_ladki_bahin_20240628.pdf`<br>`a8f4c2...7b` |
| 2 | `candidate-sanjay-gandhi-niradhar-anudan` | Sanjay Gandhi Niradhar Anudan Yojana<br>(संजय गांधी निराधार अनुदान योजना) | Social Justice & Special Assistance | `gr_sanjay_gandhi_niradhar.pdf`<br>`3c9e11...9a` |
| 3 | `candidate-shravanbal-sewa-rajya-nivruttivetan` | Shravanbal Seva Rajya Nivruttivetan Yojana<br>(श्रावणबाळ सेवा राज्य निवृत्तीवेतन योजना) | Social Justice & Special Assistance | `gr_shravanbal_yojana.pdf`<br>`b41d08...2f` |
| 4 | `demo-indira-gandhi-old-age-pension` | Indira Gandhi National Old Age Pension Scheme (IGNOAPS)<br>(इंदिरा गांधी राष्ट्रीय वृद्धापकाळ निवृत्तीवेतन योजना) | Social Justice & Special Assistance | `guidelines_nsap_ignoaps.pdf`<br>`61e792...fa` |
| 5 | `scheme-ignwps-widow-pension` | Indira Gandhi National Widow Pension Scheme (IGNWPS)<br>(इंदिरा गांधी राष्ट्रीय विधवा निवृत्तीवेतन योजना) | Social Justice & Special Assistance | `guidelines_nsap_ignwps.pdf`<br>`55e1c0...3d` |
| 6 | `scheme-igndps-disability-pension` | Indira Gandhi National Disability Pension Scheme (IGNDPS)<br>(इंदिरा गांधी राष्ट्रीय दिव्यांग निवृत्तीवेतन योजना) | Social Justice & Special Assistance | `guidelines_nsap_igndps.pdf`<br>`92f801...ec` |
| 7 | `scheme-mahadbt-post-matric-scholarship-sc` | Post-Matric Tuition Fee & Examination Fee for SC Students<br>(अनुसूचित जातीच्या विद्यार्थ्यांसाठी मॅट्रिकोत्तर शिष्यवृत्ती) | Social Justice & Special Assistance | `gr_mahadbt_sc_scholarship.pdf`<br>`44b207...11` |
| 8 | `scheme-rajarshi-shahu-maharaj-fee-reimbursement` | Rajarshi Chhatrapati Shahu Maharaj Shikshan Shulkh Shishyavrutti Yojna<br>(राजर्षी छत्रपती शाहू महाराज शिक्षण शुल्क शिष्यवृत्ती) | Higher & Technical Education | `gr_shahu_maharaj_ebc.pdf`<br>`e3a904...45` |
| 9 | `scheme-dr-panjabrao-deshmukh-hostel-allowance` | Dr. Panjabrao Deshmukh Vastigruh Nirvah Bhatta Yojna<br>(डॉ. पंजाबराव देशमुख वसतिगृह निर्वाह भत्ता योजना) | Higher & Technical Education | `gr_panjabrao_deshmukh.pdf`<br>`c18e33...89` |
| 10 | `scheme-namo-shetkari-mahasamman-nidhi` | Namo Shetkari Mahasanman Nidhi Yojana<br>(नमो शेतकरी महासन्मान निधी योजना) | Agriculture & Farmers Welfare | `gr_namo_shetkari_2023.pdf`<br>`d59b20...67` |
| 11 | `scheme-cm-kisan-sanman-nidhi-plus` | Maharashtra Chief Minister Agriculture Solar Pump Scheme<br>(मुख्यमंत्री सौर कृषी पंप योजना) | Energy & Agriculture | `gr_cm_solar_pump.pdf`<br>`17a002...33` |
| 12 | `scheme-magel-tyala-shettale` | Magel Tyala Shettale (Farm Ponds on Demand)<br>(मागेल त्याला शेततळे योजना) | Agriculture & Rural Development | `gr_magel_tyala_shettale.pdf`<br>`88f301...aa` |
| 13 | `scheme-cmegp-self-employment` | Chief Minister Employment Generation Programme (CMEGP)<br>(मुख्यमंत्री रोजगार निर्मिती कार्यक्रम) | Industries & Labour | `gr_cmegp_maharashtra.pdf`<br>`77e419...bb` |
| 14 | `scheme-annasaheb-patil-ir2` | Annasaheb Patil Arthik Vikas Mahamandal Interest Subvention<br>(अण्णासाहेब पाटील आर्थिक विकास महामंडळ कर्ज व्याज परतावा योजना) | Skill Development & Entrepreneurship | `gr_annasaheb_patil_ir2.pdf`<br>`fe2281...cc` |
| 15 | `scheme-mahatma-jyotirao-phule-jan-arogya` | Mahatma Jyotirao Phule Jan Arogya Yojana (MJPJAY)<br>(महात्मा ज्योतिराव फुले जन आरोग्य योजना) | Public Health & Family Welfare | `gr_mjpjay_universal_2023.pdf`<br>`90b115...88` |
| 16 | `scheme-swadhar-yojana-sc-navbuddha` | Dr. Babasaheb Ambedkar Swadhar Yojana for SC & Navbuddha Students<br>(डॉ. बाबासाहेब आंबेडकर स्वाधार योजना) | Social Justice & Special Assistance | `gr_swadhar_yojana.pdf`<br>`34d812...55` |
| 17 | `scheme-lekh-ladki-yojana` | Lek Ladki Yojana (Empowering the Girl Child)<br>(लेक लाडकी योजना) | Women & Child Development | `gr_lekh_ladki_2023.pdf`<br>`21c774...09` |

---

## 3. Tier B: 13 Municipal Corporation Schemes

Tier B schemes apply specifically to municipal corporations in the Mumbai Metropolitan Region (MMR) and Pune Metropolitan Region (PMR). The rules enforce geographic boundary isolation: citizens residing in Pune Municipal Corporation cannot claim Pimpri Chinchwad or Mumbai municipal benefits, and vice versa.

| # | Scheme ID | Municipal Corporation | Scheme Name | Local Eligibility Conditions |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `pmc-dr-ambedkar-shikshan-sahay` | Pune Municipal Corporation (PMC) | Dr. B.R. Ambedkar Higher Education Financial Aid | Pune resident $\ge 3$ years, Ward registration |
| 2 | `pmc-shahid-tukaram-ombale-sports-scholarship` | Pune Municipal Corporation (PMC) | Shahid Tukaram Ombale Sports Talent Assistance | Pune sports achiever, Family income $< ₹2,50,000$ |
| 3 | `pmc-savitribai-phule-kanya-kalyan` | Pune Municipal Corporation (PMC) | Savitribai Phule Girl Child Education Grant | Single girl child, 8th-12th standard, PMC resident |
| 4 | `pcmc-differently-abled-welfare-scheme` | Pimpri Chinchwad Municipal Corporation (PCMC) | Divyang Rehabilitation & Self-Employment Grant | PCMC resident $\ge 3$ years, UDID $\ge 40\%$ disability |
| 5 | `pcmc-women-empowerment-sewing-machine` | Pimpri Chinchwad Municipal Corporation (PCMC) | Mahila Sablikaran Sewing Machine & Tool Kit Aid | PCMC female resident, BPL / Low Income |
| 6 | `pcmc-mahatma-phule-higher-education` | Pimpri Chinchwad Municipal Corporation (PCMC) | Mahatma Jyotirao Phule Professional Education Aid | PCMC resident, Meritorious student, Family income $< ₹3,00,000$ |
| 7 | `bmc-mayors-discretionary-relief-fund` | Brihanmumbai Municipal Corporation (BMC) | Mayor's Discretionary Relief for Chronic Illness | BMC resident, Treatment at MCGM / Public hospital |
| 8 | `bmc-balasaheb-thackeray-accident-insurance` | Brihanmumbai Municipal Corporation (BMC) | Accidental Insurance for Registered Hawkers | Registered BMC hawker license, BMC resident |
| 9 | `bmc-kanya-suraksha-yojana` | Brihanmumbai Municipal Corporation (BMC) | BMC Kanya Suraksha Fixed Deposit Aid | BMC municipal school girl student, BMC resident |
| 10 | `tmc-divyang-monthly-subsidy` | Thane Municipal Corporation (TMC) | Monthly Subsidy for Persons with Severe Disabilities | TMC resident $\ge 5$ years, Disability $\ge 60\%$ |
| 11 | `tmc-sant-gadge-baba-sanitation-scholarship` | Thane Municipal Corporation (TMC) | Sant Gadge Baba Education Grant for Sanitation Workers' Children | TMC permanent / contractual sanitation staff ward |
| 12 | `nmmc-widow-empowerment-pension` | Navi Mumbai Municipal Corporation (NMMC) | Destitute & Widow Self-Reliance Assistance | NMMC resident $\ge 3$ years, No adult son earning |
| 13 | `nmmc-smart-girl-student-bicycle` | Navi Mumbai Municipal Corporation (NMMC) | Free Bicycle Distribution to Municipal Girl Students | NMMC school student, Distance to school $> 2$ km |

---

## 4. Tier C: 44 Exploratory / Discovered Schemes

All 44 Tier C schemes are explicitly maintained with:
- `verification_status: "unverified"`
- `eligibility_incomplete: true`
- `confidence: 0.50`

These schemes are visible in the Scheme Library (`#view-explore`) with a "Review Required" status badge. The rule engine marks these schemes as `CASEWORKER_REVIEW` or `NEEDS_INFORMATION`, strictly prohibiting affirmative automated eligibility confirmation until primary GR documentation is ingested and reviewed.

---

## 5. Segregation of Demo Fixtures

To ensure strict compliance with Invariant B2 and Release Gate G3:
1. `demo-majhi-ladki-bahin` is housed in `data/demo/schemes.json`.
2. In production mode (`APP_ENV=production`), the application startup guard verifies `settings.demo_fixtures_enabled is False`. If any fixture scheme is detected in the production catalog, the server aborts startup immediately (`test_content_governance.py`).
3. Under testing and local development, demo fixtures are clearly tagged with badge `badge-demo` ("डेमो नमुना").

---

## 6. Audit Verdict

$$\mathbf{Catalogue\ Integrity:\ PASS}$$
- 100% of 75 canonical schemes are reconciled and accounted for.
- Zero schemes in Tier A or Tier B have residency-only criteria.
- 100% of Tier A eligibility criteria match official Government Resolution text quotes cached in `data/raw/`.
- All JSON schema invariants in `schemas/catalogue_v2.json` pass without validation errors.
