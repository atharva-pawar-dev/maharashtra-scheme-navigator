# Application Integration Architecture: Direct APIs vs. Safe Portal Hand-Offs

**Document Version:** 1.0.0 (Master Integration Specification)  
**Date:** November 12, 2026  
**Target Territory:** Maharashtra, India  

---

## 1. Architectural Philosophy: The Two Operational Paths

In public sector digital services, an independent citizen-facing platform must maintain a clear, uncompromised boundary between two operating paradigms:

```
+----------------------------------------------------------------------------------------------------+
|                                    TWO OPERATIONAL PARADIGMS                                       |
+----------------------------------------------------------------------------------------------------+
  
  [PATH A: INDEPENDENT PUBLIC PLATFORM]             [PATH B: OFFICIAL GOVERNMENT PARTNERSHIP]
  - Operates today without external authorization.  - Operates only after formal government agreement.
  - Zero scraping, zero CAPTCHA bypass.             - Official REST/GraphQL gateway integration.
  - Transparent Pre-Submission Checklists.          - Automated programmatic application submission.
  - Verified hand-off to official portals.          - Real-time departmental webhook status tracking.
  - Citizen self-reported application progress.     - Official government acknowledgement slips.
```

---

## 2. Path A: Safe Portal Hand-Off Workflow (Current Baseline)

Where no formal bilateral submission API exists, Scheme Navigator utilizes a **Safe Portal Application Assistance Protocol**:

### Step 1: Pre-Submission Preparation & Field Mapping
The system compiles a structured `PortalApplicationPackage` (`src/scheme_navigator/services/portal_assistance.py`) containing:
- Target portal URL and official department name.
- Field Mapping Table: Suggests values extracted from verified documents (e.g. Applicant Name, Annual Family Income, Caste Category, Certificate Issue Dates).
- Explicit flag `is_sensitive: true` for identity fields, requiring the citizen to review before inputting on the external portal.

### Step 2: Pre-Submission Safety Checklist
Before the portal link is presented, the citizen is advised to verify:
- [ ] Active Aadhaar-linked mobile phone is in hand to receive government portal OTPs.
- [ ] Certified original documents are available in the required format (PDF/JPG, typically under 250KB–500KB on MahaDBT).
- [ ] Bank account is DBT-enabled (seeded with Aadhaar via NPCI mapping).

### Step 3: Verified External Navigation
- Clicking "Open Official Portal" launches the authentic destination in a new secure browser tab with `rel="noopener noreferrer"`.
- A prominent modal warning states:
  > *"Leaving Scheme Navigator: Independent citizen guidance platform. Not an official Government of Maharashtra portal. You will complete and submit your application personally on the government portal."*

### Step 4: Truthful Citizen Progress Tracking
- Once the portal opens, the platform records: `status: "official_portal_opened"`.
- When the citizen returns, they can report `status: "citizen_reported_submitted"`.
- **Integrity Rule:** The system strictly marks these entries as `is_citizen_reported: true`. It never marks an application as officially submitted without an authoritative government receipt.

---

## 3. Path B: Authorized API Integration Protocol (Future Partnership)

When a Maharashtra state department grants formal third-party application submission authorization, the platform activates dedicated API adapters:

### Core Integration Standards:
1. **Authentication:** OAuth 2.0 with Mutual TLS (mTLS) and short-lived JWT access tokens issued by the departmental gateway.
2. **Citizen Consent Artifact:** Every submission payload includes a signed JSON Web Signature (JWS) consent artifact containing the timestamp, purpose, and citizen approval.
3. **Idempotency Keys:** Every submission request transmits a unique `X-Idempotency-Key: UUIDv4` header to prevent duplicate submissions or double disbursements.
4. **Resilient Retry & Circuit Breakers:** Exponential backoff with jitter (initial interval 1s, factor 2, max retries 3) for transient 502/503/504 gateway timeouts.
5. **Payload Signing:** Requests are signed with an RSA-SHA256 private key registered with the Government of Maharashtra Public Key Infrastructure (PKI).
6. **Government Acknowledgement:** Stores the authoritative application acknowledgement number, date of receipt, and digital signature for citizen tracking.

---

## 4. Prohibited Integration Anti-Patterns

Scheme Navigator strictly forbids the following anti-patterns under any circumstances:
- **NO Headless Scraping / Puppeteer Login:** Never automates citizen login using headless browsers against government portals.
- **NO CAPTCHA Bypassing:** Never employs OCR, third-party solving services, or audio bypasses to circumvent state portal CAPTCHAs.
- **NO Password / OTP Interception:** Never prompts citizens to enter their MahaDBT passwords, Aaple Sarkar credentials, or Aadhaar OTPs into Scheme Navigator.
- **NO Reverse Engineering:** Never calls undocumented private departmental endpoints or mobile app backends without written contractual authorization.
