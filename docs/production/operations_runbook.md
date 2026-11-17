# MAHARASHTRA SCHEME NAVIGATOR — OPERATIONS RUNBOOKS & HANDOVER MANUAL

**Document Version:** 1.0.0  
**Effective Date:** 17 November 2026  
**Status:** Approved for Production Operations  

---

## 1. Routine Deployment Runbook

### 1.1 Prerequisites
- Verified release tag or commit on `release/*` branch.
- Passed CI pipeline (`.github/workflows/ci.yml`).
- Active target environment variables populated per `docs/production/architecture.md`.

### 1.2 Deployment Procedure
```bash
# 1. Pull latest production container image
docker pull msn-app:latest

# 2. Execute dry-run database migration (if schema update included)
python scripts/migrate_sqlite_to_postgres.py --postgres-url "$DATABASE_URL" --dry-run

# 3. Apply schema migrations
python scripts/migrate_sqlite_to_postgres.py --postgres-url "$DATABASE_URL"

# 4. Restart application containers with zero downtime rolling restart
docker compose up -d --no-deps --build app

# 5. Execute automated post-deployment verification
python scripts/verify_deployment.py --url http://127.0.0.1:8000
```

---

## 2. Monitoring, Health Probes & Alerting Runbook

### 2.1 Endpoint Probes
- **Liveness Probe:** `GET /healthz`  
  - Target SLA: 200 OK, latency < 50ms.  
  - Failure Action: Restart container after 3 consecutive 5xx errors (timeout 5s).
- **Readiness Probe:** `GET /readyz`  
  - Verifies canonical scheme catalogue loaded (`schemes_loaded >= 70`) and storage subsystem healthy.  
  - Failure Action: Remove instance from load balancer rotation until healthy.

### 2.2 Alerting Thresholds
| Metric | Warning Threshold | Critical Threshold | Action |
|---|---|---|---|
| HTTP 5xx Rate | > 1.0% over 5m | > 5.0% over 2m | Trigger PagerDuty; invoke rollback runbook |
| Deterministic Latency (p95) | > 200 ms | > 500 ms | Scale app replicas; check CPU throttling |
| Data Purge Failures | 1 failed cycle | 2 consecutive failed cycles | Escalate to privacy engineer |
| Database Connections | > 75% pool | > 90% pool | Check connection leaks; restart idle connections |

---

## 3. Cryptographic Secret & Key Rotation Runbook

### 3.1 Session HMAC Secret (`SCHEME_NAVIGATOR_AUTH_SECRET`)
- **Frequency:** Every 90 days or immediately upon suspected compromise.
- **Procedure:**
  1. Generate high-entropy 64-character secret: `openssl rand -hex 32`.
  2. Deploy new secret across container environment.
  3. Note: Rotating this secret invalidates active citizen sessions, requiring citizens to start fresh anonymous sessions (no PII lost).

### 3.2 Catalogue Release Signing Key (`SCHEME_NAVIGATOR_RELEASE_KEY`)
- **Frequency:** Every 180 days.
- **Procedure:**
  1. Generate new 64-character key.
  2. Update key in secret manager.
  3. Re-sign canonical catalogue snapshot: `python scripts/sign_catalogue.py --key "$NEW_KEY"`.

---

## 4. Incident Response & CERT-In Mandatory Escalation Runbook

In accordance with CERT-In Cyber Security Directions (2022), all cybersecurity incidents must be reported to `incident@cert-in.org.in` within **6 hours** of confirmation.

### 4.1 Incident Severity Classification
- **Sev-1 (Critical):** Confirmed citizen PII breach, cryptographic key compromise, or unauthorized catalogue defacement. (RTO < 15m, CERT-In notice within 6h).
- **Sev-2 (High):** Complete service outage, database corruption, or SSRF protection failure. (RTO < 30m).
- **Sev-3 (Medium):** Degraded performance, single scheme evaluation failure, or purge worker stall. (RTO < 2h).
- **Sev-4 (Low):** Minor UI styling issue or documentation discrepancy. (Resolved in normal sprint).

### 4.2 Emergency Incident Contacts
- **Incident Commander:** Single Accountable Release Engineer (`ops@scheme-navigator.internal`)
- **Security Lead:** Chief Information Security Officer
- **Legal & Privacy Officer:** Data Protection Officer (`dpo@scheme-navigator.internal`)
- **CERT-In Reporting Channel:** `incident@cert-in.org.in` / Helpdesk `+91-11-24368572`

---

## 5. Backup Verification & Point-in-Time Recovery Runbook

### 5.1 Routine Backup Verification
Run automated DR drill weekly:
```bash
python scripts/dr_drill.py --output-report /var/log/msn/dr_drill_weekly.json
```
Verify exit code is 0 and `status == "PASS"`.

### 5.2 Emergency Restore
If catastrophic data corruption occurs:
```bash
# 1. Simulate dry-run recovery
python scripts/rollback.py --target database --backup-file _backups/latest.sqlite3 --dry-run

# 2. Execute restoration and verify health
python scripts/rollback.py --target database --backup-file _backups/latest.sqlite3 --verify
```

---

## 6. RACI Operations Ownership Matrix

| Function / Task | Release Engineer | Database Admin | Security Lead | Catalogue Admin | Legal Counsel |
|---|---|---|---|---|---|
| Container Builds & CI/CD | **Accountable** | Informed | Consulted | Informed | Informed |
| Schema Migrations | Responsible | **Accountable** | Consulted | Informed | Informed |
| Secret Rotation | Responsible | Consulted | **Accountable** | Informed | Informed |
| Catalogue Approval & Signing | Consulted | Informed | Consulted | **Accountable** | Consulted |
| CERT-In Incident Reporting | Responsible | Informed | **Accountable** | Informed | Consulted |
| Data Retention & DPDP Purge | Responsible | Responsible | Consulted | Informed | **Accountable** |
| Disaster Recovery Drills | **Accountable** | Responsible | Consulted | Informed | Informed |
