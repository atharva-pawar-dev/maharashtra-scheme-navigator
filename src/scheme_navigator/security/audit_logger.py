from __future__ import annotations

import json
import logging
from pathlib import Path
import re
from threading import Lock
from typing import Any

from scheme_navigator.security.models import AuditEvent, AuditEventType

logger = logging.getLogger("scheme_navigator.audit")

DEFAULT_AUDIT_LOG_PATH = Path(__file__).resolve().parents[3] / "data" / "security_audit.log"


class SecurityAuditLogger:
    """Thread-safe append-only structured audit logger for compliance and security monitoring."""

    def __init__(self, log_path: Path = DEFAULT_AUDIT_LOG_PATH) -> None:
        self._log_path = log_path
        self._lock = Lock()
        self._buffer: list[AuditEvent] = []

    def log_event(
        self,
        event_type: AuditEventType,
        actor_id: str,
        actor_role: str,
        action: str,
        resource: str,
        client_ip: str | None = None,
        status_code: int = 200,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Record a structured security audit event."""
        # Sanitize details: strictly filter out any potential secrets or PII
        sanitized_details = {}
        aadhaar_pattern = re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b")
        for k, v in (details or {}).items():
            k_lower = k.lower()
            v_str = str(v)
            if any(s in k_lower for s in ("password", "secret", "token", "otp", "aadhaar", "key", "cvv", "auth")):
                sanitized_details[k] = "[REDACTED]"
            elif aadhaar_pattern.search(v_str):
                sanitized_details[k] = "[REDACTED_AADHAAR]"
            else:
                sanitized_details[k] = v

        event = AuditEvent(
            event_type=event_type,
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            resource=resource,
            client_ip=client_ip,
            status_code=status_code,
            details=sanitized_details,
        )

        with self._lock:
            self._buffer.append(event)
            # Write to file if parent directory is writable
            try:
                self._log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")
            except OSError as err:
                logger.warning(f"Could not append to security audit file: {err}")

        return event

    def recent_events(self, limit: int = 50) -> list[AuditEvent]:
        with self._lock:
            return list(self._buffer[-limit:])


audit_logger = SecurityAuditLogger()
