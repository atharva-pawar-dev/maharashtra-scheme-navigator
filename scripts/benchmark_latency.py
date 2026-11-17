#!/usr/bin/env python3
"""
Maharashtra Scheme Navigator — Latency & Throughput Benchmark Harness
Evaluates deterministic rule evaluation latency across synthetic citizen personas and canonical schemes.
Computes percentile distributions (p50, p90, p95, p99) against production SLAs (p95 < 500ms).
"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from scheme_navigator.domain.models import CitizenProfile, Language
from scheme_navigator.services.catalog import CanonicalCatalogService
from scheme_navigator.services.rule_engine import evaluate_scheme

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("msn.benchmark")


def load_personas() -> List[Dict[str, Any]]:
    personas_path = REPO_ROOT / "data" / "fixtures" / "synthetic_personas.json"
    if not personas_path.exists():
        raise FileNotFoundError(f"Synthetic personas fixture missing at {personas_path}")
    with open(personas_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("personas", [])


def run_benchmark(iterations: int = 10) -> Dict[str, Any]:
    catalog_service = CanonicalCatalogService()
    schemes = catalog_service.all()
    personas_data = load_personas()

    if not schemes:
        raise RuntimeError("No schemes loaded in catalog")
    if not personas_data:
        raise RuntimeError("No personas loaded")

    logger.info(f"Running benchmark with {len(schemes)} schemes across {len(personas_data)} personas ({iterations} iterations)...")

    latencies_ms: List[float] = []

    # Warm-up run
    for p in personas_data[:2]:
        profile = CitizenProfile.model_validate(p["profile"])
        for s in schemes[:2]:
            evaluate_scheme(s, profile)

    # Timed runs
    count = 0
    start_total = time.time()
    for _ in range(iterations):
        for p in personas_data:
            profile = CitizenProfile.model_validate(p["profile"])
            for s in schemes:
                t0 = time.perf_counter()
                res = evaluate_scheme(s, profile)
                t1 = time.perf_counter()
                elapsed_ms = (t1 - t0) * 1000.0
                latencies_ms.append(elapsed_ms)
                count += 1

    total_time = time.time() - start_total
    latencies_ms.sort()

    def percentile(data: List[float], pct: float) -> float:
        idx = int(len(data) * (pct / 100.0))
        return round(data[min(idx, len(data) - 1)], 3)

    p50 = percentile(latencies_ms, 50)
    p90 = percentile(latencies_ms, 90)
    p95 = percentile(latencies_ms, 95)
    p99 = percentile(latencies_ms, 99)
    p95_sla_met = p95 < 500.0

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_evaluations": count,
        "schemes_evaluated": len(schemes),
        "personas_evaluated": len(personas_data),
        "total_duration_seconds": round(total_time, 3),
        "throughput_evals_per_sec": round(count / total_time, 1) if total_time > 0 else 0,
        "latency_ms": {
            "min": round(min(latencies_ms), 3),
            "max": round(max(latencies_ms), 3),
            "mean": round(statistics.mean(latencies_ms), 3),
            "p50": p50,
            "p90": p90,
            "p95": p95,
            "p99": p99,
        },
        "sla_target_ms": 500.0,
        "sla_met": p95_sla_met,
        "status": "PASS" if p95_sla_met else "FAIL",
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="MSN Latency & Throughput Benchmark")
    parser.add_argument("--iterations", type=int, default=10, help="Number of full cycles (default: 10)")
    parser.add_argument("--output-json", type=Path, help="Path to write report JSON")
    args = parser.parse_args()

    report = run_benchmark(iterations=args.iterations)
    print(json.dumps(report, indent=2))

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
