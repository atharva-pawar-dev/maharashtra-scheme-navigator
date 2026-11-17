from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.core.config import settings
from scheme_navigator.core.migrations import (
    backup_database,
    check_database_integrity,
    restore_database,
    run_all_migrations,
)
from scheme_navigator.security.auth import session_manager
from scheme_navigator.security.models import UserRole


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_headers(monkeypatch):
    bootstrap_secret = "test-bootstrap-key-with-sufficient-entropy-12345"
    monkeypatch.setenv("ADMIN_BOOTSTRAP_KEY", bootstrap_secret)
    monkeypatch.setattr(settings, "admin_bootstrap_key", bootstrap_secret)
    session_manager.reset_bootstrap()

    tc = TestClient(app)
    res = tc.post(
        "/admin/auth/provision",
        headers={"X-Admin-Bootstrap-Key": bootstrap_secret},
        json={"role": "catalogue_admin", "user_id": "migration_admin"},
    )
    assert res.status_code == 200, res.text
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def analyst_headers(admin_headers):
    tc = TestClient(app)
    res = tc.post(
        "/admin/auth/provision-user",
        headers=admin_headers,
        json={"role": "analyst", "user_id": "source_analyst"},
    )
    assert res.status_code == 200, res.text
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _create_synthetic_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), text)
    raw = doc.tobytes()
    doc.close()
    return raw


# ==============================================================================
# 1. SQLITE MIGRATION ENGINE & BACKUP / RESTORE
# ==============================================================================


def test_sqlite_migration_runner_and_idempotency(tmp_path: Path):
    """Migration runner creates databases, applies versioned migrations, and is idempotent."""
    reports = run_all_migrations(tmp_path)
    assert len(reports) == 3

    for db_name, applied in reports.items():
        assert len(applied) >= 1
        db_path = tmp_path / f"{db_name}.sqlite3"
        assert db_path.exists()

        # Check integrity
        integrity = check_database_integrity(db_path)
        assert integrity["status"] == "healthy"
        assert integrity["integrity_check"] == ["ok"]

        # Check schema_migrations table
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version, applied_at FROM schema_migrations")
            rows = cursor.fetchall()
            assert len(rows) >= 1

    # Running migrations again applies 0 new migrations (idempotent)
    second_reports = run_all_migrations(tmp_path)
    for db_name, applied in second_reports.items():
        assert len(applied) == 0


def test_sqlite_backup_and_restore(tmp_path: Path):
    """Crash-consistent SQLite backup copies data and can be restored with 100% integrity."""
    db_path = tmp_path / "test_source.sqlite3"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE citizen_notes (id INTEGER PRIMARY KEY, note TEXT)")
        conn.execute("INSERT INTO citizen_notes (note) VALUES ('Initial citizen grant record')")
        conn.commit()

    backup_dir = tmp_path / "backups"
    backup_file = backup_database(db_path, backup_dir)
    assert backup_file.exists()
    assert backup_file.is_file()

    # Modify original
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM citizen_notes")
        conn.commit()

    # Restore from backup
    restored_status = restore_database(backup_file, db_path)
    assert restored_status is True

    # Verify content restored
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT note FROM citizen_notes")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "Initial citizen grant record"

    # Verify integrity
    integrity = check_database_integrity(db_path)
    assert integrity["status"] == "healthy"


# ==============================================================================
# 2. ADMIN DATABASE MANAGEMENT API
# ==============================================================================


def test_admin_db_status_and_migration_api(client, admin_headers):
    """Catalogue admins can query database integrity, trigger migrations, and generate backups."""
    # 1. DB status endpoint
    status_resp = client.get("/admin/db/status", headers=admin_headers)
    assert status_resp.status_code == 200, status_resp.text
    status_data = status_resp.json()
    assert "interviews" in status_data
    assert "document_reviews" in status_data
    assert "ingestion" in status_data
    for db_key in ("interviews", "document_reviews", "ingestion"):
        assert status_data[db_key]["status"] in {"healthy", "missing"}

    # 2. Trigger migration
    migrate_resp = client.post("/admin/db/migrate", headers=admin_headers)
    assert migrate_resp.status_code == 200
    migrate_data = migrate_resp.json()
    assert migrate_data["status"] == "success"
    assert "applied" in migrate_data

    # 3. Trigger backup
    backup_resp = client.post("/admin/db/backup", headers=admin_headers)
    assert backup_resp.status_code == 200
    backup_data = backup_resp.json()
    assert backup_data["status"] == "success"
    assert len(backup_data["backups"]) >= 1

    # 4. Citizen access is forbidden
    citizen_sess = client.post("/auth/session").json()["token"]
    forbidden_resp = client.get(
        "/admin/db/status",
        headers={"Authorization": f"Bearer {citizen_sess}"},
    )
    assert forbidden_resp.status_code == 403


# ==============================================================================
# 3. MANUAL SOURCE UPLOAD & DIFF COMPARISON API
# ==============================================================================


def test_air_gapped_manual_source_upload(client, analyst_headers):
    """Analysts can upload official government sources directly for air-gapped ingestion."""
    pdf_bytes = _create_synthetic_pdf(
        "Government Resolution No. MMLBY-2024-001\n"
        "Mukhyamantri Majhi Ladki Bahin Yojana\n"
        "Monthly financial assistance: Rs. 1500.\n"
        "Eligible age: 21 to 65 years. Annual income ceiling: Rs. 250000."
    )

    upload_resp = client.post(
        "/ingestion/upload-source",
        headers=analyst_headers,
        data={
            "source_url": "https://gr.maharashtra.gov.in/Site/Upload/GR/20240628.pdf",
            "official_reference": "GR-MMLBY-2024-001",
            "publication_date": "2024-06-28",
            "source_kind": "government_resolution",
        },
        files={"file": ("20240628.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_resp.status_code == 200, upload_resp.text
    data = upload_resp.json()
    assert data["snapshot_id"]
    assert data["sha256"]
    assert data["review_status"] == "pending_review"

    # Ingestion creates an item in review queue
    queue_resp = client.get("/ingestion/queue", headers=analyst_headers)
    assert queue_resp.status_code == 200
    items = queue_resp.json()
    assert any(i["source_url"] == "https://gr.maharashtra.gov.in/Site/Upload/GR/20240628.pdf" for i in items)


def test_ingestion_compare_api(client, analyst_headers):
    """Compare endpoint computes unified text diffs between successive source snapshots."""
    # Upload Version 1
    v1_pdf = _create_synthetic_pdf(
        "Government Resolution MMLBY-2024-01\n"
        "Rule 1: Benefit is Rs. 1500 per month for women aged 21-65."
    )
    res1 = client.post(
        "/ingestion/upload-source",
        headers=analyst_headers,
        data={
            "source_url": "https://gr.maharashtra.gov.in/Site/Upload/GR/v1.pdf",
            "official_reference": "GR-V1",
            "source_kind": "government_resolution",
        },
        files={"file": ("v1.pdf", io.BytesIO(v1_pdf), "application/pdf")},
    )
    assert res1.status_code == 200, res1.text
    snap1_id = res1.json()["snapshot_id"]

    # Upload Version 2 (amendment changing benefit)
    v2_pdf = _create_synthetic_pdf(
        "Government Resolution MMLBY-2024-01\n"
        "Rule 1: Benefit is Rs. 2100 per month for women aged 21-65."
    )
    res2 = client.post(
        "/ingestion/upload-source",
        headers=analyst_headers,
        data={
            "source_url": "https://gr.maharashtra.gov.in/Site/Upload/GR/v2.pdf",
            "official_reference": "GR-V2",
            "source_kind": "government_resolution",
        },
        files={"file": ("v2.pdf", io.BytesIO(v2_pdf), "application/pdf")},
    )
    assert res2.status_code == 200, res2.text
    snap2_id = res2.json()["snapshot_id"]

    # Compare snapshots
    diff_resp = client.get(
        f"/ingestion/compare?snapshot_id_a={snap1_id}&snapshot_id_b={snap2_id}",
        headers=analyst_headers,
    )
    assert diff_resp.status_code == 200, diff_resp.text
    diff_data = diff_resp.json()
    assert diff_data["snapshot_a"]["id"] == snap1_id
    assert diff_data["snapshot_b"]["id"] == snap2_id
    assert diff_data["is_content_identical"] is False
    assert diff_data["diff_line_count"] > 0
    assert diff_data["unified_diff"]
    # Check that diff captured the change
    assert "1500" in diff_data["unified_diff"]
    assert "2100" in diff_data["unified_diff"]
