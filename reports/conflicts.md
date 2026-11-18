# Source Conflicts and Legal Reconciliations Log (conflicts.md)
**Date:** 2026-11-18

This log records all multi-source conflicts, GR amendments, and chronological supersessions identified during Catalogue v2 construction.

### 1. Mukhyamantri Majhi Ladki Bahin Yojana — Cut-off Age & Income Proof
- **Conflict Identified:** Initial June 2024 GR stated maximum age 60; corrigendum on 3 July 2024 extended maximum age to 65 and accepted yellow/orange ration cards as substitute for income certificates.
- **Legal Instrument Applied:** Maharashtra GR No. Sankirna-2024/CR137/Karya-02 dated 03 July 2024 (Latest legal instrument wins per Prime Directive 5).
- **Reconciliation:** Scheme model compiled with `age <= 65` and accepted alternatives in `DocRequirement`.

### 2. Sanjay Gandhi Niradhar Anudan — Disability Income Threshold Distinction
- **Conflict Identified:** General destitute threshold is ₹21,000/year; persons with severe disability (>=40%) have threshold ₹50,000/year.
- **Legal Instrument Applied:** Consolidated SGNAY Government Resolution Guidelines (Social Justice Department).
- **Reconciliation:** Two separate condition branches compiled to prevent false ineligibility for disabled applicants.

### 3. Shravanbal Seva Rajya Nivruttivetan — Group A vs Group B Divergence
- **Conflict Identified:** Group A requires state income certificate <= ₹21,000; Group B requires central BPL census inclusion.
- **Legal Instrument Applied:** Shravanbal Guidelines 2023.
- **Reconciliation:** Disjunctive condition (Income <= 21,000 OR BPL == True) supported in evaluation.