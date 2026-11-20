# Final Mutation Canary Verification Report (reports/final_mutation_canary_results.md)
**Project:** Maharashtra Scheme Navigator  
**Mission ID:** MSN-FINAL-001  
**Generated:** 2026-11-21  
**Governing Standard:** Production Release Program v2.0 (Gate G23, Appendix H5)  

---

## 1. Real-Codebase Mutation Invariance

All 12 individual mutation canaries specified in Appendix H5 were executed on the real codebase using `scripts/verify_individual_canaries.py`. Each mutation was confirmed caught by the test suite (`mutated rc=1`) and restored cleanly (`restored rc=0`).

| # | Canary Name | Mutation Target | Test Suite Response | Result |
|---|:---|:---|:---:|:---:|
| **01** | Flip income ceiling comparison ($<=$ to $<$) | `src/scheme_navigator/domain/rules.py` | `rc=1` $	o$ `rc=0` | **PASS (CAUGHT)** |
| **02** | Make UNKNOWN evaluate as FALSE in conjunction | `src/scheme_navigator/domain/rules.py` | `rc=1` $	o$ `rc=0` | **PASS (CAUGHT)** |
| **03** | Swap PMC and PCMC ward boundary membership | `src/scheme_navigator/domain/jurisdiction.py` | `rc=1` $	o$ `rc=0` | **PASS (CAUGHT)** |
| **04** | Remove owner check from interview endpoint (IDOR) | `src/scheme_navigator/api/main.py` | `rc=1` $	o$ `rc=0` | **PASS (CAUGHT)** |
| **05** | Let production profile load a fixture scheme | `src/scheme_navigator/services/catalog.py` | `rc=1` $	o$ `rc=0` | **PASS (CAUGHT)** |
| **06** | Allow a published claim with no source ID | `src/scheme_navigator/security/publication.py` | `rc=1` $	o$ `rc=0` | **PASS (CAUGHT)** |
| **07** | Drop Secure flag from session cookie | `src/scheme_navigator/api/main.py` | `rc=1` $	o$ `rc=0` | **PASS (CAUGHT)** |
| **08** | Serve signed URL with expiry of days instead of minutes | `src/scheme_navigator/security/storage.py` | `rc=1` $	o$ `rc=0` | **PASS (CAUGHT)** |
| **09** | Skip magic-byte check on upload | `src/scheme_navigator/security/upload.py` | `rc=1` $	o$ `rc=0` | **PASS (CAUGHT)** |
| **10** | Log a raw session token unredacted | `src/scheme_navigator/security/audit_logger.py` | `rc=1` $	o$ `rc=0` | **PASS (CAUGHT)** |
| **11** | Permit an author to approve their own publication | `src/scheme_navigator/security/publication.py` | `rc=1` $	o$ `rc=0` | **PASS (CAUGHT)** |
| **12** | Cache a personalised response under a shared key | `src/scheme_navigator/api/main.py` | `rc=1` $	o$ `rc=0` | **PASS (CAUGHT)** |

**Detection Rate:** **12 / 12 (100.0%)**
