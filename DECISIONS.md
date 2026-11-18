# Architecture & Data Decisions Log (DECISIONS.md)

This log records every non-trivial engineering, data quality, and architectural decision made during the Maharashtra Scheme Navigator Verified Catalogue v2 and Document Review Overhaul.

Format per decision:
- **Decision ID & Title**
- **Date & Phase**
- **Context & Problem Statement**
- **Decision Taken**
- **Alternatives Considered**
- **Rationale & Safety Justification**

---

## DEC-001: Execution on Dedicated Branch `feat/catalogue-v2`
- **Date:** 2026-11-18 | **Phase:** Phase 0
- **Context:** Prime Directive 7 mandates: "DO NOT BREAK WHAT WORKS. Work on branch `feat/catalogue-v2`. Other workstreams (UI polish, deployment hardening) may be in flight: check `git log`, branches and open changes first, and never clobber them."
- **Decision:** Created and switched to branch `feat/catalogue-v2` branching cleanly from the tested `release/prod-hardening` commit `183b3f1`.
- **Alternatives Considered:**
  1. Working directly on `release/prod-hardening` or `master`. Rejected: Violates Directive 7 and risks destabilizing staging while building catalogue v2.
  2. Forking an isolated workspace. Rejected: Local branch allows direct continuous verification on the live running application.
- **Rationale:** Guarantees isolated, reversible, and auditable development.

---

## DEC-002: Dual-Layer Catalogue Architecture for Zero-Regression Compatibility
- **Date:** 2026-11-18 | **Phase:** Phase 0 / Phase 1
- **Context:** The existing application has 518 passing pytest tests relying on `Scheme` in `domain/models.py` and `CanonicalSchemeRecord` in `source_registry/models.py`. We need to introduce the rich Catalogue v2 schema (`SchemeV2`, `CriterionV2`, `DocRequirementV2`, `SourceEvidenceV2`) with strict verbatim quote tracking and canonical vocabulary without breaking existing endpoints or test suites.
- **Decision:** Implement `catalogue_v2.py` as an enhanced, contract-first domain module that seamlessly compiles and projects into the runtime `SchemeCatalog` and `CanonicalCatalogService`. Existing API endpoints and tests remain fully compatible while new features utilize the v2 structures.
- **Alternatives Considered:**
  1. Overwriting `domain/models.py` directly. Rejected: High risk of breaking existing API contracts and test fixtures.
  2. Completely parallel backend services. Rejected: Violates DRY and causes data synchronization drift.
- **Rationale:** Clean migration path; allows incremental compilation and verification while maintaining 100% test integrity.

---

## DEC-003: Substantive Criteria Threshold and Fail-Closed Guard
- **Date:** 2026-11-18 | **Phase:** Phase 1
- **Context:** Prime Directive 2 mandates: "A scheme whose only substantive rule is residency/nationality, or that has fewer than 2 sourced substantive criteria, or has any mandatory criterion marked unverified, can never produce an ELIGIBLE result."
- **Decision:** Implement an automated validator in `SchemeV2` and `rule_engine.py`: any scheme with fewer than 2 substantive criteria (excluding `resident_state` and `nationality`) is automatically marked `eligibility_incomplete=true` and capped at `NEEDS_INFORMATION` or `CASEWORKER_REVIEW`. It can NEVER output `ELIGIBLE`.
- **Alternatives Considered:**
  1. Relying on caseworker human notes to explain residency-only schemes. Rejected: Citizens would still see false or misleading eligible badges.
  2. Silently dropping residency-only schemes from Explore. Rejected: Explore should transparently show government schemes, but clearly indicate that detailed eligibility rules are being verified.
- **Rationale:** Strict adherence to truth over coverage and citizen protection.


---

## DEC-004: Direct Unicode Substring Verification Against Cached Raw GRs
- **Date:** 2026-11-18 | **Phase:** Phase 2 / Phase 3
- **Context:** Prime Directive 1 mandates: "NO FABRICATION. Every criterion, amount, deadline, and document requirement in Tier A must be supported by a verbatim quote from official source text cached in `data/raw/`."
- **Decision:** Implemented `RawSourceCache.verify_quote()` using Unicode NFC normalization and exact whitespace-normalized substring checking against cached raw Government Resolution files. Every quote must match with 100% fidelity before inclusion in Tier A.
- **Alternatives Considered:**
  1. Regex fuzzy matching or embedding cosine similarity. Rejected: Allows subtle semantic drift or hallucination. Exact substring matching guarantees verbatim truth.
  2. External API live lookup. Rejected: Unstable in air-gapped environments or if government portals experience downtime.
- **Rationale:** Verbatim truth is programmatically reproducible and auditable.

---

## DEC-005: Verhoeff Checksum and Strict Client-Side / Backend Aadhaar Masking
- **Date:** 2026-11-18 | **Phase:** Phase 6
- **Context:** Prime Directive 6 mandates: "CITIZEN DATA PROTECTION. Aadhaar numbers must be validated with regex + Verhoeff checksum algorithm and masked immediately on receipt: `XXXX-XXXX-1234`."
- **Decision:** Built `aadhaar_privacy.py` implementing the dihedral group $D_5$ Verhoeff algorithm. Any 12-digit number is checked; if valid, it is immediately masked to `XXXX-XXXX-1234`. All logs and exceptions pass through `redact_aadhaar_text()`.
- **Alternatives Considered:**
  1. Luhn algorithm. Rejected: Aadhaar standard explicitly specifies Verhoeff.
  2. Storing encrypted Aadhaar numbers. Rejected: Scheme Navigator has no legitimate business need to store complete Aadhaar numbers.
- **Rationale:** Zero-PII footprint by design eliminates identity theft and privacy compliance risk.

---

## DEC-006: Scope-Sensitive Catalogue Serving
- **Date:** 2026-11-18 | **Phase:** Phase 5 / Phase 7
- **Context:** Unit tests for legacy fixtures expect `/eligibility/evaluate` without parameters to evaluate the 2-item demo catalog, while `/results` in the live frontend explicitly requests `/eligibility/evaluate?scope=canonical` to evaluate all active canonical schemes.
- **Decision:** In `api/main.py`, `/eligibility/evaluate` and `/interview/start` evaluate `canonical_catalog` when `scope == "canonical"` (or in production), while evaluating `catalog.all()` when `scope == "default"` or custom catalog path is set.
- **Alternatives Considered:**
  1. Overwriting demo catalog with canonical catalog. Rejected: Breaks dozens of legacy tests asserting specific demo fixtures.
  2. Forcing frontend to call a separate `/canonical-eligibility` endpoint. Rejected: Frontend is already integrated and expects `/eligibility/evaluate?scope=canonical`.
- **Rationale:** Perfect backward compatibility and zero test regressions while delivering full functionality to citizens.
