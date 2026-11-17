# Application Channel Registry & Safe Portal Hand-Off Architecture

**Document Version:** 1.0.0 (Master Application Operations)  
**Date:** November 12, 2026  
**Target Territory:** Maharashtra, India  

---

## 1. Executive Summary

A critical mission of **Maharashtra Scheme Navigator** is transitioning citizens safely from discovery and preparation to genuine, official application submission. Scheme Navigator is **not a fake submission website**. Because neither MahaDBT nor Aaple Sarkar provides open third-party submission APIs, automated headless scraping, bot submission, or CAPTCHA bypass is strictly prohibited under the Information Technology Act 2000.

Scheme Navigator implements a **Safe Application Channel & Hand-Off Architecture**:
1. Verifies the authentic departmental portal or office counter.
2. Compiles a verified Pre-Submission Checklist and Field Mapping Table.
3. Provides an explicit statutory hand-off warning before leaving the platform.
4. Tracks citizen-reported application progress with rigorous truthfulness.

---

## 2. Seven Channel Classification Types

Every published welfare scheme and notified public service is assigned an authoritative channel type:

| Channel Type Code | Meaning & Citizen Action | Example Maharashtra Channels |
|---|---|---|
| `DIRECT_OFFICIAL_PORTAL` | Citizen applies online directly on an authenticated state portal using their personal credentials. | MahaDBT 2.0 / 1.0, Ladki Bahin Portal, PM-KISAN. |
| `AUTHORIZED_API_INTEGRATION` | Direct programmatic submission via an authorized, authenticated government API (Release Path B only). | *Status: Pending formal GoM bilateral agreement.* |
| `OFFLINE_OFFICE_APPLICATION` | Citizen submits physical printed form and certificates to designated government office or scrutiny committee. | Sanjay Gandhi Niradhar Branch at Taluka Tehsildar Office. |
| `AUTHORIZED_ASSISTANCE_CENTRE` | Citizen visits a sanctioned government facilitation centre (e.g. Setu Suvidha Kendra, Maha e-Seva Kendra, CSC). | Aaple Sarkar Setu Kendras, Gram Panchayat Anganwadi. |
| `PORTAL_STATUS_UNKNOWN` | Portal endpoint or departmental server unreachable or returning unexpected HTTP errors. | System warns citizen and provides physical departmental contact. |
| `APPLICATION_WINDOW_CLOSED` | Application intake period for the current financial or academic year has closed. | Post-matric scholarship portals outside intake cycle. |
| `APPLICATION_CHANNEL_UNAVAILABLE`| Scheme is announced in media or budget but formal application channel has not yet been notified via GR. | Candidate schemes pending gazetted launch. |

---

## 3. Official Channel Profiles for Maharashtra Schemes

### 3.1 Mukhyamantri Majhi Ladki Bahin Yojana
- **Channel Type:** `DIRECT_OFFICIAL_PORTAL` / `AUTHORIZED_ASSISTANCE_CENTRE`
- **Official URL:** `https://ladkibahin.maharashtra.gov.in/`
- **Facilitation Counters:** Anganwadi Centres, Gram Panchayat offices, Ward Offices, Setu Suvidha Kendras.
- **Login Requirements:** Citizen mobile number + Aadhaar OTP verification.
- **Fresh vs. Renewal:** Fresh applications open; periodic Aadhaar e-KYC verification.
- **Pre-Submission Checklist:**
  1. Aadhaar Card linked with active mobile number.
  2. Domicile Certificate of Maharashtra OR Maharashtra Ration Card (issued 15+ years ago).
  3. Income Certificate ($\le$ ₹2.5 Lakh) OR Yellow/Orange Ration Card.
  4. Aadhaar-seeded / DBT-enabled bank account passbook.

### 3.2 MahaDBT Post-Matric Scholarships (SC, OBC, VJNT, EBC)
- **Channel Type:** `DIRECT_OFFICIAL_PORTAL`
- **Official URLs:** `https://mahadbt.maharashtra.gov.in/` (1.0) and `https://mahadbt2.maharashtra.gov.in/` (2.0)
- **Login Requirements:** MahaDBT citizen registration + Aadhaar biometric / OTP verification.
- **Fresh vs. Renewal:**
  - *Fresh Applicants (1st Year):* Create new profile, upload caste, income, CAP admission slip, fee receipt.
  - *Renewal Applicants (Continuing Years):* Must log into original portal and provide previous year marksheet and promotion slip.
- **Pre-Submission Checklist:**
  1. Domicile Certificate of Maharashtra.
  2. Caste Certificate & Caste Validity (for professional courses).
  3. Current financial year Tahsildar Income Certificate.
  4. College bonafide certificate & CAP allotment slip.

### 3.3 Sanjay Gandhi Niradhar Anudan Yojana (SGNAY) & Shravanbal
- **Channel Type:** `OFFLINE_OFFICE_APPLICATION` / `AUTHORIZED_ASSISTANCE_CENTRE`
- **Official Portal Reference:** `https://aaplesarkar.mahaonline.gov.in/`
- **Physical Submission Counter:** Sanjay Gandhi Yojana Branch, Taluka Tehsildar Office.
- **Approval Body:** Monthly Taluka Committee chaired by Tehsildar with local non-official members.
- **Fresh vs. Renewal:** Fresh application; mandatory annual survival certificate (हयात असल्याचा दाखला) submission in November.

---

## 4. Citizen Application Tracking & Truth Invariants

Citizens can report their progress within their private session. In strict compliance with digital governance integrity:

```
[Not Started]
      │
      ▼
[Preparation in Progress]
      │
      ▼
[Ready to Apply]
      │
      ▼
[Official Portal Opened] ─── (Citizen navigates to official external URL)
      │
      ▼
[Submitted (Citizen Reported)] ── (Strictly labeled is_citizen_reported=True)
      │
      ▼
[Official Decision] ──────── (ONLY via verified authorized API or citizen upload of sanction letter)
```

**Non-Negotiable Tracking Rule:**
- Opening an external portal URL **never** marks an application as submitted.
- Any status submitted by the citizen is explicitly stamped `is_citizen_reported: true`.
- An application is marked `OFFICIALLY_SUBMITTED`, `OFFICIALLY_APPROVED`, or `OFFICIALLY_REJECTED` **only** when supported by an authentic government API response (Release Path B) or formal administrative sanction letter.
