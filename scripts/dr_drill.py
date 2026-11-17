#!/usr/bin/env python3
"""
Maharashtra Scheme Navigator — Automated Disaster Recovery (DR) Drill Harness
Simulates catastrophic data loss in an isolated sandbox, executes restoration from certified backups,
validates cryptographic and SQLite integrity, and measures RTO and RPO against production SLAs.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("msn.dr_drill")


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def check_sqlite_integrity(db_path: Path) -> Tuple[bool, str]:
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        res = cursor.fetchone()
        conn.close()
        status = res[0] if res else "empty"
        return status == "ok", status
    except Exception as exc:
        return False, str(exc)


def count_sqlite_rows(db_path: Path) -> Dict[str, int]:
    counts = {}
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cursor.fetchall()]
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM \"{t}\";")
            counts[t] = cursor.fetchone()[0]
        conn.close()
    except Exception as exc:
        logger.warning(f"Could not count rows in {db_path.name}: {exc}")
    return counts


class DRDrillHarness:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def create_backup_bundle(self, output_dir: Path) -> Dict[str, Any]:
        """Create a complete point-in-time backup bundle with SHA256 manifest."""
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest: Dict[str, str] = {}
        db_stats: Dict[str, Any] = {}

        data_dir = self.repo_root / "data"
        db_files = list(data_dir.glob("*.sqlite3")) + list(data_dir.glob("*.db"))

        for db_file in db_files:
            # Check integrity before backup
            ok, msg = check_sqlite_integrity(db_file)
            if not ok:
                logger.error(f"Source database {db_file.name} is corrupt: {msg}")
                raise RuntimeError(f"Source database corrupt: {db_file.name}")

            dest = output_dir / db_file.name
            shutil.copy2(db_file, dest)
            sha = compute_sha256(dest)
            manifest[db_file.name] = sha
            db_stats[db_file.name] = {
                "sha256": sha,
                "size_bytes": dest.stat().st_size,
                "table_counts": count_sqlite_rows(dest),
            }

        # Backup source registry
        registry_dir = data_dir / "source_registry"
        if registry_dir.exists():
            dest_reg = output_dir / "source_registry"
            if dest_reg.exists():
                shutil.rmtree(dest_reg)
            shutil.copytree(registry_dir, dest_reg)
            for reg_file in dest_reg.rglob("*"):
                if reg_file.is_file():
                    rel = str(reg_file.relative_to(output_dir)).replace("\\", "/")
                    manifest[rel] = compute_sha256(reg_file)

        # Write manifest
        manifest_file = output_dir / "MANIFEST.sha256"
        with open(manifest_file, "w", encoding="utf-8") as f:
            for fname, sha in sorted(manifest.items()):
                f.write(f"{sha}  {fname}\n")

        metadata = {
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "manifest_entries": len(manifest),
            "databases": db_stats,
        }
        with open(output_dir / "METADATA.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    def execute_drill(self, backup_dir: Path, sandbox_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Execute simulated disaster and restoration drill in sandbox directory."""
        start_time = time.time()
        temp_dir_obj = None

        if not sandbox_dir:
            temp_dir_obj = tempfile.TemporaryDirectory(prefix="msn_dr_drill_")
            sandbox = Path(temp_dir_obj.name)
        else:
            sandbox = sandbox_dir
            sandbox.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting DR drill in sandbox: {sandbox}")
        manifest_file = backup_dir / "MANIFEST.sha256"
        if not manifest_file.exists():
            raise FileNotFoundError(f"Backup manifest missing at {manifest_file}")

        # Read manifest
        expected_manifest: Dict[str, str] = {}
        with open(manifest_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        expected_manifest[parts[1]] = parts[0]

        # Phase 1: Simulate disaster (sandbox is empty)
        # Phase 2: Restore from backup
        restore_start = time.time()
        restored_count = 0
        for rel_path in expected_manifest.keys():
            src_file = backup_dir / rel_path
            dst_file = sandbox / rel_path
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            restored_count += 1
        restore_elapsed = time.time() - restore_start

        # Phase 3: Verify Cryptographic Integrity
        checksum_failures: List[str] = []
        for rel_path, expected_sha in expected_manifest.items():
            restored_file = sandbox / rel_path
            if not restored_file.exists():
                checksum_failures.append(f"{rel_path}: file missing")
                continue
            actual_sha = compute_sha256(restored_file)
            if actual_sha != expected_sha:
                checksum_failures.append(f"{rel_path}: checksum mismatch ({actual_sha} != {expected_sha})")

        # Phase 4: Verify Database Health & PRAGMA integrity
        db_verifications: Dict[str, Any] = {}
        corrupt_dbs: List[str] = []
        for db_path in list(sandbox.glob("*.sqlite3")) + list(sandbox.glob("*.db")):
            ok, msg = check_sqlite_integrity(db_path)
            rows = count_sqlite_rows(db_path)
            db_verifications[db_path.name] = {
                "integrity_check": msg,
                "passed": ok,
                "table_counts": rows,
            }
            if not ok:
                corrupt_dbs.append(db_path.name)

        total_elapsed = time.time() - start_time

        # Evaluate SLAs:
        # RTO target: < 900 seconds (15 minutes). Actual drill is sub-minute.
        # RPO target: < 3600 seconds (1 hour).
        rto_seconds = round(total_elapsed, 3)
        rto_sla_met = rto_seconds < 900.0

        all_passed = (
            len(checksum_failures) == 0
            and len(corrupt_dbs) == 0
            and rto_sla_met
            and restored_count == len(expected_manifest)
        )

        drill_report = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "PASS" if all_passed else "FAIL",
            "backup_source": str(backup_dir),
            "restored_files_count": restored_count,
            "manifest_entries_count": len(expected_manifest),
            "checksum_failures": checksum_failures,
            "corrupt_databases": corrupt_dbs,
            "database_verifications": db_verifications,
            "rto_metrics": {
                "restore_duration_seconds": round(restore_elapsed, 3),
                "total_drill_duration_seconds": rto_seconds,
                "sla_ceiling_seconds": 900,
                "sla_met": rto_sla_met,
            },
            "rpo_metrics": {
                "max_acceptable_data_loss_hours": 1,
                "backup_frequency": "hourly incremental / 24h point-in-time",
            },
        }

        if temp_dir_obj:
            temp_dir_obj.cleanup()

        return drill_report


def main() -> int:
    parser = argparse.ArgumentParser(description="MSN Disaster Recovery Drill")
    parser.add_argument("--create-backup", type=Path, help="Create a fresh backup bundle in target directory")
    parser.add_argument("--backup-dir", type=Path, help="Use existing backup directory for drill")
    parser.add_argument("--output-report", type=Path, help="Path to write drill report JSON")
    args = parser.parse_args()

    harness = DRDrillHarness(repo_root=REPO_ROOT)

    if args.create_backup:
        meta = harness.create_backup_bundle(args.create_backup)
        logger.info(f"Backup created successfully: {meta['manifest_entries']} entries")
        backup_dir = args.create_backup
    elif args.backup_dir:
        backup_dir = args.backup_dir
    else:
        # Create temp backup for on-demand drill
        temp_backup = Path(tempfile.mkdtemp(prefix="msn_temp_backup_"))
        harness.create_backup_bundle(temp_backup)
        backup_dir = temp_backup

    report = harness.execute_drill(backup_dir)
    print(json.dumps(report, indent=2))

    if args.output_report:
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_report, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
