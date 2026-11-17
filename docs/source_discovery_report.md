# Maharashtra Government Scheme Source Discovery & Lineage Report

**Document Version:** 1.3.0 (Reality Audit Baseline)  
**Date:** November 13, 2026  
**Target Territory:** Maharashtra, India  
**Audit Principle:** Verifiable Lineage & Canonical Identity Resolution  
**Publication Reality Invariant:** Active Published Production Schemes = 0 (ZERO) | Active Demo Fixtures = 2 | Quarantined Draft Candidates = 7  

---

## 1. Discovery Methodology & Architecture

Scheme discovery in **Maharashtra Scheme Navigator** does not rely on random web scraping or unverified search engine queries. The platform utilizes an **air-gapped, verifiable discovery pipeline** founded on structured state directories, gazetted Government Resolutions, and official departmental registries.

```
+----------------------------------------------------------------------------------------------------+
|                                    OFFICIAL DISCOVERY PIPELINE                                     |
+----------------------------------------------------------------------------------------------------+
  1. Discovery Target Identification (iGOD, State Planning Portal, MahaDBT, Aaple Sarkar)
  2. Respectful Retrieval (Robots.txt compliance, zero bypass of CAPTCHA/Auth, rate-throttling)
  3. Artifact Preservations (SHA-256 Content Hashing & Local Staging)
  4. Multilingual Entity & Clause Extraction (Devanagari OCR, Annexure parsing, Table extraction)
  5. Canonical Deduplication (Alias resolution across multiple state portal listings)
  6. Source Evidence Binding (Gazette GR -> Guidelines -> Department Portal -> Portal FAQ)
  7. Fail-Closed Reviewer Gate (Candidate Scheme Dossier Review prior to Publication)
```

---

## 2. In-Depth Analysis of Core Official Portals

### 2.1 myScheme Maharashtra Aggregator
- **URL:** `https://www.myscheme.gov.in/search/state/Maharashtra`
- **Role in Pipeline:** Discovery lead generator. myScheme indexes 112+ schemes available in Maharashtra.
- **Limitation:** myScheme summaries frequently lack exact operational cut-offs (e.g. precise land ceiling in irrigated vs. non-irrigated talukas) and do not reflect real-time Maharashtra departmental circulars.
- **Rule of Treatment:** myScheme entries are treated as *discovery leads*, never as standalone proof of a statutory rule. Every leaf condition extracted from myScheme must be substantiated against a gazetted Government Resolution on `gr.maharashtra.gov.in`.

### 2.2 MahaDBT (1.0 Legacy & 2.0 Modern)
- **MahaDBT 2.0:** `https://mahadbt2.maharashtra.gov.in/`
- **MahaDBT 1.0:** `https://mahadbt.maharashtra.gov.in/`
- **Architecture & Migration Status:**
  - MahaDBT 2.0 represents the state's modernized direct benefit transfer portal featuring responsive mobile interfaces and improved Aadhaar authentication.
  - MahaDBT 1.0 continues to handle continuing students and specific departments (Social Justice, Tribal Welfare, Higher Education).
  - Scheme Navigator maps the exact target destination based on whether the citizen is seeking a fresh admission or a continuing renewal.
- **Application Windows:** Academic intake operates on an annual cycle typically opening in July and closing with extensions between December and February.

### 2.3 MahaSarathi Unified Citizen Portal
- **URL:** `https://mahasarathi.maharashtra.gov.in/`
- **Role:** Maharashtra's next-generation unified citizen portal incorporating MahaID and single sign-on (SSO).
- **Interoperability Finding:** MahaSarathi is architected for government-to-citizen (G2C) and department-to-department (G2G) interoperability. While public APIs are not yet exposed for third-party public platforms without formal MOUs, Scheme Navigator establishes an authorized integration adapter specification ready for deployment upon formal GoM authorization.

### 2.4 Maharashtra Government Resolutions (शासन निर्णय)
- **URL:** `https://gr.maharashtra.gov.in/1145/Government-Resolutions`
- **Hierarchy:** Primary legal authority for every state condition.
- **Lineage Verification:** Every rule leaf tracks:
  - GR Date (e.g. 28 June 2024 for Majhi Ladki Bahin base rules).
  - GR Number (Unique Departmental Identification Code).
  - Department (e.g. महिला व बाल विकास विभाग).
  - SHA-256 Digest of the authoritative PDF.

### 2.5 Aaple Sarkar (Right to Services Portal)
- **URL:** `https://aaplesarkar.mahaonline.gov.in/`
- **Public Services Registry:** Contains 504 notified citizen services under the Maharashtra Right to Services Act 2015.
- **Statutory Timelines:** Establishes legally mandated maximum service delivery days (e.g., Domicile: 15 days; Income Certificate: 15 days; Caste Certificate: 21 days).

---

## 3. Discovered Raw Artifacts vs. Canonical Scheme Deduplication

The 1,319 records indexed in initial scans represent raw portal items, gazette documents, RTS service listings, and directory entries. Through the deduplication engine (`src/scheme_navigator/ingestion/dedup.py`), these are synthesized into **9 Canonical Schemes**:

| Canonical Scheme ID | Official Scheme Title | Key Department | Mapped Aliases | Raw Docs Linked | Current Status | Publication Reality |
|---|---|---|:---:|:---:|---|---|
| `demo-majhi-ladki-bahin` | Mukhyamantri Majhi Ladki Bahin Yojana (Demo Fixture) | Women and Child Development | 5 | 8 | Active Demo Fixture | **ACTIVE_DEMO_FIXTURE** (Badge Enforced) |
| `demo-indira-gandhi-old-age-pension` | Indira Gandhi National Old Age Pension Scheme (IGNOAPS) (Demo Fixture) | Social Justice and Special Assistance | 4 | 6 | Active Demo Fixture | **ACTIVE_DEMO_FIXTURE** (Badge Enforced) |
| `candidate-majhi-ladki-bahin` | Mukhyamantri Majhi Ladki Bahin Yojana (Candidate) | Women and Child Development | 5 | 8 | Draft Candidate | **DRAFT_QUARANTINED** (`publication_authorized: false`) |
| `candidate-sanjay-gandhi-niradhar-anudan` | Sanjay Gandhi Niradhar Anudan Yojana (SGNAY) | Social Justice and Special Assistance | 4 | 7 | Draft Candidate | **DRAFT_QUARANTINED** (`publication_authorized: false`) |
| `candidate-shravanbal-sewa-rajya-nivruttivetan` | Shravanbal Seva Rajya Nivruttivetan Yojana | Social Justice and Special Assistance | 4 | 6 | Draft Candidate (Inquiry `POL-SHRAVANBAL-01`) | **DRAFT_QUARANTINED** (`publication_authorized: false`) |
| `candidate-post-matric-sc` | Post-Matric Scholarship for SC Students | Social Justice and Special Assistance | 3 | 5 | Draft Candidate | **DRAFT_QUARANTINED** (`publication_authorized: false`) |
| `candidate-post-matric-obc` | Post-Matric Scholarship for OBC Students | OBC, VJNT, SBC & SEBC Welfare | 3 | 5 | Draft Candidate (Inquiry `POL-OBC-01`) | **DRAFT_QUARANTINED** (`publication_authorized: false`) |
| `candidate-post-matric-obc-girls-professional` | Tuition Fee Reimbursement for OBC/EBC Girls (Higher & Tech) | Higher and Technical Education | 3 | 4 | Draft Candidate | **DRAFT_QUARANTINED** (`publication_authorized: false`) |
| `candidate-tuition-fees-obc-girls` | 100% Tuition & Exam Fee Reimbursement for Girls | Higher and Technical Education | 3 | 4 | Draft Candidate | **DRAFT_QUARANTINED** (`publication_authorized: false`) |

---

## 4. Official Source Acquisition & Lineage Integrity

For all core and departmental registries in `data/source_registry/sources.json`:
- **Retrieval Status:** `RETRIEVED` via air-gapped ingestion tools or verified offline snapshot archives.
- **Cryptographic Lineage:** Every source payload is stamped with a SHA-256 hash.
- **Parsing Verification:** Core portals parsed into `PARSED_CANONICAL` schemas; departmental directories parsed into `PARSED_PARTIAL` lead listings awaiting individual GR binding.
- **Zero Hallucination Gate:** An unverified scheme lead from a portal cannot be promoted to a candidate without an authoritative Government Resolution SHA-256 digest.
