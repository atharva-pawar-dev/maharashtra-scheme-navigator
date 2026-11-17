# Scheme Navigator — Enterprise Data Governance & Privacy Architecture

**Document Version:** 1.0.0 (Master Governance Standard)  
**Date:** November 12, 2026  
**Target Territory:** Maharashtra, India  
**Statutory Basis:** Digital Personal Data Protection Act (DPDPA) 2023, Information Technology Act 2000, Aadhaar Act 2016  

---

## 1. Core Principles of Citizen Data Protection

Scheme Navigator processes sensitive citizen demographic and socio-economic data (income, caste category, disability percentage, family status). To ensure ethical stewardship and complete regulatory compliance, the platform enforces five non-negotiable principles:

1. **Strict Data Minimization:** Only attributes strictly required to evaluate eligibility for active schemes are requested. Anonymous exploration requires zero personal data.
2. **Ephemeral Session Retention (24-Hour TTL):** Citizen interview transcripts, temporary files, and OCR extracts are permanently purged after 24 hours of inactivity.
3. **Zero Plaintext Aadhaar or Credential Storage:** Full 12-digit Aadhaar numbers, biometric templates, passwords, and OTPs are strictly rejected and never persisted.
4. **Purpose-Specific Citizen Consent:** Transparent, unambiguous consent is obtained in the citizen's preferred language before document extraction or profile assessment.
5. **No AI Model Training on Citizen Documents:** Uploaded citizen documents are never used to fine-tune or train third-party or internal machine learning models.

---

## 2. Data Classification & Handling Matrix

| Data Classification Tier | Examples in Scheme Navigator | Storage Mechanism | Retention Period | Encryption Standard | Access Control |
|---|---|---|---|---|---|
| **Tier 1: Public Knowledge** | Scheme descriptions, Government Resolutions, RTS statutory limits, portal URLs. | Public SQLite / PostgreSQL, JSON files. | Permanent (Versioned) | Plaintext / TLS 1.3 | Public Read-Only |
| **Tier 2: Anonymous Discovery Profile** | Age (years), gender, district, annual income estimate, bank link flag. | Ephemeral server session / in-memory. | 24 Hours (Purged) | In-Memory / AES-256 | Bound to Thread Owner |
| **Tier 3: Sensitive Extracted Data** | Extracted name, certificate numbers, disability percentage, caste category. | Document review SQLite / encrypted staging. | 24 Hours (or until audit complete) | AES-256-GCM at rest | Restricted to Thread Owner & Verified Reviewer |
| **Tier 4: Prohibited Credentials** | 12-digit Aadhaar, Aadhaar OTP, MahaDBT password, biometric data. | **NEVER STORED / REJECTED AT GATEWAY** | 0 Seconds (Zero retention) | N/A | N/A |

---

## 3. Automated Retention & Purge Pipeline (`src/scheme_navigator/security/retention.py`)

The platform implements an automated background retention purge engine:

```
[Hourly Retention Daemon]
           │
           ▼
[Identify Expired Sessions (Created > 24 Hours Ago)]
           │
           ├─► Delete Interview Records from interviews.sqlite3
           ├─► Delete Document Staging Files from disk / object storage
           ├─► Delete Review Queue Records from document_reviews.sqlite3
           │
           ▼
[Log Purge Audit Event (AuditEventType.DATA_RETENTION_PURGED)]
```

### Manual Trigger for Administrators:
Authorized administrators (`CATALOGUE_ADMIN`) can trigger on-demand data purging via:
`POST /admin/retention/purge?retention_hours=24`

---

## 4. Cryptographic Session Ownership & Isolation

In shared computing environments (such as Village Gram Panchayat centres, Maha e-Seva Kendras, or public library terminals), cross-citizen session leakage is a critical threat.

### Protection Mechanism:
- Every citizen session is issued a stateless, cryptographically signed token (`X-Session-Token`) signed with HMAC-SHA256.
- The server maintains strict thread-to-session ownership maps (`_thread_owners` and `_review_owners`).
- Any attempt to access an interview thread, document upload, or assessment response using a session token belonging to another citizen raises an immediate **HTTP 403 Forbidden** security error.

---

## 5. Citizen Rights under DPDPA 2023

1. **Right to Access Information:** Citizens can review all self-reported profile attributes and extracted document previews within their active session.
2. **Right to Correction & Erasure:** Citizens can edit extracted attributes prior to assessment or click "Reset Session" to erase all in-memory data immediately.
3. **Right of Grievance Redressal:** Transparent contact routing is provided for privacy inquiries and data-protection concerns.
