"""TRIMURTI v3 Thin-Rule Lint and Superficial Model Detector.

Enforces Invariant I-07 (Thin-Rule Protection):
A scheme whose only approved rules are generic attributes, such as Maharashtra residence,
cannot return definitive eligibility.
Thin-rule schemes must be displayed as LIMITED_INFO, LIKELY_RELEVANT or the equivalent
appropriate non-definitive state. They cannot return MEETS_VERIFIED_CRITERIA.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

from scheme_navigator.domain.models import RuleNode, Scheme
from scheme_navigator.domain.profile_vocabulary import is_field_substantive


@dataclass(frozen=True)
class LintResult:
    is_valid: bool
    substantive_criteria_count: int
    defects: tuple[str, ...] = ()
    reason: str = ""


def _extract_all_leaf_nodes(node: RuleNode) -> list[RuleNode]:
    """Recursively collect all leaf condition nodes from a RuleNode tree."""
    leaves: list[RuleNode] = []
    if node.op in {"all", "any"}:
        for child in node.children:
            leaves.extend(_extract_all_leaf_nodes(child))
    elif node.op == "not":
        if node.children:
            leaves.extend(_extract_all_leaf_nodes(node.children[0]))
    else:
        leaves.append(node)
    return leaves


def lint_scheme_rules(scheme: Scheme | Any) -> LintResult:
    """Evaluate whether a scheme's rule model is substantive or superficial/thin.
    
    A scheme passes thin-rule linting ONLY when:
    1. It has at least 2 substantive eligibility criteria (excluding residency/nationality).
    2. It does not rely exclusively on generic residency or existence checks.
    3. Mandatory income criteria specify valid bounds and units.
    """
    defects: list[str] = []

    # If scheme object has substantive_criteria_count attribute directly (e.g. SchemeV2)
    substantive_count = getattr(scheme, "substantive_criteria_count", None)
    
    rule_tree = getattr(scheme, "eligibility_rule", None)
    if rule_tree is None:
        return LintResult(
            is_valid=False,
            substantive_criteria_count=0,
            defects=("MISSING_RULE_TREE",),
            reason="Scheme has no eligibility rule tree defined.",
        )

    leaves = _extract_all_leaf_nodes(rule_tree)
    if not leaves:
        return LintResult(
            is_valid=False,
            substantive_criteria_count=0,
            defects=("EMPTY_RULE_TREE",),
            reason="Scheme rule tree contains no leaf criteria.",
        )

    fields_present = [leaf.field for leaf in leaves if leaf.field]
    substantive_fields = [f for f in fields_present if is_field_substantive(f)]
    
    calculated_substantive_count = len(substantive_fields)
    final_count = substantive_count if substantive_count is not None else calculated_substantive_count

    # Check 1: Must have >= 2 substantive criteria
    if final_count < 2:
        defects.append(
            f"THIN_RULE: Scheme has only {final_count} substantive criteria (minimum 2 required)."
        )

    # Check 2: Residency-only rule check
    non_residency_fields = [f for f in fields_present if f not in {"resident_state", "country", "nationality"}]
    if not non_residency_fields:
        defects.append("RESIDENCY_ONLY: Scheme criteria consist solely of geographic residency.")

    # Check 3: Check income criteria sanity
    for leaf in leaves:
        if leaf.field in {"annual_family_income", "monthly_income", "income"}:
            if leaf.op in {"lte", "lt"} and (leaf.value is None or leaf.value <= 0):
                defects.append("INVALID_INCOME_CEILING: Income ceiling must be a positive integer.")

    is_valid = len(defects) == 0
    reason = "; ".join(defects) if defects else "Scheme satisfies substantive criteria requirements."

    return LintResult(
        is_valid=is_valid,
        substantive_criteria_count=final_count,
        defects=tuple(defects),
        reason=reason,
    )
