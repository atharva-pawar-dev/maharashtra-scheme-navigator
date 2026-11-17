from __future__ import annotations

import pytest

from scheme_navigator.domain.models import CitizenProfile, EligibilityStatus, RuleNode, Scheme
from scheme_navigator.services.catalog import SchemeCatalog
from scheme_navigator.services.rule_engine import evaluate_node, evaluate_scheme


def test_missing_field_is_unknown_not_false():
    rule = RuleNode.model_validate({"op": "lte", "field": "annual_family_income", "value": 250000})
    result = evaluate_node(rule, CitizenProfile())
    assert result.value is None
    assert result.missing_fields == ("annual_family_income",)


def test_all_short_circuits_false_even_when_another_field_missing():
    rule = RuleNode.model_validate({"op": "all", "children": [
        {"op": "eq", "field": "resident_state", "value": "maharashtra"},
        {"op": "lte", "field": "annual_family_income", "value": 250000},
    ]})
    result = evaluate_node(rule, CitizenProfile(resident_state="gujarat"))
    assert result.value is False


def test_catalog_fixtures_have_hash_valid_sources():
    catalog = SchemeCatalog.from_json()
    assert len(catalog.all()) >= 2
    for scheme in catalog.all():
        assert scheme.sources
        assert len(scheme.sources[0].evidence_sha256) == 64


def test_active_rule_requires_audit_trail():
    base = {
        "scheme_id": "test-scheme", "name": "Test Scheme", "department": "Test Department",
        "summary": "A valid summary of at least ten characters.",
        "eligibility_rule": {"op": "eq", "field": "bpl", "value": True},
        "sources": [SchemeCatalog.from_json().all()[0].sources[0].model_dump(mode="json")],
        "rule_status": "active",
    }
    with pytest.raises(ValueError, match="approved_by"):
        Scheme.model_validate(base)


def test_approved_rule_decision_uses_deterministic_rules():
    scheme = next(
        s for s in SchemeCatalog.from_json().all()
        if s.scheme_id == "demo-majhi-ladki-bahin"
    )

    # Synthetic approval metadata for testing the evaluator's decision path.
    # This is not an actual government approval.
    scheme = scheme.model_copy(update={
        "approved_by": "Test Approval Authority",
        "approval_reference": "TEST-APPROVAL-001",
    })

    profile = CitizenProfile(
        age_years=25,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=200000,
        aadhaar_linked_bank_account=True,
    )

    result = evaluate_scheme(scheme, profile)

    assert result.status == EligibilityStatus.ELIGIBLE


def test_missing_field_results_in_needs_information():
    scheme = next(
        s for s in SchemeCatalog.from_json().all()
        if s.scheme_id == "demo-majhi-ladki-bahin"
    )

    # Synthetic approval metadata to test the evaluator's missing-information path.
    # This is not an actual government approval.
    scheme = scheme.model_copy(update={
        "approved_by": "Test Approval Authority",
        "approval_reference": "TEST-APPROVAL-002",
    })

    result = evaluate_scheme(
        scheme,
        CitizenProfile(gender="female", resident_state="Maharashtra"),
    )

    assert result.status == EligibilityStatus.NEEDS_INFORMATION
    assert "age" in result.missing_fields
    assert "annual_family_income" in result.missing_fields


def test_rule_schema_rejects_unapproved_fields():
    with pytest.raises(ValueError, match="Unsupported profile field"):
        RuleNode.model_validate({"op": "eq", "field": "model_dump", "value": "x"})

def test_demo_fixtures_cannot_claim_confirmed_eligibility():
    catalog = SchemeCatalog.from_json()

    profile = CitizenProfile(
        age_years=25,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=200000,
        aadhaar_linked_bank_account=True,
        bpl=True,
        receiving_other_pension=False,
    )

    demo_scheme_ids = [
        "demo-majhi-ladki-bahin",
        "demo-indira-gandhi-old-age-pension",
    ]

    for scheme_id in demo_scheme_ids:
        scheme = catalog.get(scheme_id)
        assert scheme is not None

        result = evaluate_scheme(scheme, profile)

        assert result.status == EligibilityStatus.NEEDS_REVIEW
        assert "demo fixture" in result.reason.lower()

def test_condition_breakdown_identifies_matched_failed_and_unknown():
    scheme = next(
        s for s in SchemeCatalog.from_json().all()
        if s.scheme_id == "demo-majhi-ladki-bahin"
    )

    # Synthetic metadata for testing only.
    scheme = scheme.model_copy(update={
        "approved_by": "Test Approval Authority",
        "approval_reference": "TEST-APPROVAL-003",
    })

    profile = CitizenProfile(
        age_years=25,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=300000,
    )

    result = evaluate_scheme(scheme, profile)

    assert result.status == EligibilityStatus.INELIGIBLE

    assert any(
        "gender" in item for item in result.matched_conditions
    )

    assert any(
        "annual_family_income" in item for item in result.failed_conditions
    )

    assert any(
        "aadhaar_linked_bank_account" in item
        for item in result.unknown_conditions
    )

def test_any_passes_when_one_alternative_matches():
    rule = RuleNode.model_validate({
        "op": "any",
        "children": [
            {"op": "eq", "field": "gender", "value": "female"},
            {"op": "eq", "field": "bpl", "value": True},
        ],
    })

    result = evaluate_node(
        rule,
        CitizenProfile(gender="male", bpl=True),
    )

    assert result.value is True

def test_not_reverses_a_condition():
    rule = RuleNode.model_validate({
        "op": "not",
        "children": [
            {"op": "eq", "field": "receiving_other_pension", "value": True},
        ],
    })

    result = evaluate_node(
        rule,
        CitizenProfile(receiving_other_pension=False),
    )

    assert result.value is True

def test_not_does_not_convert_missing_information_to_true():
    rule = RuleNode.model_validate({
        "op": "not",
        "children": [
            {"op": "eq", "field": "bpl", "value": True},
        ],
    })

    result = evaluate_node(rule, CitizenProfile())

    assert result.value is None
    assert result.missing_fields == ("bpl",)

def test_condition_tree_preserves_any_group_result():
    scheme = SchemeCatalog.from_json().all()[0]

    scheme = scheme.model_copy(update={
        "eligibility_rule": RuleNode.model_validate({
            "op": "any",
            "children": [
                {"op": "eq", "field": "gender", "value": "female"},
                {"op": "eq", "field": "bpl", "value": True},
            ],
        }),
        "approved_by": "Test Approval Authority",
        "approval_reference": "TEST-APPROVAL-004",
    })

    result = evaluate_scheme(
        scheme,
        CitizenProfile(gender="male", bpl=True),
    )

    tree = result.condition_tree

    assert tree is not None
    assert tree.operator == "any"
    assert tree.result == "matched"
    assert tree.children[0].result == "failed"
    assert tree.children[1].result == "matched"

def test_condition_tree_preserves_not_group_result():
    scheme = SchemeCatalog.from_json().all()[0]

    scheme = scheme.model_copy(update={
        "eligibility_rule": RuleNode.model_validate({
            "op": "not",
            "children": [
                {
                    "op": "eq",
                    "field": "receiving_other_pension",
                    "value": True,
                },
            ],
        }),
        "approved_by": "Test Approval Authority",
        "approval_reference": "TEST-APPROVAL-005",
    })

    result = evaluate_scheme(
        scheme,
        CitizenProfile(receiving_other_pension=False),
    )

    tree = result.condition_tree

    assert tree is not None
    assert tree.operator == "not"
    assert tree.result == "matched"
    assert tree.children[0].result == "failed"