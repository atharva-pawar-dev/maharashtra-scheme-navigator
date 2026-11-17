from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

import networkx as nx
import yaml

from scheme_navigator.domain.models import ApplicationPlan, PlanStep, Scheme

RTS_SOURCE_URL = "https://aaplesarkar.mahaonline.gov.in/en/CommonForm/CitizenServices_RTS"
PREREQUISITES_PATH = Path(__file__).resolve().parents[3] / "configs" / "prerequisites.yaml"

# Published Aaple Sarkar Department Notified Services limits. These are statutory service standards,
# not measurements of average duration or guarantees that a particular application will complete on time.
NOTIFIED_LIMIT_DAYS: dict[str, int] = {
    "age nationality domicile certificate": 15,
    "domicile certificate": 15,
    "income certificate": 15,
    "caste certificate": 21,
    "non creamy layer certificate": 21,
    "temporary residence certificate": 7,
    "senior citizen certificate": 7,
}

ALIASES: dict[str, str] = {
    "income proof": "income certificate",
    "income certificate": "income certificate",
    "residence proof": "domicile certificate",
    "domicile proof": "domicile certificate",
    "domicile certificate": "domicile certificate",
    "age nationality domicile certificate": "age nationality domicile certificate",
    "caste proof": "caste certificate",
    "caste certificate": "caste certificate",
    "non creamy layer certificate": "non creamy layer certificate",
    "non-creamy layer certificate": "non creamy layer certificate",
    "7/12 extract": "7/12 extract",
    "seven twelve extract": "7/12 extract",
    "aadhaar card": "identity proof",
    "identity proof": "identity proof",
    "age proof": "age proof",
    "bank account details": "bank account details",
    "affirmation letter": "affirmation letter",
    "bpl proof": "bpl proof",
}

DISPLAY_LABELS: dict[str, str] = {
    "income certificate": "Income Certificate",
    "domicile certificate": "Age, Nationality and Domicile Certificate",
    "age nationality domicile certificate": "Age, Nationality and Domicile Certificate",
    "caste certificate": "Caste Certificate",
    "non creamy layer certificate": "Non-Creamy Layer Certificate",
    "7/12 extract": "7/12 Extract",
    "identity proof": "Identity Proof",
    "age proof": "Age Proof",
    "bank account details": "Bank Account Details",
    "affirmation letter": "Affirmation Letter",
    "bpl proof": "BPL Proof",
}


def _key(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold().replace("–", "-")).strip()


def canonical_document(text: str) -> str:
    normalized = _key(text)
    return ALIASES.get(normalized, normalized)


def _load_verified_dependencies() -> dict[str, list[str]]:
    if not PREREQUISITES_PATH.exists():
        return {}
    data = yaml.safe_load(PREREQUISITES_PATH.read_text(encoding="utf-8")) or {}
    raw = data.get("verified_dependencies", {})
    if not isinstance(raw, dict):
        raise ValueError("configs/prerequisites.yaml: verified_dependencies must be a mapping")
    parsed: dict[str, list[str]] = {}
    for document, prerequisites in raw.items():
        if not isinstance(prerequisites, list) or not all(isinstance(item, str) for item in prerequisites):
            raise ValueError(f"Invalid prerequisite list for {document!r}")
        parsed[canonical_document(str(document))] = [canonical_document(item) for item in prerequisites]
    return parsed


def build_application_plan(
    scheme: Scheme,
    *,
    available_documents: list[str] | None = None,
    scheme_application_url: str | None = None,
    verified_dependencies: Mapping[str, list[str]] | None = None,
) -> ApplicationPlan:
    """Build a topological roadmap using only scheme-required and explicitly verified dependencies."""
    owned = {canonical_document(doc) for doc in (available_documents or [])}
    direct_required = list(dict.fromkeys(canonical_document(doc) for doc in scheme.required_documents))
    dependency_map = (
        {canonical_document(key): [canonical_document(dep) for dep in value] for key, value in verified_dependencies.items()}
        if verified_dependencies is not None else _load_verified_dependencies()
    )

    needed_order: list[str] = []
    needed: set[str] = set()
    queue = [doc for doc in direct_required if doc not in owned]
    while queue:
        doc = queue.pop(0)
        if doc in needed or doc in owned:
            continue
        needed.add(doc)
        needed_order.append(doc)
        for prerequisite in dependency_map.get(doc, []):
            if prerequisite not in owned and prerequisite not in needed:
                queue.append(prerequisite)

    graph = nx.DiGraph()
    descriptions: dict[str, tuple[str, int | None, str | None]] = {}
    step_id_by_doc: dict[str, str] = {}
    for key in needed_order:
        step_id = f"doc:{re.sub(r'[^a-z0-9]+', '-', key).strip('-')}"
        step_id_by_doc[key] = step_id
        limit = NOTIFIED_LIMIT_DAYS.get(key)
        label = DISPLAY_LABELS.get(key, key.title())
        source_url = RTS_SOURCE_URL if limit is not None else None
        graph.add_node(step_id)
        descriptions[step_id] = (label, limit, source_url)

    for document in needed_order:
        dependent_id = step_id_by_doc[document]
        for prerequisite in dependency_map.get(document, []):
            if prerequisite in owned:
                continue
            prerequisite_id = step_id_by_doc.get(prerequisite)
            if prerequisite_id:
                graph.add_edge(prerequisite_id, dependent_id)

    application_id = "apply:scheme"
    graph.add_node(application_id)
    # The scheme application depends on each outstanding document directly required by the scheme.
    for doc in direct_required:
        if doc in step_id_by_doc:
            graph.add_edge(step_id_by_doc[doc], application_id)

    try:
        order = list(nx.lexicographical_topological_sort(graph, key=str))
    except nx.NetworkXUnfeasible as exc:
        raise ValueError("Verified certificate prerequisites contain a cycle; fix the dependency registry.") from exc

    steps: list[PlanStep] = []
    for node in order:
        if node == application_id:
            deps = sorted(graph.predecessors(node))
            steps.append(PlanStep(
                step_id=application_id,
                title=f"Review and apply for {scheme.name}",
                step_type="apply_scheme",
                depends_on=deps,
                notified_limit_days=None,
                timeline_source_url=scheme_application_url,
                notes="Check eligibility and document audit findings, review every prefilled field, then submit yourself on the official portal.",
            ))
        else:
            title, limit, source_url = descriptions[node]
            deps = sorted(graph.predecessors(node))
            if limit is not None:
                note = f"Published RTS limit: {limit} days. Confirm the current notification and whether days are calendar or working days."
            else:
                note = "Required by the selected scheme or a verified dependency; confirm the issuing authority's current checklist. Do not infer a statutory timeline."
            steps.append(PlanStep(
                step_id=node,
                title=f"Obtain {title}",
                step_type="obtain_document",
                depends_on=deps,
                notified_limit_days=limit,
                timeline_source_url=source_url,
                notes=note,
            ))

    # Calculate the known part of the weighted critical path. Unknown durations are exposed separately.
    finish_days: dict[str, int] = {}
    for node in order:
        if node == application_id:
            continue
        predecessors = [parent for parent in graph.predecessors(node) if parent != application_id]
        start_day = max((finish_days.get(parent, 0) for parent in predecessors), default=0)
        limit = descriptions[node][1]
        finish_days[node] = start_day + (limit or 0)
    critical_path = max(finish_days.values(), default=0)
    unknown_steps = [node for node, (_title, limit, _url) in descriptions.items() if limit is None]
    if not descriptions:
        coverage = "complete"
    elif not unknown_steps:
        coverage = "complete"
    elif len(unknown_steps) == len(descriptions):
        coverage = "none"
    else:
        coverage = "partial"

    note = (
        "Published RTS limits are service standards, not a guarantee of actual completion. "
        "The critical-path figure includes only known notified limits; steps with unknown timelines are excluded. "
        "Confirm the current service notification and counting convention."
    )
    return ApplicationPlan(
        scheme_id=scheme.scheme_id,
        steps=steps,
        estimated_notified_days_on_critical_path=critical_path,
        timeline_coverage=coverage,
        unknown_timeline_step_ids=unknown_steps,
        timeline_note=note,
    )
