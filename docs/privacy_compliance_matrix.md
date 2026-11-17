# Scheme Navigator — DPDP Act 2023 & Statutory Privacy Compliance Matrix

**Document Version:** 1.0.0 (Master Statutory Audit)  
**Date:** November 12, 2026  
**Target Territory:** Maharashtra, India  
**Applicable Statutes:** Digital Personal Data Protection Act (DPDPA) 2023, DPDP Rules 2025, IT Act 2000, Aadhaar Act 2016, CERT-In Directions  

---

## 1. Statutory Compliance Matrix

| DPDPA 2023 Section | Legal Obligation Description | Technical Implementation in Scheme Navigator | Compliance Status |
|:---|:---|:---|:---:|
| **Section 5(1) & (2)** | **Notice Requirement:** Transparent notice explaining personal data sought, specific purpose, and principal rights in multiple recognized languages. | Multilingual privacy notices provided in English, Marathi, and Hindi before interview or document upload. Clear notice: independent guidance only. | **COMPLIANT** |
| **Section 6(1)** | **Valid Consent:** Consent must be free, specific, informed, unconditional, and unambiguous with clear affirmative action. | Explicit affirmative toggle required before voice transcription or document processing; consent is unbundled from anonymous scheme browsing. | **COMPLIANT** |
| **Section 6(4)** | **Consent Withdrawal:** Citizen must be able to withdraw consent as easily as giving it. | Single-click "Reset Session" button instantly clears local session tokens and terminates server-side interview thread. | **COMPLIANT** |
| **Section 4 & 7** | **Data Minimization & Purpose Limitation:** Process data strictly necessary for preliminary eligibility evaluation. | Only relevant fields are collected; anonymous browsing requires zero PII; no secondary marketing or behavioral analytics. | **COMPLIANT** |
| **Section 8(1)** | **Accuracy & Completeness:** Ensure personal data processed is accurate and complete where used to make decisions. | Deterministic rule engine checks exact fields; machine extractions are presented to citizen for confirmation before evaluation. | **COMPLIANT** |
| **Section 8(5)** | **Reasonable Security Safeguards:** Implement technical and organizational measures to prevent breach. | AES-256 encryption at rest, TLS 1.3 in transit, HMAC-SHA256 session ownership tokens, SSRF protection, strict rate limiting. | **COMPLIANT** |
| **Section 8(6)** | **Data Breach Notification:** Inform Data Protection Board and affected principals in the event of personal data breach. | Incident response plan documented with 6-hour CERT-In / DPBI reporting SLA in [docs/security_assessment.md](file:///c:/Users/Admin/Downloads/scheme-navigator/scheme-navigator/docs/security_assessment.md). | **COMPLIANT** |
| **Section 8(7) & (8)** | **Storage Limitation & Erasure:** Erase personal data once the purpose is served or consent is withdrawn. | Automated retention engine enforces 24-hour TTL on interview transcripts, staged files, and review queues (`purge_expired_data`). | **COMPLIANT** |
| **Section 9** | **Processing of Children's Data:** No processing causing detrimental effect on well-being of child; obtain verifiable parental consent. | Scholarship features for minors do not track behavioral telemetry; educational fee queries operate anonymously or with guardian consent. | **COMPLIANT** |
| **Section 11, 12, 13** | **Rights of Data Principal:** Right to access summary of data, right to correction, erasure, and grievance redressal. | Real-time live profile summary displays all stored attributes; citizen can edit extracted fields; contact channels provided. | **COMPLIANT** |
| **Section 16** | **Cross-Border Transfer:** Restriction on transfer of personal data outside India as notified by Central Government. | System architecture binds locally to `127.0.0.1` and is configured for domestic hosting within India (AWS ap-south-1 Mumbai / MeitY-empaneled cloud). | **COMPLIANT** |

---

## 2. Aadhaar Act 2016 & UIDAI Circulars Compliance

- **Zero Plaintext Aadhaar Storage:** Full 12-digit Aadhaar numbers are never stored in databases, logs, or file storage.
- **No Aadhaar Biometric or OTP Interception:** In portal assistance mappings, Aadhaar authentication fields are classified as `RESTRICTED_SECURITY_FIELD`. Scheme Navigator explicitly directs citizens to perform Aadhaar authentication directly on official government portals.
- **Masked Reference Only:** Where a citizen uploads a document containing an Aadhaar reference, only the masked last 4 digits (e.g. `XXXX-XXXX-1234`) are parsed for consistency auditing.

---

## 3. CERT-In Directions 2022 Compliance

- **System Clock Synchronization:** All event logging synchronizes with National Physical Laboratory (NPL) NTP servers using UTC timestamps.
- **Audit Logging Integrity:** Security logs (`security_audit.log`) record authentication events, access denials, and administrative actions with HMAC digests.
- **Log Retention Policy:** In production configurations, operational access logs are retained in secure, read-only storage for 180 days in compliance with CERT-In directions.
