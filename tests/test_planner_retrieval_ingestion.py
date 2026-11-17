from __future__ import annotations

import pytest

from scheme_navigator.domain.models import Scheme
from scheme_navigator.ingestion.pipeline import _check_url
from scheme_navigator.planner.dag import RTS_SOURCE_URL, build_application_plan
from scheme_navigator.retrieval.hybrid import HybridRetriever, RetrievalDocument
from scheme_navigator.services.catalog import SchemeCatalog


def test_plan_uses_rts_timelines_and_does_not_sum_parallel_requests():
    scheme = next(s for s in SchemeCatalog.from_json().all() if s.scheme_id == "demo-majhi-ladki-bahin")
    plan = build_application_plan(scheme)
    assert plan.estimated_notified_days_on_critical_path == 15
    income = next(step for step in plan.steps if "Income Certificate" in step.title)
    assert income.notified_limit_days == 15
    assert income.timeline_source_url == RTS_SOURCE_URL
    apply_step = next(step for step in plan.steps if step.step_type == "apply_scheme")
    assert len(apply_step.depends_on) == len(plan.steps) - 1


def test_known_documents_are_not_recreated():
    scheme = next(s for s in SchemeCatalog.from_json().all() if s.scheme_id == "demo-majhi-ladki-bahin")
    plan = build_application_plan(scheme, available_documents=["income certificate"])
    assert not any("Income Certificate" in step.title for step in plan.steps)


def test_bm25_search_returns_source_grounded_hit():
    docs = [
        RetrievalDocument("a", "Income Certificate", "family annual income certificate limit", "https://example.org/a", "official"),
        RetrievalDocument("b", "Domicile", "residence proof for Maharashtra", "https://example.org/b", "official"),
    ]
    hits = HybridRetriever(docs).search("annual income certificate", limit=2)
    assert hits and hits[0].doc.doc_id == "a"


def test_ingestion_rejects_non_allowlisted_and_http_urls():
    with pytest.raises(ValueError):
        _check_url("https://example.com/fake-gr.pdf")
    with pytest.raises(ValueError):
        _check_url("http://myscheme.gov.in/schemes/test")


def test_plan_missing_service_time_does_not_invent_one():
    base = SchemeCatalog.from_json().all()[0]
    item = base.model_copy(update={"required_documents": ["unlisted supporting document"]})
    plan = build_application_plan(item)
    doc_step = next(step for step in plan.steps if step.step_type == "obtain_document")
    assert doc_step.notified_limit_days is None
    assert "do not infer" in doc_step.notes.lower()


def test_verified_dependency_is_topologically_ordered_and_timeline_is_chain_sum():
    scheme = SchemeCatalog.from_json().all()[0].model_copy(update={"required_documents": ["income certificate"]})
    plan = build_application_plan(
        scheme,
        verified_dependencies={"income certificate": ["domicile certificate"]},
    )
    domicile = next(step for step in plan.steps if "Domicile" in step.title)
    income = next(step for step in plan.steps if "Income Certificate" in step.title)
    assert domicile.step_id in income.depends_on
    assert plan.estimated_notified_days_on_critical_path == 30
    assert plan.timeline_coverage == "complete"


def test_unknown_timeline_coverage_is_explicit():
    scheme = SchemeCatalog.from_json().all()[0].model_copy(update={"required_documents": ["unlisted item"]})
    plan = build_application_plan(scheme)
    assert plan.timeline_coverage == "none"
    assert plan.unknown_timeline_step_ids

def test_verified_dependency_cycle_is_rejected():
    scheme = SchemeCatalog.from_json().all()[0].model_copy(
        update={"required_documents": ["income certificate"]}
    )

    with pytest.raises(ValueError, match="contain a cycle"):
        build_application_plan(
            scheme,
            verified_dependencies={
                "income certificate": ["domicile certificate"],
                "domicile certificate": ["income certificate"],
            },
        )