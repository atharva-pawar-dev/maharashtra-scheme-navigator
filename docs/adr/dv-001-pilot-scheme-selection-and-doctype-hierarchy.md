# ADR dv-001: Pilot Scheme Selection and Two-Layer Document Architecture

## Status
ACCEPTED

## Context
Under Mission MSN-DV-001 ("Your Papers, Ready"), the Document Readiness Engine must be built depth-before-breadth without manufacturing unsupported document requirements. Section 5.3 mandates selecting 8–12 pilot schemes by (a) catalogue tier, (b) availability of an official document list with source evidence, and (c) citizen reach across diverse demographics. Furthermore, §4.2 establishes a two-layer model: global, reusable `DocTypeProfile` definitions and scheme-specific `RequirementSlot` definitions.

## Decision
1. **Top 5 Global `DocTypeProfile`s Selected by Empirical Frequency:**
   - `DOC-INCOME-CERT`: Income Certificate (उत्पन्नाचा दाखला) — Tahsildar / Revenue Department
   - `DOC-DOMICILE-CERT`: Domicile / 15-Year Residence Certificate (अधिवास / रहिवासी दाखला) — SDO / Tahsildar
   - `DOC-RATION-CARD`: Ration Card (शिधापत्रिका — Yellow / Orange / White) — Food & Civil Supplies Dept
   - `DOC-BANK-PASSBOOK`: Bank Passbook / Bank Account Statement (बँक पासबुक) — Scheduled Banks
   - `DOC-AADHAAR-CARD`: Aadhaar Card (आधार कार्ड) — UIDAI (Masked / Redacted with Verhoeff validation)

2. **10 Pilot Schemes Selected for Full Document Slot Implementation:**
   - `scheme-namo-shetkari-maha-samman` (Farmers / Agriculture)
   - `scheme-pm-kisan` (Farmers / Direct Income Support)
   - `scheme-mukhyamantri-vayoshri` (Senior Citizens 65+)
   - `scheme-igndps-disability-pension` (Divyang / Disability Pension)
   - `scheme-ignwps-widow-pension` (Widows / Social Security)
   - `scheme-ebc-tuition-waiver` (Higher Education / Students)
   - `candidate-post-matric-obc` (OBC Students / Scholarships)
   - `scheme-cmegp-self-employment` (Youth / Micro-Entrepreneurs)
   - `scheme-annasaheb-patil-ir2` (Economically Backward Youth / Credit Subsidy)
   - `scheme-ramai-awas-yojana` (Rural Housing / SC Families)

3. **Fallback Policy for Non-Pilot Schemes:**
   - All schemes outside the pilot set will honestly display `DOCUMENT_REQUIREMENTS_AWAITING_VERIFICATION` alongside the official source portal and advisory guidance to consult the nearest Seva Kendra or Tahsil office. No synthetic requirements will be fabricated to artificially inflate coverage.

4. **Slot-Based Architecture ("Needs vs. Documents"):**
   - Eligibility connects to "needs" (e.g. "Proof of Income", "Proof of Identity", "Proof of Residence").
   - A single requirement slot can accept multiple document types (e.g. Tahsildar Income Certificate OR Yellow Ration Card).
   - A single multi-purpose document (e.g. 15-year Ration Card) can satisfy both the Identity and Domicile slots.
   - Denominator counts reflect satisfied *needs*, never raw file uploads.

## Alternatives Considered
- *Per-scheme custom validators*: Rejected due to fragmentation, combinatorial explosion, and high maintenance burden.
- *Broad, shallow coverage of all 88 schemes*: Rejected because official source evidence is only confirmed for flagship tiers; shallow coverage would violate Law L1 ("Evidence before requirement").
- *Document-centric checklist*: Rejected because citizens possess different alternative papers satisfying the same statutory criteria.

## Cost of Reversal
Low to moderate. Adding new `DocTypeProfile`s and mapping them into additional schemes is purely additive and decoupled from existing scheme eligibility logic.
