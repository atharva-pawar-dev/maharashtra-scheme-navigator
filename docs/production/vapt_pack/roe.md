# VAPT Readiness Pack — Rules of Engagement (RoE)
## Maharashtra Scheme Navigator (MSN)

---

### 1. Test Window & Communications
- **Authorized Testing Window:** 09:00 IST to 21:00 IST, Monday through Friday.
- **Incident Escalation:** Any high or critical finding (e.g. RCE, unauthorized data exfiltration, or complete authentication bypass) must be reported within 2 hours to the Security Lead.

---

### 2. Testing Constraints and Safety Rules
1. **No Destructive Exploits:** Assessors must not execute destructive actions that corrupt the underlying file system, wipe operating system bins, or execute `DROP DATABASE` on staging.
2. **No Real PII Extraction:** Only synthetic test accounts and personas may be assessed. No real citizen data exists in the test database.
3. **Denial of Service Limits:** Volumetric DDoS attacks against staging network infrastructure are prohibited. Application-layer rate limit testing is permitted up to 100 requests per minute.
4. **Third-Party Boundary:** In accordance with Section 43/66 of the Information Technology Act 2000, testing against external government portals (`*.gov.in`) or AI APIs (Google Gemini, Bhashini) is strictly prohibited.
