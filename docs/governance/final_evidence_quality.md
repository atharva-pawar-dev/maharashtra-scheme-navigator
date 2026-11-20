# Final Evidence Quality & Source Health Audit (docs/governance/final_evidence_quality.md)
**Project:** Maharashtra Scheme Navigator  
**Mission ID:** MSN-FINAL-001  
**Generated:** 2026-11-21  
**Governing Standard:** TRIMURTI v4 — Evidence Before Claims  

---

## 1. Source Link Health Inventory Breakdown

A comprehensive, non-bypass audit was conducted across **135 unique government and portal URLs** referenced in the scheme registry and catalogue.

| Verification State | Count | Percentage | Operational Policy |
| :--- | :---: | :---: | :--- |
| **`WORKING_AND_CONTENT_VERIFIED`** | 35 | 25.9% | Primary GRs cached in `data/raw/` with verified SHA-256 digests. Decision-ready. |
| **`WORKING_CONTENT_UNVERIFIED`** | 22 | 16.3% | Portal root or service landing page operational (HTTP 200). Serves for application handoff. |
| **`DEAD_CONFIRMED`** | 26 | 19.3% | Returned persistent HTTP 404. Linked schemes automatically fail closed to `LIMITED_INFORMATION`. |
| **`TIMEOUT_OR_CONNECTION_ERROR`** | 46 | 34.1% | Official NIC / department server connection timeout or rate limit under polite crawling. |
| **`UNKNOWN`** | 6 | 4.4% | Non-standard protocol or portal redirect loop requiring manual inspection. |
| **TOTAL** | **135** | **100.0%** | **Full inventory tracked in reports/final_source_health.csv** |

---

## 2. Evidence Remediation & Fail-Closed Protection

1. **No Silent Guesswork:**  
   When a source URL is confirmed dead (`HTTP 404`) or times out, the platform **never infers or fabricates eligibility rules**. Instead, the linked scheme is classified as `LIMITED_INFORMATION`, rendering the standard advisory banner:
   > *"This scheme has limited information. Eligibility cannot be confirmed."*

2. **Cached Raw GRs for Tier A Flagship Schemes:**  
   All 17 Tier A flagship schemes do not rely on live network fetches during runtime assessment. Their primary source documents are preserved with cryptographic digests in `data/raw/` and validated by `scripts/build_verified_catalogue_v2.py`.

3. **Remediation Action Register:**  
   Specific actions for all 78 non-working or transient links are catalogued in `reports/final_source_remediation.csv`, including alternative Aaple Sarkar/MahaDBT archive endpoints and manual review queue tickets.
