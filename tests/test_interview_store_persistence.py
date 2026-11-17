from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from scheme_navigator.agents.interview_store import InterviewSessionStore


class _State(TypedDict, total=False):
    value: int


def _build_graph(checkpointer):
    builder = StateGraph(_State)
    builder.add_node("save_value", lambda state: {"value": state["value"]})
    builder.add_edge(START, "save_value")
    builder.add_edge("save_value", END)
    return builder.compile(checkpointer=checkpointer)


def test_sqlite_checkpoints_survive_store_reopen(tmp_path):
    database = tmp_path / "interviews.sqlite3"
    config = {"configurable": {"thread_id": "persistent-thread"}}

    first_store = InterviewSessionStore(db_path=database)
    first_store.create_session("persistent-thread")
    first_graph = _build_graph(first_store.checkpointer)
    first_graph.invoke({"value": 42}, config=config)
    first_store.close()

    second_store = InterviewSessionStore(db_path=database)
    try:
        assert second_store.is_active("persistent-thread")
        second_graph = _build_graph(second_store.checkpointer)
        snapshot = second_graph.get_state(config)
        assert snapshot.values["value"] == 42
    finally:
        second_store.close()
