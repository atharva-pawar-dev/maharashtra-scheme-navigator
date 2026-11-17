# MahaSarathi Interoperability & Integration Readiness Assessment

**Document Version:** 1.0.0 (Master Interoperability Blueprint)  
**Date:** November 12, 2026  
**Target Platform:** MahaSarathi (महासारथी — Maharashtra Unified Citizen Services Portal)  
**URL:** `https://mahasarathi.maharashtra.gov.in/`  
**Governing Department:** General Administration Department (GAD) & Directorate of Information Technology (DIT), Government of Maharashtra  

---

## 1. Executive Summary & Core Principle

MahaSarathi is the flagship unified citizen service delivery initiative of the Government of Maharashtra. It aims to unify government scheme discovery, public services delivery, citizen identity (MahaID), and single sign-on (MahaONE) across all state departments.

### The Non-Negotiable Integration Invariant:
> **Scheme Navigator DOES NOT simulate, reverse-engineer, or impersonate MahaSarathi, MahaID, or state citizen golden records.**  
> **Software cannot grant itself government authorization.**

In accordance with strict digital public infrastructure governance:
- Under **Release Path A (Independent Public Platform)**, Scheme Navigator operates as an independent guidance tool, using public government documentation and verified hand-offs.
- Under **Release Path B (Official Government Partnership)**, Scheme Navigator is architecturally prepared for authorized bilateral integration with MahaSarathi once formal administrative agreements, data-sharing protocols, and technical credentials are provided.

---

## 2. MahaSarathi Subsystems & Technical Landscape

### 2.1 MahaID (Citizen Identity Framework)
- **Concept:** A unique state-level citizen identifier linking family welfare entitlements across departments while adhering to UIDAI regulations prohibiting raw Aadhaar storage.
- **Interoperability Analysis:**
  - MahaID is an internal state enterprise identity system.
  - Third-party platforms cannot create, issue, or validate MahaIDs without direct access to the state identity service.
  - **Scheme Navigator Compliance:** The platform strictly avoids creating "mock MahaIDs" or internal pseudonyms labeled as government identity tokens. In local discovery, citizens are identified solely by ephemeral, cryptographic session tokens (`thread_id`).

### 2.2 MahaONE (Single Sign-On & Consent Management)
- **Concept:** Standardized OIDC / OAuth 2.0 identity provider allowing citizens to authenticate once and access departmental services (Aaple Sarkar, MahaDBT, Revenue, Municipal).
- **Consent Gateway:** Integrates electronic consent artifacts allowing citizens to authorize the release of DigiLocker documents to specific departmental processing queues.
- **Interoperability Analysis:**
  - Public REST API endpoints for external client registration are not currently open on the public web without departmental accreditation.
  - Attempting to scrape or script MahaONE login sessions violates portal security policies.

### 2.3 DigiLocker State Ingress
- MahaSarathi integrates directly with the National DigiLocker API and the Maharashtra State DigiLocker Repository (e-District / Aaple Sarkar).
- Enables automated pulling of digitally signed Domicile, Income, and Caste certificates.

---

## 3. Scheme Navigator Integration Adapter Architecture (Release Path B)

Scheme Navigator is architected with a modular, pluggable **MahaSarathi Integration Adapter** (`src/scheme_navigator/services/mahasarathi_adapter.py` design specification) ready for immediate activation upon formal government authorization:

```
+----------------------------------------------------------------------------------------------------+
|                                    SCHEME NAVIGATOR (FRONTEND)                                     |
+----------------------------------------------------------------------------------------------------+
                                                 |
                                                 | 1. Redirect to MahaONE SSO (Authorization Code + PKCE)
                                                 v
+----------------------------------------------------------------------------------------------------+
|                                      MAHASARATHI GATEWAY                                          |
|   [MahaONE Authentication] ──> [Citizen Consent Modal] ──> [Signed Consent Artifact (JWT)]         |
+----------------------------------------------------------------------------------------------------+
                                                 |
                                                 | 2. Callback with Auth Code & Signed Token
                                                 v
+----------------------------------------------------------------------------------------------------+
|                          SCHEME NAVIGATOR BACKEND (INTEGRATION ADAPTER)                            |
|   - Exchanges Auth Code for Token at MahaSarathi Token Endpoint                                    |
|   - Validates MahaSarathi Public Key Signature (RS256)                                             |
|   - Retrieves Verified Citizen Profile Attributes (Age, Category, District, Verified Domicile)     |
|   - Ingests Pre-Verified DigiLocker Document Metadata (Eliminating Manual Upload & OCR)            |
|   - Runs Deterministic Rule Engine against Verified Government Data                                |
+----------------------------------------------------------------------------------------------------+
```

### Technical Specification for Government Onboarding:
- **Protocol:** OpenID Connect (OIDC) Core 1.0 with PKCE (RFC 7636).
- **Data Minimization:** Requests only essential scopes: `openid`, `profile.basic`, `residence.district`, `documents.metadata`. Full Aadhaar number is never requested or transmitted.
- **Consent Artifacts:** Uses MeitY Electronic Consent Framework compliant consent records stored in cryptographic audit logs.

---

## 4. Current Status & Transition Matrix

| Capability | Current Status (Release Path A) | Target Status (Release Path B) | Prerequisites for Activation |
|---|---|---|---|
| **Scheme Discovery** | Independently indexed from public sources | Synchronized via MahaSarathi Catalogue API | Bilateral API Data Agreement |
| **Citizen Authentication** | Ephemeral HMAC Session Tokens | MahaONE OIDC Single Sign-On | Departmental Client ID & Secret |
| **Citizen Profile Ingress** | Self-reported via guided interview | Pulled via citizen consent from MahaID | Executed DPDPA Data Processing Agreement |
| **Document Verification** | Pre-audit via vision extraction + reviewer | Verified directly from DigiLocker repository | DigiLocker Org Gateway Approval |
| **Application Submission** | Safe hand-off to official portals | Direct programmatic API submission | Departmental API Gateway Whitelist |
| **Application Tracking** | Citizen-reported progress tracking | Real-time government webhook updates | MahaSarathi Event Webhook Subscription |
