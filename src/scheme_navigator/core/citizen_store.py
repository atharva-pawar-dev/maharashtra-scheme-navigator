"""Persistent SQLite store for CitizenProfile, scoped InterviewRuns, and single-active-scheme Progress."""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scheme_navigator.core.migrations import CITIZEN_PROFILE_MIGRATIONS, apply_migrations
from scheme_navigator.domain.models import CitizenProfile

logger = logging.getLogger("scheme_navigator.citizen_store")


class CitizenProfileStore:
    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path:
            self._db_path = Path(db_path).resolve()
        else:
            self._db_path = Path(__file__).resolve().parents[3] / "data" / "citizen_profiles.sqlite3"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        apply_migrations(self._db_path, CITIZEN_PROFILE_MIGRATIONS)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=15.0)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    # -------------------------------------------------------------------------
    # CITIZEN PROFILE OPERATIONS
    # -------------------------------------------------------------------------

    def get_profile(self, session_id: str) -> CitizenProfile | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT profile_json FROM citizen_profiles WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if not row:
                return None
            try:
                data = json.loads(row["profile_json"])
                return CitizenProfile.model_validate(data)
            except Exception as exc:
                logger.warning("Failed parsing profile for session %s: %exc", session_id, exc)
                return None

    def get_profile_with_provenance(self, session_id: str) -> tuple[CitizenProfile, dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT profile_json, provenance_json FROM citizen_profiles WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if not row:
                return CitizenProfile(), {}
            try:
                profile = CitizenProfile.model_validate(json.loads(row["profile_json"]))
                provenance = json.loads(row["provenance_json"] or "{}")
                return profile, provenance
            except Exception:
                return CitizenProfile(), {}

    def save_profile(
        self,
        session_id: str,
        profile: CitizenProfile,
        provenance: dict[str, Any] | None = None,
    ) -> CitizenProfile:
        now_iso = datetime.now(timezone.utc).isoformat()
        profile_json = json.dumps(profile.model_dump(mode="json"))
        prov_dict = provenance or {}
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT provenance_json FROM citizen_profiles WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if existing:
                try:
                    merged_prov = json.loads(existing["provenance_json"] or "{}")
                except Exception:
                    merged_prov = {}
                merged_prov.update(prov_dict)
                conn.execute(
                    """
                    UPDATE citizen_profiles
                    SET profile_json = ?, provenance_json = ?, updated_at = ?
                    WHERE session_id = ?
                    """,
                    (profile_json, json.dumps(merged_prov), now_iso, session_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO citizen_profiles (session_id, profile_json, provenance_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (session_id, profile_json, json.dumps(prov_dict), now_iso, now_iso),
                )
            conn.commit()
        return profile

    def update_profile_field(
        self,
        session_id: str,
        field: str,
        value: Any,
        source: str = "citizen_interview",
    ) -> CitizenProfile:
        profile, prov = self.get_profile_with_provenance(session_id)
        dump = profile.model_dump(mode="python")
        dump[field] = value
        updated_profile = CitizenProfile.model_validate(dump)
        prov[field] = {
            "source": source,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.save_profile(session_id, updated_profile, provenance=prov)

    # -------------------------------------------------------------------------
    # INTERVIEW RUN OPERATIONS
    # -------------------------------------------------------------------------

    def create_interview_run(
        self,
        thread_id: str,
        session_id: str,
        scheme_id: str | None = None,
        initial_state: dict[str, Any] | None = None,
        mode: str = "DISCOVERY",
        target_scheme_id: str | None = None,
        target_jurisdiction_id: str | None = None,
        catalogue_version: str = "2026.11",
        rule_version: str = "1.0.0",
        language: str = "en",
    ) -> dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        state_json = json.dumps(initial_state or {})
        effective_target = target_scheme_id or scheme_id
        with self._conn() as conn:
            cols = {col[1] for col in conn.execute("PRAGMA table_info(interview_runs)").fetchall()}
            if "target_jurisdiction_id" in cols:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO interview_runs
                    (thread_id, session_id, scheme_id, status, state_json, created_at, updated_at,
                     mode, target_scheme_id, target_jurisdiction_id, catalogue_version, rule_version, language)
                    VALUES (?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (thread_id, session_id, effective_target, state_json, now_iso, now_iso,
                     mode, effective_target, target_jurisdiction_id, catalogue_version, rule_version, language),
                )
            else:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO interview_runs
                    (thread_id, session_id, scheme_id, status, state_json, created_at, updated_at,
                     mode, target_scheme_id, catalogue_version, rule_version, language)
                    VALUES (?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (thread_id, session_id, effective_target, state_json, now_iso, now_iso,
                     mode, effective_target, catalogue_version, rule_version, language),
                )
            conn.commit()
        return {
            "thread_id": thread_id,
            "session_id": session_id,
            "scheme_id": effective_target,
            "mode": mode,
            "target_scheme_id": effective_target,
            "target_jurisdiction_id": target_jurisdiction_id,
            "status": "active",
            "created_at": now_iso,
        }

    def get_interview_run(self, thread_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM interview_runs WHERE thread_id = ?",
                (thread_id,),
            ).fetchone()
            if not row:
                return None
            keys = row.keys()
            results = json.loads(row["results_json"]) if "results_json" in keys and row["results_json"] else None
            return {
                "thread_id": row["thread_id"],
                "session_id": row["session_id"],
                "scheme_id": row["scheme_id"],
                "mode": row["mode"] if "mode" in keys else "DISCOVERY",
                "target_scheme_id": row["target_scheme_id"] if "target_scheme_id" in keys else row["scheme_id"],
                "catalogue_version": row["catalogue_version"] if "catalogue_version" in keys else "2026.11",
                "rule_version": row["rule_version"] if "rule_version" in keys else "1.0.0",
                "language": row["language"] if "language" in keys else "en",
                "status": row["status"],
                "state": json.loads(row["state_json"] or "{}"),
                "results": results,
                "created_at": row["created_at"],
                "completed_at": row["completed_at"] if "completed_at" in keys else None,
                "updated_at": row["updated_at"],
            }

    def update_interview_run_state(
        self,
        thread_id: str,
        state: dict[str, Any],
        status: str = "active",
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE interview_runs
                SET state_json = ?, status = ?, updated_at = ?
                WHERE thread_id = ?
                """,
                (json.dumps(state), status, now_iso, thread_id),
            )
            conn.commit()

    def complete_interview_run(
        self,
        thread_id: str,
        results: list[dict[str, Any]] | dict[str, Any] | None = None,
        final_state: dict[str, Any] | None = None,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        results_json = json.dumps(results) if results is not None else None
        with self._conn() as conn:
            if final_state is not None:
                conn.execute(
                    """
                    UPDATE interview_runs
                    SET status = 'completed', completed_at = ?, results_json = ?, state_json = ?, updated_at = ?
                    WHERE thread_id = ?
                    """,
                    (now_iso, results_json, json.dumps(final_state), now_iso, thread_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE interview_runs
                    SET status = 'completed', completed_at = ?, results_json = ?, updated_at = ?
                    WHERE thread_id = ?
                    """,
                    (now_iso, results_json, now_iso, thread_id),
                )
            conn.commit()

    def get_interview_run_results(self, thread_id: str) -> dict[str, Any] | None:
        return self.get_interview_run(thread_id)

    def get_latest_run_for_session(self, session_id: str, mode: str | None = None) -> dict[str, Any] | None:
        with self._conn() as conn:
            if mode:
                row = conn.execute(
                    "SELECT thread_id FROM interview_runs WHERE session_id = ? AND mode = ? ORDER BY created_at DESC LIMIT 1",
                    (session_id, mode),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT thread_id FROM interview_runs WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
                    (session_id,),
                ).fetchone()
            if not row:
                return None
            return self.get_interview_run(row["thread_id"])

    # -------------------------------------------------------------------------
    # CITIZEN PROGRESS OPERATIONS (EXACTLY ONE ACTIVE SCHEME)
    # -------------------------------------------------------------------------

    def get_progress(self, session_id: str) -> dict[str, Any]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM citizen_progress WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if not row:
                return {
                    "session_id": session_id,
                    "active_scheme_id": None,
                    "active_scheme_version": None,
                    "paused_schemes": {},
                    "dismissed_schemes": [],
                }
            active = row["active_scheme_id"]
            paused = json.loads(row["paused_schemes_json"] or "{}")
            dismissed = json.loads(row["dismissed_schemes_json"] or "[]")
            non_active_paused = {k: v for k, v in paused.items() if k != active and k not in dismissed}
            return {
                "session_id": session_id,
                "active_scheme_id": active,
                "active_scheme_version": row["active_scheme_version"],
                "paused_schemes": non_active_paused,
                "dismissed_schemes": dismissed,
            }

    def set_active_scheme(
        self,
        session_id: str,
        scheme_id: str,
        version: str = "1.0.0",
        progress_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Atomically set the single active scheme. If another scheme was active, it is paused."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM citizen_progress WHERE session_id = ?",
                (session_id,),
            ).fetchone()

            if not row:
                # First time setting progress
                initial_paused = {}
                if progress_data:
                    initial_paused[scheme_id] = {
                        "scheme_id": scheme_id,
                        "version": version,
                        "progress_data": progress_data,
                        "progress": progress_data,
                    }
                conn.execute(
                    """
                    INSERT INTO citizen_progress
                    (session_id, active_scheme_id, active_scheme_version, paused_schemes_json, dismissed_schemes_json, updated_at)
                    VALUES (?, ?, ?, ?, '[]', ?)
                    """,
                    (session_id, scheme_id, version, json.dumps(initial_paused), now_iso),
                )
                conn.commit()
                return {
                    "active_scheme_id": scheme_id,
                    "active_scheme_version": version,
                    "paused_schemes": {},
                    "dismissed_schemes": [],
                    "status": "activated",
                }

            current_active = row["active_scheme_id"]
            current_ver = row["active_scheme_version"]
            paused = json.loads(row["paused_schemes_json"] or "{}")
            dismissed = json.loads(row["dismissed_schemes_json"] or "[]")

            if current_active and current_active != scheme_id:
                # Pause previous active scheme, retaining any document/roadmap progress
                prior_entry = paused.get(current_active, {})
                prior_prog = prior_entry.get("progress_data") or prior_entry.get("progress")
                paused[current_active] = {
                    "scheme_id": current_active,
                    "version": current_ver or "1.0.0",
                    "paused_at": now_iso,
                    "progress_data": prior_prog or {},
                    "progress": prior_prog or {},
                }

            # Update new active scheme's record
            paused[scheme_id] = {
                "scheme_id": scheme_id,
                "version": version,
                "progress_data": progress_data or paused.get(scheme_id, {}).get("progress_data", {}),
                "progress": progress_data or paused.get(scheme_id, {}).get("progress", {}),
                "updated_at": now_iso,
            }

            # Ensure not in dismissed list if reactivated
            if scheme_id in dismissed:
                dismissed.remove(scheme_id)

            conn.execute(
                """
                UPDATE citizen_progress
                SET active_scheme_id = ?, active_scheme_version = ?, paused_schemes_json = ?, dismissed_schemes_json = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (scheme_id, version, json.dumps(paused), json.dumps(dismissed), now_iso, session_id),
            )
            conn.commit()

            non_active_paused = {k: v for k, v in paused.items() if k != scheme_id and k not in dismissed}
            return {
                "active_scheme_id": scheme_id,
                "active_scheme_version": version,
                "paused_schemes": non_active_paused,
                "dismissed_schemes": dismissed,
                "status": "activated",
                "previously_paused": current_active if current_active and current_active != scheme_id else None,
            }

    def dismiss_scheme(self, session_id: str, scheme_id: str) -> dict[str, Any]:
        """Permanently remove scheme from My Progress, recording dismissal so it is excluded from suggestions."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM citizen_progress WHERE session_id = ?",
                (session_id,),
            ).fetchone()

            if not row:
                conn.execute(
                    """
                    INSERT INTO citizen_progress
                    (session_id, active_scheme_id, active_scheme_version, paused_schemes_json, dismissed_schemes_json, updated_at)
                    VALUES (?, NULL, NULL, '{}', ?, ?)
                    """,
                    (session_id, json.dumps([scheme_id]), now_iso),
                )
                conn.commit()
                return {"active_scheme_id": None, "dismissed_schemes": [scheme_id], "status": "dismissed"}

            active = row["active_scheme_id"]
            paused = json.loads(row["paused_schemes_json"] or "{}")
            dismissed = json.loads(row["dismissed_schemes_json"] or "[]")

            if active == scheme_id:
                active = None

            paused.pop(scheme_id, None)
            if scheme_id not in dismissed:
                dismissed.append(scheme_id)

            conn.execute(
                """
                UPDATE citizen_progress
                SET active_scheme_id = ?, paused_schemes_json = ?, dismissed_schemes_json = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (active, json.dumps(paused), json.dumps(dismissed), now_iso, session_id),
            )
            conn.commit()
            return {
                "active_scheme_id": active,
                "paused_schemes": paused,
                "dismissed_schemes": dismissed,
                "status": "dismissed",
            }

    # -------------------------------------------------------------------------
    # RESET DATA & RETENTION PURGE
    # -------------------------------------------------------------------------

    def reset_citizen_data(self, session_id: str) -> bool:
        """Securely wipe the citizen's profile, interview runs, and progress records."""
        with self._conn() as conn:
            conn.execute("DELETE FROM citizen_profiles WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM interview_runs WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM citizen_progress WHERE session_id = ?", (session_id,))
            conn.commit()
        return True

    def purge_expired_records(self, retention_hours: int = 24) -> dict[str, int]:
        cutoff = datetime.now(timezone.utc).timestamp() - (retention_hours * 3600)
        cutoff_iso = datetime.fromtimestamp(cutoff, timezone.utc).isoformat()
        with self._conn() as conn:
            cur1 = conn.execute("DELETE FROM citizen_profiles WHERE updated_at < ?", (cutoff_iso,))
            p_deleted = cur1.rowcount
            cur2 = conn.execute("DELETE FROM interview_runs WHERE updated_at < ?", (cutoff_iso,))
            r_deleted = cur2.rowcount
            cur3 = conn.execute("DELETE FROM citizen_progress WHERE updated_at < ?", (cutoff_iso,))
            pr_deleted = cur3.rowcount
            conn.commit()
        return {"profiles_purged": p_deleted, "interview_runs_purged": r_deleted, "progress_purged": pr_deleted}


citizen_store = CitizenProfileStore()
