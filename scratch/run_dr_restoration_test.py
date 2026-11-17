"""Measured disaster recovery backup and restoration benchmark."""
import time
import sqlite3
from pathlib import Path
from scheme_navigator.core.migrations import (
    run_all_migrations,
    backup_database,
    restore_database,
    check_database_integrity,
)

def main():
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    test_db = data_dir / "interviews.sqlite3"

    print("Step 1: Ensuring migrations are applied...")
    run_all_migrations(data_dir)

    print("Step 2: Inserting sentinel record...")
    with sqlite3.connect(str(test_db)) as conn:
        conn.execute("INSERT OR REPLACE INTO interview_sessions (thread_id, created_at, last_activity_at, expires_at) VALUES ('dr-test-thread-001', '2026-11-13T00:00:00Z', '2026-11-13T00:00:00Z', '2026-11-14T00:00:00Z')")
        conn.commit()

    integrity_pre = check_database_integrity(test_db)
    print(f"Pre-backup integrity check: {integrity_pre['status']}")

    print("Step 3: Creating backup via sqlite3 backup API...")
    t0 = time.perf_counter()
    backup_path = backup_database(test_db, data_dir / "test_backups")
    backup_time_ms = (time.perf_counter() - t0) * 1000.0
    print(f"Backup created at: {backup_path.name} in {backup_time_ms:.2f} ms")

    print("Step 4: Simulating disaster (dropping table or mutating data)...")
    with sqlite3.connect(str(test_db)) as conn:
        conn.execute("DELETE FROM interview_sessions WHERE thread_id = 'dr-test-thread-001'")
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM interview_sessions WHERE thread_id = 'dr-test-thread-001'").fetchone()[0]
        assert count == 0, "Data was not cleared!"
    print("Disaster simulated: Sentinel record cleared.")

    print("Step 5: Performing measured disaster recovery restore...")
    t_start = time.perf_counter()
    restored = restore_database(backup_path, test_db)
    restore_time_ms = (time.perf_counter() - t_start) * 1000.0

    print("Step 6: Verifying restored database integrity and record presence...")
    integrity_post = check_database_integrity(test_db)
    with sqlite3.connect(str(test_db)) as conn:
        count_restored = conn.execute("SELECT COUNT(*) FROM interview_sessions WHERE thread_id = 'dr-test-thread-001'").fetchone()[0]

    print("\n=== DISASTER RECOVERY RESTORATION RESULTS ===")
    print(f"  target_database: {test_db.name}")
    print(f"  backup_duration_ms: {backup_time_ms:.2f}")
    print(f"  restoration_duration_ms: {restore_time_ms:.2f}")
    print(f"  integrity_check: {integrity_post['integrity_check']}")
    print(f"  integrity_status: {integrity_post['status']}")
    print(f"  sentinel_record_recovered: {count_restored == 1}")
    print(f"  dr_verification_successful: {restored and count_restored == 1 and integrity_post['status'] == 'healthy'}")

    # Clean up test backup
    try:
        backup_path.unlink(missing_ok=True)
        backup_path.parent.rmdir()
    except Exception:
        pass

if __name__ == "__main__":
    main()
