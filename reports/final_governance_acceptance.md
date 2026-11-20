# Final Reviewer Governance & RBAC Acceptance Report (reports/final_governance_acceptance.md)
**Project:** Maharashtra Scheme Navigator  
**Mission ID:** MSN-FINAL-001  
**Generated:** 2026-11-21  
**Governing Standard:** TRIMURTI v4 — Human Governance & Separation of Attestation (Invariants I-04, I-05, I-06)  

---

## 1. Separate Governance Workflows

The governance subsystem maintains strict separation between:
1. **Dossier Completeness Attestation (`CompletenessAttestation`):**
   - Verifies that all statutory conditions, exclusions, alternative tracks, and benefit limitations are fully mapped from official GRs.
   - Binds cryptographically to the exact SHA-256 hash of the scheme rule set and source document digests.
2. **Eligibility-Rule Approval (`RuleApprovalRecord`):**
   - Independent verification of rule AST logic by authorized legal reviewer.
   - Requires double confirmation of all numerical limits (income ceiling, land hectares, age boundaries).

---

## 2. Invariant I-05 Enforcement: No AI Agent Self-Authorization

- Attestation endpoints (`/governance/review-queue/{id}/attest`) enforce server-side RBAC checks.
- Sessions with role `ANONYMOUS`, `CITIZEN`, or unauthorized roles receive HTTP 403 Forbidden.
- Only authenticated sessions with `LEGAL_REVIEWER` or `CATALOGUE_ADMIN` role can sign attestations.
- AI agents cannot programmatically self-approve eligibility rules.

---

## 3. Reviewer Dashboard Integration

The Reviewer Portal (`static/reviewer.html` / `/reviewer`) provides:
- Live review queue with priority sorting.
- Dossier inspection and source evidence links.
- Interactive candidate reconciliation table with filterable dispositions.
- Official authority directory with LGD status tracking.
