from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scheme_navigator.ingestion.models import (
    DocumentChangeEvent,
    IngestedSnapshot,
    IngestionReviewItem,
    IngestionReviewStatus,
    IngestionSourceKind,
)


class IngestionStore:
    """Persistent SQLite store for official source snapshots, document change detection, and human-review queues."""

    def __init__(self, db_path: str | Path | None = None):
        configured_path = db_path or os.getenv(
            "INGESTION_DB_PATH", "data/ingestion.sqlite3"
        )
        self.db_path = Path(configured_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=15.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS source_snapshots (
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
                    is_aggregator INTEGER NOT NULL DEFAULT 0,
                    etag TEXT,
                    last_modified TEXT,
                    notes TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_snapshots_url ON source_snapshots(source_url)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_snapshots_sha256 ON source_snapshots(sha256)
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS document_changes (
                    change_id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    previous_sha256 TEXT NOT NULL,
                    new_sha256 TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    previous_snapshot_id TEXT NOT NULL,
                    new_snapshot_id TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    summary TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS review_queue (
                    item_id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    source_title TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    review_status TEXT NOT NULL,
                    extracted_data_json TEXT NOT NULL,
                    reviewer_id TEXT,
                    review_notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_review_status ON review_queue(review_status)
                """
            )

    def save_snapshot(self, snapshot: IngestedSnapshot) -> tuple[IngestedSnapshot, DocumentChangeEvent | None]:
        """Save an ingested snapshot. If the document content at source_url has changed, generate a DocumentChangeEvent."""
        latest = self.get_latest_snapshot_for_url(snapshot.source_url)
        change_event = None

        if latest is not None and latest.sha256 != snapshot.sha256:
            change_id = f"chg_{uuid.uuid4().hex[:12]}"
            now_iso = datetime.now(UTC).isoformat()
            change_event = DocumentChangeEvent(
                change_id=change_id,
                source_url=snapshot.source_url,
                previous_sha256=latest.sha256,
                new_sha256=snapshot.sha256,
                detected_at=now_iso,
                previous_snapshot_id=latest.snapshot_id,
                new_snapshot_id=snapshot.snapshot_id,
                change_type="content_updated",
                summary=f"Official document at {snapshot.source_url} was modified (Hash changed from {latest.sha256[:8]}... to {snapshot.sha256[:8]}...).",
            )
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO document_changes (
                        change_id, source_url, previous_sha256, new_sha256,
                        detected_at, previous_snapshot_id, new_snapshot_id, change_type, summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        change_event.change_id,
                        change_event.source_url,
                        change_event.previous_sha256,
                        change_event.new_sha256,
                        change_event.detected_at,
                        change_event.previous_snapshot_id,
                        change_event.new_snapshot_id,
                        change_event.change_type,
                        change_event.summary,
                    ),
                )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO source_snapshots (
                    snapshot_id, source_url, final_url, source_kind, sha256,
                    byte_size, retrieved_at, publication_date, official_reference,
                    title, extracted_text, is_aggregator, etag, last_modified, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.source_url,
                    snapshot.final_url,
                    snapshot.source_kind.value,
                    snapshot.sha256,
                    snapshot.byte_size,
                    snapshot.retrieved_at,
                    snapshot.publication_date,
                    snapshot.official_reference,
                    snapshot.title,
                    snapshot.extracted_text,
                    1 if snapshot.is_aggregator else 0,
                    snapshot.etag,
                    snapshot.last_modified,
                    snapshot.notes,
                ),
            )

        return snapshot, change_event

    def get_latest_snapshot_for_url(self, source_url: str) -> IngestedSnapshot | None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT * FROM source_snapshots
                WHERE source_url = ?
                ORDER BY retrieved_at DESC
                LIMIT 1
                """,
                (source_url,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_snapshot(row)

    def get_snapshot_by_id(self, snapshot_id: str) -> IngestedSnapshot | None:
        with self._connect() as connection:
            cursor = connection.execute(
                "SELECT * FROM source_snapshots WHERE snapshot_id = ?",
                (snapshot_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_snapshot(row)

    def list_snapshots(self, source_kind: str | None = None) -> list[IngestedSnapshot]:
        with self._connect() as connection:
            if source_kind:
                cursor = connection.execute(
                    "SELECT * FROM source_snapshots WHERE source_kind = ? ORDER BY retrieved_at DESC",
                    (source_kind,),
                )
            else:
                cursor = connection.execute(
                    "SELECT * FROM source_snapshots ORDER BY retrieved_at DESC"
                )
            return [self._row_to_snapshot(r) for r in cursor.fetchall()]

    def list_changes(self, source_url: str | None = None) -> list[DocumentChangeEvent]:
        with self._connect() as connection:
            if source_url:
                cursor = connection.execute(
                    "SELECT * FROM document_changes WHERE source_url = ? ORDER BY detected_at DESC",
                    (source_url,),
                )
            else:
                cursor = connection.execute(
                    "SELECT * FROM document_changes ORDER BY detected_at DESC"
                )
            return [
                DocumentChangeEvent(
                    change_id=r["change_id"],
                    source_url=r["source_url"],
                    previous_sha256=r["previous_sha256"],
                    new_sha256=r["new_sha256"],
                    detected_at=r["detected_at"],
                    previous_snapshot_id=r["previous_snapshot_id"],
                    new_snapshot_id=r["new_snapshot_id"],
                    change_type=r["change_type"],
                    summary=r["summary"],
                )
                for r in cursor.fetchall()
            ]

    def enqueue_for_review(self, item: IngestionReviewItem) -> str:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO review_queue (
                    item_id, source_url, source_title, source_kind, sha256,
                    retrieved_at, review_status, extracted_data_json, reviewer_id,
                    review_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.item_id,
                    item.source_url,
                    item.source_title,
                    item.source_kind.value,
                    item.sha256,
                    item.retrieved_at,
                    item.review_status.value,
                    json.dumps(item.extracted_scheme_data, ensure_ascii=False),
                    item.reviewer_id,
                    item.review_notes,
                    item.created_at,
                    item.updated_at,
                ),
            )
        return item.item_id

    def get_review_item(self, item_id: str) -> IngestionReviewItem | None:
        with self._connect() as connection:
            cursor = connection.execute(
                "SELECT * FROM review_queue WHERE item_id = ?",
                (item_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_review_item(row)

    def list_review_queue(self, status: IngestionReviewStatus | str | None = None) -> list[IngestionReviewItem]:
        status_val = status.value if isinstance(status, IngestionReviewStatus) else status
        with self._connect() as connection:
            if status_val:
                cursor = connection.execute(
                    "SELECT * FROM review_queue WHERE review_status = ? ORDER BY created_at DESC",
                    (status_val,),
                )
            else:
                cursor = connection.execute(
                    "SELECT * FROM review_queue ORDER BY created_at DESC"
                )
            return [self._row_to_review_item(r) for r in cursor.fetchall()]

    def update_review_status(
        self,
        item_id: str,
        status: IngestionReviewStatus | str,
        reviewer_id: str,
        notes: str | None = None,
    ) -> bool:
        status_val = status.value if isinstance(status, IngestionReviewStatus) else status
        now_iso = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE review_queue
                SET review_status = ?, reviewer_id = ?, review_notes = ?, updated_at = ?
                WHERE item_id = ?
                """,
                (status_val, reviewer_id, notes, now_iso, item_id),
            )
            return cursor.rowcount > 0

    def _row_to_snapshot(self, row: sqlite3.Row) -> IngestedSnapshot:
        return IngestedSnapshot(
            snapshot_id=row["snapshot_id"],
            source_url=row["source_url"],
            final_url=row["final_url"],
            source_kind=IngestionSourceKind(row["source_kind"]),
            sha256=row["sha256"],
            byte_size=row["byte_size"],
            retrieved_at=row["retrieved_at"],
            publication_date=row["publication_date"],
            official_reference=row["official_reference"],
            title=row["title"],
            extracted_text=row["extracted_text"],
            is_aggregator=bool(row["is_aggregator"]),
            etag=row["etag"],
            last_modified=row["last_modified"],
            notes=row["notes"],
        )

    def _row_to_review_item(self, row: sqlite3.Row) -> IngestionReviewItem:
        return IngestionReviewItem(
            item_id=row["item_id"],
            source_url=row["source_url"],
            source_title=row["source_title"],
            source_kind=IngestionSourceKind(row["source_kind"]),
            sha256=row["sha256"],
            retrieved_at=row["retrieved_at"],
            review_status=IngestionReviewStatus(row["review_status"]),
            extracted_scheme_data=json.loads(row["extracted_data_json"] or "{}"),
            reviewer_id=row["reviewer_id"],
            review_notes=row["review_notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
