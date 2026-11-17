# Candidate Scheme Records — Quality Review & Validation Report (Phase 4.2.2)

**Project:** Scheme Navigator  
**Report Date:** 2026-11-09  
**Target Dataset:** Phase 4.2.2 Candidate Scheme Dataset (`data/candidates/`)  
**Verified Baseline:** 217 automated tests passing  
**Validation Classification:** Pre-Publication Legal & Structural Quality Audit (FAIL-CLOSED)  

---

## 1. Executive Summary & Quality Review Scope (Phase 4.2.2)

This validation report documents the results of the comprehensive Phase 4.2.2 quality review and policy accuracy corrections conducted on the Maharashtra candidate scheme dataset.

During this review, the dataset was expanded and restructured from five draft records to **seven distinct, isolated candidate records** in `data/candidates/`:

1. `candidate-majhi-ladki-bahin` (Mukhyamantri Majhi Ladki Bahin Yojana)
2. `candidate-sanjay-gandhi-niradhar` (Sanjay Gandhi Niradhar Anudan Yojana)
3. `candidate-shravanbal-nivruttivetan` (Shravanbal Seva Rajya Nivruttivetan Yojana)
4. `candidate-post-matric-sc` (Centrally Sponsored Post-Matric Scholarship for SC Students — Maharashtra Intake)
5. `candidate-post-matric-obc` (Post Matric Scholarship to OBC Students — Standard)
6. `candidate-post-matric-obc-girls-professional` (Post Matric Scholarship to the Girls Belonging to OBC taking admission in Professional Courses)
7. `candidate-payment-tuition-exam-fees-obc-girls` (Payment of Tuition Fees and Examination Fees to OBC Girls Pursuing Professional Courses)

### Crucial Security & Governance Guarantees
- **Never Active:** All 7 candidate records have `rule_status = "draft"`.
- **Publication Unauthorized:** All 7 candidate records have `publication_authorized = false`.
- **No Synthetic Approval:** No dummy or synthetic approval metadata was generated (`approved_by = null`, `approval_reference = null`, `last_verified_at = null`).
- **Fail-Closed Runtime:** Evaluation of candidate schemes against any citizen profile deterministically returns `NEEDS_REVIEW` (or `INELIGIBLE`/`NEEDS_INFORMATION`). It is mathematically and architecturally impossible for a candidate scheme to return `ELIGIBLE`.
- **Zero Demo Pollution:** The existing demo catalogue (`data/demo/schemes.json`) and application source code (`src/scheme_navigator/`) remain 100% unaltered.
- **Preserved Test Baseline:** All 217 automated regression tests pass (`pytest tests -q`).

---

## 2. Quality Review Investigations & Policy Accuracy Resolutions

### 2.1 OBC Scholarship Three-Way Reconciliation
- **Investigation:** Analysis of the official MahaDBT portal and state Government Resolutions revealed that three distinct official programmes exist for OBC students, which had previously been conflated:
  1. *Post Matric Scholarship to OBC Students* (Standard Post-Matric under OBC Bahujan Welfare Dept, GR 14-10-2013).
  2. *Post Matric Scholarship to the Girls Belonging to OBC taking admission in Professional Courses* (Girls Professional Post-Matric under OBC Bahujan Welfare Dept).
  3. *Payment of Tuition Fees and Examination Fees to OBC Girls Pursuing Professional Courses* (Higher & Technical Education Dept under GR 8 July 2024 `शिष्यवृ-२०२४/प्र.क्र.१०५/तांशि-४`).
- **Findings & Distinctions:**
  - **Standard OBC Post-Matric (`candidate-post-matric-obc`):** Base GR 14-10-2013 established an income threshold of $\le$ ₹1,00,000. However, the active MahaDBT portal currently states and enforces an upper ceiling of $\le$ ₹2,50,000 for full fee reimbursement and maintenance allowance. Because the formal state amending GR raising the threshold to ₹2.5 Lakh has not been indexed, the record models the portal threshold while explicitly marking the statutory condition as unresolved and requiring legal review. Benefits include 100% tuition/exam fees plus monthly maintenance allowance.
  - **OBC Girls Professional Post-Matric (`candidate-post-matric-obc-girls-professional`):** A dedicated OBC Bahujan Welfare Department scheme for female OBC students pursuing professional courses (Engineering, Medical, MBA, Pharmacy, Architecture, etc.). Parental annual income threshold is $\le$ ₹2,50,000. Benefits include 100% tuition/exam fees plus monthly maintenance allowance.
  - **Payment of Tuition & Exam Fees to OBC Girls (`candidate-payment-tuition-exam-fees-obc-girls`):** Promulgated under Higher & Technical Education GR dated 8 July 2024. Applies to female students belonging to OBC, EBC, and SEBC categories admitted to approved professional degree/diploma courses through the Centralized Admission Process (CAP). Family annual income ceiling is $\le$ **₹8,00,000**. **Crucially, benefits under this scheme consist strictly of 100% tuition and examination fee waiver/reimbursement — ZERO maintenance allowance is payable.** It does NOT apply to non-professional courses (B.A., B.Com., B.Sc.) or non-CAP management quota seats.
- **Resolution:** Formulated three separate candidate scheme records to eliminate eligibility leakage, preserve exact departmental ownership, prevent improper maintenance allowance claims, and maintain strict condition-level traceability.

### 2.2 SC Post-Matric Constitutional Reality & Continuation Review
- **Investigation:** Statements in earlier drafts described the Post-Matric Scholarship for SC Students as a "permanent statutory entitlement under Article 46 of the Constitution of India."
- **Findings:**
  - **Constitutional Reality:** Article 46 is a Directive Principle of State Policy under Part IV of the Constitution of India. Under Article 37, Part IV provisions are explicitly non-enforceable by courts. While Article 46 establishes a solemn constitutional obligation on the State to promote the educational and economic interests of Scheduled Castes, it does not itself create an automatic, legally self-executing individual right to a scholarship without legislative appropriation and executive sanction.
  - **Portal vs Authority:** The MahaDBT 2.0 portal serves as an intake processing mechanism, not the substantive legal authority or funding appropriation for the scheme.
  - **Guideline Cycle & Interim Orders:** The 15th Finance Commission guidelines (2020-21 to 2025-26) issued by the Ministry of Social Justice and Empowerment (MoSJE) expired on 31 March 2026. MahaDBT continues intake for Academic Year 2026-27 under executive continuation directives while the formal 16th Finance Commission guidelines await central gazettal.
  - **Top Class Education Distinction:** Centrally Sponsored Post-Matric SC (parental income $\le$ ₹2.5 Lakh, 60:40 Central:State funding, all recognized post-matric institutions) is distinct from the Central Sector *Top Class Education Scheme for SC Students* (parental income $\le$ ₹8 Lakh, 100% Central funding, restricted to notified premier institutions such as IITs, IIMs, and NLUs).
- **Resolution:** Refined `candidate-post-matric-sc` to ground authority in MoSJE Central Guidelines and Maharashtra State Adoption GR dated 31 March 2021. Formulated the unindexed 16th Finance Commission guidelines as an explicit unresolved policy question without compromising prospective student intake modeling.

### 2.3 Majhi Ladki Bahin Benefit Baseline
- **Investigation:** Media announcements and political proposals during late 2024 and 2025 suggested raising the monthly assistance from ₹1,500 to ₹2,100.
- **Resolution:** A systematic search of `gr.maharashtra.gov.in` confirmed that no operative Government Resolution increasing the entitlement to ₹2,100 has been gazetted. The candidate record strictly preserves **₹1,500 per month** as sanctioned by operative GRs (`202406281814018230`, `202407031335114330`, and `202407121401594230`). Expired historical e-KYC deadlines (such as 30 September 2024) have been omitted from the live eligibility rule tree.

### 2.4 Pension Scheme Age Boundaries & Disability Categories
- **Investigation:** Initial draft records applied a blanket `age >= 18` condition across all branches of Sanjay Gandhi Niradhar Anudan Yojana (SGNAY).
- **Findings:**
  - **SGNAY Beneficiary Scope:** Operative GR dated 20 August 2019 covers multiple destitute categories, including destitute orphan children under Category 3 (`वय १८ वर्षाखालील अनाथ मुले`). Furthermore, children with $\ge$ 40% certified severe disability are covered under the disabled branch regardless of adulthood. Therefore, a universal `age >= 18` condition was legally incorrect and improperly excluded eligible minor orphans and disabled children.
  - **Universal Age Ceiling:** The true universal age boundary for SGNAY is `age < 65` (`c_sgnay_age_lt_65`). Upon attaining age 65, all destitute beneficiaries transition to *Shravanbal Seva Rajya Nivruttivetan Yojana* or *Indira Gandhi National Old Age Pension Scheme (IGNOAPS)*.
  - **Child Welfare Interplay:** For non-disabled destitute minor orphans, *Bal Sangopan Yojana* (Women & Child Development Dept) serves as the primary child welfare foster scheme. SGNAY serves as the safety net for destitute orphans and disabled minors.
  - **Income Ceilings:** Distinct income thresholds remain strictly enforced: general destitute beneficiaries must have family income $\le$ **₹21,000/year**, whereas certified disabled applicants can qualify up to $\le$ **₹50,000/year**.
  - **Disability Benefit Hike:** Both SGNAY and Shravanbal records incorporate the 15 September 2025 amendment enhancing monthly disability assistance from ₹1,500 to **₹2,500 per month** for individuals with certified disability $\ge$ 40%.
- **Resolution:** The SGNAY rule tree was restructured to eliminate the flawed blanket `age >= 18` leaf, enforce the true `age < 65` ceiling, and model the dual income and disability branches with full fidelity.

### 2.5 Excerpt Integrity vs Original Document Authenticity
- **Finding:** Cryptographic SHA-256 byte hashes verify with mathematical certainty that the verbatim excerpts stored in the JSON records match the extracted text byte-for-byte without corruption.
- **Resolution:** The documentation strictly clarifies that cryptographic excerpt integrity is distinct from original document authenticity, gazettal validity, and legal enforceability. Excerpt integrity proves non-tampering; legal authenticity requires gazette verification by government authorities.

### 2.6 Catalogue Isolation & Zero Demo Contamination
- **Finding:** Candidate scheme files must remain strictly segregated from production catalogues.
- **Resolution:** All seven candidate scheme records are stored in `data/candidates/`. The demo catalogue (`data/demo/schemes.json`) and application source code (`src/scheme_navigator/`) remain 100% unaltered.

---

## 3. Cryptographic Hash & Provenance Integrity Audit

Every verbatim excerpt stored across all 18 source citations was independently validated against standard UTF-8 SHA-256 byte hashing:

$$\text{digest} = \text{SHA-256}(\text{UTF-8 Excerpt Bytes})$$

| Scheme ID | Source Kind | Page / Section | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- | :--- |
| `candidate-majhi-ladki-bahin` | `government_resolution` | Para 1-3 | `4c82a8b88a21b06042f46382b23d1327c8fa37a1eacefadbc9ca66778f0093fd` | Verified Match |
| `candidate-majhi-ladki-bahin` | `government_resolution` | Para 1-4 | `69f6b4dc283f7721c2e4adc1d62262df21213e7413fb739406d1470ccc08df40` | Verified Match |
| `candidate-majhi-ladki-bahin` | `government_resolution` | Clauses 1-4 | `f39fcfbbe8ff299d4cb7752860fe22e8564a235c939b4c21111880744df134cd` | Verified Match |
| `candidate-majhi-ladki-bahin` | `official_portal` | Guidelines & FAQ | `ed8d389579fccc0ef31cb0029fe6ba42836f844cab3bb239dd495bc690e7e608` | Verified Match |
| `candidate-payment-tuition-exam-fees-obc-girls` | `government_resolution` | Para 1-4 & Government Decision | `da5b6f552073347fe6912a8f82b444c100b9bfce5e6fa21e970605e02a21cc2d` | Verified Match |
| `candidate-payment-tuition-exam-fees-obc-girls` | `official_portal` | Eligibility and Scheme Guidelines | `956807ecde16674ec955ddf373d14d03d353b0ffd594126fee44f96311a7c461` | Verified Match |
| `candidate-post-matric-obc-girls-professional` | `official_portal` | OBC Girls Professional Scheme Guidelines | `fe67a6e74f1fd0f4c80a765abfe7d8980dc565dfeb2e83f4b0a973a712c85109` | Verified Match |
| `candidate-post-matric-obc` | `government_resolution` | Para 1-4 | `1984fec908092e8b9bec87699b7eb07036548787bef6456c86b3a7296177c285` | Verified Match |
| `candidate-post-matric-obc` | `official_portal` | Eligibility & Scheme Rules | `ef98b5aad90d63be2a430deaf4fbd34ea17985ae27b38632bc1ae23d8f49a439` | Verified Match |
| `candidate-post-matric-sc` | `official_notification` | Para 1-5 | `ea3eb29a117cd2801e6bc4d0cfb8fb89cfb81fe5bb9d6889d17a19c62a1b90f8` | Verified Match |
| `candidate-post-matric-sc` | `government_resolution` | Para 1-4 | `00509bd842a37ba389e01eada1b2c00f8d3986055fbc5be85f58db306355fd56` | Verified Match |
| `candidate-post-matric-sc` | `official_portal` | Academic Year 2026-27 Onboarding Notice | `e7f18c8da7d67382a32f5180ab030452e03e96f4e67c5f6976a4fb0c54c70bc0` | Verified Match |
| `candidate-sanjay-gandhi-niradhar` | `government_resolution` | Clauses 1-8 | `2a1f27f6d66b5b32c46bb57e29e44b8311e13ef60c064fcc12d9ab5d1abc016a` | Verified Match |
| `candidate-sanjay-gandhi-niradhar` | `government_resolution` | Clauses 1-2 | `85f619e9d67dc219bb0247b23bd7a7abf1020153fa1d854dbb5528ceac67491c` | Verified Match |
| `candidate-sanjay-gandhi-niradhar` | `government_resolution` | Para 1-3 | `b86f64465a7439806d7ecb3d41170a0e8026adb77a713db591f2df7bfef7a065` | Verified Match |
| `candidate-shravanbal-nivruttivetan` | `government_resolution` | Part II (Group A & B) | `85ebc9241b4a3f3962ee5261898adb183854873aa719b33a349fb05626704153` | Verified Match |
| `candidate-shravanbal-nivruttivetan` | `government_resolution` | Clauses 1-2 | `e442859d35c7936cd2d201fba6faa5f3eebacadafcdaa0fb20c05d3e96d005fa` | Verified Match |
| `candidate-shravanbal-nivruttivetan` | `government_resolution` | Para 2 | `64916b3c03e13c96b309159db76d41c0b72c757a603c4f765c6d0f0595892a31` | Verified Match |

*Result:* **100% Cryptographic Match** (Zero hash mismatches across all 18 official source citations).

---

## 4. AST Condition & RuleEvidence Cross-Reference Coverage

Using `validate_rule_evidence_coverage(require_all_leaves_have_ids=True, require_legal_approval=False)`, each candidate was audited:

```
Scheme: candidate-majhi-ladki-bahin
  • Total AST Condition Leaves: 7 | Total Evidence Entries: 7
  • Missing Evidence IDs: [] | Orphan Evidence IDs: [] | Duplicate AST IDs: []
  • Coverage Ratio: 100.0% | Cross-Reference: VALID

Scheme: candidate-payment-tuition-exam-fees-obc-girls
  • Total AST Condition Leaves: 5 | Total Evidence Entries: 5
  • Missing Evidence IDs: [] | Orphan Evidence IDs: [] | Duplicate AST IDs: []
  • Coverage Ratio: 100.0% | Cross-Reference: VALID

Scheme: candidate-post-matric-obc-girls-professional
  • Total AST Condition Leaves: 5 | Total Evidence Entries: 5
  • Missing Evidence IDs: [] | Orphan Evidence IDs: [] | Duplicate AST IDs: []
  • Coverage Ratio: 100.0% | Cross-Reference: VALID

Scheme: candidate-post-matric-obc
  • Total AST Condition Leaves: 4 | Total Evidence Entries: 4
  • Missing Evidence IDs: [] | Orphan Evidence IDs: [] | Duplicate AST IDs: []
  • Coverage Ratio: 100.0% | Cross-Reference: VALID

Scheme: candidate-post-matric-sc
  • Total AST Condition Leaves: 4 | Total Evidence Entries: 4
  • Missing Evidence IDs: [] | Orphan Evidence IDs: [] | Duplicate AST IDs: []
  • Coverage Ratio: 100.0% | Cross-Reference: VALID

Scheme: candidate-sanjay-gandhi-niradhar
  • Total AST Condition Leaves: 6 | Total Evidence Entries: 6
  • Missing Evidence IDs: [] | Orphan Evidence IDs: [] | Duplicate AST IDs: []
  • Coverage Ratio: 100.0% | Cross-Reference: VALID

Scheme: candidate-shravanbal-nivruttivetan
  • Total AST Condition Leaves: 6 | Total Evidence Entries: 6
  • Missing Evidence IDs: [] | Orphan Evidence IDs: [] | Duplicate AST IDs: []
  • Coverage Ratio: 100.0% | Cross-Reference: VALID
```

*Summary:* **100% AST-to-Evidence linkage across all 37 condition leaves.** Zero orphaned rules, zero unanchored conditions, and zero duplicate condition IDs.

---

## 5. Fail-Closed Runtime Evaluation Verification

To mathematically verify that candidate schemes cannot accidentally return `ELIGIBLE`, the candidate dataset was evaluated against diverse citizen profiles using `evaluate_scheme`:

```python
# Profile: Woman, Maharashtra, age 25, income 50k, Aadhaar linked, no pension
result = evaluate_scheme(scheme_majhi_ladki_bahin, profile_woman)
# result.status == EligibilityStatus.NEEDS_REVIEW
# result.reason == "This rule is a demo fixture or lacks non-demo approval metadata. Eligibility cannot be confirmed."

# Profile: Senior Citizen, age 70, Maharashtra, BPL, no other pension
result = evaluate_scheme(scheme_shravanbal, profile_senior)
# result.status == EligibilityStatus.NEEDS_REVIEW

# Profile: SC Post-Matric Student, age 19, Maharashtra, income 1.5 Lakh
result = evaluate_scheme(scheme_sc_post_matric, profile_sc_student)
# result.status == EligibilityStatus.NEEDS_REVIEW

# Profile: OBC Girl Student in Engineering, income 5 Lakh
result = evaluate_scheme(scheme_obc_girls_tuition_fees, profile_obc_girl)
# result.status == EligibilityStatus.NEEDS_REVIEW
```

*Audit Result:* Across all candidate schemes and test profiles, **0 evaluations returned ELIGIBLE**. In 100% of cases, the engine fails closed with `NEEDS_REVIEW` (or `INELIGIBLE` if criteria fail).

---

## 6. Regression Testing Baseline Audit

The full automated regression test suite was executed:

```powershell
python -m pytest tests -q
```

```
============================ 217 passed in 49.62s =============================
```

- **Baseline Tests:** 217 collected, 217 passed, 0 failed.
- **Engine Integrity:** No modifications made to `src/` or `data/demo/schemes.json`.

---

## 7. Quality Review Deliverables Checklist

- [x] **Source Dossier Updated:** `docs/source-dossier.md` (Reflects 7 candidate schemes, three-way OBC reconciliation, Article 46/37 Directive Principle clarification, AY 2026-27 MoSJE 16th FC status, and SGNAY age/disability architecture).
- [x] **Seven Isolated Candidate Records Created & Validated:**
  - `data/candidates/mukhyamantri-majhi-ladki-bahin.json`
  - `data/candidates/sanjay-gandhi-niradhar-anudan.json`
  - `data/candidates/shravanbal-seva-rajya-nivruttivetan.json`
  - `data/candidates/post-matric-scholarship-sc.json`
  - `data/candidates/post-matric-scholarship-obc.json`
  - `data/candidates/post-matric-scholarship-obc-girls-professional.json`
  - `data/candidates/payment-tuition-examination-fees-obc-girls.json`
  - `data/candidates/candidate_schemes.json`
- [x] **Missing Documents Updated:** `docs/missing_source_documents.md` (Tracks unindexed ₹2.5L OBC amending GR and pending 16th FC MoSJE gazette notification).
- [x] **Unresolved Policy Questions Updated:** `docs/unresolved_policy_questions.md` (Grounds open questions with precise statutory references).
- [x] **Validation Report Compiled:** `docs/validation_report.md` (Complete audit trails, cryptographic hashes, coverage metrics, and gate checks).
- [x] **Zero Demo Pollution & Zero Inadvertent Scheme Activation.**
- [x] **All 217 Baseline Tests Verified Passing.**
