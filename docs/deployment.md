# Deployment, Infrastructure & Production Engineering Guide

## 1. Overview & Runtime Environments
Scheme Navigator supports two primary deployment topologies:
1. **Local Development / Single-Node Evaluation (`APP_ENV=local`)**:
   - Lightweight SQLite databases (`data/*.sqlite3`).
   - Direct execution via Python 3.11 virtual environment.
   - Hot-reloading enabled for local frontend and API development.
   - Demo fixtures enabled for sandbox testing.
2. **Production Multi-User Containerized Cluster (`APP_ENV=production`)**:
   - Containerized application services running under Uvicorn with multiple worker processes.
   - Externalized PostgreSQL database for concurrent ACID transactions.
   - External Qdrant vector database for semantic scheme retrieval.
   - Reverse-proxy (NGINX / Caddy) terminating TLS and enforcing rate limits.
   - Demo fixtures strictly disabled; fail-closed secret and signature validation enforced.

---

## 2. Local Development Deployment

### Prerequisites:
- Python 3.11 (tested on 3.11.4)
- Virtual environment with dependencies installed:
  ```powershell
  Set-Location -Path "C:\Users\Admin\Downloads\scheme-navigator\scheme-navigator"
  ..\.venv\Scripts\Activate.ps1
  ```

### Starting the Application:
```powershell
# Run Uvicorn development server
..\.venv\Scripts\python.exe -m uvicorn scheme_navigator.api.main:app --host 127.0.0.1 --port 8000 --reload
```
Access the application:
- Citizen Guidance Portal: `http://127.0.0.1:8000/`
- Explore Schemes: `http://127.0.0.1:8000/explore`
- Find Schemes for Me: `http://127.0.0.1:8000/interview`
- Reviewer Portal: `http://127.0.0.1:8000/reviewer.html`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

---

## 3. Production Container Deployment (Docker & Compose)

### 3.1 Production Environment Variables (`.env.production`)
Create a production configuration file from `.env.example`:
```ini
APP_ENV=production
LOG_LEVEL=INFO
DATA_RETENTION_HOURS=24
PRIVILEGED_SESSION_TTL_HOURS=1

# High-entropy cryptographic secrets (minimum 32 characters, distinct)
SCHEME_NAVIGATOR_AUTH_SECRET=REPLACE_WITH_OPENSSL_RAND_HEX_32
SCHEME_NAVIGATOR_RELEASE_KEY=REPLACE_WITH_OPENSSL_RAND_HEX_32
ADMIN_BOOTSTRAP_KEY=GENERATE_ONE_TIME_ADMIN_BOOTSTRAP_KEY

# Database Configuration
DATABASE_URL=postgresql://DB_USER:CHANGE_ME@DB_HOST:5432/DB_NAME

# Qdrant Vector DB
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=scheme_sources

# LLM & Extraction Providers
GEMINI_API_KEY=your-production-gemini-key
OLLAMA_BASE_URL=http://ollama:11434
```

### 3.2 Running via Docker Compose:
```bash
docker compose -f docker-compose.yml up --build -d
```

---

## 4. PostgreSQL Production Schema & Migrations
In production mode, the SQLite data files (`interviews.sqlite3`, `document_reviews.sqlite3`, `ingestion.sqlite3`) migrate to PostgreSQL tables:

```sql
-- Production PostgreSQL DDL
CREATE TABLE IF NOT EXISTS citizen_profiles (
    profile_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    profile_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_profiles_session ON citizen_profiles(session_id);

CREATE TABLE IF NOT EXISTS interview_sessions (
    thread_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    mode VARCHAR(32) NOT NULL,
    target_scheme_id VARCHAR(100),
    language VARCHAR(8) NOT NULL DEFAULT 'mr',
    transcript JSONB NOT NULL DEFAULT '[]',
    state_data JSONB NOT NULL,
    results JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_interviews_session ON interview_sessions(session_id);

CREATE TABLE IF NOT EXISTS document_reviews (
    review_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    source_file_sha256 VARCHAR(64) NOT NULL,
    extracted_fields JSONB NOT NULL,
    audit_events JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_reviews_expiry ON document_reviews(expires_at);
```

To execute database migrations:
```bash
curl -X POST http://127.0.0.1:8000/admin/db/migrate \
  -H "Authorization: Bearer <admin-token>"
```

---

## 5. Reverse-Proxy & Hardened NGINX Configuration
Deploy NGINX in front of Uvicorn to handle TLS termination, HTTP/2, security headers, and rate limiting:

```nginx
# /etc/nginx/conf.d/scheme_navigator.conf

limit_req_zone $binary_remote_addr zone=api_limit:10m rate=15r/s;
limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=2r/s;

server {
    listen 443 ssl http2;
    server_name schemenavigator.maharashtra.gov.in;

    ssl_certificate /etc/ssl/certs/scheme_navigator.crt;
    ssl_certificate_key /etc/ssl/private/scheme_navigator.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self';" always;

    client_max_body_size 12M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        limit_req zone=api_limit burst=30 nodelay;
    }

    location /documents/audit-upload {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        limit_req zone=upload_limit burst=5 nodelay;
    }
}
```

---

## 6. Backup, Restore & Operational Probes
1. **Health Probes**:
   - `/healthz`: Liveness check (verifies process responsiveness).
   - `/readyz`: Readiness check (verifies database connectivity and catalogue loading).
2. **Automated Live Backup**:
   ```bash
   curl -X POST http://127.0.0.1:8000/admin/db/backup \
     -H "Authorization: Bearer <admin-token>"
   ```
   Generates timestamped hot backups in `data/backups/`.
3. **Restoration Protocol**:
   Documented in `docs/disaster_recovery.md` with zero-data-loss validation.
