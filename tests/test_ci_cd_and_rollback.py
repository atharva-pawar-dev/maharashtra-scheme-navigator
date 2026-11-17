"""
Tests for WS10: CI/CD Pipeline & Rollback Strategy.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.rollback import RollbackManager


def test_ci_workflow_specification():
    """Verify GitHub Actions workflow file exists and defines all required stages."""
    import yaml

    ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), "ci.yml workflow must exist"

    with open(ci_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "jobs" in data
    jobs = data["jobs"]

    # Verify 3 required stages
    assert "security-and-lint" in jobs
    assert "test-suite" in jobs
    assert "container-verification" in jobs

    # Verify critical check references
    raw_content = ci_path.read_text(encoding="utf-8")
    assert "security_audit_scanner.py" in raw_content
    assert "release/evidence/baseline/test_inventory.json" in raw_content
    assert "verify_deployment.py" in raw_content


def test_rollback_code_dry_run():
    """Verify rollback code dry run behaves deterministically."""
    mgr = RollbackManager(repo_root=REPO_ROOT, dry_run=True)

    # Valid commit (HEAD)
    res_valid = mgr.rollback_code("HEAD")
    assert res_valid is True
    assert mgr.log_entries[-1]["status"] == "SIMULATED"

    # Invalid commit
    res_invalid = mgr.rollback_code("non_existent_commit_hash_12345")
    assert res_invalid is False
    assert mgr.log_entries[-1]["status"] == "FAILED"


def test_rollback_catalogue_dry_run():
    """Verify rollback catalogue dry run with commit checkout."""
    mgr = RollbackManager(repo_root=REPO_ROOT, dry_run=True)
    res = mgr.rollback_catalogue(commit="HEAD")
    assert res is True
    assert len(mgr.log_entries) > 0


def test_rollback_database_dry_run_and_execution(tmp_path: Path):
    """Verify database rollback dry-run and actual file restoration with pre-rollback backup."""
    fake_db = tmp_path / "test_profiles.sqlite3"
    fake_db.write_text("initial database content", encoding="utf-8")

    fake_backup = tmp_path / "backup_profiles.sqlite3"
    fake_backup.write_text("restored backup content", encoding="utf-8")

    # Dry run
    mgr_dry = RollbackManager(repo_root=tmp_path, dry_run=True)
    res_dry = mgr_dry.rollback_database(fake_backup)
    assert res_dry is True
    assert fake_db.read_text(encoding="utf-8") == "initial database content"

    # Actual rollback
    # Point repo_root so dest is tmp_path / data / backup_profiles.sqlite3
    dest_dir = tmp_path / "data"
    dest_dir.mkdir(parents=True, exist_ok=True)
    target_active_db = dest_dir / "backup_profiles.sqlite3"
    target_active_db.write_text("active content before rollback", encoding="utf-8")

    mgr_real = RollbackManager(repo_root=tmp_path, dry_run=False)
    res_real = mgr_real.rollback_database(fake_backup)
    assert res_real is True
    assert target_active_db.read_text(encoding="utf-8") == "restored backup content"

    # Verify pre-rollback snapshot was preserved
    pre_backups = list(dest_dir.glob("*.pre_rollback_*"))
    assert len(pre_backups) == 1
    assert pre_backups[0].read_text(encoding="utf-8") == "active content before rollback"


def test_post_rollback_health_verification():
    """Verify RollbackManager health verification executes in-process checks successfully."""
    mgr = RollbackManager(repo_root=REPO_ROOT, dry_run=True)
    passed = mgr.verify_system_health()
    assert passed is True
    assert mgr.log_entries[-1]["action"] == "post_rollback_health_check"
    assert mgr.log_entries[-1]["status"] == "PASSED"
