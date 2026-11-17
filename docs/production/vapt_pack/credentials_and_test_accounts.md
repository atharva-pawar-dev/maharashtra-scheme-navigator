# VAPT Readiness Pack — Credentials & Test Accounts
## Maharashtra Scheme Navigator (MSN)

---

### Test Account Matrix for Security Assessors

| Account Persona | Assigned Role | Provisioning Method | Token Type | Intended Scope of Testing |
|---|---|---|---|---|
| **Citizen Tester A** | `CITIZEN` | `POST /auth/session` | Standard session cookie (`sn_session`) | Core journeys, anonymous access, rate limiting |
| **Citizen Tester B** | `CITIZEN` | `POST /auth/session` | Standard session cookie (`sn_session`) | Cross-tenant IDOR attacks against Citizen Tester A |
| **Department Analyst** | `ANALYST` | Admin provisioned via `POST /admin/auth/provision-user` | Bearer token | Ingestion queue, candidate review, privilege escalation |
| **Legal Reviewer** | `LEGAL_REVIEWER` | Admin provisioned via `POST /admin/auth/provision-user` | Bearer token | Content verification, lifecycle progression |
| **Catalogue Administrator** | `CATALOGUE_ADMIN` | Minted via `POST /admin/auth/provision` with bootstrap key | High-privilege Bearer token | Catalogue signing, user provisioning, database migrations |

---

### Staging Bootstrap Key Configuration
- In the dedicated staging environment, assessors will be provided an isolated bootstrap key:
  `ADMIN_BOOTSTRAP_KEY=vapt-staging-bootstrap-key-32chars-min-entropy`
- This key permits assessors to test privileged provisioning and verify that role escalation from `CITIZEN` or `ANALYST` is blocked.
