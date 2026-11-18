"""SQLite schema migration, integrity verification, and safe live backup engine."""
from __future__ import annotations

import hashlib
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger("scheme_navigator.migrations")


class Migration:
    def __init__(self, version: int, name: str, apply_sql: str) -> None:
        self.version = version
        self.name = name
        self.apply_sql = apply_sql.strip()

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.apply_sql.encode("utf-8")).hexdigest()[:16]


# Define migrations for each core database
INTERVIEW_MIGRATIONS = [
    Migration(
        version=1,
        name="initial_interview_sessions",
        apply_sql="""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            thread_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            last_activity_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_interview_sessions_expiry 
        ON interview_sessions(expires_at);
        """,
    ),
]

REVIEW_MIGRATIONS = [
    Migration(
        version=1,
        name="initial_document_reviews_and_events",
        apply_sql="""
        CREATE TABLE IF NOT EXISTS document_reviews (
            review_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_pdf INTEGER NOT NULL,
            source_file_sha256 TEXT NOT NULL,
            target_financial_year TEXT NOT NULL,
            original_documents_json TEXT NOT NULL,
            current_documents_json TEXT NOT NULL,
            original_page_extractions_json TEXT NOT NULL,
            current_page_extractions_json TEXT NOT NULL,
            original_document_groups_json TEXT NOT NULL,
            current_document_groups_json TEXT NOT NULL,
            original_audit_json TEXT NOT NULL,
            current_audit_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS document_review_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id TEXT NOT NULL,
            action TEXT NOT NULL,
            reviewer_id TEXT NOT NULL,
            document_id TEXT,
            field_name TEXT,
            original_value_json TEXT,
            previous_value_json TEXT,
            new_value_json TEXT,
            note TEXT NOT NULL,
            page_numbers_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(review_id) REFERENCES document_reviews(review_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_document_reviews_expiry 
        ON document_reviews(expires_at);
        CREATE INDEX IF NOT EXISTS idx_review_events_review 
        ON document_review_events(review_id, event_id);
        """,
    ),
]

INGESTION_MIGRATIONS = [
    Migration(
        version=1,
        name="initial_ingestion_snapshots_and_queue",
        apply_sql="""
        CREATE TABLE IF NOT EXISTS ingested_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            source_url TEXT NOT NULL,
            final_url TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            byte_size INTEGER NOT NULL,
            retrieved_at TEXT NOT NULL,
            publication_date TEXT,
            official_reference TEXT,
            title TEXT NOT NULL,
            extracted_text TEXT NOT NULL,
            file_path TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_snapshots_url ON ingested_snapshots(source_url);
        CREATE INDEX IF NOT EXISTS idx_snapshots_sha256 ON ingested_snapshots(sha256);

        CREATE TABLE IF NOT EXISTS document_change_events (
            change_id TEXT PRIMARY KEY,
            source_url TEXT NOT NULL,
            change_type TEXT NOT NULL,
            previous_sha256 TEXT,
            new_sha256 TEXT NOT NULL,
            detected_at TEXT NOT NULL,
            summary TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_changes_url ON document_change_events(source_url);

        CREATE TABLE IF NOT EXISTS ingestion_review_queue (
            item_id TEXT PRIMARY KEY,
            source_url TEXT NOT NULL,
            source_title TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            review_status TEXT NOT NULL,
            reviewer_id TEXT,
            review_notes TEXT,
            extracted_scheme_data_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_queue_status ON ingestion_review_queue(review_status);
        """,
    ),
    Migration(
        version=2,
        name="catalogue_v2_provenance_and_rules",
        apply_sql="""
        CREATE TABLE IF NOT EXISTS catalogue_v2_schemes (
            scheme_id TEXT PRIMARY KEY,
            name_en TEXT NOT NULL,
            name_mr TEXT NOT NULL,
            department TEXT NOT NULL,
            implementing_body TEXT NOT NULL,
            level TEXT NOT NULL,
            status TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            confidence REAL NOT NULL,
            substantive_criteria_count INTEGER NOT NULL,
            eligibility_incomplete INTEGER NOT NULL,
            scheme_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_catalogue_v2_status ON catalogue_v2_schemes(status);
        CREATE INDEX IF NOT EXISTS idx_catalogue_v2_verification ON catalogue_v2_schemes(verification_status);

        CREATE TABLE IF NOT EXISTS catalogue_v2_criteria_evidence (
            criterion_id TEXT PRIMARY KEY,
            scheme_id TEXT NOT NULL,
            field TEXT NOT NULL,
            operator TEXT NOT NULL,
            quote_original TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_tier TEXT NOT NULL,
            gr_ref TEXT,
            verified_at TEXT NOT NULL,
            FOREIGN KEY(scheme_id) REFERENCES catalogue_v2_schemes(scheme_id)
        );
        CREATE INDEX IF NOT EXISTS idx_criteria_scheme ON catalogue_v2_criteria_evidence(scheme_id);
        """,
    ),
]

CITIZEN_PROFILE_MIGRATIONS = [
    Migration(
        version=1,
        name="initial_citizen_profile_and_progress",
        apply_sql="""
        CREATE TABLE IF NOT EXISTS citizen_profiles (
            session_id TEXT PRIMARY KEY,
            profile_json TEXT NOT NULL,
            provenance_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS interview_runs (
            thread_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            scheme_id TEXT,
            status TEXT NOT NULL,
            state_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_interview_runs_session ON interview_runs(session_id);

        CREATE TABLE IF NOT EXISTS citizen_progress (
            session_id TEXT PRIMARY KEY,
            active_scheme_id TEXT,
            active_scheme_version TEXT,
            paused_schemes_json TEXT NOT NULL DEFAULT '{}',
            dismissed_schemes_json TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT NOT NULL
        );
        """,
    ),
    Migration(
        version=2,
        name="add_interview_run_context_and_results",
        apply_sql="""
        ALTER TABLE interview_runs ADD COLUMN mode TEXT NOT NULL DEFAULT 'DISCOVERY';
        ALTER TABLE interview_runs ADD COLUMN target_scheme_id TEXT;
        ALTER TABLE interview_runs ADD COLUMN catalogue_version TEXT NOT NULL DEFAULT '2026.11';
        ALTER TABLE interview_runs ADD COLUMN rule_version TEXT NOT NULL DEFAULT '1.0.0';
        ALTER TABLE interview_runs ADD COLUMN language TEXT NOT NULL DEFAULT 'en';
        ALTER TABLE interview_runs ADD COLUMN completed_at TEXT;
        ALTER TABLE interview_runs ADD COLUMN results_json TEXT;
        """,
    ),
    Migration(
        version=3,
        name="add_geographic_jurisdiction_and_location",
        apply_sql="""
        ALTER TABLE interview_runs ADD COLUMN target_jurisdiction_id TEXT;
        ALTER TABLE citizen_profiles ADD COLUMN local_government_type TEXT;
        ALTER TABLE citizen_profiles ADD COLUMN municipal_corporation TEXT;
        ALTER TABLE citizen_profiles ADD COLUMN municipal_council TEXT;
        ALTER TABLE citizen_profiles ADD COLUMN nagar_panchayat TEXT;
        ALTER TABLE citizen_profiles ADD COLUMN gram_panchayat TEXT;
        ALTER TABLE citizen_profiles ADD COLUMN ward TEXT;
        ALTER TABLE citizen_profiles ADD COLUMN locality TEXT;
        ALTER TABLE citizen_profiles ADD COLUMN residence_years INTEGER;
        ALTER TABLE citizen_profiles ADD COLUMN pin_code TEXT;
        """,
    ),
]


def ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            checksum TEXT NOT NULL
        )
        """
    )
    conn.commit()


def get_applied_migrations(conn: sqlite3.Connection) -> dict[int, str]:
    ensure_migration_table(conn)
    cursor = conn.execute("SELECT version, checksum FROM schema_migrations ORDER BY version")
    return {row[0]: row[1] for row in cursor.fetchall()}


def apply_migrations(db_path: Path | str, migrations: list[Migration]) -> list[int]:
    path = Path(db_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    applied_now = []
    with sqlite3.connect(str(path), timeout=15.0) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        applied = get_applied_migrations(conn)

        for migration in sorted(migrations, key=lambda m: m.version):
            if migration.version in applied:
                continue

            logger.info("Applying migration v%d (%s) to %s", migration.version, migration.name, path.name)
            # Execute migration SQL script
            conn.executescript(migration.apply_sql)
            now_iso = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO schema_migrations (version, name, applied_at, checksum) VALUES (?, ?, ?, ?)",
                (migration.version, migration.name, now_iso, migration.checksum),
            )
            conn.commit()
            applied_now.append(migration.version)

    return applied_now


def check_database_integrity(db_path: Path | str) -> dict[str, Any]:
    path = Path(db_path).resolve()
    if not path.is_file():
        return {"status": "missing", "path": str(path), "integrity": "file_not_found"}

    with sqlite3.connect(str(path), timeout=10.0) as conn:
        cursor = conn.execute("PRAGMA integrity_check")
        rows = [row[0] for row in cursor.fetchall()]
        is_ok = len(rows) == 1 and rows[0].casefold() == "ok"
        applied = get_applied_migrations(conn)

    return {
        "status": "healthy" if is_ok else "corrupted",
        "path": str(path),
        "integrity_check": rows,
        "schema_version": max(applied.keys()) if applied else 0,
        "applied_migrations": applied,
    }


def backup_database(db_path: Path | str, backup_dir: Path | str | None = None) -> Path:
    """Perform a live, crash-consistent SQLite backup using the SQLite backup API.

    Safely backs up databases in WAL mode without lock contention or file corruption.
    """
    src_path = Path(db_path).resolve()
    if not src_path.is_file():
        raise FileNotFoundError(f"Database file does not exist: {src_path}")

    target_dir = Path(backup_dir).resolve() if backup_dir else src_path.parent / "backups"
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest_path = target_dir / f"{src_path.stem}_{timestamp}.sqlite3"

    with sqlite3.connect(str(src_path), timeout=15.0) as src_conn, \
         sqlite3.connect(str(dest_path), timeout=15.0) as dest_conn:
        src_conn.backup(dest_conn)

    logger.info("Created live SQLite backup of %s at %s", src_path.name, dest_path.name)
    return dest_path


def restore_database(backup_path: Path | str, target_path: Path | str) -> bool:
    """Restore target database from a backup file."""
    src = Path(backup_path).resolve()
    dest = Path(target_path).resolve()
    if not src.is_file():
        raise FileNotFoundError(f"Backup file does not exist: {src}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(src), timeout=15.0) as src_conn, \
         sqlite3.connect(str(dest), timeout=15.0) as dest_conn:
        src_conn.backup(dest_conn)

    logger.info("Restored database from %s to %s", src.name, dest.name)
    return True


def run_all_migrations(data_dir: Path | str | None = None) -> dict[str, list[int]]:
    """Run all schema migrations across the three core application SQLite stores."""
    base_dir = Path(data_dir).resolve() if data_dir else Path(__file__).resolve().parents[3] / "data"

    interviews_db = base_dir / "interviews.sqlite3"
    reviews_db = base_dir / "document_reviews.sqlite3"
    ingestion_db = base_dir / "ingestion.sqlite3"

    results = {
        "interviews": apply_migrations(interviews_db, INTERVIEW_MIGRATIONS),
        "document_reviews": apply_migrations(reviews_db, REVIEW_MIGRATIONS),
        "ingestion": apply_migrations(ingestion_db, INGESTION_MIGRATIONS),
    }
    return results
