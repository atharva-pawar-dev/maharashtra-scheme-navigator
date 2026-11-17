"""Tests for WS7: Privacy Engineering, Legal Notices, Retention, and Cloud Consent."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.security.retention import purge_expired_data

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def client():
    return TestClient(app)


# -------------------------------------------------------------------------
# 1. Automated Data Retention Purging
# -------------------------------------------------------------------------

def test_automated_retention_purge_execution():
    """Verify purge_expired_data runs cleanly and returns structured purge counts."""
    # Run purge with 0 hours to force immediate purge evaluation
    res = purge_expired_data(retention_hours=0)
    assert isinstance(res, dict)
    assert "purged_sessions" in res
    assert "purged_rate_limits" in res
    assert "purged_files" in res
    assert "purged_interviews" in res
    assert "purged_reviews" in res
    assert "purged_citizen_records" in res


# -------------------------------------------------------------------------
# 2. Cloud AI Consent Architecture
# -------------------------------------------------------------------------

def test_cloud_translation_requires_explicit_consent(client):
    """Verify Bhashini cloud processing rejects unconsented requests with HTTP 400."""
    resp = client.post(
        "/voice/transcribe?provider=bhashini&language=mr&consent_to_cloud_processing=false",
        files={"file": ("sample.wav", b"dummy-audio-bytes-for-consent-check", "audio/wav")},
    )
    assert resp.status_code == 400
    assert "consent" in resp.json()["detail"].lower()


# -------------------------------------------------------------------------
# 3. Multilingual Legal Artifacts Integrity
# -------------------------------------------------------------------------

def test_privacy_notices_multilingual_integrity():
    """Verify privacy notices exist in EN, MR, HI with valid structures and translation flags."""
    legal_dir = REPO_ROOT / "data" / "legal"
    assert legal_dir.exists()

    for lang in ["en", "mr", "hi"]:
        p_file = legal_dir / f"privacy_notice_{lang}.json"
        assert p_file.exists(), f"Missing {p_file}"
        data = json.loads(p_file.read_text(encoding="utf-8"))
        assert "title" in data
        assert "data_fiduciary" in data
        assert "legal_framework" in data
        assert "retention_policy" in data

        # Check translation review flag
        if lang == "en":
            assert data.get("needs_human_translation_review") is False
        else:
            assert data.get("needs_human_translation_review") is True


def test_terms_of_service_multilingual_integrity():
    """Verify terms of service exist in EN, MR, HI with statutory disclaimers."""
    legal_dir = REPO_ROOT / "data" / "legal"
    for lang in ["en", "mr", "hi"]:
        t_file = legal_dir / f"terms_of_service_{lang}.json"
        assert t_file.exists(), f"Missing {t_file}"
        data = json.loads(t_file.read_text(encoding="utf-8"))
        assert "title" in data
        assert "statutory_role" in data
        assert "disclaimer" in data["statutory_role"]

        if lang != "en":
            assert data.get("needs_human_translation_review") is True
