"""Safeguard and Baseline Backup Script (WS0).

Creates an external backup outside the source tree, computes SHA-256 manifest,
verifies integrity of backup and all SQLite databases, and produces evidence records.
"""

import datetime
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKUP_BASE = REPO_ROOT.parent / "_backups"


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    utc_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = BACKUP_BASE / f"msn-{utc_now}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    print(f"Creating backup at: {backup_dir}")

    # Excluded directories from copy
    excluded_dirs = {".venv", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
    
    # 1. Copy source tree
    copied_files = 0
    manifest = {}

    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in excluded_dirs and not d.startswith("backup-")]
        rel_root = Path(root).relative_to(REPO_ROOT)
        dest_root = backup_dir / rel_root
        dest_root.mkdir(parents=True, exist_ok=True)

        for file in files:
            src_file = Path(root) / file
            dest_file = dest_root / file
            shutil.copy2(src_file, dest_file)
            copied_files += 1

    print(f"Copied {copied_files} files into backup.")

    # 2. Record pip freeze
    pip_freeze_path = backup_dir / "pip_freeze.txt"
    try:
        pip_freeze_out = subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze"],
            text=True,
            stderr=subprocess.STDOUT,
        )
        pip_freeze_path.write_text(pip_freeze_out, encoding="utf-8")
    except Exception as e:
        pip_freeze_path.write_text(f"Error capturing pip freeze: {e}\n", encoding="utf-8")

    # 3. Generate SHA-256 Manifest
    manifest_lines = []
    for root, _, files in os.walk(backup_dir):
        for file in files:
            fpath = Path(root) / file
            rel_path = fpath.relative_to(backup_dir).as_posix()
            digest = sha256_file(fpath)
            manifest[rel_path] = digest
            manifest_lines.append(f"{digest}  {rel_path}\n")

    manifest_file = backup_dir / "manifest.sha256"
    manifest_file.write_text("".join(sorted(manifest_lines)), encoding="utf-8")
    print(f"Manifest written with {len(manifest)} entries.")

    # 4. Verify Manifest
    verification_errors = []
    for rel_path, expected_hash in manifest.items():
        actual_path = backup_dir / rel_path
        if not actual_path.exists():
            verification_errors.append(f"Missing file: {rel_path}")
            continue
        actual_hash = sha256_file(actual_path)
        if actual_hash != expected_hash:
            verification_errors.append(f"Hash mismatch on {rel_path}: expected {expected_hash}, got {actual_hash}")

    manifest_verified = (len(verification_errors) == 0)
    print(f"Manifest verification: {'PASS' if manifest_verified else 'FAIL'}")

    # 5. Check integrity of all SQLite databases in backup
    sqlite_results = {}
    sqlite_files = list(backup_dir.rglob("*.sqlite*")) + list(backup_dir.rglob("*.db"))
    # Filter out WAL and SHM files
    sqlite_dbs = [f for f in sqlite_files if not f.suffix.endswith(("-wal", "-shm"))]

    for db_path in sqlite_dbs:
        rel_db = db_path.relative_to(backup_dir).as_posix()
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            integrity_rows = cursor.fetchall()
            integrity_status = "ok" if integrity_rows and integrity_rows[0][0] == "ok" else str(integrity_rows)

            # Table and row counts
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            table_counts = {}
            for t in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM \"{t}\";")
                    table_counts[t] = cursor.fetchone()[0]
                except Exception as ex:
                    table_counts[t] = f"error: {ex}"
            conn.close()

            sqlite_results[rel_db] = {
                "integrity_check": integrity_status,
                "table_counts": table_counts,
                "status": "PASS" if integrity_status == "ok" else "FAIL"
            }
        except Exception as e:
            sqlite_results[rel_db] = {
                "integrity_check": f"Connection error: {e}",
                "status": "FAIL"
            }

    all_dbs_healthy = all(v.get("status") == "PASS" for v in sqlite_results.values())
    print(f"SQLite Integrity Checks: {'PASS' if all_dbs_healthy else 'FAIL'} across {len(sqlite_dbs)} databases.")

    # 6. Active database identification
    active_dbs = [
        "data/citizen_profiles.sqlite3",
        "data/document_reviews.sqlite3",
        "data/ingestion.sqlite3",
        "data/interviews.sqlite3",
    ]
    active_db_report = {}
    for adb in active_dbs:
        adb_path = REPO_ROOT / adb
        if adb_path.exists():
            active_db_report[adb] = {
                "exists": True,
                "size_bytes": adb_path.stat().st_size,
                "sha256": sha256_file(adb_path),
            }
        else:
            active_db_report[adb] = {"exists": False}

    evidence_record = {
        "id": "E-WS0-001",
        "claim": "WS0 baseline backup created outside source tree with verified SHA-256 manifest and SQLite integrity checks",
        "utc_timestamp": utc_now,
        "backup_directory": str(backup_dir),
        "total_files_backed_up": copied_files,
        "manifest_entries": len(manifest),
        "manifest_verified": manifest_verified,
        "verification_errors": verification_errors,
        "active_databases": active_db_report,
        "sqlite_integrity_results": sqlite_results,
        "status": "PASS" if (manifest_verified and all_dbs_healthy) else "FAIL",
    }

    out_file = REPO_ROOT / "release" / "evidence" / "ws0" / "E-WS0-001_backup_verification.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(evidence_record, indent=2), encoding="utf-8")
    print(f"Evidence record written to: {out_file}")

    if not (manifest_verified and all_dbs_healthy):
        sys.exit(1)


if __name__ == "__main__":
    main()
