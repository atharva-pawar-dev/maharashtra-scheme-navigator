"""
Tests for WS13: Trust Surface & Statutory Notice Alignment.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from fastapi.testclient import TestClient
from scheme_navigator.api.main import app


def test_top_banner_disclaimer_present():
    """Verify top disclaimer banner is rendered with appropriate ARIA semantics."""
    index_html = REPO_ROOT / "static" / "index.html"
    content = index_html.read_text(encoding="utf-8")

    assert 'class="disclaimer-bar"' in content
    assert 'role="note"' in content
    assert 'id="disclaimer-banner-text"' in content


def test_trilingual_statutory_disclaimers_present():
    """Verify statutory notices are defined in English, Marathi, and Hindi."""
    index_html = REPO_ROOT / "static" / "index.html"
    content = index_html.read_text(encoding="utf-8")

    # English notice
    assert "Scheme Navigator provides independent preliminary guidance" in content
    assert "Final eligibility is determined exclusively by the competent departmental authorities" in content

    # Marathi notice
    assert "स्कीम नेव्हिगेटर सार्वजनिक शासन निर्णयांवर आधारित स्वतंत्र प्राथमिक मार्गदर्शन पुरवते" in content
    assert "अंतिम पात्रता केवळ सक्षम सरकारी प्राधिकरणाकडूनच ठरवली जाते" in content

    # Hindi notice
    assert "स्कीम नेविगेटर सार्वजनिक शासन निर्णयों पर आधारित स्वतंत्र प्रारंभिक मार्गदर्शन प्रदान करता है" in content
    assert "अंतिम पात्रता केवल सक्षम सरकारी प्राधिकरण द्वारा तय की जाती है" in content


def test_zero_lorem_ipsum_or_forbidden_mock_tokens():
    """Verify user-facing templates contain no placeholder or mock text."""
    for html_file in [REPO_ROOT / "static" / "index.html", REPO_ROOT / "static" / "reviewer.html"]:
        if html_file.exists():
            text = html_file.read_text(encoding="utf-8").lower()
            assert "lorem ipsum" not in text
            assert "placeholder text" not in text


def test_footer_independent_platform_notice():
    """Verify footer contains clear advisory statement."""
    index_html = REPO_ROOT / "static" / "index.html"
    content = index_html.read_text(encoding="utf-8")

    assert "Independent citizen guidance platform" in content
    assert "Not an official Government of Maharashtra portal" in content


def test_trust_issue_reporting_integration():
    """Verify POST /trust/report-issue generates valid ticket and structured response."""
    client = TestClient(app)
    payload = {
        "scheme_id": "candidate-sanjay-gandhi-niradhar-anudan",
        "issue_type": "incorrect_criteria",
        "description": "Citizen reports income limit for Sanjay Gandhi Niradhar changed in recent GR.",
        "citizen_contact": "citizen@example.org",
        "language": "mr",
    }
    resp = client.post("/trust/report-issue", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("RECEIVED", "received")
    assert data["ticket_id"].startswith("TICKET-")
    assert "अभिप्राय" in data["message"] or "नोंदवला" in data["message"]
