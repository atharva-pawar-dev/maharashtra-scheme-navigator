"""
Tests for WS12: Quality Engineering, Localisation & Performance.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scheme_navigator.domain.evidence import MultilingualText
from scheme_navigator.domain.models import Language
from scripts.benchmark_latency import run_benchmark


def test_static_html_accessibility_wcag_and_gigw():
    """Verify static/index.html complies with WCAG 2.1 AA / GIGW structural standards."""
    index_html = REPO_ROOT / "static" / "index.html"
    assert index_html.exists(), "index.html must exist"
    content = index_html.read_text(encoding="utf-8")

    # Document language and viewport
    assert "<html" in content and "lang=" in content
    assert 'name="viewport"' in content
    assert "<title>" in content

    # Structural landmarks
    assert "<main" in content or 'role="main"' in content
    assert "<header" in content or 'role="banner"' in content
    assert "<footer" in content or 'role="contentinfo"' in content

    # Contrast & typography tokens
    assert "--primary-saffron:" in content
    assert "--font-family:" in content
    assert "Noto Sans Devanagari" in content or "Mukta" in content


def test_multilingual_text_container_and_fallbacks():
    """Verify MultilingualText provides correct language lookup and fallback chains."""
    multi = MultilingualText(
        en="Sanjay Gandhi Niradhar Anudan Scheme",
        mr="संजय गांधी निराधार अनुदान योजना",
        hi="संजय गांधी निराधार अनुदान योजना",
    )

    assert multi.for_language(Language.MR) == "संजय गांधी निराधार अनुदान योजना"
    assert multi.for_language("mr") == "संजय गांधी निराधार अनुदान योजना"
    assert multi.for_language("hi") == "संजय गांधी निराधार अनुदान योजना"
    assert multi.for_language("en") == "Sanjay Gandhi Niradhar Anudan Scheme"

    # Fallback test: Marathi missing, returns English
    fallback_multi = MultilingualText(
        en="English Only Text",
        mr="",
        hi="",
    )
    assert fallback_multi.for_language("mr") == "English Only Text"
    assert fallback_multi.for_language("hi") == "English Only Text"


def test_legal_notices_trilingual_coverage():
    """Verify privacy notices and terms of service exist in English, Marathi, and Hindi."""
    legal_dir = REPO_ROOT / "data" / "legal"
    assert legal_dir.exists(), "data/legal must exist"

    expected_files = [
        "privacy_notice_en.json",
        "privacy_notice_mr.json",
        "privacy_notice_hi.json",
        "terms_of_service_en.json",
        "terms_of_service_mr.json",
        "terms_of_service_hi.json",
    ]
    for ef in expected_files:
        p = legal_dir / ef
        assert p.exists(), f"Legal document {ef} missing"
        assert p.stat().st_size > 100, f"Legal document {ef} empty"


def test_deterministic_rule_engine_latency_sla():
    """Verify deterministic rule engine executes sub-500ms p95 latency SLA."""
    report = run_benchmark(iterations=2)
    assert report["status"] == "PASS"
    assert report["sla_met"] is True
    assert report["latency_ms"]["p95"] < 500.0, f"p95 exceeded 500ms: {report['latency_ms']['p95']}"
    assert report["throughput_evals_per_sec"] > 500.0
