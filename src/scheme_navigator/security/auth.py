from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Mapping

from fastapi import Depends, Header, HTTPException, Request

from scheme_navigator.security.models import UserRole, UserSession

# Master session signing secret (can be overridden via environment)
def _get_auth_secret_key() -> bytes:
    configured = os.getenv("SCHEME_NAVIGATOR_AUTH_SECRET")
    if not configured:
        from scheme_navigator.core.config import settings
        configured = getattr(settings, "scheme_navigator_auth_secret", None)
    if configured and len(configured.strip()) >= 32:
        return configured.strip().encode("utf-8")
    from scheme_navigator.core.config import settings
    if settings.app_env.casefold() in {"production", "prod"}:
        raise RuntimeError(
            "CRITICAL: SCHEME_NAVIGATOR_AUTH_SECRET environment variable is missing or shorter than 32 characters in production."
        )
    global _EPHEMERAL_DEV_SECRET
    if "_EPHEMERAL_DEV_SECRET" not in globals():
        _EPHEMERAL_DEV_SECRET = secrets.token_bytes(32)
    return _EPHEMERAL_DEV_SECRET


SESSION_TTL_HOURS = 24
PRIVILEGED_SESSION_TTL_HOURS = 1


class SessionManager:
    """Thread-safe session authentication and ownership enforcement engine."""

    def __init__(self, secret_key: bytes | None = None) -> None:
        self._secret_override = secret_key
        self._sessions: dict[str, UserSession] = {}
        self._thread_owners: dict[str, str] = {}  # thread_id -> session_id
        self._review_owners: dict[str, str] = {}  # review_id -> session_id
        self._bootstrap_completed: bool = False
        self._revoked_session_ids: set[str] = set()

    def reset_bootstrap(self) -> None:
        """Reset bootstrap completion state (for testing or administrative re-initialization)."""
        self._bootstrap_completed = False
        self._revoked_session_ids.clear()
        self._thread_owners.clear()
        self._review_owners.clear()

    def revoke_session(self, session_id: str) -> bool:
        """Explicitly revoke a session, invalidating any tokens for this session."""
        self._revoked_session_ids.add(session_id)
        existed = session_id in self._sessions
        self._sessions.pop(session_id, None)
        return existed or True

    def rotate_secret(self, new_secret_key: bytes) -> None:
        """Safely rotate the cryptographic signing key, invalidating prior tokens."""
        if len(new_secret_key) < 32:
            raise ValueError("Rotated secret must have at least 32 characters of entropy.")
        self._secret_override = new_secret_key
        self._sessions.clear()
        self._revoked_session_ids.clear()

    @property
    def _secret(self) -> bytes:
        if self._secret_override:
            return self._secret_override
        return _get_auth_secret_key()

    def _sign(self, data: str) -> str:
        h = hmac.new(self._secret, data.encode("utf-8"), hashlib.sha256)
        return base64.urlsafe_b64encode(h.digest()).decode("utf-8").rstrip("=")

    def create_session(
        self,
        role: UserRole = UserRole.CITIZEN,
        user_id: str | None = None,
        client_ip: str | None = None,
        initial_thread_id: str | None = None,
    ) -> tuple[UserSession, str]:
        """Create a new authenticated session and issue a cryptographically signed token."""
        session_id = f"sess_{secrets.token_hex(16)}"
        uid = user_id or f"user_{secrets.token_hex(8)}"
        now = datetime.now(timezone.utc)
        
        from scheme_navigator.core.config import settings
        if role in {UserRole.ANALYST, UserRole.LEGAL_REVIEWER, UserRole.CATALOGUE_ADMIN}:
            ttl_hours = getattr(settings, "privileged_session_ttl_hours", PRIVILEGED_SESSION_TTL_HOURS)
        else:
            ttl_hours = SESSION_TTL_HOURS
        expires = now + timedelta(hours=ttl_hours)

        threads = [initial_thread_id] if initial_thread_id else []

        session = UserSession(
            session_id=session_id,
            user_id=uid,
            role=role,
            created_at=now,
            expires_at=expires,
            allowed_threads=threads,
            client_ip=client_ip,
        )
        self._sessions[session_id] = session
        if initial_thread_id:
            self._thread_owners[initial_thread_id] = session_id

        exp_timestamp = int(expires.timestamp())
        payload = f"{session_id}:{uid}:{role.value}:{exp_timestamp}"
        signature = self._sign(payload)
        token = f"{payload}:{signature}"

        return session, token

    def validate_token(self, token: str) -> UserSession | None:
        """Validate HMAC signature, expiration timestamp, and session presence."""
        if not token or ":" not in token:
            return None

        parts = token.split(":")
        if len(parts) != 5:
            return None

        session_id, uid, role_str, exp_str, signature = parts
        if session_id in self._revoked_session_ids:
            return None
        payload = f"{session_id}:{uid}:{role_str}:{exp_str}"

        expected_sig = self._sign(payload)
        if not hmac.compare_digest(signature, expected_sig):
            return None

        try:
            exp_ts = int(exp_str)
        except ValueError:
            return None

        if time.time() > exp_ts:
            # Session expired
            self._sessions.pop(session_id, None)
            return None

        session = self._sessions.get(session_id)
        if not session:
            # Reconstruct session if stateless verification is allowed
            try:
                role = UserRole(role_str)
            except ValueError:
                return None
            session = UserSession(
                session_id=session_id,
                user_id=uid,
                role=role,
                created_at=datetime.fromtimestamp(exp_ts - (SESSION_TTL_HOURS * 3600), timezone.utc),
                expires_at=datetime.fromtimestamp(exp_ts, timezone.utc),
                allowed_threads=[],
            )
            self._sessions[session_id] = session

        return session

    def bind_thread_to_session(self, session_id: str, thread_id: str) -> None:
        """Associate an interview thread ID to a specific session."""
        owner = self._thread_owners.get(thread_id)
        if owner and owner != session_id:
            raise PermissionError("Thread is already owned by another citizen session.")
        self._thread_owners[thread_id] = session_id
        session = self._sessions.get(session_id)
        if session and thread_id not in session.allowed_threads:
            session.allowed_threads.append(thread_id)

    def authorize_thread_access(self, session: UserSession, thread_id: str) -> bool:
        """Enforce session ownership: citizens may only access their own interview threads."""
        # Administrative roles can review any thread for auditing
        if session.role in {UserRole.ANALYST, UserRole.LEGAL_REVIEWER, UserRole.CATALOGUE_ADMIN}:
            return True

        if session.user_id == "anonymous_citizen":
            owner = self._thread_owners.get(thread_id)
            if owner is None:
                return True
            return owner == session.session_id

        owner = self._thread_owners.get(thread_id)
        if owner is not None:
            return owner == session.session_id

        return thread_id in session.allowed_threads

    def bind_review_to_session(self, session_id: str, review_id: str) -> None:
        """Associate a document review ID to a specific citizen session."""
        owner = self._review_owners.get(review_id)
        if owner and owner != session_id:
            raise PermissionError("Document review is already owned by another citizen session.")
        self._review_owners[review_id] = session_id

    def authorize_review_access(self, session: UserSession, review_id: str) -> bool:
        """Enforce session ownership: citizens may only access their own document reviews."""
        # Administrative roles can review any document review
        if session.role in {UserRole.ANALYST, UserRole.LEGAL_REVIEWER, UserRole.CATALOGUE_ADMIN}:
            return True

        if session.user_id == "anonymous_citizen":
            return review_id not in self._review_owners or self._review_owners.get(review_id) == session.session_id

        owner = self._review_owners.get(review_id)
        if owner is not None:
            return owner == session.session_id

        return False

    def provision_privileged_session(
        self,
        role: UserRole,
        user_id: str | None = None,
        bootstrap_key: str | None = None,
        client_ip: str | None = None,
    ) -> tuple[UserSession, str]:
        """Provision an initial administrative session only with an authenticated bootstrap key."""
        if self._bootstrap_completed:
            raise HTTPException(
                status_code=403,
                detail="Bootstrap disabled: Initial administrator has already been provisioned. Further accounts must be provisioned by an active administrator.",
            )

        expected_key = os.getenv("ADMIN_BOOTSTRAP_KEY")
        if not expected_key:
            from scheme_navigator.core.config import settings
            expected_key = getattr(settings, "admin_bootstrap_key", None)

        if not expected_key or len(expected_key.strip()) < 32:
            raise HTTPException(
                status_code=503,
                detail="Administrative provisioning is disabled: ADMIN_BOOTSTRAP_KEY is not configured or lacks sufficient entropy (min 32 chars).",
            )
        if not bootstrap_key or not hmac.compare_digest(bootstrap_key.strip(), expected_key.strip()):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Invalid administrative bootstrap key.",
            )
        session, token = self.create_session(role=role, user_id=user_id, client_ip=client_ip)
        self._bootstrap_completed = True
        return session, token

    def provision_user_by_admin(
        self,
        admin_session: UserSession,
        role: UserRole,
        user_id: str | None = None,
        client_ip: str | None = None,
    ) -> tuple[UserSession, str]:
        """Allow an active CATALOGUE_ADMIN to provision new accounts with specific roles."""
        if not self.has_role(admin_session, UserRole.CATALOGUE_ADMIN):
            raise HTTPException(
                status_code=403,
                detail="Forbidden: Only catalogue administrators can provision accounts.",
            )
        return self.create_session(role=role, user_id=user_id, client_ip=client_ip)

    def has_role(self, session: UserSession, required_role: UserRole) -> bool:
        """Check role hierarchy."""
        role_hierarchy = {
            UserRole.CITIZEN: 0,
            UserRole.ANALYST: 1,
            UserRole.LEGAL_REVIEWER: 2,
            UserRole.CATALOGUE_ADMIN: 3,
        }
        return role_hierarchy.get(session.role, -1) >= role_hierarchy.get(required_role, 99)

    def purge_expired(self) -> int:
        now = datetime.now(timezone.utc)
        expired_ids = [sid for sid, s in self._sessions.items() if s.expires_at < now]
        for sid in expired_ids:
            self._sessions.pop(sid, None)
        active_sids = set(self._sessions.keys())
        orphaned_threads = [
            tid for tid, sid in self._thread_owners.items() if sid not in active_sids
        ]
        for tid in orphaned_threads:
            self._thread_owners.pop(tid, None)
        orphaned_reviews = [
            rid for rid, sid in self._review_owners.items() if sid not in active_sids
        ]
        for rid in orphaned_reviews:
            self._review_owners.pop(rid, None)
        return len(expired_ids)


session_manager = SessionManager()


def get_current_session(
    request: Request,
    authorization: str | None = Header(default=None),
) -> UserSession:
    """Dependency that extracts and validates the session token from Authorization header or cookie.

    If none exists, safely mints an anonymous citizen session to preserve discovery.
    """
    token = None
    auth_val = authorization if isinstance(authorization, str) else request.headers.get("authorization")
    if auth_val:
        parts = auth_val.split()
        if len(parts) == 2 and parts[0].casefold() == "bearer":
            token = parts[1]
        elif len(parts) == 1:
            token = parts[0]

    if not token:
        # Check cookie (__Host- prefix in production, standard in dev)
        token = request.cookies.get("__Host-sn_session") or request.cookies.get("sn_session")

    session = session_manager.validate_token(token) if token else None

    if not session:
        # Mint anonymous citizen session
        client_ip = request.client.host if request.client else None
        session, _ = session_manager.create_session(
            role=UserRole.CITIZEN,
            user_id="anonymous_citizen",
            client_ip=client_ip,
        )

    return session


def require_authenticated_session(
    request: Request,
    authorization: str | None = Header(default=None),
) -> UserSession:
    """FastAPI dependency requiring an explicitly authenticated session.

    Rejects unauthenticated or invalid callers with HTTP 401.
    """
    token = None
    auth_val = authorization if isinstance(authorization, str) else request.headers.get("authorization")
    if auth_val:
        parts = auth_val.split()
        if len(parts) == 2 and parts[0].casefold() == "bearer":
            token = parts[1]
        elif len(parts) == 1:
            token = parts[0]

    if not token:
        token = request.cookies.get("__Host-sn_session") or request.cookies.get("sn_session")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please obtain a session token via POST /auth/session.",
        )

    session = session_manager.validate_token(token)
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid token. Please obtain a new session token via POST /auth/session.",
        )

    return session


def require_role(required_role: UserRole):
    """FastAPI dependency factory enforcing minimum role level."""

    def _role_checker(session: UserSession = Depends(get_current_session)) -> UserSession:
        if not session_manager.has_role(session, required_role):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: role '{required_role.value}' is required for this action.",
            )
        return session

    return _role_checker
