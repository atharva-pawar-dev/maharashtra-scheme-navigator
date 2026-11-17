"""Tests for WS6: Production Security Engineering, Protocol C8 Startup Guard, and Security Headers."""
from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.core.config import Settings

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def client():
    return TestClient(app)


# -------------------------------------------------------------------------
# 1. Protocol C8 Production-Profile Startup Guard
# -------------------------------------------------------------------------

def test_c8_guard_rejects_debug_mode_in_production():
    """Verify production startup refuses if debug mode is enabled."""
    s = Settings(
        app_env="production",
        debug=True,
        scheme_navigator_auth_secret="a" * 32,
        scheme_navigator_release_key="b" * 32,
        database_url="postgresql://user:pass@host:5432/db",
    )
    with pytest.raises(RuntimeError, match="CRITICAL C8 GUARD: Debug mode"):
        s.validate_production_startup()


def test_c8_guard_rejects_reload_mode_in_production():
    """Verify production startup refuses if reload is enabled."""
    s = Settings(
        app_env="production",
        reload=True,
        scheme_navigator_auth_secret="a" * 32,
        scheme_navigator_release_key="b" * 32,
        database_url="postgresql://user:pass@host:5432/db",
    )
    with pytest.raises(RuntimeError, match="CRITICAL C8 GUARD: Auto-reload"):
        s.validate_production_startup()


def test_c8_guard_rejects_weak_or_default_secrets_in_production():
    """Verify production startup refuses default or short secrets."""
    # Short secret
    s_short = Settings(
        app_env="production",
        scheme_navigator_auth_secret="short",
        scheme_navigator_release_key="b" * 32,
        database_url="postgresql://user:pass@host:5432/db",
    )
    with pytest.raises(RuntimeError, match="minimum 32 characters"):
        s_short.validate_production_startup()

    # Forbidden default secret
    s_default = Settings(
        app_env="production",
        scheme_navigator_auth_secret="changeme",
        scheme_navigator_release_key="b" * 32,
        database_url="postgresql://user:pass@host:5432/db",
    )
    with pytest.raises(RuntimeError, match="minimum 32 characters"):
        s_default.validate_production_startup()


def test_c8_guard_rejects_sqlite_in_production():
    """Verify production startup refuses SQLite or missing database URL."""
    s = Settings(
        app_env="production",
        scheme_navigator_auth_secret="a" * 32,
        scheme_navigator_release_key="b" * 32,
        database_url="sqlite:///data/local.db",
    )
    with pytest.raises(RuntimeError, match="mandates PostgreSQL"):
        s.validate_production_startup()


def test_c8_guard_passes_with_hardened_production_config():
    """Verify valid production settings pass validation."""
    s = Settings(
        app_env="production",
        debug=False,
        reload=False,
        scheme_navigator_auth_secret="high_entropy_prod_auth_secret_key_64_bytes_secure_12345",
        scheme_navigator_release_key="high_entropy_prod_release_key_64_bytes_distinct_secure_67890",
        database_url="postgresql://msn_user:strong_password@db.prod.internal:5432/scheme_navigator",
    )
    # Should execute cleanly without error
    s.validate_production_startup()
    assert s.demo_fixtures_enabled is False


# -------------------------------------------------------------------------
# 2. HTTP Security Headers Middleware
# -------------------------------------------------------------------------

def test_security_headers_present_on_responses(client):
    """Verify OWASP-recommended security headers are set on all responses."""
    resp = client.get("/healthz")
    assert resp.status_code == 200

    # 1. Content Type Options
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    # 2. Frame Options (Clickjacking defense)
    assert resp.headers.get("X-Frame-Options") == "DENY"

    # 3. Referrer Policy
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    # 4. Content Security Policy
    csp = resp.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp

    # 5. Permissions Policy
    assert "geolocation=()" in resp.headers.get("Permissions-Policy", "")


# -------------------------------------------------------------------------
# 3. Rate Limiting Enforcement
# -------------------------------------------------------------------------

def test_rate_limiting_protects_sensitive_endpoints(client):
    """Verify burst traffic exceeds rate limit and returns HTTP 429."""
    # /trust/report-issue is rate-limited to 10 requests per 60 seconds
    payload = {
        "scheme_id": "candidate-majhi-ladki-bahin",
        "issue_type": "broken_link",
        "description": "Rate limiting burst test description payload.",
    }
    status_codes = []
    for _ in range(15):
        r = client.post("/trust/report-issue", json=payload)
        status_codes.append(r.status_code)

    assert 429 in status_codes, f"Rate limit not triggered in 15 requests: {status_codes}"
