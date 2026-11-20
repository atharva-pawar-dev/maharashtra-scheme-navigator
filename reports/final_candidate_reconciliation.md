# Final Candidate Reconciliation Report (reports/final_candidate_reconciliation.md)
**Mission ID:** MSN-FINAL-001  
**Generated:** 2026-11-21  
**Governing Standard:** TRIMURTI v4 — Forensic Scheme Accounting  

---

## 1. Candidate Accounting Reconciliation

The previous SC-G2 textual summary reported a candidate count of 142 while publishing category figures that summed to 141 due to an inadvertent typographical omission (`DUPLICATE_OF: 8` instead of `DUPLICATE_OF: 9`).

A physical verification of `scheme_discovery_master_register.csv` confirms **exactly 142 distinct candidate rows** with unique candidate IDs (`CAND-001` through `CAND-142`).

### Disposition Distribution (142 Total Candidates)

| Disposition | Count | Percentage | Explanation |
| :--- | :---: | :---: | :--- |
| **`IN_CATALOGUE_VERIFIED`** | 17 | 12.0% | 17 Tier A P0 Flagship schemes with 100% verified verbatim Marathi quotes from official GRs. |
| **`IN_CATALOGUE_LIMITED`** | 71 | 50.0% | 71 active schemes (57 Tier B/C + 14 newly integrated candidates) failing closed to `LIMITED_INFORMATION`. |
| **`NEEDS_RESEARCH`** | 18 | 12.7% | 18 discovered schemes requiring additional primary Government Resolution retrieval. |
| **`BLOCKED_SOURCE`** | 6 | 4.2% | 6 candidates where department portal returned persistent HTTP 403 or TLS failure. |
| **`DUPLICATE_OF`** | 9 | 6.3% | 9 candidates representing portal forms, app variants, or demo fixtures of canonical schemes. |
| **`SUB_SCHEME_OF`** | 6 | 4.2% | 6 candidates identified as statutory components/components of umbrella parent schemes. |
| **`HISTORICAL`** | 5 | 3.5% | 5 schemes superseded by modern umbrella schemes (e.g., Sanjay Gandhi, old scholarship rules). |
| **`EXCLUDED_NOT_INDIVIDUAL_BENEFIT`** | 7 | 4.9% | 7 records representing public infrastructure, Gram Panchayat community grants, or institutional aid. |
| **`EXCLUDED_OUT_OF_GEOGRAPHIC_SCOPE`** | 3 | 2.1% | 3 records targeting other states or non-Maharashtra exclusive territories. |
| **TOTAL** | **142** | **100.0%** | **Mathematically verified across 142 physical rows** |

---

## 2. Forensic Reconciliation of the 9 DUPLICATE_OF Candidates

The discrepancy arose because `CAND-075` (the quarantined demo fixture) was counted in the CSV as `DUPLICATE_OF` (`demo-majhi-ladki-bahin`), alongside 8 other duplicate portal registration forms:

1. `CAND-075`: Mukhyamantri Majhi Ladki Bahin Yojana (Demo Fixture) $	o$ `demo-majhi-ladki-bahin`
2. `CAND-114`: Namo Shetkari Maha Samman Nidhi Application (Krishi Portal Form) $	o$ `scheme-namo-shetkari-maha-samman`
3. `CAND-115`: Majhi Ladki Bahin Nari Shakti Doot Mobile Registration $	o$ `candidate-majhi-ladki-bahin`
4. `CAND-116`: Vayoshri Direct Benefit DBT Form $	o$ `scheme-mukhyamantri-vayoshri`
5. `CAND-117`: Rajarshi Shahu Maharaj Tuition Fee Reimbursement $	o$ `scheme-ebc-tuition-waiver`
6. `CAND-118`: Annasaheb Patil Karj Vyaj Partawa Yojana $	o$ `scheme-annasaheb-patil-ir2`
7. `CAND-119`: Ramai Gharkul Anudan Yojana $	o$ `scheme-ramai-awas-yojana`
8. `CAND-120`: Indira Gandhi National Old Age Pension Portal Entry $	o$ `demo-indira-gandhi-old-age-pension`
9. `CAND-121`: Fundkar Phalbag Yojna Maharashtra $	o$ `scheme-bhausaheb-fundkar-phalbag`

All 9 relationships are non-conflicting, uniquely referenced, and verified.
