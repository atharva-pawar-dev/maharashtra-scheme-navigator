from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserRole(StrEnum):
    """Hierarchical roles for Scheme Navigator."""

    CITIZEN = "citizen"
    ANALYST = "analyst"
    LEGAL_REVIEWER = "legal_reviewer"
    CATALOGUE_ADMIN = "catalogue_admin"


class AuditEventType(StrEnum):
    """Classifications for security-relevant events."""

    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    PERMISSION_DENIED = "permission_denied"
    SESSION_CREATED = "session_created"
    DOC_UPLOADED = "doc_uploaded"
    DOC_PURGED = "doc_purged"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SCHEME_PUBLISHED = "scheme_published"
    CATALOGUE_SIGNED = "catalogue_signed"
    SECURITY_VIOLATION = "security_violation"
    CITIZEN_REPORT_SUBMITTED = "citizen_report_submitted"


class UserSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    user_id: str
    role: UserRole
    created_at: datetime
    expires_at: datetime
    allowed_threads: list[str] = Field(default_factory=list)
    client_ip: str | None = None


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: AuditEventType
    actor_id: str
    actor_role: str
    action: str
    resource: str
    client_ip: str | None = None
    status_code: int = 200
    details: dict[str, Any] = Field(default_factory=dict)


class CatalogueReleaseSignature(BaseModel):
    """Cryptographic manifest and release authorization for Scheme Navigator catalogue releases.

    CRITICAL NOTE:
    A Scheme Navigator release signature proves ONLY that the Scheme Navigator
    catalogue administrator has signed and frozen this specific version of rules.
    It DOES NOT prove that the Government of Maharashtra has reviewed or endorsed
    this software interpretation.
    """

    model_config = ConfigDict(extra="forbid")

    release_id: str
    catalogue_version: str
    scheme_count: int
    signed_at: str
    signed_by_admin: str
    catalogue_sha256: str
    signature_token: str
    provenance_declaration: str = (
        "This signature is an internal Scheme Navigator software release signature. "
        "It establishes catalog integrity and administrator approval within Scheme Navigator; "
        "it DOES NOT constitute official government endorsement or approval."
    )
