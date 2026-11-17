# Executive Policy & Technology Briefing: Scheme Navigator
## A Maharashtra-Wide Digital Public Infrastructure Proposal for Citizen Scheme Discovery, Eligibility Explanation & Application Preparation

**Document Version:** 1.0.0  
**Date:** November 12, 2026  
**Presented To:** Government of Maharashtra Technology & Policy Stakeholders  
**Classification:** Independent Technology Proposal & Demonstration  

---

## 1. The Citizen Problem in Maharashtra

The Government of Maharashtra administers hundreds of welfare schemes, scholarships, farmer subsidies, and social pensions across more than 35 departments, attached directorates, and state development corporations. 

Despite significant investments in digital governance, citizens face severe structural friction:
1. **Extreme Portal Fragmentation:** A citizen must navigate separate portals for scholarships (MahaDBT 1.0 / 2.0), public service certificates (Aaple Sarkar), unified services (MahaSarathi), and women's welfare (Ladki Bahin), or visit physical Taluka Tehsildar offices for destitute pensions.
2. **Opaque Statutory Eligibility:** Government Resolutions (शासन निर्णय) are written in dense legal Marathi. Citizens frequently do not know if they qualify, what family income thresholds mean in practice, or how disability percentages are evaluated.
3. **The "Missing Information vs. Rejection" Fallacy:** Existing heuristic portals often report a citizen as "Ineligible" simply because a single piece of information (such as landholding or disability percentage) was omitted.
4. **Certificate Prerequisite Roadblocks:** Citizens frequently arrive at an application deadline only to discover they need a Domicile Certificate, which requires an Income Certificate, which takes 15 statutory days on Aaple Sarkar.

---

## 2. The Solution: Scheme Navigator

**Scheme Navigator** is an independently developed, digital public infrastructure software platform designed to serve as an intelligent, transparent citizen guidance gateway.

```
+----------------------------------------------------------------------------------------------------+
|                                      SCHEME NAVIGATOR SOLUTION                                     |
+----------------------------------------------------------------------------------------------------+
  1. Comprehensive Discovery: Single entry point indexing state, central, and corporation schemes.
  2. Explainable Deterministic Eligibility: Three-valued logic (True / False / Unknown).
  3. Multilingual Accessibility: 100% monolingual separation in Marathi, Hindi, and English.
  4. Document Pre-Audit & Extraction: In-browser pre-audit ensuring document completeness.
  5. Prerequisite Roadmap: DAG calculation of required Aaple Sarkar certificates with RTS days.
  6. Safe Official Hand-Off: Seamless transfer to official portals with pre-submission checklists.
  7. Multi-Tier Geographic Isolation: All 29 Municipal Corporations & 424 ULBs strictly isolated.
```

---

## 3. Core Architectural Highlights

- **Multi-Tier Municipal & Local Governance Intelligence:** Complete coverage of all 29 Maharashtra Municipal Corporations (reconciled with the Directorate of Municipal Administration) and 424 Urban Local Bodies. Enforces mathematical boundary isolation (e.g., Pune Municipal Corporation vs. PCMC, BMC, TMC) with zero misallocation of municipal funds.
- **Fail-Closed Boundary Ambiguity Protection:** Postal PIN codes traversing municipal boundary lines (e.g., 411027, 411061) are flagged with `LOCATION_REQUIRES_CONFIRMATION` instead of heuristic guessing.
- **Deterministic Rule Engine (Zero AI Hallucination):** Eligibility evaluations are strictly computed using deterministic mathematical ASTs bound directly to operative Government Resolutions. Generative AI is used solely for natural-language dialogue and explanation; it is **never** permitted to decide eligibility or alter rules.
- **Fail-Closed Evidence Lineage:** Every rule leaf links to an authentic Government Resolution, departmental notification, and SHA-256 cryptographic digest.
- **Enterprise Privacy & Security:** Built strictly compliant with DPDPA 2023. Enforces 24-hour ephemeral session purging, zero plaintext Aadhaar storage, zero password collection, and HMAC-SHA256 session ownership.
- **Three Dignified Citizen Journeys:**
  - *Find Schemes for Me:* Guided, conversational interview for citizens who do not know what schemes exist.
  - *Explore Schemes:* Instant, independent library search for citizens who know what they want.
  - *Prepare My Application:* Session-bound document checklist and prerequisite dependency roadmap.

---

## 4. The Collaborative Path Forward: Release Path B

Scheme Navigator is fully operational today as an **Independent Public Platform (Release Path A)**. However, its true transformative power can be unlocked through formal partnership with the Government of Maharashtra:

```
[Release Path A: Independent Public Platform]
- Public documentation & GR lineage
- Safe portal hand-offs & checklists
- Citizen-reported tracking
                      │
                      ▼ (Formal GoM Bilateral Authorization / MOU)
[Release Path B: Official Government Partnership]
- Integration with MahaSarathi & MahaID
- MahaONE Single Sign-On (OIDC / PKCE)
- Automated pulling of verified certificates from DigiLocker
- Direct programmatic submission via Departmental REST APIs
- Official application tracking via Government Webhooks
```

### Recommendation to Leadership:
We propose an exploratory technical review between the Directorate of Information Technology (DIT), General Administration Department (GAD), and the Scheme Navigator engineering team to evaluate pilot deployment opportunities at Gram Panchayat Setu Kendras and Citizen Assistance Desks.
