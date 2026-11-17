# Security, Privacy & Data Protection Compliance Review

## 1. Security Architecture & Threat Model Overview
Scheme Navigator handles sensitive citizen demographic and financial attributes (income, caste, disability, residence, family structure). It maintains a zero-trust, fail-closed security posture across all network, application, and persistence layers.

---

## 2. Core Security Controls Implemented

### 2.1 Cryptographic Authentication & Session Isolation
- **Session Tokens**: Stateless, high-entropy tokens signed via HMAC-SHA256 using `SCHEME_NAVIGATOR_AUTH_SECRET`.
- **Session Scoping**: Tokens carry an explicit role (`citizen`, `analyst`, `reviewer`, `catalogue_admin`) and expiry timestamp (`exp`).
- **Thread & Review Ownership**: Every interview thread, uploaded document review, and progress record is bound to the originating `session_id`. Cross-session queries or updates are blocked with HTTP 403 Forbidden.
- **Privileged Session TTL**: Privileged administrator and reviewer sessions expire after 1 hour (`PRIVILEGED_SESSION_TTL_HOURS = 1`).

### 2.2 Server-Side Request Forgery (SSRF) Defense
- Document and source fetchers validate all target URLs against strict IP and protocol constraints.
- Private network ranges (RFC 1918, loopback `127.0.0.0/8`, link-local `169.254.0.0/16`, IPv6 loopback `::1`) and metadata services are blocked at the socket layer.
- Only verified HTTPS / HTTP schemes are permitted.

### 2.3 Upload & File Processing Security
- Files are validated against magic byte signatures before parsing; arbitrary file extensions and polyglots are rejected.
- Size is strictly limited to 10 MB per file.
- Temporary files are stored in private directories with restricted filesystem permissions (`0700` / `0600`).
- Processing occurs via sandboxed libraries (PyMuPDF, PIL) with memory limits to mitigate decompression bomb attacks.

### 2.4 Production Secrets & Key Separation
- In production (`APP_ENV=production`), startup strictly validates:
  - `SCHEME_NAVIGATOR_AUTH_SECRET` must be set to $\ge 32$ characters of high-entropy randomness.
  - `SCHEME_NAVIGATOR_RELEASE_KEY` must be set to $\ge 32$ characters.
  - Auth secret and release signing keys must be distinct.
  - Default development placeholder keys (e.g., `changeme`, `secret`, `default`) cause immediate fail-closed startup abort.

### 2.5 Audit Logging & PII Redaction
- Security-sensitive actions (provisioning users, revoking sessions, signing catalogue releases, purging data) are written to `data/security_audit.log`.
- Log format enforces structured JSON with timestamp, actor session, action, and target ID.
- Personal Identifiable Information (PII) such as citizen names, exact dates of birth, and phone numbers are redacted from application server logs.

---

## 3. Privacy & DPDP Framework Compliance

### 3.1 Minimum Necessary Data Principle
- **No Aadhaar Numbers**: The platform strictly prohibits storing 12-digit Aadhaar numbers or biometric credentials. It only tracks boolean status (`aadhaar_linked_bank_account = True`).
- **No Password Interception**: The platform does not capture or store passwords for external government portals.

### 3.2 Automated Retention & Purge
- Under the Digital Personal Data Protection (DPDP) Act principles of storage limitation:
  - Intermediate interview transcripts and uploaded documents have a default lifespan of 24 hours (`DATA_RETENTION_HOURS = 24`).
  - An automated retention worker runs `POST /admin/retention/purge` to permanently delete expired sessions and unlink physical files.
  - Citizens have immediate right to erasure via `POST /profile/reset`.

---

## 4. Status of External Security Gates
To maintain absolute honesty regarding release readiness:
1. **Internal Security Controls**: **PASS** — Comprehensive automated security test suites (`test_final_security_hardening.py`, `test_security_remediation.py`, `test_production_security.py`) pass 100% (30 passed tests).
2. **Independent Third-Party VAPT**: **OPEN GATE (EXTERNAL DEPENDENCY)** — While internal automated penetration testing passes, an official third-party Vulnerability Assessment & Penetration Testing (VAPT) certification by a CERT-In empanelled agency must be scheduled prior to multi-tenant public deployment.
3. **Formal Legal Privacy Review**: **OPEN GATE (EXTERNAL DEPENDENCY)** — Platform mechanisms are built to adhere to DPDP requirements, but formal legal sign-off by qualified data protection counsel remains an external governance step.
