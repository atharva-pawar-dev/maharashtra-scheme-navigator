from __future__ import annotations

import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Use the restricted MessagePack deserializer for persisted LangGraph checkpoints.
os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: E402

logger = logging.getLogger(__name__)


class InterviewSessionStore:
    """Persist LangGraph checkpoints and enforce a configurable session TTL.

    The checkpointer and session metadata share one SQLite file but use separate
    connections. This is intended for local development and lightweight use,
    not high-concurrency production deployments.
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        retention_hours: int = 24,
    ) -> None:
        configured_path = db_path or os.getenv(
            "INTERVIEW_DB_PATH", "data/interviews.sqlite3"
        )
        self.db_path = Path(configured_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.retention_hours = max(1, int(retention_hours))
        self._lock = threading.RLock()
        self._closed = False

        self._checkpoint_connection = sqlite3.connect(
            str(self.db_path),
            timeout=10.0,
            check_same_thread=False,
        )
        self._checkpoint_connection.execute("PRAGMA busy_timeout = 10000")
        self.checkpointer = SqliteSaver(self._checkpoint_connection)
        # Create LangGraph checkpoint tables before any thread operation.
        self.checkpointer.setup()

        self._metadata_connection = sqlite3.connect(
            str(self.db_path),
            timeout=10.0,
            check_same_thread=False,
        )
        self._metadata_connection.row_factory = sqlite3.Row
        self._metadata_connection.execute("PRAGMA busy_timeout = 10000")
        self._initialize_metadata()
        self.last_purge_count = self.purge_expired()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _initialize_metadata(self) -> None:
        with self._metadata_connection:
            self._metadata_connection.execute(
                """
                CREATE TABLE IF NOT EXISTS interview_sessions (
                    thread_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_activity_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
            self._metadata_connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_interview_sessions_expiry "
                "ON interview_sessions(expires_at)"
            )

    def create_session(self, thread_id: str) -> None:
        """Register a new interview thread with a sliding inactivity expiry."""
        if not thread_id or not thread_id.strip():
            raise ValueError("thread_id must not be empty")

        self.purge_expired()
        now = self._now()
        now_text = now.isoformat()
        expires_text = (now + timedelta(hours=self.retention_hours)).isoformat()

        with self._lock, self._metadata_connection:
            # A reused thread ID must never inherit checkpoints from an older run.
            self.checkpointer.delete_thread(thread_id)
            self._metadata_connection.execute(
                """
                INSERT INTO interview_sessions (
                    thread_id, created_at, last_activity_at, expires_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                    created_at = excluded.created_at,
                    last_activity_at = excluded.last_activity_at,
                    expires_at = excluded.expires_at
                """,
                (thread_id, now_text, now_text, expires_text),
            )

    def is_active(self, thread_id: str) -> bool:
        """Return whether the thread is registered and has not expired."""
        self.purge_expired()
        now_text = self._now().isoformat()
        with self._lock:
            row = self._metadata_connection.execute(
                "SELECT 1 FROM interview_sessions "
                "WHERE thread_id = ? AND expires_at > ?",
                (thread_id, now_text),
            ).fetchone()
        return row is not None

    def touch_session(self, thread_id: str) -> bool:
        """Extend the inactivity TTL after a successfully processed answer."""
        now = self._now()
        now_text = now.isoformat()
        expires_text = (now + timedelta(hours=self.retention_hours)).isoformat()
        with self._lock, self._metadata_connection:
            cursor = self._metadata_connection.execute(
                """
                UPDATE interview_sessions
                SET last_activity_at = ?, expires_at = ?
                WHERE thread_id = ? AND expires_at > ?
                """,
                (now_text, expires_text, thread_id, now_text),
            )
            return cursor.rowcount == 1

    def delete_session(self, thread_id: str) -> bool:
        """Delete both session metadata and all LangGraph checkpoints."""
        with self._lock:
            self.checkpointer.delete_thread(thread_id)
            with self._metadata_connection:
                cursor = self._metadata_connection.execute(
                    "DELETE FROM interview_sessions WHERE thread_id = ?",
                    (thread_id,),
                )
            return cursor.rowcount == 1

    def purge_expired(self) -> int:
        """Delete expired metadata and the matching LangGraph checkpoints."""
        now_text = self._now().isoformat()
        with self._lock:
            rows = self._metadata_connection.execute(
                "SELECT thread_id FROM interview_sessions WHERE expires_at <= ?",
                (now_text,),
            ).fetchall()

            deleted_ids: list[str] = []
            for row in rows:
                thread_id = str(row["thread_id"])
                try:
                    self.checkpointer.delete_thread(thread_id)
                except sqlite3.Error:
                    logger.exception(
                        "Unable to purge expired interview checkpoint thread_id=%s",
                        thread_id,
                    )
                    continue
                deleted_ids.append(thread_id)

            if not deleted_ids:
                return 0

            placeholders = ",".join("?" for _ in deleted_ids)
            with self._metadata_connection:
                cursor = self._metadata_connection.execute(
                    f"DELETE FROM interview_sessions WHERE thread_id IN ({placeholders})",
                    deleted_ids,
                )
            return int(cursor.rowcount)

    @property
    def is_closed(self) -> bool:
        """Report whether the SQLite connections have been closed."""
        with self._lock:
            return self._closed

    def close(self) -> None:
        """Close SQLite connections during application shutdown."""
        with self._lock:
            if self._closed:
                return
            self._metadata_connection.close()
            self._checkpoint_connection.close()
            self._closed = True
