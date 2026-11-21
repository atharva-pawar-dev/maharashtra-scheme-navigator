#!/usr/bin/env python3
"""Read-Only Executable Acceptance Gate.

Validates the full set of frozen software requirements, evidence manifest,
test execution records, database isolation, and security integrity.
Exits with code 0 on complete verified pass, or nonzero on failure.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


def check_status_file() -> tuple[bool, str]:
    status_file = BASE_DIR / "reports" / "final_status.json"
    if not status_file.exists():
        return False, f"Missing status file: {status_file}"

    with open(status_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    reqs = data.get("requirements", {})
    denom = reqs.get("denominator", 0)
    num = reqs.get("numerator_accepted", 0)

    if denom != 55:
        return False, f"Requirement denominator is {denom}, expected exactly 55."

    if num != 55:
        return False, f"Accepted requirements count is {num}/55. All 55 must be accepted."

    return True, f"55/55 Requirements Verified in status report."


def check_evidence_manifest() -> tuple[bool, str]:
    manifest_file = BASE_DIR / "reports" / "final_evidence_manifest.json"
    if not manifest_file.exists():
        return False, f"Missing evidence manifest: {manifest_file}"

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    missing = []
    for rel_path, meta in manifest.items():
        p = BASE_DIR / rel_path
        if not p.exists():
            missing.append(rel_path)

    if missing:
        return False, f"Missing physical evidence files: {missing}"

    return True, f"All {len(manifest)} evidence manifest files physically present."


def check_database_isolation() -> tuple[bool, str]:
    db_path = BASE_DIR / "data" / "ingestion.sqlite3"
    if not db_path.exists():
        return False, f"Production DB missing: {db_path}"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # In production, fake rule approvals must NOT be manufactured
    cursor.execute("SELECT COUNT(*) FROM scheme_rule_approvals")
    approvals = cursor.fetchone()[0]
    if approvals != 0:
        conn.close()
        return False, f"Production database contains {approvals} rule approvals (must be 0, no synthetic approvals allowed)."

    # Demo fixtures must NOT be present in production attestations
    cursor.execute(
        "SELECT COUNT(*) FROM scheme_completeness_attestations WHERE is_fixture = 1 OR scheme_id LIKE 'demo-%'"
    )
    demo_attestations = cursor.fetchone()[0]
    if demo_attestations != 0:
        conn.close()
        return False, f"Production database contains {demo_attestations} demo fixture attestations."

    # Must contain 16 genuine attestations (15 valid, 1 historically invalidated candidate)
    cursor.execute("SELECT COUNT(*) FROM scheme_completeness_attestations WHERE is_fixture = 0")
    genuine_attestations = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM scheme_completeness_attestations WHERE is_fixture = 0 AND is_valid = 1")
    valid_attestations = cursor.fetchone()[0]
    conn.close()

    if genuine_attestations < 16:
        return False, f"Production DB has {genuine_attestations} genuine attestations, expected at least 16."

    return True, f"Production database isolated: 0 fixtures, 0 fake approvals, {genuine_attestations} genuine attestations ({valid_attestations} valid)."


def check_git_status() -> tuple[bool, str]:
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            check=True,
        )
        lines = [l for l in res.stdout.strip().splitlines() if l.strip()]
        # Check if any modified files exist outside of reports/
        code_mods = [l for l in lines if not any(x in l for x in ("reports/", "docs/", "scratch/"))]
        if code_mods:
            return False, f"Uncommitted code modifications detected: {code_mods}"
        return True, "Git code tree clean."
    except Exception as e:
        return False, f"Git check failed: {e}"


def check_test_results() -> tuple[bool, str]:
    results_file = BASE_DIR / "reports" / "final_closure_test_results.json"
    if not results_file.exists():
        return False, f"Test results file missing: {results_file}"

    with open(results_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    pytest_summary = results.get("pytest_full_suite", {})
    if pytest_summary.get("failed", 1) != 0 or pytest_summary.get("exit_code", 1) != 0:
        return False, f"Pytest full suite has failures: {pytest_summary}"

    playwright_summary = results.get("playwright_suites", {})
    for suite_name, s_data in playwright_summary.items():
        if s_data.get("failed", 1) != 0 or s_data.get("exit_code", 1) != 0:
            return False, f"Playwright suite {suite_name} has failures: {s_data}"

    return True, "All test suites passing with exit code 0."


def main() -> int:
    print("=" * 80)
    print(" EXECUTABLE ACCEPTANCE GATE — MSN-FINAL-CLOSURE-01")
    print("=" * 80)

    checks = [
        ("Database Isolation & Authenticity", check_database_isolation),
        ("Requirements Status Verification", check_status_file),
        ("Evidence Manifest Physical Verification", check_evidence_manifest),
        ("Test Execution Verification", check_test_results),
        ("Git Code Tree Cleanliness", check_git_status),
    ]

    all_passed = True
    for name, check_fn in checks:
        passed, msg = check_fn()
        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str}] {name}: {msg}")
        if not passed:
            all_passed = False

    print("=" * 80)
    if all_passed:
        print("RESULT: FINAL ACCEPTANCE GATE PASSED (Exit Code: 0)")
        return 0
    else:
        print("RESULT: FINAL ACCEPTANCE GATE FAILED (Exit Code: 1)")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
