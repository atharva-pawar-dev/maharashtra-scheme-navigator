"""
Tests for WS11: Backup & Disaster Recovery Drill.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.dr_drill import (
    DRDrillHarness,
    check_sqlite_integrity,
    compute_sha256,
)


def test_compute_sha256(tmp_path: Path):
    """Verify SHA-256 calculation matches known standard."""
    import hashlib

    test_file = tmp_path / "sample.txt"
    test_file.write_text("Maharashtra Scheme Navigator DR Test Content", encoding="utf-8")

    expected_sha = hashlib.sha256("Maharashtra Scheme Navigator DR Test Content".encode("utf-8")).hexdigest()
    assert compute_sha256(test_file) == expected_sha


def test_sqlite_integrity_check_healthy_and_corrupt(tmp_path: Path):
    """Verify check_sqlite_integrity passes on valid DB and fails on corrupted DB."""
    import sqlite3

    valid_db = tmp_path / "valid.sqlite3"
    conn = sqlite3.connect(str(valid_db))
    conn.execute("CREATE TABLE test (id INT, val TEXT);")
    conn.execute("INSERT INTO test VALUES (1, 'ok');")
    conn.commit()
    conn.close()

    ok, msg = check_sqlite_integrity(valid_db)
    assert ok is True
    assert msg == "ok"

    corrupt_db = tmp_path / "corrupt.sqlite3"
    corrupt_db.write_bytes(b"NOT_A_VALID_SQLITE_DATABASE_HEADER_DATA_1234567890")

    bad_ok, bad_msg = check_sqlite_integrity(corrupt_db)
    assert bad_ok is False
    assert "file is not a database" in bad_msg or "corrupt" in bad_msg or "error" in bad_msg.lower()


def test_backup_bundle_creation_and_manifest(tmp_path: Path):
    """Verify create_backup_bundle creates valid manifest and metadata."""
    harness = DRDrillHarness(repo_root=REPO_ROOT)
    backup_dir = tmp_path / "backup_out"

    metadata = harness.create_backup_bundle(backup_dir)

    assert (backup_dir / "MANIFEST.sha256").exists()
    assert (backup_dir / "METADATA.json").exists()
    assert metadata["manifest_entries"] > 0
    assert len(metadata["databases"]) >= 4


def test_execute_dr_drill_success(tmp_path: Path):
    """Verify full end-to-end disaster recovery drill execution passes with SLA compliance."""
    harness = DRDrillHarness(repo_root=REPO_ROOT)
    backup_dir = tmp_path / "backup_source"
    harness.create_backup_bundle(backup_dir)

    sandbox = tmp_path / "sandbox"
    report = harness.execute_drill(backup_dir=backup_dir, sandbox_dir=sandbox)

    assert report["status"] == "PASS"
    assert report["checksum_failures"] == []
    assert report["corrupt_databases"] == []
    assert report["rto_metrics"]["sla_met"] is True
    assert report["rto_metrics"]["total_drill_duration_seconds"] < 900.0


def test_execute_dr_drill_detects_tampering(tmp_path: Path):
    """Verify DR drill detects tampered backup files and fails closed."""
    harness = DRDrillHarness(repo_root=REPO_ROOT)
    backup_dir = tmp_path / "backup_tampered"
    harness.create_backup_bundle(backup_dir)

    # Tamper with one database file in the backup
    db_file = next(backup_dir.glob("*.sqlite3"))
    db_file.write_bytes(db_file.read_bytes() + b"\xFF\xFF\xFF\xFF")

    sandbox = tmp_path / "sandbox_tampered"
    report = harness.execute_drill(backup_dir=backup_dir, sandbox_dir=sandbox)

    assert report["status"] == "FAIL"
    assert len(report["checksum_failures"]) > 0
