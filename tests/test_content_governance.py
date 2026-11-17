"""Tests for WS3: Content Governance, Scheme Truth, SSRF Protection, and Invariant B3."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.core.config import Settings
from scheme_navigator.domain.models import Language, Scheme
from scheme_navigator.security.models import AuditEventType
from scheme_navigator.security.ssrf import validate_safe_url
from scheme_navigator.services.catalog import SchemeCatalog, canonical_catalog
from scheme_navigator.source_registry.models import SchemePublicationStatus

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def client():
    return TestClient(app)


# -------------------------------------------------------------------------
# 1. Invariant B3: Agent Ceiling is EXTRACTED, No Simulated Human Review
# -------------------------------------------------------------------------

def test_invariant_b3_agent_ceiling_is_extracted():
    """Verify that automated candidate intake cannot self-promote past EXTRACTED."""
    # When an external or candidate scheme record is read, it must default to unverified/draft
    candidates_path = REPO_ROOT / "data" / "candidates"
    candidate_files = [f for f in candidates_path.glob("*.json") if f.name != "candidate_schemes.json"]
    assert len(candidate_files) > 0

    for cf in candidate_files:
        data = json.loads(cf.read_text(encoding="utf-8"))
        scheme = Scheme.model_validate(data)
        # B3 Invariant: Agent cannot set publication_authorized to True
        assert scheme.publication_authorized is False
        assert scheme.rule_status in ("draft", "under_review", "extracted")
        assert scheme.rule_status != "active"


# -------------------------------------------------------------------------
# 2. Demo Fixture Segregation in Production Profile
# -------------------------------------------------------------------------

def test_demo_fixtures_segregated_in_production():
    """Verify that in production mode, demo fixtures are disabled and omitted."""
    prod_settings = Settings(app_env="production")
    assert prod_settings.demo_fixtures_enabled is False

    # SchemeCatalog loaded with demo_fixtures_enabled=False should be empty if no path
    runtime_catalog = SchemeCatalog.for_runtime(configured_path=None, demo_fixtures_enabled=False)
    assert len(runtime_catalog.all()) == 0

    local_settings = Settings(app_env="local")
    assert local_settings.demo_fixtures_enabled is True


def test_production_rejects_demo_fixtures_startup_guard(monkeypatch):
    """Canary 5 verification: validate_production_startup must raise RuntimeError if demo_fixtures_enabled=True in production."""
    s = Settings(
        app_env="production",
        scheme_navigator_auth_secret="a" * 32,
        scheme_navigator_release_key="b" * 32,
        database_url="postgresql://msn:pw@localhost:5432/db",
    )
    monkeypatch.setattr(Settings, "demo_fixtures_enabled", property(lambda self: True))
    with pytest.raises(RuntimeError, match="Demo fixtures must be disabled in production"):
        s.validate_production_startup()


def test_canonical_catalog_active_demo_fixtures_flagged():
    """Verify that any demo fixtures in canonical registry are explicitly marked DEMO."""
    all_schemes = canonical_catalog.all()
    demo_count = 0
    for s in all_schemes:
        if "demo" in s.scheme_id.lower():
            demo_count += 1
            # Must not be publication authorized
            assert s.publication_authorized is False
    assert demo_count >= 1


# -------------------------------------------------------------------------
# 3. SSRF Protection & Safe Source Fetching
# -------------------------------------------------------------------------

def test_ssrf_rejects_insecure_protocols():
    """Verify HTTP, FTP, file, and javascript protocols are blocked."""
    with pytest.raises(ValueError, match="HTTPS"):
        validate_safe_url("http://maharashtra.gov.in/schemes")

    with pytest.raises(ValueError, match="HTTPS"):
        validate_safe_url("file:///etc/passwd")

    with pytest.raises(ValueError, match="HTTPS"):
        validate_safe_url("ftp://gov.in/data")


def test_ssrf_rejects_loopback_private_and_metadata_ips():
    """Verify localhost, link-local, private IPs, and cloud metadata endpoints are blocked."""
    blocked_urls = [
        "https://127.0.0.1/admin",
        "https://localhost:8000/api",
        "https://169.254.169.254/latest/meta-data/",
        "https://metadata.google.internal/computeMetadata/v1/",
        "https://10.0.0.1/status",
        "https://192.168.1.1/config",
        "https://172.16.0.1/internal",
    ]
    for url in blocked_urls:
        with pytest.raises(ValueError):
            validate_safe_url(url, enforce_allowlist=False)


def test_ssrf_rejects_userinfo():
    """Verify credentials in URL (user:pass@host) are rejected."""
    with pytest.raises(ValueError, match="userinfo"):
        validate_safe_url("https://admin:password@maharashtra.gov.in/schemes")


def test_ssrf_enforces_domain_allowlist():
    """Verify only official Maharashtra/Gov domains are accepted when enforce_allowlist is on."""
    valid_url = "https://maharashtra.gov.in/schemes/view/123"
    assert validate_safe_url(valid_url, enforce_allowlist=True) == valid_url

    invalid_url = "https://evil-phishing-site.com/scheme"
    with pytest.raises(ValueError, match="official government allowlist"):
        validate_safe_url(invalid_url, enforce_allowlist=True)


# -------------------------------------------------------------------------
# 4. Citizen Issue Reporting Endpoint (Feedback Loop)
# -------------------------------------------------------------------------

def test_citizen_report_issue_success(client):
    """Verify citizen can report an inaccuracy on a valid scheme."""
    payload = {
        "scheme_id": "candidate-sanjay-gandhi-niradhar-anudan",
        "issue_type": "outdated_info",
        "description": "The pension amount was recently revised by the latest government resolution.",
        "citizen_contact": "citizen@example.com",
        "language": "en",
    }
    resp = client.post("/trust/report-issue", json=payload)
    assert resp.status_code == 200, f"Failed: {resp.text}"
    data = resp.json()
    assert data["status"] == "RECEIVED"
    assert data["ticket_id"].startswith("TICKET-")
    assert data["scheme_id"] == "candidate-sanjay-gandhi-niradhar-anudan"
    assert "Your issue report has been registered" in data["message"]


def test_citizen_report_issue_multilingual(client):
    """Verify citizen report responds in Marathi and Hindi appropriately."""
    payload_mr = {
        "scheme_id": "candidate-majhi-ladki-bahin",
        "issue_type": "broken_link",
        "description": "अर्ज करण्याची लिंक चालू नाही आहे. कृपया तपासा.",
        "language": "mr",
    }
    resp = client.post("/trust/report-issue", json=payload_mr)
    assert resp.status_code == 200
    assert "तुमचा अभिप्राय यशस्वीरीत्या नोंदवला गेला आहे" in resp.json()["message"]


def test_citizen_report_issue_nonexistent_scheme(client):
    """Verify reporting against a non-existent scheme returns 404."""
    payload = {
        "scheme_id": "invalid-unknown-scheme-999",
        "issue_type": "other",
        "description": "This is a report for a fake scheme ID.",
    }
    resp = client.post("/trust/report-issue", json=payload)
    assert resp.status_code == 404


def test_citizen_report_issue_validation(client):
    """Verify reporting rejects invalid issue type and short descriptions."""
    # Description too short (< 10 chars)
    payload_short = {
        "scheme_id": "candidate-majhi-ladki-bahin",
        "issue_type": "broken_link",
        "description": "bad",
    }
    resp = client.post("/trust/report-issue", json=payload_short)
    assert resp.status_code == 422

    # Invalid issue type
    payload_bad_type = {
        "scheme_id": "candidate-majhi-ladki-bahin",
        "issue_type": "completely_unsupported_type",
        "description": "Valid description length for testing.",
    }
    resp_type = client.post("/trust/report-issue", json=payload_bad_type)
    assert resp_type.status_code == 422
