"""Genuine Load & Concurrency Benchmark for Scheme Navigator."""
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app

def run_load_benchmark(total_requests=250, concurrency=10):
    client = TestClient(app)
    endpoints = [
        ("GET", "/schemes", None),
        ("GET", "/source-registry/sources", None),
        ("GET", "/source-registry/coverage", None),
        ("GET", "/canonical-schemes", None),
        ("GET", "/public-services", None),
        ("GET", "/channels", None),
        ("POST", "/eligibility/evaluate?language=en", {
            "age_years": 28,
            "gender": "female",
            "annual_income": 45000,
            "resident_state": "maharashtra",
            "bank_account_aadhaar_linked": True
        })
    ]

    latencies = []
    status_codes = {}
    errors = []

    def make_request(idx):
        method, path, body = endpoints[idx % len(endpoints)]
        start = time.perf_counter()
        try:
            if method == "GET":
                resp = client.get(path)
            else:
                resp = client.post(path, json=body)
            duration_ms = (time.perf_counter() - start) * 1000
            return resp.status_code, duration_ms, None
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return None, duration_ms, str(e)

    print(f"Starting load test: {total_requests} requests across {concurrency} concurrent threads...")
    benchmark_start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request, i) for i in range(total_requests)]
        for f in as_completed(futures):
            code, dur, err = f.result()
            latencies.append(dur)
            if code:
                status_codes[code] = status_codes.get(code, 0) + 1
            if err:
                errors.append(err)

    total_time_s = time.perf_counter() - benchmark_start
    rps = total_requests / total_time_s if total_time_s > 0 else 0

    sorted_lat = sorted(latencies)
    p50 = statistics.median(sorted_lat)
    p90 = sorted_lat[int(len(sorted_lat) * 0.90)]
    p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
    p99 = sorted_lat[int(len(sorted_lat) * 0.99)]
    mean_lat = statistics.mean(sorted_lat)
    min_lat = min(sorted_lat)
    max_lat = max(sorted_lat)

    report = {
        "total_requests": total_requests,
        "concurrency": concurrency,
        "total_time_seconds": round(total_time_s, 3),
        "requests_per_second": round(rps, 2),
        "status_code_distribution": status_codes,
        "unhandled_errors_count": len(errors),
        "latency_ms": {
            "min": round(min_lat, 2),
            "mean": round(mean_lat, 2),
            "p50": round(p50, 2),
            "p90": round(p90, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "max": round(max_lat, 2),
        }
    }

    print("\n=== LOAD & CONCURRENCY BENCHMARK RESULTS ===")
    for k, v in report.items():
        print(f"  {k}: {v}")
    return report

if __name__ == "__main__":
    run_load_benchmark()
