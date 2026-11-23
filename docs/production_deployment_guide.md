# Scheme Navigator — Enterprise Production Deployment Guide

**Document Version:** 1.0.0 (Master Deployment Manual)
**Date:** November 12, 2026
**Target Territory:** Maharashtra, India

---

## 1. Local Development vs. Production Architecture

Scheme Navigator is designed to operate seamlessly across two distinct infrastructure topologies:

```
+----------------------------------------------------------------------------------------------------+
|                                      TOPOLOGY COMPARISON                                           |
+----------------------------------------------------------------------------------------------------+

  [1. LOCAL DEVELOPMENT & SYNTHETIC DEMO]           [2. ENTERPRISE CLOUD PRODUCTION]
  - Host: Local developer workstation (Windows)     - Host: Linux VM / Kubernetes (AWS Mumbai / OCI)
  - Binding: 127.0.0.1:8000                         - Ingress: TLS 1.3 Reverse Proxy (Nginx / Cloudflare)
  - Database: SQLite 3.40+ (WAL mode)               - Database: Managed PostgreSQL 16+ (Multi-AZ)
  - Rate Limiter: In-memory sliding window          - Rate Limiter: Redis 7+ Cluster (Token Bucket)
  - Workers: Uvicorn --workers 1                    - Workers: Gunicorn + Uvicorn Workers (Multi-process)
  - Document Storage: Local ephemeral disk          - Document Storage: Encrypted S3-compatible Object Store
```

---

## 2. Infrastructure Requirements & Dependencies

### Hardware Sizing (Minimum Production Baseline):
- **API Nodes (App Tier):** 2x Virtual Machines, 4 vCPU, 8 GB RAM, 50 GB SSD (Ubuntu 22.04 LTS).
- **PostgreSQL Database:** 4 vCPU, 16 GB RAM, 100 GB GP3 SSD with automated backups.
- **Redis Cluster:** 3-node primary/replica cluster, 4 GB RAM.
- **Reverse Proxy / Load Balancer:** AWS ALB / Nginx with TLS 1.3 and WAF inspection.

---

## 3. Strict Network Exposure Conditions (`0.0.0.0`)

> [!WARNING]
> **MANDATORY SECURITY INVARIANT:**
> Binding directly to `0.0.0.0` is strictly forbidden in development or raw network environments.
> Scheme Navigator binds strictly to `127.0.0.1` by default.

Network exposure (`0.0.0.0`) is **only** permitted when all of the following criteria are satisfied:
1. **TLS 1.3 Reverse Proxy:** Nginx, Envoy, or Cloudflare terminates HTTPS and enforces modern cipher suites.
2. **Network Firewall / VPC Ingress:** Ingress rules restrict traffic strictly to port 443; raw port 8000 is never exposed to unauthorized LANs or the public Internet.
3. **WAF & Rate Limiting:** A Web Application Firewall inspects incoming payloads for SQLi, XSS, and bot scrapers before forwarding to Scheme Navigator.
4. **Administrative Protection:** Administrative routes (`/admin/*`) are completely blocked at the reverse proxy from public IP addresses and accessible only via management VPN.
5. **Distributed State Integration:** In-memory rate limiting and session ownership must be migrated to Redis before enabling `--workers > 1`.

---

## 4. Production Configuration Template (`.env.production`)

```ini
# Production Environment Configuration
APP_ENV=production
LOG_LEVEL=INFO
HOST=127.0.0.1
PORT=8000
WORKERS=4

# Production Relational Database
DATABASE_URL=postgresql://scheme_user:SECURE_PG_PASSWORD@db-primary.internal:5432/scheme_navigator

# Redis Distributed Cache & Rate Limiting
REDIS_URL=rediss://:CHANGE_ME@REDIS_HOST:6379/0

# Cryptographic Master Secrets (Must be 64-char hex strings generated via openssl rand -hex 32)
# CRITICAL: If these contain defaults or placeholders, the application fails closed on startup.
SESSION_SECRET=REPLACE_WITH_OPENSSL_RAND_HEX_32
CATALOGUE_RELEASE_SIGNING_KEY=REPLACE_WITH_OPENSSL_RAND_HEX_32

# S3 Compatible Encrypted Document Storage
S3_ENDPOINT_URL=https://s3.ap-south-1.amazonaws.com
S3_BUCKET_NAME=scheme-navigator-documents-prod
S3_ACCESS_KEY_ID=AKIA_SECURE_KEY_ID
S3_SECRET_ACCESS_KEY=SECURE_SECRET_ACCESS_KEY
S3_ENCRYPTION_MODE=aws:kms

# Data Retention
DATA_RETENTION_HOURS=24
DEMO_FIXTURES_ENABLED=false
```

---

## 5. Deployment & Health Verification Runbook

```bash
# 1. Clone repository and set up virtual environment
git clone https://github.com/maharashtra/scheme-navigator.git /opt/scheme-navigator
cd /opt/scheme-navigator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run database migrations
python -m scheme_navigator.core.migrations

# 3. Verify health and secrets validation
python -c "from scheme_navigator.core.config import settings; settings.validate_production_secrets()"

# 4. Start systemd service
sudo systemctl restart scheme-navigator
sudo systemctl status scheme-navigator

# 5. Check health endpoint
curl -s http://127.0.0.1:8000/source-registry/coverage | jq .
```
