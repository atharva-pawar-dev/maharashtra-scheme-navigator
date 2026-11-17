from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone

from scheme_navigator.domain.evidence import RuleEvidence, RuleVerificationStatus
from scheme_navigator.domain.models import Scheme
from scheme_navigator.security.models import CatalogueReleaseSignature, UserRole, UserSession

def _get_release_signing_key() -> bytes:
    configured = os.getenv("SCHEME_NAVIGATOR_RELEASE_KEY")
    if not configured:
        from scheme_navigator.core.config import settings
        configured = getattr(settings, "scheme_navigator_release_key", None)
    if configured and len(configured.strip()) >= 32:
        return configured.strip().encode("utf-8")
    from scheme_navigator.core.config import settings
    if settings.app_env.casefold() in {"production", "prod"}:
        raise RuntimeError(
            "CRITICAL: SCHEME_NAVIGATOR_RELEASE_KEY environment variable is missing or shorter than 32 characters in production."
        )
    global _EPHEMERAL_RELEASE_KEY
    if "_EPHEMERAL_RELEASE_KEY" not in globals():
        _EPHEMERAL_RELEASE_KEY = secrets.token_bytes(32)
    return _EPHEMERAL_RELEASE_KEY


class PublicationAuthorizationError(Exception):
    """Raised when scheme release publication preconditions are violated."""


class PublicationManager:
    """Manages secure, fail-closed catalogue publication authorization and cryptographic signing."""

    def __init__(self, signing_key: bytes | None = None) -> None:
        self._key_override = signing_key

    @property
    def _key(self) -> bytes:
        if self._key_override:
            return self._key_override
        return _get_release_signing_key()

    def calculate_catalogue_digest(self, schemes: list[Scheme]) -> str:
        """Calculate canonical SHA-256 digest over normalized scheme records."""
        # Sort schemes deterministically by scheme_id
        sorted_schemes = sorted(schemes, key=lambda s: s.scheme_id)
        serialized = json.dumps(
            [s.model_dump(mode="json") for s in sorted_schemes],
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def authorize_and_sign_release(
        self,
        schemes: list[Scheme],
        admin_session: UserSession,
        version: str = "1.0.0",
    ) -> tuple[CatalogueReleaseSignature, list[Scheme]]:
        """Authorize and sign a catalogue release.

        ENFORCES STRICT INVARIANTS:
        1. Caller must hold CATALOGUE_ADMIN role.
        2. Non-demo schemes must have 100% LEGAL_APPROVED condition-evidence coverage.
        3. Fails closed if any condition is unverified, draft, or disputed.
        4. Stamped with explicit disclaimer that software release signature is NOT government approval.
        """
        if admin_session.role != UserRole.CATALOGUE_ADMIN:
            raise PublicationAuthorizationError(
                f"Access denied: only '{UserRole.CATALOGUE_ADMIN.value}' may sign catalogue releases. "
                f"Actor role is '{admin_session.role.value}'."
            )

        if not schemes:
            raise PublicationAuthorizationError("Cannot sign an empty scheme catalogue release.")

        # Validate evidence coverage for every scheme
        authorized_schemes: list[Scheme] = []
        for s in schemes:
            is_demo = (
                s.scheme_id.startswith("demo-")
                or (s.approved_by or "").casefold() == "local_demo_fixture_only"
            )
            if not is_demo:
                if not s.evidence:
                    raise PublicationAuthorizationError(
                        f"Scheme '{s.scheme_id}' has no verified evidence items. Publication rejected."
                    )
                for ev in s.evidence:
                    status = getattr(ev, "verification_status", None)
                    if isinstance(ev, dict):
                        status = ev.get("verification_status")
                    if status != RuleVerificationStatus.LEGAL_APPROVED:
                        raise PublicationAuthorizationError(
                            f"Scheme '{s.scheme_id}' condition has unapproved evidence status '{status}'. "
                            f"All conditions must be 'legal_approved' for release publication."
                        )

            # Mark publication authorized for the signed copy
            signed_scheme = s.model_copy(update={"publication_authorized": True})
            authorized_schemes.append(signed_scheme)

        digest = self.calculate_catalogue_digest(authorized_schemes)
        now_str = datetime.now(timezone.utc).isoformat()
        release_id = f"rel_{secrets.token_hex(8)}"

        payload = f"{release_id}:{version}:{len(authorized_schemes)}:{digest}:{now_str}:{admin_session.user_id}"
        h = hmac.new(self._key, payload.encode("utf-8"), hashlib.sha256)
        token = base64.urlsafe_b64encode(h.digest()).decode("utf-8").rstrip("=")

        sig = CatalogueReleaseSignature(
            release_id=release_id,
            catalogue_version=version,
            scheme_count=len(authorized_schemes),
            signed_at=now_str,
            signed_by_admin=admin_session.user_id,
            catalogue_sha256=digest,
            signature_token=token,
        )

        return sig, authorized_schemes

    def verify_release_signature(
        self,
        schemes: list[Scheme],
        signature: CatalogueReleaseSignature,
    ) -> bool:
        """Verify that a signed catalogue release matches the current scheme content."""
        computed_digest = self.calculate_catalogue_digest(schemes)
        if not hmac.compare_digest(computed_digest, signature.catalogue_sha256):
            return False

        payload = (
            f"{signature.release_id}:{signature.catalogue_version}:"
            f"{signature.scheme_count}:{signature.catalogue_sha256}:"
            f"{signature.signed_at}:{signature.signed_by_admin}"
        )
        h = hmac.new(self._key, payload.encode("utf-8"), hashlib.sha256)
        expected_token = base64.urlsafe_b64encode(h.digest()).decode("utf-8").rstrip("=")

        return hmac.compare_digest(signature.signature_token, expected_token)


publication_manager = PublicationManager()
