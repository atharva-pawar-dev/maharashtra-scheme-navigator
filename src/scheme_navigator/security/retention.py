from __future__ import annotations

from __future__ import annotations

import logging
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scheme_navigator.core.config import settings
from scheme_navigator.security.audit_logger import audit_logger
from scheme_navigator.security.auth import session_manager
from scheme_navigator.security.models import AuditEventType
from scheme_navigator.security.rate_limiter import rate_limiter

logger = logging.getLogger("scheme_navigator.retention")


def purge_expired_data(
    retention_hours: int | None = None,
    temp_dir: Path | None = None,
    interview_db_path: Path | None = None,
    review_db_path: Path | None = None,
) -> dict[str, Any]:
    """Enforce data minimization and retention limits by purging expired sessions,
    idle rate-limiter entries, expired temporary uploaded files, and expired
    records in interview and document-review SQLite databases.
    """
    hours = retention_hours if retention_hours is not None else settings.data_retention_hours
    cutoff = time.time() - (hours * 3600)

    # 1. Purge expired sessions and thread ownership
    purged_sessions = session_manager.purge_expired()

    # 2. Purge idle rate limiter buckets
    purged_rate_limits = rate_limiter.purge_idle(idle_seconds=hours * 3600)

    # 3. Purge temp upload artifacts older than cutoff
    # Explicitly protect active SQLite database files, WAL, and SHM indices
    sqlite_protected_extensions = {
        ".sqlite3",
        ".sqlite3-wal",
        ".sqlite3-shm",
        ".wal",
        ".shm",
        ".db",
        ".db-wal",
        ".db-shm",
    }
    purged_files = 0
    target_temp = temp_dir or (Path(__file__).resolve().parents[3] / "data" / "temp_uploads")
    if target_temp.exists() and target_temp.is_dir():
        for f in target_temp.glob("*"):
            if f.is_file():
                if f.suffix.lower() in sqlite_protected_extensions or any(
                    f.name.lower().endswith(ext) for ext in sqlite_protected_extensions
                ):
                    continue
                try:
                    if f.stat().st_mtime < cutoff:
                        f.unlink()
                        purged_files += 1
                except OSError:
                    pass

    # 4. Purge expired interview records from SQLite
    purged_interviews = 0
    try:
        from scheme_navigator.agents.interview_store import InterviewSessionStore
        int_store = InterviewSessionStore(db_path=interview_db_path, retention_hours=hours)
        purged_interviews = getattr(int_store, "last_purge_count", 0) + int_store.purge_expired()
        int_store.close()
    except Exception as exc:
        logger.warning(f"Retention purge error on interview store: {exc}")

    # 5. Purge expired document review records from SQLite
    purged_reviews = 0
    try:
        from scheme_navigator.documents.review_store import DocumentReviewStore
        rev_store = DocumentReviewStore(db_path=review_db_path, retention_hours=hours)
        purged_reviews = rev_store.purge_expired()
    except Exception as exc:
        logger.warning(f"Retention purge error on document review store: {exc}")

    # 6. Purge expired citizen profiles and progress records
    purged_citizen_records = 0
    try:
        from scheme_navigator.core.citizen_store import CitizenProfileStore
        c_store = CitizenProfileStore()
        c_res = c_store.purge_expired_records(retention_hours=hours)
        purged_citizen_records = sum(c_res.values())
    except Exception as exc:
        logger.warning(f"Retention purge error on citizen profile store: {exc}")

    audit_logger.log_event(
        event_type=AuditEventType.DOC_PURGED,
        actor_id="system_retention_job",
        actor_role="system",
        action="retention_purge",
        resource="sessions_and_databases",
        details={
            "retention_hours": hours,
            "purged_sessions": purged_sessions,
            "purged_rate_limits": purged_rate_limits,
            "purged_files": purged_files,
            "purged_interviews": purged_interviews,
            "purged_reviews": purged_reviews,
        },
    )

    return {
        "retention_hours": hours,
        "purged_sessions": purged_sessions,
        "purged_rate_limits": purged_rate_limits,
        "purged_files": purged_files,
        "purged_interviews": purged_interviews,
        "purged_reviews": purged_reviews,
        "purged_at": datetime.now(timezone.utc).isoformat(),
    }
