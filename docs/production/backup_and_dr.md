# MAHARASHTRA SCHEME NAVIGATOR — BACKUP & DISASTER RECOVERY SPECIFICATION

**Document Version:** 1.0.0  
**Effective Date:** 17 November 2026  
**Status:** Approved for Production Hardening  

---

## 1. Disaster Recovery Objectives & SLAs

Maharashtra Scheme Navigator operates under strict recovery objectives to ensure data protection, compliance with CERT-In directions, and continuity of citizen services:

| Metric | Production Target | Verified Drill Result | Status |
|---|---|---|---|
| **Recovery Point Objective (RPO)** | < 1 hour | Hourly incremental / 24h point-in-time | COMPLIANT |
| **Recovery Time Objective (RTO)** | < 15 minutes (900s) | **0.337 seconds** | COMPLIANT |
| **Data Integrity Verification** | SHA-256 & `PRAGMA integrity_check` | 100% matched, zero corruption | COMPLIANT |

---

## 2. Backup Topology & Assets

```
┌──────────────────────────────────────────────────────────────┐
│                    Backup & Storage Topology                 │
├──────────────────┬───────────────────┬───────────────────────┤
│ 1. Persistence   │ 2. Scheme Truth   │ 3. Object Storage     │
│    Databases     │    & Catalogs     │    (Citizen Docs)     │
├──────────────────┼───────────────────┼───────────────────────┤
│ • citizen_profiles│ • data/source_    │ • MinIO / S3 private  │
│ • interviews     │   registry/       │   bucket              │
│ • ingestion      │ • data/candidates/│ • 24h retention limit │
│ • doc_reviews    │ • MANIFEST.sha256 │ • AES256 encryption   │
└──────────────────┴───────────────────┴───────────────────────┘
```

1. **Relational Databases:**
   - SQLite development / staging instances: Atomic copy using snapshot lock with pre-backup `PRAGMA integrity_check;`.
   - PostgreSQL production instances: Continuous WAL archiving + daily logical dumps via `pg_dump -Fc`.
2. **Canonical Scheme Catalogue:**
   - Git-backed, cryptographically signed release snapshots (`data/source_registry/`).
   - Every file indexed in `MANIFEST.sha256`.
3. **Citizen Uploaded Documents:**
   - Object storage documents are subject to a 24-hour retention ceiling (DPDP Act compliance).
   - In-transit encryption (TLS 1.3) and at-rest encryption (AES-256).

---

## 3. Automated DR Drill Harness (`scripts/dr_drill.py`)

Disaster recovery capabilities are exercised continuously using `scripts/dr_drill.py`.

### 3.1 Drill Workflow
1. **Disaster Simulation:**
   - An isolated temporary sandbox is created.
   - The primary data directory is simulated as lost or corrupted.
2. **Restoration Execution:**
   - The harness extracts the certified backup bundle into the sandbox.
   - Restores database files and canonical registries.
3. **Cryptographic & Database Integrity Audit:**
   - Every file's SHA-256 hash is computed and compared against `MANIFEST.sha256`.
   - SQLite `PRAGMA integrity_check;` is executed on all restored databases (must return `"ok"`).
   - Table schema and record counts are compared against pre-disaster baselines.
4. **SLA Measurement:**
   - Total restore duration is timed with millisecond precision and checked against the 900s RTO ceiling.

### 3.2 Running the DR Drill
```bash
# Execute full drill and output JSON report:
python scripts/dr_drill.py --output-report release/evidence/ws11/E-WS11-001_dr_drill.json

# Run drill against a specific historical backup archive:
python scripts/dr_drill.py --backup-dir _backups/msn-20261117T164517Z
```
