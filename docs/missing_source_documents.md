# Missing Official Source Documents & Gazettal Gaps (Phase 4.2)

**Project:** Scheme Navigator  
**Jurisdiction:** Government of Maharashtra & Ministry of Social Justice and Empowerment (GoI)  
**Status:** Audit & Compliance Review  

This document inventories official government records, resolutions, circulars, and gazettes that are currently **missing, unverified, un-gazetted, or unavailable in primary public repositories** for the five candidate schemes.

Under Scheme Navigator's **fail-closed source policy**, no eligibility rule or benefit quantum may be inferred from media reports, political announcements, or secondary aggregators in the absence of these authoritative primary texts.

---

## 1. Mukhyamantri Majhi Ladki Bahin Yojana

### 1.1 Un-Gazetted Benefit Quantum Hike (₹2,100 / Month Proposal)
* **Document Needed:** Formal Government Resolution (शासन निर्णय) amending Paragraph 1 of GR No. संकीर्ण-2024/प्र.क्र.137/कार्या-०२ to increase the monthly cash benefit from ₹1,500 to ₹2,100.
* **Current Status:** **MISSING / UNNOTIFIED ON OFFICIAL GR PORTAL.**
* **Investigation:** Political leaders and media reports widely referenced an upcoming increase to ₹2,100/month during late 2024 and 2025 state budget announcements. However, a rigorous inspection of `https://gr.maharashtra.gov.in/` confirms that no operative GR or gazette notification altering the ₹1,500 DBT rate has been issued by the Women and Child Development Department.
* **System Action:** Preserved the legally verified baseline of **₹1,500 per month**. Flagged prospective ₹2,100 benefit rules as unverified.

### 1.2 Statewide Standard Operating Procedure (SOP) for Rejected e-KYC Appeals
* **Document Needed:** Official Departmental SOP / Circular detailing statutory appeal procedures and re-verification timelines for applicants disqualified due to clerical errors during e-KYC (e.g. accidental selection of government employee/pensioner option).
* **Current Status:** **FRAGMENTED / INTERNAL ORDERS ONLY.**
* **Investigation:** The department opened an ad-hoc correction module on `ladakibahin.maharashtra.gov.in`, but the formal gazetted circular defining appellate authorities (e.g., Tahsildar vs. DWCDO) and statutory disposal timelines under the Right to Services (RTS) Act is missing from public archives.

---

## 2. Sanjay Gandhi Niradhar Anudan Yojana

### 2.1 Searchable GR Code Indexing for Divyang Kalyan 15 September 2025 Order
* **Document Needed:** Full canonical Government Resolution PDF with digital signature certificate and computer code on `gr.maharashtra.gov.in` for the 15 September 2025 disability pension revision to ₹2,500/month.
* **Current Status:** **DEPARTMENTALLY NOTIFIED; AWAITING CENTRAL REPOSITORY MIRRORING.**
* **Investigation:** Following the creation of the independent Department of Divyang Kalyan (दिव्यांग कल्याण विभाग), certain social assistance GRs were issued under new departmental budget heads. While departmental implementation circulars confirm the ₹2,500 disbursement rate for ≥ 40% disability, the permanent archival mirror on the primary state GR portal is experiencing re-indexing delays.
* **System Action:** Coded under `RuleVerificationStatus.EXTRACTED_UNVERIFIED` citing departmental orders; requires manual confirmation of final gazette PDF metadata before publication authorization.

### 2.2 Income Threshold Revision GR for General Destitute Category
* **Document Needed:** Government Resolution revising the general destitute annual family income ceiling from the historical ₹21,000 threshold established on 20 August 2019.
* **Current Status:** **NO REVISION ISSUED (STATUTORILY FROZEN AT ₹21,000).**
* **Investigation:** Inquiries revealed public demand to align the general income threshold with the BPL or Ladki Bahin threshold (₹2.5 Lakh). However, no gazette notification exists. Any candidate rule attempting to use a higher threshold (such as ₹50,000 or ₹1,00,000) for general destitute applicants is legally invalid.

---

## 3. Shravanbal Seva Rajya Nivruttivetan Yojana

### 3.1 Inter-Departmental Accounting Reconciliation Order for Group A Component Sharing
* **Document Needed:** Official Finance Department / Social Justice Department Accounting Directive specifying the exact budgetary breakdown between Central NSAP (IGNOAPS) and State Shravanbal allocations following the July 2023 increase to ₹1,500.
* **Current Status:** **INTERNAL FINANCE CONCURRENCE ONLY.**
* **Investigation:** In Group A, the Central Government contribution under IGNOAPS remains statutorily capped at ₹200 (ages 65–79) and ₹500 (ages 80+). Maharashtra State tops up the remainder (₹1,300 and ₹1,000 respectively). The public portal displays a consolidated ₹1,500 payment, but the administrative treasury order governing component deductions during central disbursement lags is not published for citizen transparency.

---

## 4. Centrally Sponsored Post-Matric Scholarship for SC Students

### 4.1 Central Scheme Guidelines for the 16th Finance Commission Cycle (2026-27 Onward)
* **Document Needed:** Official Policy Guidelines and Gazette Notification from the Ministry of Social Justice and Empowerment (MoSJE), Government of India, formally promulgating the operational terms of the Centrally Sponsored Post-Matric Scholarship Scheme for SC Students for the 16th Finance Commission cycle (2026-27 through 2030-31).
* **Current Status:** **PENDING CENTRAL CABINET / GAZETTE PUBLICATION (INTERIM EXECUTIVE CONTINUATION IN EFFECT).**
* **Investigation & Constitutional Analysis:**
  - The authoritative operational guidelines issued vide MoSJE Letter No. `14011/1/2020-SCD-V` were bounded to the 15th Finance Commission window ending 31 March 2026.
  - While educational upliftment of Scheduled Castes is guided by the principles of **Article 46** of the Constitution of India, Article 46 is located in Part IV (Directive Principles of State Policy). Under **Article 37**, provisions of Part IV are explicitly unenforceable by courts. Therefore, Article 46 cannot alone be relied upon as legal proof that a specific scholarship scheme is permanently or self-executingly operational.
  - In administrative practice, the **MahaDBT 2.0 portal** is actively accepting fresh and renewal applications for AY 2026-27 under interim executive continuation directives issued by the Maharashtra Directorate of Social Welfare.
  - However, the MahaDBT portal is an administrative processing gateway and not the foundational legal authority for scheme funding. The central statutory text specifying revised income limits, group-wise maintenance allowance rates, and central-state matching ratios for the 16th Finance Commission has not yet been notified in the Gazette of India.
* **System Action:** Coded `effective_until: null` to reflect active intake, while explicitly logging the un-gazetted 16th Finance Commission guidelines as a mandatory human policy review flag before publication authorization. Distinctly differentiated from the Central Sector *Top Class Education Scheme for SC Students* (₹8 Lakh income ceiling, premier institutes only).

### 4.2 Maharashtra State Adoption GR for AY 2026-27
* **Document Needed:** Maharashtra Government Resolution formally adopting the post-2026 central guidelines and sanctioning the state 40% matching contribution on MahaDBT 2.0.
* **Current Status:** **AWAITING CENTRAL SCHEME NOTIFICATION.**

---

## 5. OBC Post-Matric Scholarship & Fee Waiver Schemes

### 5.1 Operative Maharashtra GR Amending Income Limit from ₹1.0 Lakh to ₹2.5 Lakh
* **Document Needed:** Official Government Resolution published on `gr.maharashtra.gov.in` formally amending Paragraph 2 of GR No. ईबीसी-२०१२/प्र.क्र.२२९/मावक-२ to increase the parental annual income ceiling from ₹1,00,000 to ₹2,50,000 for the Post-Matric Scholarship to OBC Students.
* **Current Status:** **PORTAL-LEVEL ADOPTION ONLY; STANDALONE AMENDING GR NOT LOCATED IN GAZETTE REPOSITORY.**
* **Investigation:** The official MahaDBT 2.0 portal explicitly displays and enforces an annual income threshold of **up to ₹2.50 Lakh** for both the standard OBC Post-Matric Scholarship and the OBC Girls' Professional Post-Matric Scholarship, aligning with the Central Government PM-YASASVI framework. However, a specific state GR formally notifying this change under Department Demand No. `2225F002` could not be retrieved from `gr.maharashtra.gov.in`.
* **System Action:** Coded `annual_family_income <= 250000` to match operational reality on MahaDBT, but set verification status to `EXTRACTED_UNVERIFIED` and logged the unindexed GR as an unresolved policy question.

### 5.2 Standalone Status: OBC Girls' Professional Fee Waiver (8 July 2024 GR)
* **Document Needed:** Codified circular clarifying the non-applicability of maintenance allowance under GR `शिष्यवृ-२०२४/प्र.क्र.१०५/तांशि-४` and its relationship to Other Backward Bahujan Welfare Department schemes.
* **Current Status:** **SEPARATE PROGRAMME UNDER HIGHER & TECHNICAL EDUCATION DEPARTMENT.**
* **Investigation:** The 8 July 2024 GR is issued by the *Higher and Technical Education Department*, provides **100% tuition and examination fee waiver only**, is capped at **₹8,00,000/-** family income, and requires **CAP admission in professional courses**. It provides **NO maintenance allowance**.
* **System Action:** Formally separated into three distinct candidate records:
  1. `candidate-post-matric-obc`: Standard Post-Matric Scholarship (Fees + Maintenance, ₹2.5L threshold).
  2. `candidate-post-matric-obc-girls-professional`: Girls' Professional Post-Matric (Fees + Maintenance, ₹2.5L threshold).
  3. `candidate-payment-tuition-exam-fees-obc-girls`: Girls' Professional Fee Waiver under GR 8 July 2024 (Fees only, ₹8L threshold).

---

## Summary of Actionable Next Steps

| Document Gap | Owning Department / Authority | Impact on Rule Engine | Target Resolution Path |
| :--- | :--- | :--- | :--- |
| Ladki Bahin ₹2,100 GR | WCD Dept, Maharashtra | Retain ₹1,500 baseline; do not promise ₹2,100 | Monitor `gr.maharashtra.gov.in` weekly |
| SC Scholarship 16th FC Guidelines | MoSJE, Government of India | Continuous intake on MahaDBT; 16th FC terms unnotified | Ingest formal 16th FC notification upon central gazettal |
| SGNAY Age Provisions Rulebook | Social Justice Dept, Maharashtra | Bounded `age < 65` universally; distinct minor/disabled rules | Verify Mantralaya scheme circulars |
| OBC ₹2.5L Amending GR | Other Backward Bahujan Welfare Dept | Active MahaDBT threshold (₹2.5L) preserved as unverified | Retrieve physical GR from department archives |
| OBC 3-Way Programme Separation | Bahujan Welfare & Higher Education | Partitioned into 3 distinct candidate records | Independent AST validation per administering department |
