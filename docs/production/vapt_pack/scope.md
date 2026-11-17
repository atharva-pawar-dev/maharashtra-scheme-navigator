# VAPT Readiness Pack — Assessment Scope
## Maharashtra Scheme Navigator (MSN)

---

### 1. In-Scope Target Systems

| Asset / Endpoint | Nature | Environment | Network Boundary |
|---|---|---|---|
| `https://msn.staging.maharashtra.gov.in` (Staging Target) | Public Web Application | Staging VPC | External Internet |
| `/auth/*` (Authentication & Session Endpoints) | REST API | Staging | External Internet |
| `/interview/*` (LangGraph Citizen Interview Engine) | REST API | Staging | External Internet |
| `/eligibility/*` (Rule Engine & Explanations) | REST API | Staging | External Internet |
| `/documents/*` (Upload, Extraction & Pre-audit) | REST API & Storage | Staging | External Internet |
| `/trust/*` (Scheme Trust & Citizen Feedback) | REST API | Staging | External Internet |
| `/admin/*` (Catalogue Administration & Signing) | Privileged REST API | Staging | Restricted / IP-Allowlisted |

---

### 2. Out-of-Scope Assets

The following systems are strictly OUT OF SCOPE. Any testing against these targets is prohibited:
1. Official Government of Maharashtra production servers (`https://*.maharashtra.gov.in`, `https://gr.maharashtra.gov.in`).
2. National Informatics Centre (NIC) and MahaOnline production portals (`https://aaplesarkar.mahaonline.gov.in`).
3. Google Gemini API endpoints (`generativelanguage.googleapis.com`).
4. Bhashini / MeitY ULCA translation endpoints (`meity-auth.ulcacontrib.org`).
5. Underlying cloud hypervisor or DNS infrastructure of the staging host.

---

### 3. Assessment Classification
- **Type:** Gray-Box Web Application and API Vulnerability Assessment and Penetration Testing.
- **Standards:** OWASP Top 10 (2021), OWASP ASVS 5.0.0 Level 2, CERT-In Technical Security Guidelines for Government Websites.
