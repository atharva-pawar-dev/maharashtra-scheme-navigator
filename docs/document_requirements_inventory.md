# Scheme Document Requirements Inventory
## Statutory Checklists, Issuing Authorities, and Permitted Alternatives Across 75 Schemes

---

### 1. Requirements Architecture

The document requirements dataset (`data/source_registry/scheme_document_requirements.json`) catalogues **319 distinct requirement specifications** across all 75 canonical schemes.

Every document requirement specifies:
1. `requirement_id`: Globally unique identifier scoped to the scheme (e.g. `req_candidate-majhi-ladki-bahin_1_aadhaar`).
2. `document_name`: Official departmental nomenclature (English and Marathi equivalents).
3. `document_category`: Functional classification (`identity`, `residence`, `income`, `caste_social`, `land_agricultural`, `banking_dbt`, `welfare_specific`, `medical_disability`).
4. `requirement_type`: Statutory mandate level (`MANDATORY`, `CONDITIONAL`, `OPTIONAL`).
5. `is_mandatory`: Boolean flag driving hard eligibility prerequisites and application blockers.
6. `condition_description`: Contextual trigger for conditional documents (e.g., "Applicable if family annual income exceeds BPL threshold but under ₹2.5 Lakh").
7. `accepted_alternatives`: Registered alternative documents sanctioned by Maharashtra administrative guidelines or Acts.
8. `issuing_authority`: Competent statutory body empowered to issue or certify the document under Maharashtra Rules of Business.
9. `rts_statutory_days`: Timeframe in calendar/working days notified under the Maharashtra Right to Public Services Act 2015.
10. `validity_conditions`: Rules governing certification expiry, financial year relevance, or periodic re-validation.
11. `source_reference`: Cites the governing Government Resolution or legal enactment.

---

### 2. High-Frequency Statutory Requirements Inventory

#### 2.1 Identity Proof
- **Standard Document:** Aadhaar Card (आधार कार्ड)
- **Document Category:** `identity`
- **Mandatory Status:** MANDATORY (Section 7, Aadhaar Act 2016)
- **Competent Issuing Authority:** Unique Identification Authority of India (UIDAI) / MahaIT Setu Centers
- **Statutory RTS Timeline:** Real-time online validation; 30 days for fresh enrolment / demographic updates.
- **Permitted Alternatives:** Official 28-digit Aadhaar Enrolment Slip (EID) accompanied by Voter ID or Passport.
- **Validity Conditions:** Active Aadhaar number linked with mobile and biometric records.

#### 2.2 Residence & Domicile Proof
- **Standard Document:** Age, Nationality and Domicile Certificate (वय, अधिवास व राष्ट्रीयत्व प्रमाणपत्र)
- **Document Category:** `residence`
- **Mandatory Status:** MANDATORY across Maharashtra state-specific schemes.
- **Competent Issuing Authority:** Sub-Divisional Officer (SDO) / Tahsildar (Revenue & Forest Department)
- **Statutory RTS Timeline:** 15 calendar days under RTS Service Notification No. 12/2015.
- **Permitted Alternatives:**
  - 15-year continuous Ration Card with Tahsildar Self-Declaration.
  - School Leaving Certificate / Transfer Certificate issued in Maharashtra showing birthplace in Maharashtra.
  - Paternal Domicile Certificate + Applicant's Birth Certificate.
  - Voter ID issued in Maharashtra held for >15 years.
- **Validity Conditions:** Lifetime validity unless cancelled by competent revenue court.

#### 2.3 Income Verification
- **Standard Document:** Annual Family Income Certificate (वार्षिक उत्पन्न प्रमाणपत्र)
- **Document Category:** `income`
- **Mandatory Status:** MANDATORY for means-tested welfare programs.
- **Competent Issuing Authority:** Tahsildar / Naib Tahsildar through MahaOnline / Aaple Sarkar
- **Statutory RTS Timeline:** 15 calendar days under RTS Act.
- **Permitted Alternatives:**
  - Active BPL Yellow Ration Card or Antyodaya Anna Yojana (AAY) Card.
  - Form 16 / Income Tax Assessment Return (ITR-V) for the previous Assessment Year.
- **Validity Conditions:** Valid strictly for the stated Financial Year (e.g., FY 2026-27). Multi-year certificates valid for 3 financial years if explicitly endorsed.

#### 2.4 Banking & DBT Enrolment
- **Standard Document:** Bank Account Passbook (बँक पासबुक)
- **Document Category:** `banking_dbt`
- **Mandatory Status:** MANDATORY for direct benefit disbursement.
- **Competent Issuing Authority:** Scheduled Commercial Banks, Regional Rural Banks, India Post Payments Bank (IPPB)
- **Statutory RTS Timeline:** Same-day account statement generation; 7 days for new account opening.
- **Permitted Alternatives:**
  - Personalized Cancelled Cheque leaf with printed applicant name and IFS Code.
  - Bank Account Statement bearing official branch stamp and authorized signature.
- **Validity Conditions:** Account must be operational, in the single name of the applicant (or designated legal guardian), and Aadhaar-seeded via NPCI DBT mapper.

#### 2.5 Land Ownership & Agricultural Proof
- **Standard Document:** 7/12 Extract (सातबारा उतारा) & 8-A Extract (८-अ उतारा)
- **Document Category:** `land_agricultural`
- **Mandatory Status:** MANDATORY for PM-Kisan, Namo Shetkari, and agricultural subsidies.
- **Competent Issuing Authority:** Talathi / Revenue Department / Mahabhulekh Portal
- **Statutory RTS Timeline:** Instant digital download for digitally signed extracts; 3 days from Talathi office.
- **Permitted Alternatives:** Digital Ferfar Mutation Extract showing confirmed inheritance or purchase mutation.
- **Validity Conditions:** Extract must be fresh and reflect the current revenue year.

#### 2.6 Social Category & Caste Verification
- **Standard Document:** Caste Certificate (जात प्रमाणपत्र)
- **Document Category:** `caste_social`
- **Mandatory Status:** MANDATORY for SC/ST/OBC/VJNT/SBC schemes and scholarships.
- **Competent Issuing Authority:** Sub-Divisional Officer (SDO) / Sub-Divisional Magistrate (SDM)
- **Statutory RTS Timeline:** 21 days for Caste Certificate; 45 days for Caste Validity Certificate under Maharashtra Act XXIII of 2001.
- **Permitted Alternatives:** Caste Validity Certificate issued by Divisional Caste Scrutiny Committee.
- **Validity Conditions:** Lifetime validity; Non-Creamy Layer (NCL) certificate required separately for OBC/VJNT/SBC valid for 1 or 3 financial years.

---

### 3. Summary Statistics Across 75 Schemes

- **Total Catalogued Requirements:** 319
- **Mandatory Requirements:** 273 (85.6%)
- **Conditional Requirements:** 28 (8.8%)
- **Optional / Expedited Processing Requirements:** 18 (5.6%)
- **Statutory Alternatives Catalogued:** 104 distinct legal alternative paths
- **RTS Statutory Time Standard Average:** 15.4 days
- **Verification Provenance:** 100% matched to active Government Resolutions.
