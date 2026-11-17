# Maharashtra Scheme Navigator — Observability, Health Probes & Incident Response Manual
## Health Probes, Structured Logging, Redaction Canaries, and CERT-In 6-Hour Incident Runbook

---

## 1. Health Probes Specification

Maharashtra Scheme Navigator exposes decoupled liveness and readiness probes:

### 1.1 Liveness Probe (`GET /healthz`)
- **Purpose:** Verifies that the FastAPI process is active and responsive to HTTP traffic.
- **Payload:** `{"status": "ok", "timestamp": "2026-11-17T17:30:00Z"}`
- **Success HTTP Code:** `200 OK`
- **Failure Condition:** Process hung, memory exhausted, or deadlock.

### 1.2 Readiness Probe (`GET /readyz`)
- **Purpose:** Verifies that all subsystems required to serve citizen traffic are operational:
  - Scheme catalogue loaded (`schemes_loaded > 0`)
  - Storage subsystem initialized (`storage_ready: true`)
- **Payload:**
  ```json
  {
    "status": "ready",
    "schemes_loaded": 75,
    "storage_ready": true,
    "environment": "local",
    "demo_fixtures_enabled": true,
    "data_retention_hours": 24
  }
  ```
- **Success HTTP Code:** `200 OK`
- **Degraded HTTP Code:** `503 Service Unavailable` if catalogue is empty or storage failed.

---

## 2. Structured Logging & Redaction Canaries

- **Format:** Single-line JSON objects output to `data/security_audit.log`.
- **Mandatory Schema:**
  - `timestamp`: UTC ISO 8601 string
  - `event_type`: Classified audit event (`SESSION_CREATED`, `DOC_UPLOADED`, `DOC_PURGED`, `CITIZEN_REPORT_SUBMITTED`, etc.)
  - `actor_id`: Anonymous citizen or authenticated staff user ID
  - `actor_role`: Hierarchical role (`citizen`, `analyst`, `legal_reviewer`, `catalogue_admin`, `system`)
  - `action`: Specific operation performed
  - `resource`: Target resource identifier
  - `client_ip`: Client IP address
  - `details`: Sanitized metadata dictionary
- **Redaction Filter:**
  - Keys containing `password`, `secret`, `token`, `otp`, `aadhaar`, `key`, `cvv` are sanitized to `"[REDACTED]"`.
  - Values containing 12-digit Indian Aadhaar patterns (`\b\d{4}[ -]?\d{4}[ -]?\d{4}\b`) are sanitized to `"[REDACTED_AADHAAR]"`.
- **Retention:** Retained for **180 days** in accordance with CERT-In Directive Section 70B(6).

---

## 3. CERT-In Mandatory 6-Hour Cyber Incident Response Runbook

Under CERT-In Directions 2022 (Direction ii), any cybersecurity incident (including unauthorized access, data breach, ransomware, or defacement) must be reported to CERT-In within **6 hours** of noticing.

### Incident Severity Classification

| Severity | Definition | Examples | Response SLA |
|---|---|---|---|
| **P0 (Critical)** | Active citizen data breach or system takeover | Exfiltration of uploaded documents, database compromise | 15 min response; CERT-In notify < 6h |
| **P1 (High)** | Tampering with scheme rules or signing key compromise | Unauthorized scheme published; signing key leaked | 30 min response; CERT-In notify < 6h |
| **P2 (Medium)** | Intermittent availability or abnormal rate of errors | Denial of service, rate limit exhaustion | 2 hour response |
| **P3 (Low)** | Informational or low-risk anomaly | Citizen reporting broken link on external portal | 24 hour response |

### CERT-In Incident Notification Template
- **To:** `incident@cert-in.org.in`
- **Subject:** `[CYBER INCIDENT REPORT] Maharashtra Scheme Navigator — <Incident Type>`
- **Body Template:**
  ```text
  1. Name of the Organisation: Department of Information Technology, Government of Maharashtra
  2. Date and Time of Incident (UTC/IST): [Timestamp]
  3. Nature and Type of Incident: [e.g. Unauthorized Administrative Account Provisioning / Data Tampering]
  4. Affected Systems / IPs / Domains: msn.staging.maharashtra.gov.in
  5. Description of the Incident: [Technical details including vectors, logs, and affected components]
  6. Impact Assessment: [Citizen PII impact: None, 24h retention limit active]
  7. Remedial Actions Taken: [Session revoked via POST /admin/auth/revoke, keys rotated, IP blocked]
  8. Contact Person / Incident Commander: Chief Information Security Officer (CISO)
     Email: ciso@maharashtra.gov.in / Phone: +91-22-XXXXXXXX
  ```

---

## 4. Incident Response Tabletop Simulation

### Scenario: "Malicious Candidate Injection / Scheme Defacement"
- **Trigger:** Automated ingestion crawler captures a third-party webpage mimicking an official Maharashtra Government Resolution promising unverified cash disbursements.
- **Step 1 — Automated Containment:**
  - Ingestion parser extracts content but enforces **Invariant B3**: Publication status is strictly capped at `EXTRACTED`.
  - The unverified scheme CANNOT enter the production catalogue without human legal review.
- **Step 2 — Reviewer Alert:**
  - Automated hash check notes mismatch against official Mantralaya gazette registry (`https://gr.maharashtra.gov.in`).
  - Scheme flagged with `REVIEW_REQUIRED` and alert logged to `security_audit.log`.
- **Step 3 — Administrative Rejection:**
  - Legal reviewer rejects candidate scheme in Reviewer UI.
  - Audit event recorded: `actor_role: legal_reviewer, action: reject_candidate`.
- **Step 4 — Domain Blocking:**
  - If malicious source URL was supplied by untrusted input, domain is added to SSRF blocklist in `src/scheme_navigator/security/ssrf.py`.
- **Conclusion:** Zero citizen exposure occurred because Invariant B3 fails closed by construction.
