# VAPT Readiness Pack — Threat Model (STRIDE Methodology)
## Maharashtra Scheme Navigator (MSN)

---

### STRIDE Assessment Summary

| Threat Category | Potential Attack Vector | Primary Mitigation Control | ASVS Control |
|---|---|---|---|
| **Spoofing** | Forging citizen session tokens or spoofing administrative bootstrap key | HMAC-SHA256 signature verification with high-entropy secret; constant-time comparison | V2.1, V3.1 |
| **Tampering** | Modifying scheme eligibility criteria, benefits, or document requirements | Release key signature verification; immutable audit logs; Invariant B3 human approval ceiling | V1.4, V6.2 |
| **Repudiation** | Denying an administrative action (e.g. scheme publication or user provisioning) | Structured append-only audit trail (`security_audit.log`) with actor ID, IP, and timestamp | V7.2, V7.4 |
| **Information Disclosure** | Intercepting citizen PII, income, or caste documents; IDOR across threads | Zero PII in cookies; IDOR checks on all threads/reviews; 15-min signed URL TTL; TLS 1.3 | V3.2, V4.3, V8.3 |
| **Denial of Service** | Flooding API with document uploads, speech audio, or interview starts | Sliding-window per-IP rate limiting; strict payload limits (15 MiB PDF, 12 MiB image) | V13.1 |
| **Elevation of Privilege** | Citizen or Analyst acquiring Catalogue Administrator permissions | Server-side role hierarchy verification (`require_role`); bootstrap locked after initial use | V4.1, V4.2 |
| **SSRF** | Ingestion crawler tricked into fetching internal cloud metadata (169.254.169.254) | `validate_safe_url` blocks private IPs, metadata, localhost, and enforces `.gov.in` allowlist | V5.3 |
