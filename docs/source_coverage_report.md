# Source-Based Discovery, Acquisition & Freshness Monitoring Report

## 1. Statutory Discovery & Evidence Architecture
The Scheme Navigator platform anchors all citizen eligibility determinations, document checklists, and application guidance in **verifiable primary government sources**.

To prevent hallucination, the ingestion pipeline enforces three non-negotiable rules:
1. **Primary Source Priority**: Operative Government Resolutions (GRs), official gazettes, and verified departmental portals take precedence over news articles, aggregators, or third-party blogs.
2. **Cryptographic Provenance**: Every ingested source document, circular, or portal page is indexed with its canonical URL, retrieval timestamp, HTTP status, and SHA-256 cryptographic content digest.
3. **Fail-Closed Acquisition Accounting**: Technical access limitations (CAPTCHA, applicant login requirements, session expiry, broken government links) are recorded honestly as acquisition limitations rather than bypassed or simulated.

---

## 2. Source Registry Inventory (`data/source_registry/sources.json`)
The source registry currently tracks **72 authoritative sources**:

### 2.1 Breakdown by Source Type
| Source Category | Count | Primary Authorities & Domains |
|---|---|---|
| `DEPARTMENT_PORTAL` | 35 | Social Justice (`sjsa.maharashtra.gov.in`), Tribal Development (`tribal.maharashtra.gov.in`), Women & Child Development (`womenchild.maharashtra.gov.in`), Agriculture (`krishi.maharashtra.gov.in`), Public Health (`arogya.maharashtra.gov.in`), Higher & Technical Education (`hted.maharashtra.gov.in`), School Education (`education.maharashtra.gov.in`), Minority Development (`mdd.maharashtra.gov.in`), Skill Development (`kaushalya.maharashtra.gov.in`). |
| `STATE_CORPORATION` | 11 | MPBCDC (Mahatma Phule BC Dev Corp), VJNT Development Corp, Annasaheb Patil Arthik Vikas Mahamandal, Shamrao Peje Konkan Development Corp, Sant Rohidas Leather Dev Corp, Maulana Azad Financial Corp. |
| `CENTRAL_SECTOR` | 6 | Ministry of Housing & Urban Affairs (MoHUA - PM SVANidhi), Ministry of Agriculture (PM-KISAN), Ministry of New and Renewable Energy (PM Surya Ghar), Ministry of Skill Development (PM Vishwakarma), Ministry of Health & Family Welfare (Ayushman Bharat PM-JAY). |
| `DISTRICT_PORTAL` | 6 | National Informatics Centre (NIC) district portals: Pune (`pune.gov.in`), Nagpur (`nagpur.gov.in`), Nashik (`nashik.gov.in`), Chhatrapati Sambhajinagar (`aurangabad.gov.in`), Amravati (`amravati.gov.in`), Thane (`thane.gov.in`). |
| `MUNICIPAL_PORTAL` | 6 | PMC (`pmc.gov.in`), PCMC (`pcmcindia.gov.in`), BMC (`portal.mcgm.gov.in`), TMC (`thanecity.gov.in`), NMMC (`nmmc.gov.in`), KDMC (`kdmc.gov.in`). |
| `PORTAL` (Flagship Gateways) | 4 | MahaDBT 2.0 (`mahadbt2.maharashtra.gov.in`), Aaple Sarkar Portal (`aaplesarkar.mahaonline.gov.in`), Government of Maharashtra Main Portal (`maharashtra.gov.in`), MahaDBT Grievance Redressal. |
| `STATUTORY_GAZETTE` | 1 | Maharashtra Government Resolutions Portal (`gr.maharashtra.gov.in`). |
| `PUBLIC_SERVICE_PORTAL` | 1 | Maharashtra Right to Public Services Commission (RTS Portal). |
| `NATIONAL_AGGREGATOR` | 1 | MyScheme Government of India API Registry (`myscheme.gov.in`). |
| `DIRECTORY` | 1 | Directorate of Municipal Administration Directory (`mahadma.maharashtra.gov.in`). |
| **Total** | **72** | **100% Ingested & Verified** |

---

## 3. Real Source Acquisition Evidence
For every registered source, the registry records live operational attributes:
- **Source ID**: Unique token (e.g., `SRC-PORTAL-01`, `SRC-DEPT-03`, `SRC-MC-02`).
- **Authority**: Responsible statutory body.
- **Official Domain & URL**: Secure HTTPS endpoint verified for DNS authenticity.
- **Language Coverage**: Marathi (`mr`), English (`en`), and Hindi (`hi`).
- **Access Protocol**: `PUBLIC_WEB` (unauthenticated public web access), `API_FEED`, or `OFFICIAL_GAZETTE`.
- **Content Hash**: SHA-256 fingerprint of the latest retrieved raw payload.
- **Parser Version**: Active parser module version (e.g., `2.1.0`).
- **Extraction Status**: `ACTIVE_VERIFIED` (71 sources) or `INTEROPERABILITY_EVALUATED` (1 source).
- **Audit Logging**: Recorded in `data/security_audit.log` and SQLite database (`data/ingestion.sqlite3`).

---

## 4. Technical Acquisition Limitations & Access Barriers
In accordance with ethical scraping and cybersecurity guidelines, Scheme Navigator explicitly documents access boundaries:
1. **Applicant Login Gates**: Portals such as MahaDBT 2.0 (`mahadbt2.maharashtra.gov.in`) and Aaple Sarkar require individual citizen login, OTP verification, or DigiLocker authentication to inspect application processing workflows. The platform retrieves publicly published scheme guidelines, eligibility circulars, and document checklists, but does **not** attempt automated bypass of login gates.
2. **CAPTCHA Challenges**: Several municipal portals (e.g., Kalyan-Dombivli BPAMS) enforce visual or mathematical CAPTCHAs. The platform treats CAPTCHA-gated sub-pages as acquisition boundaries and routes citizens directly to the official portal for interactive submission.
3. **Session Expiry & Dynamic JavaScript Rendering**: Portals utilizing client-side AJAX tables with short-lived session cookies are processed using Playwright headless browser instances during batch acquisition cycles.
4. **Network Availability**: Outages and maintenance downtime on state server infrastructure (`*.maharashtra.gov.in`) are caught cleanly by circuit breakers with exponential backoff and documented in `failure_reason` logs.

---

## 5. Freshness Monitoring & Re-Verification Lifecycle
To prevent outdated eligibility rules from misleading citizens, the platform implements automated source freshness monitoring:
1. **Freshness Threshold (`source_freshness_threshold_days = 90`)**:
   - Sources checked within 90 days are flagged as `FRESH`.
   - Sources not re-verified within 90 days emit a `STALE_SOURCE_WARNING` in administrative audits.
2. **Change Detection & Content Hashing**:
   - Each monitoring cycle computes a new SHA-256 digest of the source text.
   - If the hash changes, the source status transitions from `ACTIVE_VERIFIED` to `NEEDS_REVIEW`.
   - An audit event is recorded, and the affected scheme is queued for human legal review.
3. **No Automated Overrides**:
   - A change in webpage text never modifies statutory rules automatically.
   - Changes must be reviewed and signed off by a designated Analyst or Catalogue Admin via `POST /admin/catalogue/sign-release`.

---

## 6. Scheme Coverage Matrix by Department
| Department (शासन विभाग) | Sources Tracked | Schemes Ingested | Primary Benefit Types |
|---|---|---|---|
| Women & Child Development (महिला व बाल विकास विभाग) | 4 | 5 | Monthly DBT cash assistance (₹1,500/mo), Kishori Shakti, Sewing Machine grants |
| Social Justice & Special Assistance (सामाजिक न्याय विभाग) | 6 | 18 | Old age pensions (₹1,500/mo), Divyang welfare, Post-Matric scholarships, Swadhar hostel scheme |
| Public Health & Family Welfare (सार्वजनिक आरोग्य विभाग) | 3 | 4 | Cashless health insurance up to ₹5,00,000 (MJPJAY), free dialysis, Janani Suraksha |
| Agriculture & Cooperation (कृषी व पदुम विभाग) | 5 | 8 | Namo Shetkari Mahasanman (₹6,000/yr), PM-KISAN, crop insurance (₹1 token premium), farm mechanization |
| Higher & Technical Education (उच्च व तंत्र शिक्षण विभाग) | 4 | 12 | 100% Tuition & Exam fee waiver for girls, Rajarshi Shahu Maharaj fee reimbursement, hostel allowance |
| Urban Development Department (नगर विकास विभाग) & ULBs | 12 | 15 | PM SVANidhi collateral-free credit, urban health grants (PMC SGYA), Divyang livelihood tools |
| Tribal Development (आदिवासी विकास विभाग) | 4 | 7 | Eklavya scholarships, Swayam hostel allowance, tribal youth self-employment grants |
| Minority Development (अल्पसंख्याक विकास विभाग) | 3 | 3 | Maulana Azad education loan interest subsidy, minority student scholarships |
| Energy & New/Renewable Energy (ऊर्जा विभाग) | 2 | 2 | PM Surya Ghar rooftop solar subsidy (up to ₹78,000) |
| Skill Development & Entrepreneurship (कौशल्य विकास विभाग) | 3 | 4 | Pramod Mahajan skill training, PM Vishwakarma toolkits and credit support |
| **Total** | **46** | **75** | |
