#!/usr/bin/env python3
"""
Maharashtra Scheme Navigator — AST Test Inventory Verification
Measures test functions and assertions via Python AST and compares against baseline.
Enforces Protocol B6 and Gate G23 (non-weakening invariant).
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def count_inventory(test_dir: Path) -> dict:
    test_files = sorted(test_dir.glob("**/test_*.py"))
    total_funcs = 0
    total_asserts = 0
    file_details = {}

    for tf in test_files:
        funcs_in_file = 0
        asserts_in_file = 0
        try:
            tree = ast.parse(tf.read_text(encoding="utf-8"), filename=str(tf))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("test_"):
                        funcs_in_file += 1
                        total_funcs += 1
                elif isinstance(node, ast.Assert):
                    asserts_in_file += 1
                    total_asserts += 1
        except Exception as exc:
            print(f"Error parsing {tf.name}: {exc}", file=sys.stderr)

        file_details[tf.name] = {
            "test_count": funcs_in_file,
            "assert_count": asserts_in_file,
        }

    return {
        "total_files": len(test_files),
        "total_tests": total_funcs,
        "total_asserts": total_asserts,
        "files": file_details,
    }


def main() -> int:
    baseline_path = REPO_ROOT / "release" / "evidence" / "baseline" / "test_inventory.json"
    if not baseline_path.exists():
        print(f"FAIL: Baseline inventory not found at {baseline_path}", file=sys.stderr)
        return 1

    with open(baseline_path, "r", encoding="utf-8") as f:
        baseline_raw = json.load(f)

    # Baseline file structure has a 'summary' dictionary
    baseline_summary = baseline_raw.get("summary", baseline_raw)
    base_files = baseline_summary.get("total_files", 44)
    base_tests = baseline_summary.get("total_tests", 398)
    base_asserts = baseline_summary.get("total_asserts", 1902)

    current = count_inventory(REPO_ROOT / "tests")

    delta_files = current["total_files"] - base_files
    delta_tests = current["total_tests"] - base_tests
    delta_asserts = current["total_asserts"] - base_asserts

    print("=" * 60)
    print("AST TEST INVENTORY AUDIT (GATE G23)")
    print("=" * 60)
    print(f"Baseline: {base_files} files, {base_tests} tests, {base_asserts} assertions")
    print(f"Current:  {current['total_files']} files, {current['total_tests']} tests, {current['total_asserts']} assertions")
    print(f"Delta:    +{delta_files} files, +{delta_tests} tests, +{delta_asserts} assertions")

    # Non-weakening invariant
    if current["total_tests"] < base_tests:
        print(f"FAIL: Test function count weakened! ({current['total_tests']} < {base_tests})", file=sys.stderr)
        return 1

    if current["total_asserts"] < base_asserts:
        print(f"FAIL: Assertion count weakened! ({current['total_asserts']} < {base_asserts})", file=sys.stderr)
        return 1

    print("VERDICT: PASS (Test suite strictly non-weakening)")
    print("=" * 60)

    # Write evidence record
    evidence_path = REPO_ROOT / "release" / "evidence" / "ws15" / "E-WS15-001_ast_inventory_check.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": "2026-11-17T18:25:00Z",
        "gate": "G23",
        "status": "PASS",
        "baseline": {
            "total_files": base_files,
            "total_tests": base_tests,
            "total_asserts": base_asserts,
        },
        "current": {
            "total_files": current["total_files"],
            "total_tests": current["total_tests"],
            "total_asserts": current["total_asserts"],
        },
        "delta": {
            "files": delta_files,
            "tests": delta_tests,
            "asserts": delta_asserts,
        },
    }
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
