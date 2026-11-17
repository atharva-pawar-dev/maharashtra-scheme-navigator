# Maharashtra Scheme Navigator — Application Channel Coverage Report
## Multi-Channel Hand-Off, Portal Integration & Citizen Assistance Infrastructure

**Total Mapped Channels:** 60
**Coverage Ratio:** 100% of Canonical Schemes Mapped to Operational Application Channels
**Statutory Hand-Off Mandate:** Complete anti-spoofing notifications and direct verified government links.

---

### 1. Application Channel Distribution

| Channel Type | Count | Description & Delivery Mechanism |
| :--- | :---: | :--- |
| `DIRECT_OFFICIAL_PORTAL` | 34 | Verified official application route |
| `OFFLINE_OFFICE_APPLICATION` | 23 | Verified official application route |
| `AUTHORIZED_ASSISTANCE_CENTRE` | 3 | Verified official application route |

---

### 2. Key Portals & Delivery Hubs

1. **MahaDBT (https://mahadbt.maharashtra.gov.in):** Direct online Aadhaar-linked beneficiary registration for education, scholarships, and farmer subsidies.
2. **Aaple Sarkar (https://aaplesarkar.mahaonline.gov.in):** Citizen service portal for prerequisite revenue and social welfare certificates under the RTS Act 2015.
3. **Mahaswayam (https://www.mahaswayam.gov.in):** Employment, skill training, and entrepreneurship loan application tracking.
4. **PM-Kisan & MahaDBT Agriculture (https://pmkisan.gov.in):** Central-state integrated DBT for farmer income assistance.
5. **MJPJAY Portal (https://www.jeevandayee.gov.in):** Cashless hospital empanelment and healthcare pre-authorization at 1,000+ hospitals across Maharashtra.

---

### 3. Detailed Channel Mapping Sample

| Scheme ID | Portal Name | Application Window | Login Requirement | Tracking / Hand-Off |
| :--- | :--- | :--- | :--- | :--- |
| `demo-majhi-ladki-bahin` | Official Ladki Bahin Portal / Nari Shakti Doot | Open (FY 2024-2025) | Citizen Mobile OTP + Aadhaar Verification | Yes |
| `demo-indira-gandhi-old-age-pension` | Taluka Tehsildar Office (Sanjay Gandhi Yojana Branch) & Aaple Sarkar | Open (FY 2024-2025) | Aaple Sarkar Citizen Login or In-person submission | Yes |
| `candidate-majhi-ladki-bahin` | Official Ladki Bahin Portal | Open (FY 2024-2025) | Mobile OTP + Aadhaar Verification | Yes |
| `candidate-sanjay-gandhi-niradhar-anudan` | Taluka Tehsildar Office (Sanjay Gandhi Branch) | Open (FY 2024-2025) | In-person submission at Taluka Tehsildar Office | Yes |
| `candidate-shravanbal-sewa-rajya-nivruttivetan` | Taluka Tehsildar Office / Aaple Sarkar Kendra | Open (FY 2024-2025) | In-person at Tehsildar Sanjay Gandhi Branch | Yes |
| `candidate-post-matric-sc` | MahaDBT (Social Justice and Special Assistance Department) | Open (FY 2024-2025) | MahaDBT Citizen Registration with Biometric / Aadhaar OTP Verification | Yes |
| `candidate-post-matric-obc` | MahaDBT (OBC, VJNT, SBC & SEBC Welfare Department) | Open (FY 2024-2025) | MahaDBT Citizen Registration + Aadhaar OTP | Yes |
| `candidate-post-matric-obc-girls-professional` | MahaDBT (Higher & Technical Education Department) | Open (FY 2024-2025) | MahaDBT Portal Login | Yes |
| `candidate-tuition-fees-obc-girls` | MahaDBT Portal | Open (FY 2024-2025) | MahaDBT Portal Login | Yes |
| `scheme-ebc-tuition-waiver` | MahaDBT Portal (Directorate of Higher Education) | Open (FY 2024-2025) | MahaDBT Citizen Registration + Aadhaar OTP | Yes |
| `scheme-majhi-kanya-bhagyashree` | Anganwadi Centre / Taluka Child Development Project Officer (CDPO) | Open (FY 2024-2025) | In-person submission at local Anganwadi Centre | Yes |
| `scheme-bhausaheb-fundkar-phalbag` | MahaDBT Shetkari Portal | Open (FY 2024-2025) | MahaDBT Farmer Registration + Aadhaar OTP | Yes |
| `scheme-namo-shetkari-maha-samman` | Maharashtra Agriculture Portal & PM-KISAN Portal | Open (FY 2024-2025) | Aadhaar e-KYC on PM-KISAN | Yes |
| `scheme-mukhyamantri-bal-seva` | District Child Protection Unit (DCPU) / District Collector Office | Open (FY 2024-2025) | In-person submission by legal guardian at DCPU office | Yes |
| `scheme-bal-sangopan-yojana` | District Child Welfare Committee (CWC) / Taluka CDPO | Open (FY 2024-2025) | In-person submission through recognized child welfare NGOs or CDPO office | Yes |
| `scheme-pm-kisan` | PM-KISAN Central Portal / CSC Centres | Open (FY 2024-2025) | Farmer Registration on PM-KISAN Portal with Aadhaar OTP / Biometric | Yes |
| `scheme-pm-mudra-yojana` | Udyamimitra Portal / Commercial & Co-operative Banks | Open (FY 2024-2025) | Udyamimitra Online Registration or Bank Branch Visit | Yes |
| `scheme-pm-svanidhi` | PM SVANidhi Portal / Municipal Ward Offices | Open (FY 2024-2025) | Mobile OTP + Aadhaar Authentication on PM SVANidhi portal | Yes |
| `scheme-pm-surya-ghar` | National Rooftop Solar Portal (PM Surya Ghar) | Open (FY 2024-2025) | Mobile OTP + Consumer Number Verification | Yes |
| `scheme-begum-hazrat-mahal` | National Scholarship Portal (NSP) | Open (FY 2024-2025) | NSP OTR (One Time Registration) + Aadhaar Verification | Yes |
| `scheme-ignwps-widow-pension` | Taluka Tehsildar Sanjay Gandhi Branch | Open (FY 2024-2025) | Aaple Sarkar / In-person | Yes |
| `scheme-igndps-disability-pension` | Taluka Tehsildar Office | Open (FY 2024-2025) | In-person submission | Yes |
| `scheme-national-family-benefit` | Taluka Tehsildar Sanjay Gandhi Desk | Open (FY 2024-2025) | In-person at Tehsildar desk | Yes |
| `scheme-post-matric-st` | MahaDBT Tribal Development Portal | Open (FY 2024-2025) | MahaDBT Portal Login | Yes |
| `scheme-post-matric-vjnt` | MahaDBT Bahujan Kalyan Portal | Open (FY 2024-2025) | MahaDBT Portal Login | Yes |

---

### 4. Statutory Anti-Spoofing & Citizen Safety

- Every channel dossier contains a mandatory `statutory_hand_off_notice` reminding citizens that Scheme Navigator is an independent guidance tool and does not charge fees or submit applications.
- In-app outbound portal links open in a new tab with `target='_blank' rel='noopener noreferrer'`.
- Citizen self-reported application submissions are tagged with `is_citizen_reported: true` to prevent fraudulent status fabrication.