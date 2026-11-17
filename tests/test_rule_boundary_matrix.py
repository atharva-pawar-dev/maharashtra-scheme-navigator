from __future__ import annotations

from datetime import date, datetime, timezone
import pytest
from pydantic import ValidationError

from scheme_navigator.domain.evidence import (
    LegalApprovalMetadata,
    MultilingualText,
    OfficialSourceType,
    RuleEvidence,
    RuleVerificationStatus,
    validate_rule_evidence_coverage,
)
from scheme_navigator.domain.models import (
    CitizenProfile,
    EligibilityStatus,
    RuleNode,
    Scheme,
)
from scheme_navigator.services.catalog import SchemeCatalog
from scheme_navigator.services.rule_engine import (
    evaluate_node,
    evaluate_scheme,
    has_non_demo_approval_metadata,
)


# ============================================================================
# 1. Exact Age Boundaries
# ============================================================================

def test_age_exact_minimum_boundary_eligible():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21})
    profile_21 = CitizenProfile(age_years=21)
    assert evaluate_node(rule, profile_21).value is True


def test_age_below_minimum_boundary_ineligible():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21})
    profile_20 = CitizenProfile(age_years=20)
    assert evaluate_node(rule, profile_20).value is False


def test_age_exact_maximum_boundary_eligible():
    rule = RuleNode.model_validate({"op": "lte", "field": "age", "value": 65})
    profile_65 = CitizenProfile(age_years=65)
    assert evaluate_node(rule, profile_65).value is True


def test_age_above_maximum_boundary_ineligible():
    rule = RuleNode.model_validate({"op": "lte", "field": "age", "value": 65})
    profile_66 = CitizenProfile(age_years=66)
    assert evaluate_node(rule, profile_66).value is False


def test_age_composite_range_matrix():
    rule = RuleNode.model_validate({
        "op": "all",
        "children": [
            {"op": "gte", "field": "age", "value": 21},
            {"op": "lte", "field": "age", "value": 65},
        ],
    })
    assert evaluate_node(rule, CitizenProfile(age_years=20)).value is False
    assert evaluate_node(rule, CitizenProfile(age_years=21)).value is True
    assert evaluate_node(rule, CitizenProfile(age_years=40)).value is True
    assert evaluate_node(rule, CitizenProfile(age_years=65)).value is True
    assert evaluate_node(rule, CitizenProfile(age_years=66)).value is False


# ============================================================================
# 2. Income Boundaries
# ============================================================================

def test_income_exact_threshold_eligible():
    rule = RuleNode.model_validate({"op": "lte", "field": "annual_family_income", "value": 250000})
    profile_250k = CitizenProfile(annual_family_income=250000)
    assert evaluate_node(rule, profile_250k).value is True


def test_income_threshold_plus_one_ineligible():
    rule = RuleNode.model_validate({"op": "lte", "field": "annual_family_income", "value": 250000})
    profile_250k_plus_1 = CitizenProfile(annual_family_income=250001)
    assert evaluate_node(rule, profile_250k_plus_1).value is False


def test_income_threshold_minus_one_eligible():
    rule = RuleNode.model_validate({"op": "lte", "field": "annual_family_income", "value": 250000})
    profile_249k = CitizenProfile(annual_family_income=249999)
    assert evaluate_node(rule, profile_249k).value is True


def test_income_zero_eligible():
    rule = RuleNode.model_validate({"op": "lte", "field": "annual_family_income", "value": 250000})
    profile_0 = CitizenProfile(annual_family_income=0)
    assert evaluate_node(rule, profile_0).value is True


def test_income_negative_rejected_by_model():
    with pytest.raises(ValidationError):
        CitizenProfile(annual_family_income=-1)


# ============================================================================
# 3. Missing vs False Information (Three-Valued Logic)
# ============================================================================

@pytest.mark.parametrize(
    "gender,expected_val,expected_missing",
    [
        ("female", True, ()),
        ("male", False, ()),
        (None, None, ("gender",)),
    ],
)
def test_three_valued_condition_outcomes(gender, expected_val, expected_missing):
    rule = RuleNode.model_validate({"op": "eq", "field": "gender", "value": "female"})
    profile = CitizenProfile(gender=gender)
    res = evaluate_node(rule, profile)
    assert res.value is expected_val
    assert res.missing_fields == expected_missing


def test_three_valued_all_short_circuit_false_with_unknown():
    # If any child is False, overall 'all' is False, even if other children are Unknown.
    rule = RuleNode.model_validate({
        "op": "all",
        "children": [
            {"op": "eq", "field": "gender", "value": "female"},
            {"op": "gte", "field": "annual_family_income", "value": 100000},
        ],
    })
    # male (False) and income=None (Unknown) -> False
    profile = CitizenProfile(gender="male", annual_family_income=None)
    res = evaluate_node(rule, profile)
    assert res.value is False


def test_three_valued_all_with_true_and_unknown():
    # If no child is False, but at least one child is Unknown, overall 'all' is Unknown.
    rule = RuleNode.model_validate({
        "op": "all",
        "children": [
            {"op": "eq", "field": "gender", "value": "female"},
            {"op": "gte", "field": "annual_family_income", "value": 100000},
        ],
    })
    # female (True) and income=None (Unknown) -> None
    profile = CitizenProfile(gender="female", annual_family_income=None)
    res = evaluate_node(rule, profile)
    assert res.value is None
    assert "annual_family_income" in res.missing_fields


def test_three_valued_any_short_circuit_true_with_unknown():
    # If any child is True, overall 'any' is True, and missing_fields is empty.
    rule = RuleNode.model_validate({
        "op": "any",
        "children": [
            {"op": "eq", "field": "gender", "value": "female"},
            {"op": "gte", "field": "annual_family_income", "value": 100000},
        ],
    })
    # female (True) and income=None (Unknown) -> True
    profile = CitizenProfile(gender="female", annual_family_income=None)
    res = evaluate_node(rule, profile)
    assert res.value is True
    assert res.missing_fields == ()


def test_three_valued_any_all_unknown():
    # If all children of 'any' are Unknown, overall is Unknown.
    rule = RuleNode.model_validate({
        "op": "any",
        "children": [
            {"op": "eq", "field": "gender", "value": "female"},
            {"op": "gte", "field": "annual_family_income", "value": 100000},
        ],
    })
    profile = CitizenProfile()
    res = evaluate_node(rule, profile)
    assert res.value is None
    assert set(res.missing_fields) == {"gender", "annual_family_income"}


def test_three_valued_not_operator():
    rule = RuleNode.model_validate({
        "op": "not",
        "children": [{"op": "eq", "field": "bpl", "value": True}],
    })
    assert evaluate_node(rule, CitizenProfile(bpl=True)).value is False
    assert evaluate_node(rule, CitizenProfile(bpl=False)).value is True
    res_none = evaluate_node(rule, CitizenProfile(bpl=None))
    assert res_none.value is None
    assert res_none.missing_fields == ("bpl",)


# ============================================================================
# 4. Cut-Off Date Evaluation
# ============================================================================

def test_temporal_dob_boundary_on_cut_off_date():
    # Scheme requires age >= 21 as of July 1, 2024
    ref_date = date(2024, 7, 1)
    rule = RuleNode.model_validate({
        "op": "gte",
        "field": "age",
        "value": 21,
        "as_of_date": ref_date,
    })

    # Born 2003-07-01 -> Turns 21 exactly on 2024-07-01 -> Eligible
    profile_eligible = CitizenProfile(date_of_birth=date(2003, 7, 1))
    assert evaluate_node(rule, profile_eligible).value is True

    # Born 2003-07-02 -> One day short of 21 on 2024-07-01 -> Ineligible
    profile_ineligible = CitizenProfile(date_of_birth=date(2003, 7, 2))
    assert evaluate_node(rule, profile_ineligible).value is False


def test_temporal_dob_evaluated_on_different_reference_dates():
    profile = CitizenProfile(date_of_birth=date(2003, 7, 1))
    rule_cut_off_june30 = RuleNode.model_validate({
        "op": "gte",
        "field": "age",
        "value": 21,
        "as_of_date": date(2024, 6, 30),
    })
    rule_cut_off_july01 = RuleNode.model_validate({
        "op": "gte",
        "field": "age",
        "value": 21,
        "as_of_date": date(2024, 7, 1),
    })
    assert evaluate_node(rule_cut_off_june30, profile).value is False
    assert evaluate_node(rule_cut_off_july01, profile).value is True


def test_temporal_requires_dob_when_cutoff_date_used_and_only_age_years_provided():
    # Citizen provided age_years=21, but no DOB
    profile_no_dob = CitizenProfile(age_years=21)
    ref_date = date(2024, 7, 1)
    rule = RuleNode.model_validate({
        "op": "gte",
        "field": "age",
        "value": 21,
        "as_of_date": ref_date,
    })
    # Since cut-off date is not today, age cannot be accurately determined from age_years alone
    res = evaluate_node(rule, profile_no_dob)
    assert res.value is None
    assert "date_of_birth" in res.missing_fields


def test_scheme_level_eligibility_reference_date_inheritance():
    ref_date = date(2024, 7, 1)
    source = SchemeCatalog.from_json().all()[0].sources[0]
    scheme = Scheme(
        scheme_id="test-temporal-scheme",
        name="Temporal Test Scheme",
        department="Test Dept",
        summary="Testing reference date inheritance from scheme.",
        eligibility_rule=RuleNode.model_validate({"op": "gte", "field": "age", "value": 21}),
        sources=[source],
        eligibility_reference_date=ref_date,
    )
    # Citizen born 2003-07-02 is 20 as of 2024-07-01
    profile = CitizenProfile(date_of_birth=date(2003, 7, 2))
    result = evaluate_scheme(scheme, profile)
    # The condition "age must be at least 21" should be in failed_conditions
    assert any("age must be at least 21" in cond for cond in result.failed_conditions)


# ============================================================================
# 5. Evidence Coverage Validation
# ============================================================================

def test_evidence_coverage_100_percent():
    rule = RuleNode.model_validate({
        "op": "all",
        "children": [
            {"op": "gte", "field": "age", "value": 21, "condition_id": "c_age_min"},
            {"op": "eq", "field": "gender", "value": "female", "condition_id": "c_gender"},
        ],
    })
    ev1 = RuleEvidence(
        condition_id="c_age_min",
        source_title="Govt Resolution WCD-2024",
        official_reference="GR-2024/CR-101",
        official_source_url="https://maharashtra.gov.in/gr-1.pdf",
        source_type=OfficialSourceType.GOVERNMENT_RESOLUTION,
        effective_from=date(2024, 7, 1),
        verbatim_excerpt="किमान वय २१ वर्षे पूर्ण असावे.",
        page_or_section="पृष्ठ ३, परिच्छेद २",
        source_document_sha256="a" * 64,
        verification_status=RuleVerificationStatus.LEGAL_APPROVED,
        verified_by="Advocate Patil",
        verification_timestamp=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
    )
    ev2 = RuleEvidence(
        condition_id="c_gender",
        source_title="Govt Resolution WCD-2024",
        official_reference="GR-2024/CR-101",
        official_source_url="https://maharashtra.gov.in/gr-1.pdf",
        source_type=OfficialSourceType.GOVERNMENT_RESOLUTION,
        effective_from=date(2024, 7, 1),
        verbatim_excerpt="फक्त महिलांसाठी.",
        page_or_section="पृष्ठ २, परिच्छेद १",
        source_document_sha256="a" * 64,
        verification_status=RuleVerificationStatus.LEGAL_APPROVED,
        verified_by="Advocate Patil",
        verification_timestamp=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
    )
    report = validate_rule_evidence_coverage(rule, [ev1, ev2])
    assert report.is_valid is True
    assert report.missing_evidence_ids == []
    assert report.orphan_evidence_ids == []
    assert report.coverage_ratio == 1.0


def test_evidence_coverage_missing_evidence():
    rule = RuleNode.model_validate({
        "op": "all",
        "children": [
            {"op": "gte", "field": "age", "value": 21, "condition_id": "c_age_min"},
            {"op": "eq", "field": "gender", "value": "female", "condition_id": "c_gender"},
        ],
    })
    ev1 = RuleEvidence(
        condition_id="c_age_min",
        source_title="Govt Resolution WCD-2024",
        official_reference="GR-2024/CR-101",
        official_source_url="https://maharashtra.gov.in/gr-1.pdf",
        effective_from=date(2024, 7, 1),
        verbatim_excerpt="वय २१ वर्षे.",
        source_document_sha256="a" * 64,
        verification_status=RuleVerificationStatus.LEGAL_APPROVED,
        verified_by="Advocate Patil",
        verification_timestamp=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
    )
    report = validate_rule_evidence_coverage(rule, [ev1])
    assert report.is_valid is False
    assert report.missing_evidence_ids == ["c_gender"]
    assert report.coverage_ratio == 0.5


def test_evidence_coverage_duplicate_ast_condition_ids():
    rule = RuleNode.model_validate({
        "op": "all",
        "children": [
            {"op": "gte", "field": "age", "value": 21, "condition_id": "c_dup"},
            {"op": "lte", "field": "age", "value": 65, "condition_id": "c_dup"},
        ],
    })
    ev = RuleEvidence(
        condition_id="c_dup",
        source_title="Govt Resolution WCD-2024",
        official_reference="GR-2024/CR-101",
        official_source_url="https://maharashtra.gov.in/gr-1.pdf",
        effective_from=date(2024, 7, 1),
        verbatim_excerpt="वय २१ ते ६५ वर्षे.",
        source_document_sha256="a" * 64,
        verification_status=RuleVerificationStatus.LEGAL_APPROVED,
        verified_by="Advocate Patil",
        verification_timestamp=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
    )
    report = validate_rule_evidence_coverage(rule, [ev])
    assert report.is_valid is False
    assert "c_dup" in report.duplicate_ast_condition_ids


def test_evidence_coverage_orphan_evidence():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21, "condition_id": "c_age_min"})
    ev1 = RuleEvidence(
        condition_id="c_age_min",
        source_title="Govt Resolution WCD-2024",
        official_reference="GR-2024/CR-101",
        official_source_url="https://maharashtra.gov.in/gr-1.pdf",
        effective_from=date(2024, 7, 1),
        verbatim_excerpt="वय २१ वर्षे.",
        source_document_sha256="a" * 64,
        verification_status=RuleVerificationStatus.LEGAL_APPROVED,
        verified_by="Advocate Patil",
        verification_timestamp=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
    )
    ev_orphan = RuleEvidence(
        condition_id="c_nonexistent",
        source_title="Govt Resolution WCD-2024",
        official_reference="GR-2024/CR-101",
        official_source_url="https://maharashtra.gov.in/gr-1.pdf",
        effective_from=date(2024, 7, 1),
        verbatim_excerpt="अनाथ पुरावा",
        source_document_sha256="a" * 64,
        verification_status=RuleVerificationStatus.LEGAL_APPROVED,
        verified_by="Advocate Patil",
        verification_timestamp=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
    )
    report = validate_rule_evidence_coverage(rule, [ev1, ev_orphan])
    assert report.is_valid is False
    assert report.orphan_evidence_ids == ["c_nonexistent"]


def test_active_scheme_with_incomplete_evidence_raises():
    source = SchemeCatalog.from_json().all()[0].sources[0]
    rule = RuleNode.model_validate({
        "op": "all",
        "children": [
            {"op": "gte", "field": "age", "value": 21, "condition_id": "c_age_min"},
            {"op": "eq", "field": "gender", "value": "female", "condition_id": "c_gender"},
        ],
    })
    ev1 = RuleEvidence(
        condition_id="c_age_min",
        source_title="Govt Resolution WCD-2024",
        official_reference="GR-2024/CR-101",
        official_source_url="https://maharashtra.gov.in/gr-1.pdf",
        effective_from=date(2024, 7, 1),
        verbatim_excerpt="वय २१ वर्षे.",
        source_document_sha256="a" * 64,
        verification_status=RuleVerificationStatus.LEGAL_APPROVED,
        verified_by="Advocate Patil",
        verification_timestamp=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
    )
    with pytest.raises(ValueError, match="Evidence validation failed"):
        Scheme(
            scheme_id="test-incomplete-evidence-scheme",
            name="Incomplete Evidence Test Scheme",
            department="Test Dept",
            summary="Testing active scheme validation with incomplete evidence.",
            eligibility_rule=rule,
            sources=[source],
            evidence=[ev1],
            rule_status="active",
            approved_by="Actual Legal Authority",
            approval_reference="LEGAL-APP-2024-99",
            last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        )


def test_legal_approval_metadata_rejects_placeholder_approvers():
    with pytest.raises(ValueError, match="Demo or synthetic references cannot constitute legal approval"):
        LegalApprovalMetadata(
            reviewer_id="Demo Approver",
            reviewer_role="gazetted_officer",
            approval_reference="APP-2024-9999",
            gazette_or_notification_reference="MAH-GAZ-2024-001",
            approval_timestamp=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
            verification_checklist_confirmed=True,
        )


def test_rule_evidence_rejects_placeholder_reviewer():
    with pytest.raises(ValueError, match="not recognized as a legitimate approving authority"):
        RuleEvidence(
            condition_id="c_age_min",
            source_title="Govt Resolution WCD-2024",
            official_reference="GR-2024/CR-101",
            official_source_url="https://maharashtra.gov.in/gr-1.pdf",
            effective_from=date(2024, 7, 1),
            verbatim_excerpt="किमान वय २१ वर्षे पूर्ण असावे.",
            source_document_sha256="a" * 64,
            verification_status=RuleVerificationStatus.LEGAL_APPROVED,
            verified_by="test_reviewer",
            verification_timestamp=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        )


# ============================================================================
# 6. Demo Fixture Safety
# ============================================================================

def test_demo_schemes_always_return_needs_review():
    catalog = SchemeCatalog.from_json()
    demo_ids = ["demo-majhi-ladki-bahin", "demo-indira-gandhi-old-age-pension"]
    for scheme_id in demo_ids:
        scheme = catalog.get(scheme_id)
        assert scheme is not None
        assert not has_non_demo_approval_metadata(scheme)

        # Profile that otherwise satisfies all rule conditions
        profile = CitizenProfile(
            age_years=30,
            gender="female",
            resident_state="maharashtra",
            annual_family_income=100000,
            receiving_other_pension=False,
            aadhaar_linked_bank_account=True,
            bpl=True,
            has_disability=False,
        )
        res = evaluate_scheme(scheme, profile)
        assert res.status == EligibilityStatus.NEEDS_REVIEW
        assert (
            "demo fixture" in res.reason.lower()
            or "lacks non-demo approval" in res.reason.lower()
        )
