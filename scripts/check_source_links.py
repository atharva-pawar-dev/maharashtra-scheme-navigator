#!/usr/bin/env python3
"""TRIMURTI v3 Official Source & Portal Link Verification Script.

Scans all source URLs, GR links, and application portals across the canonical catalogue.
Enforces Invariant I-09 (Lawful & Polite research) and outputs structured reports.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from scheme_navigator.services.link_checker import LinkStatus, SourceLinkChecker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("check_source_links")

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    v2_path = REPO_ROOT / "data" / "catalogue" / "schemes.json"
    if not v2_path.exists():
        logger.error(f"Catalogue file not found at {v2_path}")
        return 1

    schemes = json.loads(v2_path.read_text(encoding="utf-8"))
    logger.info(f"Loaded {len(schemes)} schemes from catalogue.")

    urls_to_check: dict[str, list[str]] = {}  # url -> list of scheme_ids

    for s in schemes:
        sid = s.get("scheme_id")
        app_url = s.get("application", {}).get("url")
        if app_url:
            urls_to_check.setdefault(app_url, []).append(sid)

        for src in s.get("sources", []):
            s_url = src.get("url")
            if s_url:
                urls_to_check.setdefault(s_url, []).append(sid)

        for lb in s.get("legal_basis", []):
            lb_url = lb.get("url")
            if lb_url:
                urls_to_check.setdefault(lb_url, []).append(sid)

    logger.info(f"Identified {len(urls_to_check)} unique official URLs to verify.")

    checker = SourceLinkChecker(timeout_seconds=3.0, mock_mode=False)
    results = []
    status_summary: dict[str, int] = {}

    for i, (url, scheme_ids) in enumerate(urls_to_check.items(), start=1):
        # Polite checking
        res = checker.check_url(url)
        status_summary[res.status.value] = status_summary.get(res.status.value, 0) + 1
        results.append({
            "url": url,
            "status": res.status.value,
            "http_code": res.http_code,
            "final_url": res.final_url,
            "latency_ms": res.latency_ms,
            "affected_schemes": scheme_ids,
            "error": res.error_message,
        })
        if i % 10 == 0:
            logger.info(f"Checked {i}/{len(urls_to_check)} URLs...")

    # Write output report
    reports_dir = REPO_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_json_path = reports_dir / "source_link_health_report.json"
    report_md_path = reports_dir / "source_link_health_report.md"

    report_payload = {
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
        "total_unique_urls": len(urls_to_check),
        "status_summary": status_summary,
        "results": results,
    }
    report_json_path.write_text(json.dumps(report_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md_content = f"""# Official Source & Application Link Health Report
**Generated:** {report_payload['timestamp_iso']}  
**Total URLs Inspected:** {len(urls_to_check)}  

## Status Summary

| Status Classification | Count | Percentage |
| :--- | :--- | :--- |
"""
    for st, count in sorted(status_summary.items(), key=lambda x: -x[1]):
        pct = round(count / len(urls_to_check) * 100, 1)
        md_content += f"| `{st}` | {count} | {pct}% |\n"

    md_content += "\n## Detailed Link Findings\n\n"
    md_content += "| URL | Status | HTTP Code | Schemes |\n| :--- | :--- | :--- | :--- |\n"
    for r in results[:40]:
        md_content += f"| `{r['url'][:45]}` | `{r['status']}` | {r['http_code'] or '-'} | {', '.join(r['affected_schemes'][:2])} |\n"

    report_md_path.write_text(md_content, encoding="utf-8")
    logger.info(f"Link check complete. Summary: {status_summary}. Reports written to {report_json_path} and {report_md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
