from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class DocumentReviewStore:
    """Small SQLite store for local human-review cases.

    Only extracted values and audit metadata are stored. Original uploaded image/PDF
    bytes are never written to this database. The store is intended for local
    prototyping; reviewer identity is supplied by the caller and is not authenticated.
    """

    def __init__(self, db_path: str | Path | None = None, retention_hours: int = 24):
        configured_path = db_path or os.getenv(
            "DOCUMENT_REVIEW_DB_PATH", "data/document_reviews.sqlite3"
        )
        self.db_path = Path(configured_path).expanduser().resolve()
        self.retention_hours = max(1, int(retention_hours))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
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
                )
                """
            )
            connection.execute(
                """
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
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_document_reviews_expiry "
                "ON document_reviews(expires_at)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_review_events_review "
                "ON document_review_events(review_id, event_id)"
            )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    def purge_expired(self) -> int:
        now = self._now().isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM document_reviews WHERE expires_at <= ?", (now,)
            )
            return int(cursor.rowcount)

    def create_review(
        self,
        *,
        is_pdf: bool,
        source_file_sha256: str,
        target_financial_year: str,
        extracted_documents: list[dict[str, Any]],
        page_extractions: list[dict[str, Any]],
        document_groups: list[dict[str, Any]],
        audit: dict[str, Any],
    ) -> dict[str, Any]:
        self.purge_expired()
        now = self._now()
        expires_at = now + timedelta(hours=self.retention_hours)
        review_id = uuid.uuid4().hex

        documents_json = self._json(extracted_documents)
        pages_json = self._json(page_extractions)
        groups_json = self._json(document_groups)
        audit_json = self._json(audit)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO document_reviews (
                    review_id, status, created_at, updated_at, expires_at, is_pdf,
                    source_file_sha256, target_financial_year,
                    original_documents_json, current_documents_json,
                    original_page_extractions_json, current_page_extractions_json,
                    original_document_groups_json, current_document_groups_json,
                    original_audit_json, current_audit_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review_id,
                    "pending_review",
                    now.isoformat(),
                    now.isoformat(),
                    expires_at.isoformat(),
                    int(is_pdf),
                    source_file_sha256,
                    target_financial_year,
                    documents_json,
                    documents_json,
                    pages_json,
                    pages_json,
                    groups_json,
                    groups_json,
                    audit_json,
                    audit_json,
                ),
            )

        return self.get_review(review_id)  # type: ignore[return-value]

    def get_review(self, review_id: str) -> dict[str, Any] | None:
        self.purge_expired()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM document_reviews WHERE review_id = ?", (review_id,)
            ).fetchone()
            if row is None:
                return None
            events = connection.execute(
                """
                SELECT event_id, action, reviewer_id, document_id, field_name,
                       original_value_json, previous_value_json, new_value_json,
                       note, page_numbers_json, created_at
                FROM document_review_events
                WHERE review_id = ? ORDER BY event_id
                """,
                (review_id,),
            ).fetchall()

        decoded = dict(row)
        json_fields = {
            "original_extracted_documents": "original_documents_json",
            "extracted_documents": "current_documents_json",
            "page_extractions": "original_page_extractions_json",
            "current_page_extractions": "current_page_extractions_json",
            "original_document_groups": "original_document_groups_json",
            "document_groups": "current_document_groups_json",
            "original_audit": "original_audit_json",
            "audit": "current_audit_json",
        }
        for public_name, storage_name in json_fields.items():
            decoded[public_name] = json.loads(decoded.pop(storage_name))

        for key in (
            "created_at",
            "updated_at",
            "expires_at",
        ):
            # Keep timestamps as ISO-8601 strings for straightforward API serialization.
            decoded[key] = str(decoded[key])

        decoded["is_pdf"] = bool(decoded["is_pdf"])
        decoded["events"] = [
            {
                "event_id": row["event_id"],
                "action": row["action"],
                "reviewer_id": row["reviewer_id"],
                "document_id": row["document_id"],
                "field_name": row["field_name"],
                "original_value": json.loads(row["original_value_json"])
                if row["original_value_json"] is not None else None,
                "previous_value": json.loads(row["previous_value_json"])
                if row["previous_value_json"] is not None else None,
                "new_value": json.loads(row["new_value_json"])
                if row["new_value_json"] is not None else None,
                "note": row["note"],
                "page_numbers": json.loads(row["page_numbers_json"]),
                "created_at": row["created_at"],
            }
            for row in events
        ]
        return decoded

    def save_correction(
        self,
        review_id: str,
        *,
        extracted_documents: list[dict[str, Any]],
        page_extractions: list[dict[str, Any]],
        document_groups: list[dict[str, Any]],
        audit: dict[str, Any],
        events: list[dict[str, Any]],
    ) -> bool:
        now = self._now().isoformat()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                UPDATE document_reviews
                SET updated_at = ?,
                    current_documents_json = ?,
                    current_page_extractions_json = ?,
                    current_document_groups_json = ?,
                    current_audit_json = ?
                WHERE review_id = ? AND status = 'pending_review' AND expires_at > ?
                """,
                (
                    now,
                    self._json(extracted_documents),
                    self._json(page_extractions),
                    self._json(document_groups),
                    self._json(audit),
                    review_id,
                    now,
                ),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                return False

            for event in events:
                connection.execute(
                    """
                    INSERT INTO document_review_events (
                        review_id, action, reviewer_id, document_id, field_name,
                        original_value_json, previous_value_json, new_value_json,
                        note, page_numbers_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        review_id,
                        event["action"],
                        event["reviewer_id"],
                        event.get("document_id"),
                        event.get("field_name"),
                        self._json(event["original_value"])
                        if "original_value" in event else None,
                        self._json(event["previous_value"])
                        if "previous_value" in event else None,
                        self._json(event["new_value"])
                        if "new_value" in event else None,
                        event["note"],
                        self._json(event.get("page_numbers", [])),
                        now,
                    ),
                )
            connection.commit()
        return True

    def complete_review(
        self,
        review_id: str,
        *,
        reviewer_id: str,
        note: str,
    ) -> bool:
        now = self._now().isoformat()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                UPDATE document_reviews
                SET status = 'review_completed', updated_at = ?
                WHERE review_id = ? AND status = 'pending_review' AND expires_at > ?
                """,
                (now, review_id, now),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                return False
            connection.execute(
                """
                INSERT INTO document_review_events (
                    review_id, action, reviewer_id, note, page_numbers_json, created_at
                ) VALUES (?, 'review_completed', ?, ?, '[]', ?)
                """,
                (review_id, reviewer_id, note, now),
            )
            connection.commit()
        return True

    def delete_review(self, review_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM document_reviews WHERE review_id = ?", (review_id,)
            )
            return cursor.rowcount == 1
