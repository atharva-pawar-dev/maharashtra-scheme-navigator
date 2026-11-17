from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from scheme_navigator.agents.interview_store import InterviewSessionStore
from scheme_navigator.agents.interviewer import build_interviewer_graph
from scheme_navigator.services.catalog import SchemeCatalog


def _initial_state(thread_id: str) -> dict:
    scheme = next(
        item
        for item in SchemeCatalog.from_json().all()
        if item.scheme_id == "demo-majhi-ladki-bahin"
    )
    return {
        "thread_id": thread_id,
        "language": "en",
        "profile": {"name": "Synthetic Test Citizen"},
        "candidate_schemes": [scheme.model_dump(mode="json")],
        "pending_answer": None,
        "asked_fields": [],
        "events": [],
        "is_complete": False,
        "result_summary": [],
    }


def test_interview_checkpoint_survives_store_recreation(tmp_path):
    db_path = tmp_path / "interviews.sqlite3"
    thread_id = "restart-persistence-test"
    config = {"configurable": {"thread_id": thread_id}}

    first_store = InterviewSessionStore(db_path=db_path, retention_hours=24)
    try:
        first_store.create_session(thread_id)
        first_graph = build_interviewer_graph(
            checkpointer=first_store.checkpointer
        )
        first_graph.invoke(_initial_state(thread_id), config=config)
        first_snapshot = first_graph.get_state(config)
        assert first_snapshot.values.get("next_question")
    finally:
        first_store.close()

    second_store = InterviewSessionStore(db_path=db_path, retention_hours=24)
    try:
        second_graph = build_interviewer_graph(
            checkpointer=second_store.checkpointer
        )
        restored = second_graph.get_state(config)

        assert restored.values["thread_id"] == thread_id
        assert restored.values["profile"]["name"] == "Synthetic Test Citizen"
        assert restored.values["next_question"] == first_snapshot.values["next_question"]
        assert second_store.is_active(thread_id)
    finally:
        second_store.close()


def test_expired_interview_session_purges_its_checkpoints(tmp_path):
    db_path = tmp_path / "interviews.sqlite3"
    thread_id = "expired-persistence-test"
    config = {"configurable": {"thread_id": thread_id}}

    store = InterviewSessionStore(db_path=db_path, retention_hours=24)
    try:
        store.create_session(thread_id)
        graph = build_interviewer_graph(checkpointer=store.checkpointer)
        graph.invoke(_initial_state(thread_id), config=config)

        expired_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "UPDATE interview_sessions SET expires_at = ? WHERE thread_id = ?",
                (expired_at, thread_id),
            )

        assert store.purge_expired() == 1
        assert not store.is_active(thread_id)
        assert not graph.get_state(config).values
    finally:
        store.close()
