# Maharashtra Scheme Universe Scope & Snapshot (docs/catalogue/scheme_universe_scope.md)
**Universe Snapshot Version:** `U-20261120`  
**Governing Standard:** *TRIMURTI v3 — Completeness without fabrication. Truth above record count.*  
**Status:** Frozen Baseline Scope for Milestone SC-M0  
**Effective Date:** 2026-11-20  

---

## 1. Statutory Universe Definition and Inclusion Boundary

Under Section 5.1 of TRIMURTI v3, the Maharashtra Scheme Universe encompasses all government welfare, direct benefit transfer (DBT), pension, scholarship, subsidy, and social security programs targeted at individual citizens and households resident in Maharashtra.

### Core Inclusion Criteria
1. **Target Beneficiary**: Individual citizen, family unit, student, farmer, woman, child, person with disability, senior citizen, or smallholder resident in Maharashtra.
2. **Entitlement Character**: Direct cash transfer, recurring pension, fee waiver, maintenance stipend, agricultural input subsidy, interest subvention, or assistive equipment.
3. **Government Authority**: Enacted or administered by:
   - Maharashtra State Government Departments and Directorates.
   - Central Sector Schemes implemented within Maharashtra.
   - Centrally Sponsored Schemes (CSS) with state cost-sharing.
   - Statutory Welfare Boards (e.g. Mahabocw, Sant Rohidas Charmakar, Annasaheb Patil).
   - Local Bodies (Municipal Corporations PMC, PCMC, BMC, TMC, NMMC, and Zilla Parishads).

### Explicit Exclusions (Maintained with Evidence)
- **General Public Infrastructure**: Highways, irrigation dam construction, administrative buildings.
- **Institutional / Commercial Procurement**: Government tender opportunities, vendor contracts.
- **Certificates & Regulatory Services**: Domicile certificate issuance, caste verification (these are prerequisite documents, not benefit schemes).
- **Civil Servant Internal Administrative Allowances**: Standard internal DA/HRA.

---

## 2. Maharashtra State Department Denominator (40 Departments Target)

The official administrative directory establishes the following 40 department/authority universe for comprehensive coverage:

| # | Department / Authority | Administrative Level | Baseline Status | Discovered Schemes |
|---|:---|:---|:---|:---:|
| 1 | Social Justice and Special Assistance (SJSA) | State Department | `VERIFIED` | 13 |
| 2 | Agriculture Department (Krishi Vibhag) | State Department | `VERIFIED` | 6 |
| 3 | Women and Child Development (WCD) | State Department | `VERIFIED` | 5 |
| 4 | Higher and Technical Education | State Department | `VERIFIED` | 4 |
| 5 | Tribal Development Department (TRTI) | State Department | `VERIFIED` | 4 |
| 6 | Rural Development and Panchayati Raj | State Department | `VERIFIED` | 4 |
| 7 | Other Backward Bahujan Welfare (OBC/VJNT/SBC) | State Department | `VERIFIED` | 3 |
| 8 | Public Health and Family Welfare | State Department | `VERIFIED` | 2 |
| 9 | Industries, Energy and Labour (Labour Welfare / BoCW) | State Department | `VERIFIED` | 2 |
| 10 | Skill Development, Employment and Entrepreneurship | State Department | `VERIFIED` | 2 |
| 11 | Housing Department (Grihanirman) | State Department | `VERIFIED` | 2 |
| 12 | Food, Civil Supplies and Consumer Protection | State Department | `VERIFIED` | 2 |
| 13 | Minority Development Department | State Department | `DISCOVERED` | 2 |
| 14 | School Education and Sports | State Department | `DISCOVERED` | 2 |
| 15 | Cooperation, Marketing and Textiles | State Department | `DISCOVERED` | 1 |
| 16 | Medical Education and Drugs | State Department | `DISCOVERED` | 1 |
| 17 | Pune Municipal Corporation (PMC - Samaj Vikas) | Local Body | `VERIFIED` | 6 |
| 18 | Pimpri Chinchwad Municipal Corporation (PCMC) | Local Body | `VERIFIED` | 2 |
| 19 | Brihanmumbai Municipal Corporation (BMC) | Local Body | `VERIFIED` | 2 |
| 20 | Thane Municipal Corporation (TMC) | Local Body | `VERIFIED` | 2 |
| 21 | Navi Mumbai Municipal Corporation (NMMC) | Local Body | `VERIFIED` | 1 |
| 22 | Ministry of Agriculture & Farmers Welfare (GoI) | Central Applicable | `VERIFIED` | 1 |
| 23 | Ministry of Rural Development (GoI - IGNOAPS/PMAY) | Central Applicable | `VERIFIED` | 2 |
| 24 | Ministry of Housing and Urban Affairs (GoI) | Central Applicable | `DISCOVERED` | 1 |
| 25 | Ministry of Social Justice & Empowerment (GoI) | Central Applicable | `DISCOVERED` | 1 |
| 26-40 | Remaining State Directorates & District Zilla Parishads | State/Local Long Tail | `NOT_STARTED` | 0 |

---

## 3. Baseline Universe Metrics & Disposition Reconciliation

As of snapshot `U-20261120`:
- **Total Candidates Evaluated**: 75
- **Canonical Reconciled Records in Catalogue v2**: 74
- **Quarantined Demo Fixtures**: 1 (`demo-majhi-ladki-bahin`)
- **Tiers Breakdown**:
  - **Tier A (Verified Primary)**: 17 schemes (100% verified verbatim Marathi quotes from official GRs).
  - **Tier B (Municipal / Single Source Secondary)**: 13 schemes (PMC, PCMC, BMC, TMC, NMMC).
  - **Tier C (Discovered / Limited Info)**: 44 schemes (explicitly unverified, non-definitive matching only).
- **Substantive Rule Coverage**:
  - Schemes with $\ge 2$ substantive criteria: 21
  - Schemes with 1 substantive criterion: 9
  - Schemes with 0 substantive criteria (residency only): 44 (quarantined to non-definitive matching via Thin-Rule Protection).

---

## 4. Snapshot Invariance and Change Management

Per Invariant I-15, candidate schemes cannot be deleted or reclassified to manipulate coverage scores.
Any newly discovered scheme enters as `U+YYYYMMDD` addition and immediately increases the denominator.
Reconciled dispositions must be evidenced by official Government Resolutions or administrative directories.
