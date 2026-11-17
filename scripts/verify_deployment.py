#!/usr/bin/env python3
"""
Maharashtra Scheme Navigator — Deployment Verification Script
Verifies liveness, readiness, security headers, anonymous sessions, and catalogue integrity.
Can test a live remote/container URL or in-process using FastAPI TestClient.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure src is on path for in-process mode
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))


def verify_live(base_url: str) -> Dict[str, Any]:
    import urllib.request
    import urllib.error

    results = {
        "mode": "live",
        "target": base_url,
        "checks": {},
        "all_passed": True,
    }

    # 1. Healthz check
    try:
        req = urllib.request.Request(f"{base_url}/healthz")
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))
            headers = dict(resp.headers)
            passed = status == 200 and body.get("status") == "ok"
            results["checks"]["healthz"] = {
                "status_code": status,
                "passed": passed,
                "response": body,
            }
            if not passed:
                results["all_passed"] = False

            # Check security headers
            sec_headers_present = {
                "x-content-type-options": headers.get("x-content-type-options") == "nosniff",
                "x-frame-options": headers.get("x-frame-options") == "DENY",
                "content-security-policy": bool(headers.get("content-security-policy")),
            }
            results["checks"]["security_headers"] = {
                "passed": all(sec_headers_present.values()),
                "details": sec_headers_present,
            }
            if not all(sec_headers_present.values()):
                results["all_passed"] = False
    except Exception as exc:
        results["checks"]["healthz"] = {"passed": False, "error": str(exc)}
        results["checks"]["security_headers"] = {"passed": False, "error": str(exc)}
        results["all_passed"] = False

    # 2. Readyz check
    try:
        req = urllib.request.Request(f"{base_url}/readyz")
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))
            results["checks"]["readyz"] = {
                "status_code": status,
                "passed": status == 200 and body.get("status") == "ready",
                "response": body,
            }
            if status != 200 or body.get("status") != "ready":
                results["all_passed"] = False
    except Exception as exc:
        results["checks"]["readyz"] = {"passed": False, "error": str(exc)}
        results["all_passed"] = False

    # 3. Schemes catalogue check
    try:
        req = urllib.request.Request(f"{base_url}/schemes")
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))
            count = len(body) if isinstance(body, list) else len(body.get("items", []))
            passed = status == 200 and count > 0
            results["checks"]["schemes"] = {
                "status_code": status,
                "count": count,
                "passed": passed,
            }
            if not passed:
                results["all_passed"] = False
    except Exception as exc:
        results["checks"]["schemes"] = {"passed": False, "error": str(exc)}
        results["all_passed"] = False

    return results


def verify_in_process() -> Dict[str, Any]:
    from fastapi.testclient import TestClient
    from scheme_navigator.api.main import app

    client = TestClient(app)
    results = {
        "mode": "in-process",
        "target": "fastapi.testclient.TestClient",
        "checks": {},
        "all_passed": True,
    }

    # 1. Healthz check
    resp = client.get("/healthz")
    passed = resp.status_code == 200 and resp.json().get("status") == "ok"
    results["checks"]["healthz"] = {
        "status_code": resp.status_code,
        "passed": passed,
        "response": resp.json(),
    }
    if not passed:
        results["all_passed"] = False

    # Security headers
    sec_headers_present = {
        "x-content-type-options": resp.headers.get("x-content-type-options") == "nosniff",
        "x-frame-options": resp.headers.get("x-frame-options") == "DENY",
        "content-security-policy": bool(resp.headers.get("content-security-policy")),
    }
    results["checks"]["security_headers"] = {
        "passed": all(sec_headers_present.values()),
        "details": sec_headers_present,
    }
    if not all(sec_headers_present.values()):
        results["all_passed"] = False

    # 2. Readyz check
    resp_ready = client.get("/readyz")
    ready_passed = resp_ready.status_code == 200 and resp_ready.json().get("status") == "ready"
    results["checks"]["readyz"] = {
        "status_code": resp_ready.status_code,
        "passed": ready_passed,
        "response": resp_ready.json(),
    }
    if not ready_passed:
        results["all_passed"] = False

    # 3. Schemes check
    resp_schemes = client.get("/schemes")
    data = resp_schemes.json()
    count = len(data) if isinstance(data, list) else len(data.get("items", []))
    schemes_passed = resp_schemes.status_code == 200 and count > 0
    results["checks"]["schemes"] = {
        "status_code": resp_schemes.status_code,
        "count": count,
        "passed": schemes_passed,
    }
    if not schemes_passed:
        results["all_passed"] = False

    # 4. Anonymous session check
    resp_auth = client.post("/auth/session")
    auth_passed = resp_auth.status_code == 200 and "session_id" in resp_auth.json()
    results["checks"]["anonymous_session"] = {
        "status_code": resp_auth.status_code,
        "passed": auth_passed,
        "has_cookie": any("sn_session" in k for k in resp_auth.cookies.keys()),
    }
    if not auth_passed:
        results["all_passed"] = False

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify MSN Deployment")
    parser.add_argument("--url", help="Live deployment base URL (e.g. http://localhost:8000)")
    parser.add_argument("--in-process", action="store_true", help="Run verification against in-process TestClient")
    args = parser.parse_args()

    if args.url:
        results = verify_live(args.url.rstrip("/"))
    else:
        results = verify_in_process()

    print(json.dumps(results, indent=2))
    return 0 if results["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
