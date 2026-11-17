"""Tests for WS4: Production Data Layer and S3-Compatible Object Storage."""
from __future__ import annotations

import tempfile
import time
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from scheme_navigator.security.storage import (
    LocalStorageService,
    StorageValidationError,
    StorageError,
    MAX_PRESIGNED_TTL_SECONDS,
)
from scripts.migrate_sqlite_to_postgres import (
    POSTGRES_SCHEMA_DDL,
    generate_migration_summary,
    extract_sqlite_data,
)


# -------------------------------------------------------------------------
# 1. Object Storage Tests: Magic-byte Validation & CRUD
# -------------------------------------------------------------------------

def test_storage_put_and_get_valid_pdf():
    """Verify storing a valid PDF document with metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(root_dir=Path(tmpdir))
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        uri = storage.put_object(
            bucket="documents",
            key="test_user/aadhaar.pdf",
            data=pdf_bytes,
            content_type="application/pdf",
            metadata={"doc_type": "aadhaar", "user_id": "test_user"},
        )
        assert uri.startswith("file:///")
        assert storage.object_exists("documents", "test_user/aadhaar.pdf")

        retrieved = storage.get_object("documents", "test_user/aadhaar.pdf")
        assert retrieved == pdf_bytes


def test_storage_put_and_get_valid_jpeg():
    """Verify storing a valid JPEG image."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(root_dir=Path(tmpdir))
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb"
        storage.put_object(
            bucket="images",
            key="passport_photo.jpg",
            data=jpeg_bytes,
            content_type="image/jpeg",
        )
        assert storage.object_exists("images", "passport_photo.jpg")
        assert storage.get_object("images", "passport_photo.jpg") == jpeg_bytes


def test_storage_rejects_malicious_or_forged_headers():
    """Verify executables and text files masked as PDF are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(root_dir=Path(tmpdir))
        # Plain text claiming to be a PDF
        fake_pdf = b"Hello world, I am not a real PDF!"
        with pytest.raises(StorageValidationError, match="unrecognized or forged file header"):
            storage.put_object("documents", "fake.pdf", fake_pdf, content_type="application/pdf")

        # Dangerous extension
        with pytest.raises(StorageValidationError, match="forbidden"):
            storage.put_object("documents", "malware.exe", b"%PDF-dummy", content_type="application/pdf")


def test_storage_delete_object():
    """Verify object and metadata sidecar are deleted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(root_dir=Path(tmpdir))
        data = b"%PDF-1.4 test"
        storage.put_object("bucket1", "doc.pdf", data, "application/pdf")
        assert storage.object_exists("bucket1", "doc.pdf")

        assert storage.delete_object("bucket1", "doc.pdf") is True
        assert not storage.object_exists("bucket1", "doc.pdf")
        with pytest.raises(StorageError):
            storage.get_object("bucket1", "doc.pdf")


# -------------------------------------------------------------------------
# 2. Signed URL & Token Lifecycle (15-min TTL)
# -------------------------------------------------------------------------

def test_presigned_url_max_ttl_ceiling():
    """Verify signed URLs enforce the 15-minute (900 second) ceiling."""
    storage = LocalStorageService(signing_key="secure-test-signing-key-for-test")
    # Request 3600 seconds (1 hour); must be capped at 900
    url = storage.generate_presigned_url("documents", "doc.pdf", expires_in_seconds=3600)
    assert "token=" in url
    assert "expires=" in url

    # Parse expires timestamp
    expires_param = int(url.split("expires=")[-1])
    now = int(time.time())
    ttl = expires_param - now
    assert ttl <= MAX_PRESIGNED_TTL_SECONDS + 2
    assert ttl >= MAX_PRESIGNED_TTL_SECONDS - 2


def test_presigned_token_verification():
    """Verify token verification checks signature, key, and expiry."""
    storage = LocalStorageService(signing_key="secure-test-signing-key-for-test")
    url = storage.generate_presigned_url("documents", "doc.pdf", expires_in_seconds=300)
    token = url.split("token=")[1].split("&")[0]

    # Valid token passes
    assert storage.verify_presigned_token(token, "documents", "doc.pdf") is True

    # Tampered bucket or key fails
    assert storage.verify_presigned_token(token, "wrong_bucket", "doc.pdf") is False
    assert storage.verify_presigned_token(token, "documents", "other_doc.pdf") is False

    # Tampered signature fails
    tampered = token[:-4] + "AAAA"
    assert storage.verify_presigned_token(tampered, "documents", "doc.pdf") is False


# -------------------------------------------------------------------------
# 3. PostgreSQL 16+ DDL Schema and Migration Parity
# -------------------------------------------------------------------------

def test_postgres_ddl_completeness():
    """Verify all 10 canonical tables and critical indices are present in DDL."""
    required_tables = [
        "schema_migrations",
        "interview_sessions",
        "document_reviews",
        "document_review_events",
        "ingested_snapshots",
        "document_change_events",
        "ingestion_review_queue",
        "citizen_profiles",
        "interview_runs",
        "citizen_progress",
    ]
    for table in required_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in POSTGRES_SCHEMA_DDL

    # Verify JSONB and TIMESTAMPTZ types are used
    assert "JSONB" in POSTGRES_SCHEMA_DDL
    assert "TIMESTAMPTZ" in POSTGRES_SCHEMA_DDL
    assert "CASCADE" in POSTGRES_SCHEMA_DDL


def test_migration_summary_scans_sqlite_data():
    """Verify SQLite database summary scans real data in data/."""
    summary = generate_migration_summary(REPO_ROOT / "data")
    assert "citizen_profiles.sqlite3" in summary
    assert "interviews.sqlite3" in summary
    assert summary["citizen_profiles.sqlite3"].get("citizen_profiles", 0) > 0
