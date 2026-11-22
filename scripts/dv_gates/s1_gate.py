"""TRIMURTI / MSN-DV-001 Slice 1 Exit Gate Runner.

Executes:
1. Citizen Copy Linter (`scripts/dv_copy_lint.py`)
2. 13 Truth Contract Law Tripwires (`tests/dv/test_law_tripwires.py`)
3. Age-Inclusion Ergonomics Battery (`tests/dv/test_age_inclusion_battery.py`)
4. Models, Slots & Denominator Honesty Unit Suite (`tests/dv/test_models_and_slots.py`)
5. Journey J4 Checklist Logic Browser Suite (`tests/dv/test_j4_checklist_logic.py`)

Emits:
`reports/dv/gates/s1.json`
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYTHON_EXE = sys.executable
GATES_REPORT_DIR = REPO_ROOT / "reports" / "dv" / "gates"
GATES_REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FILE = GATES_REPORT_DIR / "s1.json"


def run_step(step_name: str, cmd: list[str]) -> dict:
    start = time.time()
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    duration = time.time() - start
    return {
        "step": step_name,
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "duration_seconds": round(duration, 2),
        "passed": proc.returncode == 0,
        "stdout": proc.stdout[-1500:] if proc.stdout else "",
        "stderr": proc.stderr[-1500:] if proc.stderr else "",
    }


def main() -> int:
    print("=" * 70)
    print("MSN-DV-001 SLICE 1 (S1) EXIT GATE EXECUTION")
    print("=" * 70)

    steps_results = []

    # 1. Copy Lint
    print("1/5 Running Citizen Copy Linter...")
    res_copy = run_step(
        "citizen_copy_lint",
        [PYTHON_EXE, "scripts/dv_copy_lint.py"]
    )
    steps_results.append(res_copy)
    print(f"    Exit code: {res_copy['exit_code']} (passed: {res_copy['passed']})")

    # 2. Law Tripwires (L1 - L13)
    print("2/5 Running 13 Truth Contract Law Tripwires...")
    res_laws = run_step(
        "law_tripwires_l1_to_l13",
        [PYTHON_EXE, "-m", "pytest", "tests/dv/test_law_tripwires.py", "-v"]
    )
    steps_results.append(res_laws)
    print(f"    Exit code: {res_laws['exit_code']} (passed: {res_laws['passed']})")

    # 3. Models & Slots Unit Tests
    print("3/5 Running Models, Slots & Denominator Honesty Tests...")
    res_models = run_step(
        "models_slots_denominator_tests",
        [PYTHON_EXE, "-m", "pytest", "tests/dv/test_models_and_slots.py", "-v"]
    )
    steps_results.append(res_models)
    print(f"    Exit code: {res_models['exit_code']} (passed: {res_models['passed']})")

    # 4. Age-Inclusion Ergonomics Battery
    print("4/5 Running Age-Inclusion Battery (Playwright)...")
    res_age = run_step(
        "age_inclusion_battery",
        [PYTHON_EXE, "-m", "pytest", "tests/dv/test_age_inclusion_battery.py", "-v"]
    )
    steps_results.append(res_age)
    print(f"    Exit code: {res_age['exit_code']} (passed: {res_age['passed']})")

    # 5. Journey J4 Checklist Logic Browser Tests
    print("5/5 Running Journey J4 Checklist Logic (Playwright)...")
    res_j4 = run_step(
        "journey_j4_checklist_logic",
        [PYTHON_EXE, "-m", "pytest", "tests/dv/test_j4_checklist_logic.py", "-v"]
    )
    steps_results.append(res_j4)
    print(f"    Exit code: {res_j4['exit_code']} (passed: {res_j4['passed']})")

    all_passed = all(s["passed"] for s in steps_results)
    gate_verdict = "PASSED" if all_passed else "FAILED"

    report = {
        "slice": "S1",
        "title": "Requirements, Slots, Evidence Tiers & 'Your Papers' Screen",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gate_verdict": gate_verdict,
        "all_passed": all_passed,
        "steps": steps_results,
        "summary": {
            "copy_lint_passed": res_copy["passed"],
            "law_tripwires_passed": res_laws["passed"],
            "models_slots_passed": res_models["passed"],
            "age_inclusion_passed": res_age["passed"],
            "journey_j4_passed": res_j4["passed"],
        }
    }

    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("-" * 70)
    print(f"S1 Gate Report written to: {REPORT_FILE}")
    print(f"GATE VERDICT: {gate_verdict}")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
