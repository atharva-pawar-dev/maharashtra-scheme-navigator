# Maharashtra Scheme Navigator: Remaining Production Risks, Open Gates & Governance Boundaries

## 1. Executive Summary
This document provides a frank, evidence-based assessment of open operational, legal, infrastructure, and policy gates for the **Maharashtra Scheme Navigator**.

The application is engineered as an **independent citizen guidance platform**. It does not represent itself as an official government agency, does not grant benefits, and does not conduct unauthorized government database writes.

---

## 2. Genuine External Blockers & Open Production Gates

### 2.1 External Security Audit (CERT-In Empanelled VAPT)
- **Status**: **OPEN GATE (EXTERNAL DEPENDENCY)**
- **What is Blocked**: Multi-tenant public internet hosting on high-traffic state infrastructure.
- **Why it is Blocked**: Internal security testing passes 100% (30 passed security tests covering HMAC tokens, session isolation, SSRF, and file upload validation). However, industry best practices and Indian government cybersecurity guidelines mandate a formal Vulnerability Assessment and Penetration Testing (VAPT) certification conducted by a CERT-In empanelled auditing agency.
- **Does it Block Independent Public Release?**: It blocks deployment as an enterprise multi-tenant cloud service. It does **not** block local evaluation, pilot kiosk testing, or staging reviews.
- **Action Required**: Retain a CERT-In empanelled security agency to execute external penetration testing against the production staging environment and issue a certificate of compliance.

### 2.2 Formal Legal Privacy Review under DPDP Act, 2023
- **Status**: **OPEN GATE (EXTERNAL DEPENDENCY)**
- **What is Blocked**: Enterprise legal sign-off for public deployment.
- **Why it is Blocked**: Technical safeguards (data minimization, zero Aadhaar number retention, 24-hour automated file purging, one-click profile reset) are implemented and verified. However, formal legal sign-off from qualified data protection counsel is required to certify terms of service, privacy notice, and data fiduciary compliance.
- **Does it Block Independent Public Release?**: It blocks public production launch without legal disclaimer.
- **Action Required**: Legal review of the privacy notice and data retention policy by specialized Indian technology and data privacy legal counsel.

### 2.3 Government API Authorization & Formal Partnership
- **Status**: **EXTERNAL BOUNDARY (NOT A CODE DEFECT)**
- **What is Blocked**: Live, automated retrieval of official government application status and direct electronic form submission into MahaDBT or Aaple Sarkar backends.
- **Why it is Blocked**: No third-party platform may access private government APIs or state databases without a formal Memorandum of Understanding (MoU), API licensing agreement, and security clearance from the Directorate of Information Technology (DIT), Government of Maharashtra.
- **Does it Block Independent Public Release?**: **NO.** The product operates cleanly as an independent citizen guidance platform using the honest tracking workflow (`is_citizen_reported = True`) and official portal handoff links.
- **Action Required**: If the State Government desires native integration, formal inter-agency MoU and API gateway provisioning with MahaDBT / MahaOnline is required.

---

## 3. Unresolved Policy Questions in Upstream Government Sources

### 3.1 Shravanbal Seva Rajya Nivruttivetan Yojana (Group A vs. Group B)
- **Status**: `POLICY_UNRESOLVED`
- **Issue**: Historical Government Resolutions stipulate an annual family income ceiling of ₹21,000 for Group A (state-funded pension for elderly persons not on the central BPL list). However, subsequent social justice department press releases and district circulars reference ₹50,000, while operative gazetted GRs have not updated the principal statutory ceiling.
- **Platform Handling**: Marked as `POLICY_UNRESOLVED` with explicit citizen advisory: *"Statutory ceiling ₹21,000 in principal GR. Contact local Tahsildar Sanjay Gandhi branch for district-level implementation orders."*

### 3.2 Post-Matric OBC Tuition Fee Reimbursement for Private Professional Courses
- **Status**: `POLICY_UNRESOLVED`
- **Issue**: Government Resolutions sanction 100% tuition fee reimbursement for girl students in higher and technical education whose family income is $\le ₹8,00,000$. However, certain unaided private university institutions have petitioned against delayed state reimbursement, leading to variable admission-time fee collection.
- **Platform Handling**: Gated as `REVIEW_REQUIRED` with transparent explanation of the operative 2024 GR.

---

## 4. Municipal Welfare Data Asymmetry
- **Finding**: Of the 29 Municipal Corporations in Maharashtra, 5 (PMC, PCMC, BMC, TMC, NMMC) publish structured welfare schemes with digital guidelines. The remaining 24 corporations focus their portals exclusively on civic services (property tax, water bills, building permissions), administering welfare through offline Standing Committee budget allocations.
- **Platform Handling**: Transparently documented as `NO PUBLIC SCHEME INFORMATION FOUND IN THE SOURCES EXAMINED`. Citizens are routed to physical Ward Offices and Urban Community Development (UCD) cells rather than falsely claiming the municipality has no welfare initiatives.

---

## 5. Storage Scalability & Production Relational Database
- **Current Setup**: SQLite with WAL mode and versioned migrations (`core/migrations.py`).
- **Production Migration**: PostgreSQL DDL schema and connection pooling configuration prepared in `docs/deployment.md`. Production deployment requires provisioning an enterprise managed PostgreSQL database instance (e.g., AWS RDS PostgreSQL or Azure Database for PostgreSQL).
