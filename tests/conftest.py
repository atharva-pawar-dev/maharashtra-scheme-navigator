"""Keep API persistence isolated from local runtime data during tests."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest

_TEST_DATA_DIRECTORY = Path(tempfile.mkdtemp(prefix="scheme-navigator-tests-"))
os.environ["APP_ENV"] = "local"
os.environ["SCHEME_CATALOG_PATH"] = ""
os.environ["INTERVIEW_DB_PATH"] = str(_TEST_DATA_DIRECTORY / "interviews.sqlite3")
os.environ["DOCUMENT_REVIEW_DB_PATH"] = str(
    _TEST_DATA_DIRECTORY / "document_reviews.sqlite3"
)
os.environ["SECURITY_AUDIT_LOG_PATH"] = str(
    _TEST_DATA_DIRECTORY / "test_security_audit.log"
)
os.environ["ATTESTATION_DB_PATH"] = str(
    _TEST_DATA_DIRECTORY / "test_ingestion.sqlite3"
)


@pytest.fixture(autouse=True)
def _reset_security_state():
    """Ensure complete isolation of rate limiter windows and one-time bootstrap per test."""
    from scheme_navigator.security.auth import session_manager
    from scheme_navigator.security.rate_limiter import rate_limiter

    rate_limiter.reset()
    session_manager.reset_bootstrap()
    yield


def pytest_sessionfinish(session, exitstatus) -> None:
    """Remove only the temporary directory created for this test run."""
    del session, exitstatus
    shutil.rmtree(_TEST_DATA_DIRECTORY, ignore_errors=True)
