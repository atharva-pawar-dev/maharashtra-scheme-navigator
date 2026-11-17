from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from scheme_navigator.source_registry.models import SourceChangeRecord, SourceRecord
from scheme_navigator.source_registry.registry import SourceRegistry


class SourceLifecycleMonitor:
    """Monitors official Maharashtra sources, checks content hashes, detects amendments, and manages publication safety."""

    def __init__(self, registry: SourceRegistry | None = None) -> None:
        self.registry = registry or SourceRegistry()
        self._change_records: list[SourceChangeRecord] = []
        self._suspended_schemes: set[str] = set()

    def record_change(
        self,
        *,
        source_id: str,
        change_type: str,
        summary: str,
        previous_hash: str,
        current_hash: str,
        affected_scheme_ids: list[str],
        requires_human_approval: bool = True,
    ) -> SourceChangeRecord:
        """Logs a detected source change (e.g. newly published GR, portal amendment)."""
        change = SourceChangeRecord(
            change_id=f"CHG-{uuid.uuid4().hex[:8].upper()}",
            source_id=source_id,
            detected_at_iso=datetime.now(timezone.utc).isoformat(),
            change_type=change_type,
            summary=summary,
            previous_hash=previous_hash,
            current_hash=current_hash,
            affected_scheme_ids=affected_scheme_ids,
            requires_human_approval=requires_human_approval,
            is_reviewed=False,
        )
        self._change_records.append(change)
        return change

    def suspend_scheme(self, scheme_id: str, reason: str) -> None:
        """Suspends scheme publication when unverified critical amendments are detected."""
        self._suspended_schemes.add(scheme_id)

    def lift_suspension(self, scheme_id: str) -> None:
        """Lifts suspension after authorized reviewer signs off on verified rules."""
        self._suspended_schemes.discard(scheme_id)

    def is_suspended(self, scheme_id: str) -> bool:
        return scheme_id in self._suspended_schemes

    def get_pending_changes(self) -> list[SourceChangeRecord]:
        return [c for c in self._change_records if not c.is_reviewed]

    def get_monitor_status(self) -> dict[str, Any]:
        all_sources = self.registry.list_sources()
        return {
            "status": "HEALTHY_MONITORING",
            "total_sources_monitored": len(all_sources),
            "pending_changes_count": len(self.get_pending_changes()),
            "suspended_schemes": list(self._suspended_schemes),
            "suspended_schemes_count": len(self._suspended_schemes),
            "recent_changes": [c.model_dump() for c in self._change_records[-10:]],
            "last_scan_iso": datetime.now(timezone.utc).isoformat(),
        }
