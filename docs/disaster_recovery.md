# Scheme Navigator — Disaster Recovery & Business Continuity Plan

**Document Version:** 1.0.0 (Master DR Runbook)  
**Date:** November 12, 2026  
**Target Territory:** Maharashtra, India  

---

## 1. Disaster Recovery Objectives & SLAs

In the event of a catastrophic host failure, hardware degradation, data corruption, or regional cloud outage, Scheme Navigator guarantees the following operational recovery metrics:

- **Recovery Time Objective (RTO):** $\le 15$ minutes (Time to restore full system availability).
- **Recovery Point Objective (RPO):** $\le 5$ minutes (Maximum tolerable data loss interval).
- **Integrity Guarantee:** 100% cryptographic verification of restored relational stores before reopening traffic.

---

## 2. Backup Architecture & Automation

### 2.1 SQLite Relational Backup (Local & Staging Tiers)
- **Non-Locking Online Snapshots:** Utilizes Python's native `sqlite3.Connection.backup()` API (`src/scheme_navigator/core/migrations.py`) to create crash-consistent snapshots without locking active read or write transactions.
- **Snapshot Storage:** Generated snapshots are stored in `data/backups/` stamped with ISO-8601 timestamps:
  `data/backups/interviews_backup_YYYYMMDD_HHMMSS.sqlite3`
- **Integrity Audit:** Prior to backup completion, the system executes `PRAGMA integrity_check` across all databases, verifying zero corruption.
- **API Trigger:** Authorized administrators can trigger online backups on demand via:
  `POST /admin/db/backup`

### 2.2 PostgreSQL Backup (Enterprise Production Tier)
- **Continuous Archiving:** Write-Ahead Logging (WAL) files are archived continuously to an encrypted secondary bucket (S3 Glacier / OCI Archive).
- **Daily Full Snapshots:** Automated `pg_dump` binary snapshots taken daily at 02:00 IST.
- **Point-in-Time Recovery (PITR):** Enables transactional roll-forward to any second within the past 30 days.

---

## 3. Database Restoration & Recovery Runbook

```bash
# ==========================================
# RECOVERY STEP 1: Stop Application Traffic
# ==========================================
sudo systemctl stop scheme-navigator

# ==========================================
# RECOVERY STEP 2: Restore from Latest Backup
# ==========================================
# For SQLite Staging:
cp data/backups/interviews_backup_20261112_214835.sqlite3 data/interviews.sqlite3
cp data/backups/document_reviews_backup_20261112_214835.sqlite3 data/document_reviews.sqlite3
cp data/backups/ingestion_backup_20261112_214835.sqlite3 data/ingestion.sqlite3

# ==========================================
# RECOVERY STEP 3: Run Integrity Verification
# ==========================================
python -c "
import sqlite3
for db in ['interviews.sqlite3', 'document_reviews.sqlite3', 'ingestion.sqlite3']:
    conn = sqlite3.connect(f'data/{db}')
    res = conn.execute('PRAGMA integrity_check').fetchall()
    assert res == [('ok',)], f'Integrity check failed for {db}'
    print(f'{db}: HEALTHY (PRAGMA integrity_check passed)')
"

# ==========================================
# RECOVERY STEP 4: Apply Schema Migrations
# ==========================================
python -m scheme_navigator.core.migrations

# ==========================================
# RECOVERY STEP 5: Restart Service & Verify Health
# ==========================================
sudo systemctl start scheme-navigator
curl -f http://127.0.0.1:8000/source-registry/coverage || exit 1
echo 'DISASTER RECOVERY COMPLETED SUCCESSFULLY.'
```
