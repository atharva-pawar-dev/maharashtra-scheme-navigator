# Maharashtra Scheme Quality Scorecard (Baseline v0)
**Scorecard Version:** `0.1.0-baseline`  
**Evaluated At:** `2026-11-20T15:08:13.414771+00:00`  
**Composite Quality Score:** **64.8 / 100**  
**Governing Standard:** *A truthful lower baseline is better than a fabricated 9.5.*

---

## 1. Quality Dimensions Breakdown

| # | Dimension | Weight | Raw Score (0-100) | Weighted Score | Key Metrics |
|---|:---|---:|---:|---:|:---|
| 1 | Official Source Universe & Department Discovery | 15.0 | 57.19 | **8.58** | unique_departments: 32, target_departments: 40 |
| 2 | Candidate Discovery & Inventory Reconciliation | 15.0 | 98.67 | **14.8** | reconciled_schemes: 74, candidate_denominator: 75 |
| 3 | Canonical Identity & Lifecycle Accuracy | 10.0 | 100.0 | **10.0** | schemes_with_lifecycle: 74 |
| 4 | Official Source Provenance & Freshness | 15.0 | 37.7 | **5.66** | verified_primary: 17, single_source_secondary: 13, unverified: 44 |
| 5 | Eligibility & Exclusion Completeness | 20.0 | 25.16 | **5.03** | schemes_with_2_substantive: 21, schemes_with_exclusions: 3 |
| 6 | Benefit Structure & Calculations | 8.0 | 100.0 | **8.0** | schemes_with_benefit_details: 74 |
| 7 | Documents & Application Requirements | 8.0 | 61.49 | **4.92** | schemes_with_docs: 17, schemes_with_portal: 74 |
| 8 | Geography & Beneficiary Coverage | 4.0 | 100.0 | **4.0** | schemes_with_geo: 74 |
| 9 | Language & Citizen-Facing Information | 3.0 | 100.0 | **3.0** | schemes_bilingual: 74 |
| 10 | Monitoring & Update Reliability | 2.0 | 40.54 | **0.81** | schemes_monitored: 30 |
| | **TOTAL COMPOSITE** | **100.0** | | **64.8 / 100** | |

---

## 2. Executive Summary & Four Independent Coverage Metrics

| Metric | Target | Baseline Status | Analysis |
| :--- | :--- | :--- | :--- |
| **Metric 1: Discovery Coverage** | 100% of declared universe | **32 / 40 departments (80.0%)** | 74 canonical schemes reconciled from 75 candidates. |
| **Metric 2: Data Completeness** | Verified quotes + exclusions | **17 Tier A fully verified (23.0%)** | 13 Tier B (17.6%), 44 Tier C limited info (59.4%). |
| **Metric 3: Decision Readiness** | Approved + Attested | **18 / 78 active schemes (23.1%)** | Unapproved/unattested schemes fail closed to `NEEDS_REVIEW`. |
| **Metric 4: Citizen-Surface Integrity** | Real UI integration | **100% reachable via UI** | Search, detail modal, and Playwright journeys operational. |

---

## 3. Road to 95/100 (TRIMURTI Program Milestones)

- **SC-M0**: Establish honest baseline, thin-rule linting, fail-closed completeness attestations, and error reporting. (Score: ~64.8)
- **SC-G1**: Deep research on P0 high-impact schemes (expanding Tier A from 17 to 30+ with human review packets).
- **SC-G2**: Full Universe Reconciliation across all 40+ departments, LGD codes, and central schemes.
- **SC-G3**: P1 depth expansion, complex exclusion trees, and alternative ANY_OF document requirement graphs.
- **SC-G4 & G5**: Quality instrumentation, continuous monitoring, and stratified sample independent audit with 95% confidence intervals.
