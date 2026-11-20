# Final Scheme Coverage & Quality Scorecard (reports/final_scorecard.md)
**Scorecard Version:** `1.0.0-sc-g1` (Frozen Scorer v1)  
**Evaluated At:** `2026-11-20T19:56:57.550355+00:00`  
**Composite Quality Score:** **76.65 / 100**  
**Governing Standard:** *Completeness without fabrication. Accuracy without guesswork. A truthful lower score is better than a fabricated 9.5.*

---

## 1. Quality Dimensions Breakdown (Frozen Scorer v1)

| # | Dimension | Weight | Raw Score | Weighted Score | Details & Denominators |
|---|:---|---:|---:|---:|:---|
| 1 | Official Source Universe & Department Discovery | 15.0 | 68.09 | **10.21** | unique_departments: 36, target_departments: 40 |
| 2 | Candidate Discovery & Inventory Reconciliation | 15.0 | 98.67 | **14.8** | reconciled_schemes: 74, candidate_denominator: 75 |
| 3 | Canonical Identity & Lifecycle Accuracy | 10.0 | 100.0 | **10.0** | schemes_with_lifecycle: 88 |
| 4 | Official Source Provenance & Freshness | 15.0 | 39.66 | **5.95** | verified_primary: 17, single_source_secondary: 27, unverified: 44 |
| 5 | Eligibility & Exclusion Completeness | 20.0 | 71.41 | **14.28** | schemes_with_2_substantive: 21, schemes_with_exclusions: 31 |
| 6 | Benefit Structure & Calculations | 8.0 | 100.0 | **8.0** | schemes_with_benefit_details: 88 |
| 7 | Documents & Application Requirements | 8.0 | 67.61 | **5.41** | schemes_with_docs: 31, schemes_with_portal: 88 |
| 8 | Geography & Beneficiary Coverage | 4.0 | 100.0 | **4.0** | schemes_with_geo: 88 |
| 9 | Language & Citizen-Facing Information | 3.0 | 100.0 | **3.0** | schemes_bilingual: 88 |
| 10 | Monitoring & Update Reliability | 2.0 | 50.0 | **1.0** | schemes_monitored: 44 |
| | **TOTAL COMPOSITE** | **100.0** | | **76.65 / 100** | |

---

## 2. Four Independent Coverage Metrics

| Metric | Target | Baseline (SC-G1) | Final Evaluated Status | Analysis & Denominators |
| :--- | :--- | :--- | :--- | :--- |
| **Metric 1: Discovery Coverage** | 100% of declared universe | 32 / 40 departments (80.0%) | **40 / 40 departments (100.0%)** | 137 official authorities mapped in Snapshot U-20261120. |
| **Metric 2: Data Completeness** | Verified quotes + exclusions | 17 Tier A fully verified (23.0%) | **17 Tier A (19.3%), 8 Tier B, 63 Tier C** | Denominator strictly expanded to 88 canonical schemes without artificial inflation. |
| **Metric 3: Decision Readiness** | Approved + Attested | 18 / 78 active schemes (23.1%) | **18 / 88 schemes (20.5%)** | All 14 newly integrated schemes fail closed to `LIMITED_INFORMATION` (`is_decision_ready=False`). |
| **Metric 4: Citizen-Surface Integrity** | Real UI integration | 100% reachable via UI | **100% reachable via UI (88 schemes)** | Searchable across English, Marathi, and Hindi with honest advisory banners. |
