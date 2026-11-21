#!/usr/bin/env python3
"""CLI Mission Status Display Script.

Reads reports/final_status.json and renders an executable dashboard in the console.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
STATUS_FILE = BASE_DIR / "reports" / "final_status.json"


def main() -> int:
    if not STATUS_FILE.exists():
        print(f"Error: {STATUS_FILE} does not exist. Run scripts/mission/compute_status.py first.")
        return 1

    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        status = json.load(f)

    print("\n" + "=" * 80)
    print(" MAHARASHTRA SCHEME NAVIGATOR — MISSION STATUS DASHBOARD")
    print(f" Mission: {status.get('mission_id', 'MSN-FINAL-CLOSURE-01')} | Classification: {status.get('closure_classification', 'UNKNOWN')}")
    print(f" Commit: {status.get('commit_sha', 'UNKNOWN')[:12]} | Branch: {status.get('branch', 'UNKNOWN')}")
    print(f" Timestamp: {status.get('generated_at', '')}")
    print("=" * 80)

    reqs = status.get("requirements", {})
    num = reqs.get("numerator_accepted", 0)
    denom = reqs.get("denominator", 0)
    pct = reqs.get("acceptance_percentage", 0)
    bar_len = 30
    filled = int(bar_len * (num / denom)) if denom else 0
    bar = "█" * filled + "░" * (bar_len - filled)

    print(f"\nRequirements Acceptance: [{bar}] {num}/{denom} ({pct}%)")

    print("\nDefect Closure Status:")
    for d_id, d_data in status.get("defects", {}).items():
        print(f"  [{d_data['status']}] {d_id}: {d_data['description']}")

    gov = status.get("governance_integrity", {})
    print("\nGovernance & Database Integrity:")
    print(f"  Production DB: {gov.get('production_db_path', 'unknown')}")
    print(f"  Genuine Completeness Attestations: {gov.get('total_genuine_attestations', gov.get('valid_genuine_attestations', 0))} ({gov.get('valid_genuine_attestations', 0)} valid)")
    print(f"  Demo Fixtures in Production DB: {gov.get('demo_fixture_attestations_in_prod', 0)}")
    print(f"  Real Human Rule Approvals: {gov.get('real_human_rule_approvals', 0)}")
    print(f"  Data Isolation Verified: {gov.get('is_isolated', False)}")

    scorer = status.get("scorer_reconciliation", {})
    print("\nFrozen Scorer Reconciliation:")
    print(f"  SC-G2 Preliminary: {scorer.get('sc_g2_reported_score', 0)} / 100")
    print(f"  Authentic Mechanical Score: {scorer.get('final_mechanical_score', 0)} / 100")
    print(f"  Variance: {scorer.get('score_variance', 0)} pts (D5 candidate denominator expansion)")

    ext = status.get("external_blockers", {})
    print("\nExternal Blockers / Pending Approvals:")
    for k, v in ext.items():
        print(f"  * {k}: {v}")

    print("\n" + "=" * 80 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
