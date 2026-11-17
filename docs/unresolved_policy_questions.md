# Unresolved Policy Questions & Legal Ambiguities (Phase 4.2)

**Project:** Scheme Navigator  
**Jurisdiction:** Government of Maharashtra & Union of India  
**Status:** Legal & Policy Review Brief  

This document catalogs critical **unresolved policy questions, statutory ambiguities, administrative conflicts, and edge cases** identified during the research and draft compilation of the five prioritized Maharashtra schemes.

In accordance with Scheme Navigator's fail-closed governance standards, these conditions are **not resolved by heuristic inference or guessing**; they remain explicitly flagged for human legal review.

---

## 1. Cross-Scheme Interlocking & Benefit Duplication (Ladki Bahin vs. SGNAY vs. Shravanbal)

### 1.1 The Single-Pension Barrier vs. Voluntary Scheme Migration
* **Policy Question:** Can an existing beneficiary of Sanjay Gandhi Niradhar Anudan Yojana (SGNAY) receiving ₹1,500/month voluntarily surrender or close their SGNAY account to enroll in Mukhyamantri Majhi Ladki Bahin Yojana, or does an existing DBT registration permanently bar them?
* **Statutory Conflict:**
  - Majhi Ladki Bahin GR (28 June 2024, Para 3.4) declares ineligible any woman receiving ₹1,500/month or more from another department's financial scheme.
  - SGNAY GR (20 August 2019, Para 4) requires that an applicant not receive any other government pension.
  - Neither GR specifies a codified procedure or statutory timeframe for **scheme portability** or formal voluntary surrender.
* **Engine Risk:** Evaluating a profile with `receiving_other_pension: false` when an active SGNAY benefit exists would result in automated fraud or DBT rejection at the PFMS gateway.

### 1.2 Disabled Women Benefit Optimization Divergence
* **Policy Question:** For a disabled woman aged 21–65 with family income between ₹21,000 and ₹50,000:
  - Under SGNAY, as amended on 15 September 2025, she is eligible for **₹2,500 per month** (disability income limit is ₹50,000).
  - Under Ladki Bahin, she is eligible for only **₹1,500 per month** (income limit ₹2.5 Lakh).
* **System Recommendation:** The discovery engine must not merely evaluate binary eligibility; it must proactively prioritize SGNAY as the economically superior legal entitlement, while preventing double application.

---

## 2. Temporal Validity & Expired Deadlines (Majhi Ladki Bahin & SC Post-Matric)

### 2.1 The "Rolling Intake" vs. "Closed Scheme" Dilemma for Majhi Ladki Bahin
* **Policy Question:** Does Mukhyamantri Majhi Ladki Bahin Yojana legally accept fresh applications from young women newly turning 21 in late 2026, or was the scheme a one-time enrollment drive bounded by the 2024-2025 deadlines?
* **Evidence Analysis:**
  - Base GR (28 June 2024) set an initial application window of 1–15 July 2024.
  - Shuddhipatra (3 July 2024) extended this to 31 August 2024.
  - Subsequent circulars extended e-KYC to 31 December 2025.
  - Departmental spokespersons have stated that the scheme is permanent and ongoing, but **no Government Resolution codifies a continuous calendar schedule for post-2025 fresh applicant batches**.
* **Engine Policy:** We have deliberately decoupled the historical e-KYC deadlines from prospective eligibility ASTs. The record is flagged as `needs_review` pending written confirmation from the WCD Department on ongoing enrollment windows.

### 2.2 SC Post-Matric Guideline Cycle Expiration vs. Constitutional Reality
* **Policy Question:** Does the expiration of the 2020-21 to 2025-26 central guidelines on 31 March 2026 mean the scheme has lapsed, and does Article 46 create an automatic permanent legal entitlement?
* **Constitutional & Statutory Reality:**
  - **Article 46 vs. Article 37:** While welfare measures for Scheduled Castes derive moral and policy guidance from Article 46, Article 46 is situated in Part IV of the Constitution (Directive Principles of State Policy). Article 37 expressly states that Directive Principles are **not enforceable by any court**. Therefore, Article 46 cannot alone be invoked as legal authority establishing that a specific scholarship programme is permanently operational or self-executing without legislative appropriations and executive sanctions.
  - **Funding Cycle Architecture:** MoSJE Letter No. `14011/1/2020-SCD-V` established guidelines strictly for the 15th Finance Commission 5-year block (ending 31 March 2026). Centrally Sponsored Schemes require Finance Commission / Cabinet sanction for each 5-year cycle.
  - **Portal Intake vs. Legal Authority:** The MahaDBT 2.0 portal is currently accepting fresh and renewal applications for AY 2026-27 under interim executive continuance directives from the Directorate of Social Welfare. However, the portal is an administrative processing interface, not statutory authority. The formal central statutory guidelines for the 16th Finance Commission cycle have not yet been gazetted in the Gazette of India.
* **Engine Decision:** We set `effective_until: null` in the candidate record to reflect ongoing operational intake, but keep the record in `draft` with an explicit human policy review flag regarding unnotified 16th Finance Commission terms.
* **Critical Distinction from Top Class Education:** The Centrally Sponsored Post-Matric Scholarship (income ceiling ₹2,50,000, 60:40 central-state ratio, all post-matric institutions) must NEVER be confused with the Central Sector *Top Class Education Scheme for SC Students* (income ceiling ₹8,00,000, 100% central funding, strictly restricted to notified premier institutions like IITs, IIMs, AIIMS, and NITs).

---

## 3. Disparities in Household Income Ceilings & Age Boundaries

### 3.1 Severe Income Compression in Traditional Destitute Schemes vs. Modern Schemes
* **Policy Question:** Why does a destitute widow without dependent children face an annual family income ceiling of **₹21,000/-** under SGNAY (unchanged since 2019), while a woman in a family earning up to **₹2,50,000/-** qualifies for Ladki Bahin?
* **Policy Impact:**
  - A destitute woman earning ₹25,000/year (₹2,083/month, well below minimum wage) is statutorily disqualified from SGNAY.
  - She can only receive ₹1,500 under Ladki Bahin, but loses the specialized protections and destitute committee support of SGNAY.
  - If she has a certified disability, she is locked out of the ₹2,500 SGNAY disability pension if her family income exceeds ₹50,000.
* **System Action:** Distinct income limits are strictly preserved in our separate AST branches (`c_sgnay_income_general: 21000` vs `c_sgnay_income_disabled: 50000`). The engine never blurs these limits.

### 3.2 SGNAY Age Boundaries & Erroneous Blanket Age Condition
* **Quality Review Finding:** Applying a blanket `age >= 18` condition across the entire SGNAY candidate scheme was legally inaccurate because:
  1. **Disabled Minors:** Blind and disabled children below 18 years are covered under the disability pension branch; they are not barred by an adult age requirement.
  2. **Destitute Orphans (अनाथ मुले):** Category 3 of GR 20-08-2019 explicitly provides monthly assistance to orphan children under age 18 (`age < 18`). While the Women & Child Development Department operates *Bal Sangopan Yojana* (बाल संगोपन योजना) for foster child care, SGNAY retains a statutory destitute orphan category under the Social Justice Department.
  3. **Universal Ceiling:** The only universal age condition across all branches is `age < 65` (`c_sgnay_age_lt_65`). At age 65, all beneficiaries transition to *Shravanbal Yojana*.
* **AST Encoding:** In our corrected candidate AST, `c_sgnay_age_lt_65` serves as the universal upper bound, allowing both adult destitute, disabled persons, and minor orphans to be evaluated within their proper statutory categories.

---

## 4. BPL List Stagnation in Shravanbal Seva Yojana (Group A vs Group B)

### 4.1 Reliance on Decades-Old BPL Census Lists
* **Policy Question:** In Shravanbal Group A, qualification depends strictly on inclusion in the Central Government BPL list. Given that no comprehensive nationwide BPL census has been conducted since 2002:
  - What happens to impoverished senior citizens whose families fell into poverty after 2002?
  - They are statutorily excluded from Group A and forced into Group B.
  - In Group B, they must obtain an annual income certificate (≤ ₹21,000) from the Tahsildar every financial year.
* **Administrative Burden:** Group A beneficiaries rarely have to recertify income once enrolled, whereas Group B beneficiaries face annual bureaucratic hurdles despite receiving the identical ₹1,500 monthly payment.

### 4.2 Apparent Conflict Between No-Other-Pension Exclusion and Central IGNOAPS Component (POL-SHRAVANBAL-01)
* **Statutory Paradox:**
  - Base GR (20 August 2019, Para 4) explicitly stipulates: `"अर्जदारास इतर कोणत्याही शासकीय योजनेतून निवृत्तीवेतन मिळत नसावे."` (*"Applicant must not be receiving pension from any other government scheme."*), encoded in AST condition `c_shravanbal_no_other_pension`.
  - Concurrently, Shravanbal Group A (Central BPL category) is structured as a co-funded joint pension incorporating the Central Government's Indira Gandhi National Old Age Pension Scheme (IGNOAPS) (₹200/500 Central component + ₹1,300/1,000 State top-up to guarantee ₹1,500/month).
* **Legal Ambiguity:** The original Government Resolution does not textually define whether an existing IGNOAPS beneficiary who applies for the State top-up is technically disqualified by the literal blanket exclusion ("any other government scheme"), or whether Group A operates as an integrated co-sanctioning framework where IGNOAPS is not considered an "other" scheme.
* **Governance Decision:** In strict adherence to Scheme Navigator's fail-closed policy, the system **does not invent an unwritten statutory exception**. Because the exact legal meaning cannot be established conclusively from the published text of GR 20-08-2019 without administrative clarification, the condition `c_shravanbal_no_other_pension` is formally marked as an **UNRESOLVED POLICY INQUIRY (`POL-SHRAVANBAL-01`)** pending written interpretation from the Social Justice and Special Assistance Department.

---

## 5. OBC Post-Matric Reconciliation: Three Non-Fungible Programmes

### 5.1 Three-Way Portal Reconciliation
* **Quality Review Reconciliation:** Detailed inspection of the official MahaDBT portal and state GRs revealed three distinct educational support interventions:
  1. **Standard Post-Matric Scholarship (`candidate-post-matric-obc`):**
     - Administering Department: *Other Backward Bahujan Welfare Department*.
     - Income Threshold: Active MahaDBT 2.0 portal specifies **up to ₹2,50,000/-** (base 2013 GR had ₹1,00,000/-).
     - Benefits: **100% Fees + Group-wise Monthly Maintenance Allowance (10 months)**.
     - Scope: Open to all genders across all recognized post-matric courses.
  2. **Girls' Professional Post-Matric Scholarship (`candidate-post-matric-obc-girls-professional`):**
     - Administering Department: *Other Backward Bahujan Welfare Department*.
     - Income Threshold: Active MahaDBT 2.0 portal specifies **up to ₹2,50,000/-**.
     - Benefits: **100% Fees + Monthly Maintenance Allowance** (1/3rd in government hostels).
     - Scope: Female students admitted to approved professional degree/diploma courses.
  3. **Girls' Professional Fee Waiver under GR 8 July 2024 (`candidate-payment-tuition-exam-fees-obc-girls`):**
     - Administering Department: *Higher and Technical Education Department*.
     - Income Threshold: Family annual income **up to ₹8,00,000/-** (backed by NCL).
     - Benefits: **100% Tuition & Exam Fees ONLY. ZERO Maintenance Allowance.**
     - Scope: Female students admitted via **CAP** in approved higher/technical professional courses. Minimum 75% attendance mandatory.

### 5.2 Source Discrepancy: The ₹1.0 Lakh vs. ₹2.50 Lakh Gap
* **Policy Conflict:** The 14 October 2013 base GR (`ईबीसी-२०१२/प्र.क्र.२२९/मावक-२`) set a ₹1,00,000 ceiling. The active MahaDBT 2.0 portal enforces ₹2,50,000 to align with central PM-YASASVI norms.
* **Resolution:** In accordance with user directives, the candidate record does not artificially retain the obsolete ₹1 Lakh ceiling which would cause unwarranted ineligibility flags for valid applicants. However, because the amending state GR has not been gazetted on `gr.maharashtra.gov.in`, the ₹2,50,000 threshold condition is logged under `EXTRACTED_UNVERIFIED` and preserved as an explicit unresolved policy inquiry.

---

## 6. Summary of Unresolved Inquiries for Legal & Policy Analysts

| Issue Ref | Subject | Pending Agency Response | Risk Level |
| :--- | :--- | :--- | :--- |
| **POL-WCD-01** | Ladki Bahin rolling intake status for 2026 | WCD Department, Mantralaya | Medium (Applicant expectations) |
| **POL-WCD-02** | Official GR for ₹2,100 benefit hike | Finance / WCD Department | High (Legal overpayment risk) |
| **POL-SJD-01** | General SGNAY income limit revision | Social Justice & Special Asst | Medium (Exclusion of destitute) |
| **POL-SHRAVANBAL-01** | No-other-pension exclusion vs. Central IGNOAPS co-funding | Social Justice & Special Asst | High (Disqualification of Group A seniors) |
| **POL-CEN-01** | PMS-SC 16th Finance Commission guidelines | MoSJE, Government of India | Critical (Statutory validity after 31 March 2026) |
| **POL-OBC-01** | Standalone State GR for OBC ₹2.5 Lakh income ceiling | Other Backward Bahujan Welfare Dept | High (Discrepancy with 2013 Base GR) |
| **POL-OBC-02** | Non-professional course scope under 8 July 2024 GR | Higher & Tech Education Dept | Medium (Fee claim rejections) |
