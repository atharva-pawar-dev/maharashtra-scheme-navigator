# Maharashtra Scheme Navigator — Identity, Sessions, and Authorisation Manual
## Token Cryptography, Cookie Security, Role Hierarchy, and Access Control

---

## 1. Identity Architecture & Principles

Maharashtra Scheme Navigator adheres to privacy-by-design principles:
1. **Unforced Anonymous Citizen Discovery:** Citizens can explore schemes, execute eligibility assessments, and audit documents without mandatory account creation or phone/Aadhaar verification.
2. **Cryptographic Session Tokens:** Sessions are identified by cryptographically random 128-bit hex tokens (`secrets.token_hex(16)`), signed with HMAC-SHA256 using `SCHEME_NAVIGATOR_AUTH_SECRET`.
3. **Zero Sensitive PII in Client Storage:** Tokens encode only `session_id:user_id:role:expiry:signature`. No name, phone number, Aadhaar number, caste, or income data is ever stored in tokens, cookies, or browser storage.
4. **Hardened Cookie Standard:** Tokens are delivered in cookies configured with `HttpOnly`, `SameSite=Lax`, `Secure` (in production), and `__Host-` prefix on HTTPS origins.

---

## 2. Role-Based Access Control (RBAC) Matrix

```mermaid
graph TD
    CITIZEN[Citizen (Role Level 0)]
    ANALYST[Analyst (Role Level 1)]
    LEGAL[Legal Reviewer (Role Level 2)]
    ADMIN[Catalogue Admin (Role Level 3)]
    
    CITIZEN --> ANALYST
    ANALYST --> LEGAL
    LEGAL --> ADMIN
```

| Action / Resource | Minimum Role | Endpoint / Operation | Enforced By |
|---|---|---|---|
| Explore Schemes & Calculate Eligibility | `CITIZEN` | `GET /schemes`, `POST /eligibility/evaluate` | `get_current_session` |
| Start & Answer Own Interview | `CITIZEN` | `POST /interview/start`, `POST /interview/answer` | Session ownership check |
| Upload & Audit Own Documents | `CITIZEN` | `POST /documents/audit-upload` | Review ownership check |
| Report Inaccurate Scheme Info | `CITIZEN` | `POST /trust/report-issue` | Rate-limited public |
| Ingest Source Documents / Review Queue | `ANALYST` | `POST /ingestion/crawl`, `GET /ingestion/queue` | `require_role(ANALYST)` |
| Human Review of Candidate Schemes | `LEGAL_REVIEWER` | `POST /reviewer/schemes/{id}/approve` | `require_role(LEGAL_REVIEWER)` |
| Sign & Publish Production Catalogue | `CATALOGUE_ADMIN` | `POST /admin/catalogue/sign-release` | `require_role(CATALOGUE_ADMIN)` |
| Provision User Accounts / Revoke Sessions | `CATALOGUE_ADMIN` | `POST /admin/auth/provision-user` | `require_role(CATALOGUE_ADMIN)` |
| Execute Live Database Migrations | `CATALOGUE_ADMIN` | `POST /admin/database/migrate` | `require_role(CATALOGUE_ADMIN)` |

---

## 3. IDOR (Insecure Direct Object Reference) Protection

To prevent cross-tenant data leakage:
- **Interview Thread Isolation:** Every interview run is bound to its initiating session (`session_manager.bind_thread_to_session`). Any call to `/interview/answer` with a thread ID owned by another citizen returns `403 Forbidden`.
- **Document Review Isolation:** Document reviews and uploaded verification artifacts are bound to the citizen's session ID (`session_manager.bind_review_to_session`).
- **Administrative Bypass:** Only roles $\ge$ `ANALYST` can inspect cross-session records for official audit purposes.

---

## 4. Administrative Bootstrapping & Secret Rotation

- **One-Time Bootstrap:** An initial `CATALOGUE_ADMIN` can be minted only once via `POST /admin/auth/provision` using the `X-Admin-Bootstrap-Key` header matching `ADMIN_BOOTSTRAP_KEY` (minimum 32 characters entropy). Subsequent bootstrap attempts are locked with `403 Forbidden`.
- **Session Revocation:** Administrators can revoke compromised or terminated sessions via `POST /admin/auth/revoke`. Revoked session IDs are added to a memory blocklist, invalidating existing tokens immediately.
- **Key Rotation:** Invoking `session_manager.rotate_secret(new_key)` rotates the HMAC signing key, immediately invalidating all previous tokens.
