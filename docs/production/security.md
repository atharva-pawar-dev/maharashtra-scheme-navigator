# Maharashtra Scheme Navigator — Security Engineering & Hardening Manual
## Protocol C8 Startup Guard, OWASP ASVS 5.0.0 Level 2 Posture, and VAPT Readiness

---

## 1. Security Architecture Principles

Maharashtra Scheme Navigator processes citizen eligibility queries and document validations for public welfare schemes. To safeguard citizen privacy and preserve government trust, the system enforces defence-in-depth:

1. **Protocol C8 Production Startup Guard:** The application refuses startup if insecure flags (`debug`, `reload`), demo fixtures, weak/default secrets (< 32 chars), or SQLite fallback are detected in production profile (`APP_ENV=production`).
2. **Deterministic Processing (Invariant B4):** Statutory eligibility logic operates entirely deterministically without relying on third-party cloud LLMs.
3. **Data Minimization:** No Aadhaar numbers, phone numbers, or unhashed citizen identifiers are retained permanently. All temporary interview state is purged on an hourly schedule.

---

## 2. Protocol C8 Production Startup Guard

Implemented in `src/scheme_navigator/core/config.py` and executed during FastAPI `lifespan`:

```python
def validate_production_startup(self) -> None:
    if self.app_env.casefold() in {"production", "prod"}:
        if self.debug:
            raise RuntimeError("CRITICAL C8 GUARD: Debug mode must be disabled in production.")
        if self.reload:
            raise RuntimeError("CRITICAL C8 GUARD: Auto-reload must be disabled in production.")
        if self.demo_fixtures_enabled:
            raise RuntimeError("CRITICAL C8 GUARD: Demo fixtures must be disabled in production.")
        self.validate_production_secrets()
        if not self.database_url or self.database_url.startswith("sqlite"):
            raise RuntimeError("CRITICAL C8 GUARD: Production profile mandates PostgreSQL DATABASE_URL.")
```

---

## 3. OWASP ASVS 5.0.0 Level 2 Compliance Posture

Full CSV audit matrix is maintained at `docs/production/asvs_matrix.csv`.

| ASVS Chapter | Controls Audited | Status | Evidence Reference |
|---|---|---|---|
| **V1 Architecture & Threat Modeling** | 4 | PASS | `docs/production/vapt_pack/threat_model.md`, `docs/production/architecture.md` |
| **V2 Authentication** | 3 | PASS | `src/scheme_navigator/core/config.py`, `src/scheme_navigator/security/auth.py` |
| **V3 Session Management** | 4 | PASS | `src/scheme_navigator/security/auth.py` (HttpOnly, SameSite, Secure cookies) |
| **V4 Access Control** | 3 | PASS | `tests/test_auth_and_sessions_hardening.py` (RBAC & IDOR checks) |
| **V5 Validation & SSRF** | 3 | PASS | `src/scheme_navigator/security/ssrf.py` (SSRF validator) |
| **V6 Cryptography** | 2 | PASS | `src/scheme_navigator/security/auth.py` (HMAC-SHA256, 32-char entropy) |
| **V7 Error Handling & Logging** | 3 | PASS | `src/scheme_navigator/security/audit_logger.py` (PII redaction) |
| **V8 Data Protection** | 2 | PASS | `src/scheme_navigator/security/retention.py` (Scheduled hourly purge) |
| **V9 Communications** | 2 | PASS | `src/scheme_navigator/api/main.py` (Security headers & HSTS) |
| **V10 Malicious Code** | 1 | PASS | `release/evidence/ws6/E-WS6-002_security_scan.json` (AST scan: 0 findings) |
| **V11 Business Logic** | 2 | PASS | `src/scheme_navigator/services/rule_engine.py` (Kleene 3-valued logic) |
| **V12 File Storage** | 2 | PASS | `src/scheme_navigator/security/storage.py` (Magic-byte validation, 15m signed URLs) |
| **V13 API Security** | 2 | PASS | `src/scheme_navigator/security/rate_limiter.py` (Sliding window rate limit) |
| **V14 Configuration** | 2 | PASS | `src/scheme_navigator/core/config.py` (Protocol C8 startup guard) |

---

## 4. HTTP Security Headers

Enforced by `security_headers_middleware` on all responses:
- `X-Content-Type-Options: nosniff` (MIME confusion prevention)
- `X-Frame-Options: DENY` (Clickjacking prevention)
- `X-XSS-Protection: 0` (Sanitization standard)
- `Referrer-Policy: strict-origin-when-cross-origin` (Leak prevention)
- `Permissions-Policy: geolocation=(), camera=(), microphone=(self), payment=()`
- `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (Enforced in production)

---

## 5. External VAPT Readiness Pack

Located at `docs/production/vapt_pack/`:
- `scope.md`: Detailed asset inventory and out-of-scope third-party systems
- `architecture_and_data_flow.md`: Topology and data flow diagrams
- `credentials_and_test_accounts.md`: 5 test personas from `CITIZEN` to `CATALOGUE_ADMIN`
- `threat_model.md`: STRIDE matrix covering 7 attack categories
- `roe.md`: Assessment schedule, safety rules, and CERT-In compliance boundaries
