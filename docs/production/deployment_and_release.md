# MAHARASHTRA SCHEME NAVIGATOR — DEPLOYMENT AND RELEASE SPECIFICATION

**Document Version:** 1.0.0  
**Effective Date:** 17 November 2026  
**Status:** Approved for Hardening / Staging  

---

## 1. Container Architecture & Hardened Multi-Stage Build

Maharashtra Scheme Navigator (MSN) uses a hardened multi-stage Docker build (`Dockerfile`) to eliminate build tooling, compiler dependencies, and unnecessary packages from the final runtime container image.

### 1.1 Multi-Stage Pipeline
1. **Builder Stage (`python:3.11-slim AS builder`):**
   - Installs `build-essential`.
   - Creates an isolated virtualenv `/opt/venv`.
   - Copies `pyproject.toml`, `README.md`, and `src/`.
   - Builds wheels and installs all Python dependencies into `/opt/venv`.
2. **Runner Stage (`python:3.11-slim AS runner`):**
   - Copies `/opt/venv` from builder stage.
   - Installs minimal shared OS libraries: `curl` (for healthcheck probes) and `libglib2.0-0` / `libgl1` (for document OCR/image processing).
   - Strips build compilers and apt package caches (`rm -rf /var/lib/apt/lists/*`).
   - Copies application source code, static frontend assets, and configuration files.

### 1.2 Non-Root Execution (UID 10001)
- The container strictly forbids execution as `root`.
- A dedicated unprivileged system user and group are provisioned:
  - User: `msnuser`
  - UID / GID: `10001:10001`
  - Shell: `/sbin/nologin`
  - Home: `/app`
- All application directories are owned by `msnuser:msnuser`.
- The container directive `USER 10001:10001` enforces unprivileged runtime rights, mitigating container breakout risks.

### 1.3 Container Healthcheck
- The `Dockerfile` incorporates an in-container healthcheck probe:
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
      CMD curl -f http://localhost:8000/healthz || exit 1
  ```
- Kubernetes, Docker Compose, and ECS engines monitor container health directly through this contract.

---

## 2. Docker Compose Topology & Infrastructure Services

For multi-container orchestrations (staging / on-premise government datacenters), `docker-compose.yml` specifies an isolated 3-tier topology:

```
┌────────────────────────────────────────────────────────┐
│                   Docker Compose Stack                 │
│                                                        │
│   ┌─────────────────┐       ┌──────────────────────┐  │
│   │     msn-app     │──────>│   postgres:16-alpine │  │
│   │   (Port 8000)   │       │     (Port 5432)      │  │
│   └────────┬────────┘       └──────────────────────┘  │
│            │                                           │
│            ▼                                           │
│   ┌─────────────────┐                                 │
│   │   minio/minio   │                                 │
│   │   (Port 9000)   │                                 │
│   └─────────────────┘                                 │
│                                                        │
└────────────────────────────────────────────────────────┘
```

1. **`app` Service:**
   - Multi-stage build based on `Dockerfile`.
   - Runs `uvicorn scheme_navigator.api.main:app --workers 2`.
   - Depends on `postgres` and `minio` with `condition: service_healthy`.
2. **`postgres` Service:**
   - Engine: PostgreSQL 16 Alpine.
   - Persistent volume: `postgres_data`.
   - Healthcheck: `pg_isready -U msn_user -d scheme_navigator`.
3. **`minio` Service:**
   - S3-compatible private object storage for citizen-uploaded documents.
   - Persistent volume: `minio_data`.
   - Healthcheck: `curl -f http://localhost:9000/minio/health/live`.

---

## 3. Deployment Verification Protocol (`scripts/verify_deployment.py`)

Deployment readiness is verified automatically using `scripts/verify_deployment.py`:

```bash
# Verify against a running live container / staging host:
python scripts/verify_deployment.py --url http://127.0.0.1:8000

# Verify in-process via FastAPI TestClient (CI/CD / hermetic test):
python scripts/verify_deployment.py --in-process
```

The script evaluates:
1. `GET /healthz`: HTTP 200, JSON status `"ok"`.
2. Security Headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy`.
3. `GET /readyz`: HTTP 200, JSON status `"ready"` with scheme catalogue loaded.
4. `GET /schemes`: HTTP 200, non-empty canonical scheme catalogue.
5. `POST /auth/session`: HTTP 200, mints secure anonymous session with session cookie.
