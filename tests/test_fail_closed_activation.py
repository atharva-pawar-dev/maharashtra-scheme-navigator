from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from scheme_navigator.domain.evidence import (
    MultilingualText,
    OfficialSourceType,
    RuleEvidence,
    RuleVerificationStatus,
)
from scheme_navigator.domain.models import (
    CitizenProfile,
    EligibilityStatus,
    RuleNode,
    Scheme,
    SourceReference,
)
from scheme_navigator.services.catalog import CatalogLoadError, SchemeCatalog
from scheme_navigator.services.rule_engine import (
    check_production_eligibility_gate,
    evaluate_scheme,
    has_non_demo_approval_metadata,
)


def _make_source() -> SourceReference:
    excerpt = "Official government resolution text for eligibility verification."
    import hashlib
    sha = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
    return SourceReference(
        source_name="Maharashtra Government Resolution",
        source_url="https://maharashtra.gov.in/gr/2024-001.pdf",
        source_kind="government_resolution",
        retrieved_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        evidence_excerpt=excerpt,
        evidence_sha256=sha,
    )


def _make_valid_evidence(
    condition_id: str,
    status: RuleVerificationStatus = RuleVerificationStatus.LEGAL_APPROVED,
    effective_from: date = date(2024, 1, 1),
    effective_until: date | None = None,
) -> RuleEvidence:
    return RuleEvidence(
        condition_id=condition_id,
        source_title="Government Resolution WCD-2024/01",
        official_reference="GR-WCD-2024-001",
        official_source_url="https://maharashtra.gov.in/gr/2024-001.pdf",
        source_type=OfficialSourceType.GOVERNMENT_RESOLUTION,
        effective_from=effective_from,
        effective_until=effective_until,
        verbatim_excerpt="पात्रतेची अधिकृत अट स्पष्ट करणारा शासकीय निर्णय परिच्छेद.",
        source_document_sha256="b" * 64,
        verification_status=status,
        verified_by="Advocate Deshmukh",
        verification_timestamp=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
    )


# ============================================================================
# PART 1: Strict Model-Level Validation for Active Non-Demo Schemes
# ============================================================================

def test_active_scheme_with_empty_evidence_raises():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"})
    with pytest.raises(ValueError, match="Active non-demo schemes require a non-empty evidence list"):
        Scheme(
            scheme_id="maha-farmer-grant",
            name="Maharashtra Farmer Grant",
            department="Agriculture Department",
            summary="Valid summary of sufficient length for the test scheme.",
            eligibility_rule=rule,
            sources=[_make_source()],
            evidence=[],
            rule_status="active",
            approved_by="Department Secretary",
            approval_reference="AGR-2024-01",
            last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        )


def test_active_scheme_with_missing_condition_ids_raises():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21})  # No condition_id!
    ev = _make_valid_evidence("c_age")
    with pytest.raises(ValueError, match="Evidence validation failed"):
        Scheme(
            scheme_id="maha-farmer-grant",
            name="Maharashtra Farmer Grant",
            department="Agriculture Department",
            summary="Valid summary of sufficient length for the test scheme.",
            eligibility_rule=rule,
            sources=[_make_source()],
            evidence=[ev],
            rule_status="active",
            approved_by="Department Secretary",
            approval_reference="AGR-2024-01",
            last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        )


def test_active_scheme_with_orphan_evidence_raises():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"})
    ev1 = _make_valid_evidence("c_age")
    ev_orphan = _make_valid_evidence("c_orphan")
    with pytest.raises(ValueError, match="Orphan evidence"):
        Scheme(
            scheme_id="maha-farmer-grant",
            name="Maharashtra Farmer Grant",
            department="Agriculture Department",
            summary="Valid summary of sufficient length for the test scheme.",
            eligibility_rule=rule,
            sources=[_make_source()],
            evidence=[ev1, ev_orphan],
            rule_status="active",
            approved_by="Department Secretary",
            approval_reference="AGR-2024-01",
            last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        )


def test_active_scheme_with_duplicate_ast_condition_ids_raises():
    rule = RuleNode.model_validate({
        "op": "all",
        "children": [
            {"op": "gte", "field": "age", "value": 21, "condition_id": "c_dup"},
            {"op": "lte", "field": "age", "value": 65, "condition_id": "c_dup"},
        ],
    })
    ev = _make_valid_evidence("c_dup")
    with pytest.raises(ValueError, match="Duplicate AST condition IDs"):
        Scheme(
            scheme_id="maha-farmer-grant",
            name="Maharashtra Farmer Grant",
            department="Agriculture Department",
            summary="Valid summary of sufficient length for the test scheme.",
            eligibility_rule=rule,
            sources=[_make_source()],
            evidence=[ev],
            rule_status="active",
            approved_by="Department Secretary",
            approval_reference="AGR-2024-01",
            last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        )


def test_active_scheme_with_extracted_unverified_evidence_raises():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"})
    ev = RuleEvidence(
        condition_id="c_age",
        source_title="Government Resolution WCD-2024/01",
        official_reference="GR-WCD-2024-001",
        official_source_url="https://maharashtra.gov.in/gr/2024-001.pdf",
        source_type=OfficialSourceType.GOVERNMENT_RESOLUTION,
        effective_from=date(2024, 1, 1),
        verbatim_excerpt="पात्रतेची अधिकृत अट स्पष्ट करणारा शासकीय निर्णय परिच्छेद.",
        source_document_sha256="b" * 64,
        verification_status=RuleVerificationStatus.EXTRACTED_UNVERIFIED,
    )
    with pytest.raises(ValueError, match="legal_approved"):
        Scheme(
            scheme_id="maha-farmer-grant",
            name="Maharashtra Farmer Grant",
            department="Agriculture Department",
            summary="Valid summary of sufficient length for the test scheme.",
            eligibility_rule=rule,
            sources=[_make_source()],
            evidence=[ev],
            rule_status="active",
            approved_by="Department Secretary",
            approval_reference="AGR-2024-01",
            last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        )


def test_active_scheme_with_analyst_reviewed_evidence_raises():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"})
    ev = RuleEvidence(
        condition_id="c_age",
        source_title="Government Resolution WCD-2024/01",
        official_reference="GR-WCD-2024-001",
        official_source_url="https://maharashtra.gov.in/gr/2024-001.pdf",
        source_type=OfficialSourceType.GOVERNMENT_RESOLUTION,
        effective_from=date(2024, 1, 1),
        verbatim_excerpt="पात्रतेची अधिकृत अट स्पष्ट करणारा शासकीय निर्णय परिच्छेद.",
        source_document_sha256="b" * 64,
        verification_status=RuleVerificationStatus.ANALYST_REVIEWED,
        verified_by="Policy Analyst Kulkarni",
        verification_timestamp=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
    )
    with pytest.raises(ValueError, match="legal_approved"):
        Scheme(
            scheme_id="maha-farmer-grant",
            name="Maharashtra Farmer Grant",
            department="Agriculture Department",
            summary="Valid summary of sufficient length for the test scheme.",
            eligibility_rule=rule,
            sources=[_make_source()],
            evidence=[ev],
            rule_status="active",
            approved_by="Department Secretary",
            approval_reference="AGR-2024-01",
            last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        )


def test_active_scheme_with_invalid_effective_dates_raises():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"})
    with pytest.raises(ValueError, match="effective_until.*cannot precede.*effective_from"):
        _make_valid_evidence(
            "c_age",
            effective_from=date(2025, 1, 1),
            effective_until=date(2024, 1, 1),  # Expired before start!
        )


def test_active_scheme_rejects_placeholder_approval_metadata():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"})
    ev = _make_valid_evidence("c_age")
    with pytest.raises(ValueError, match="placeholder approval metadata"):
        Scheme(
            scheme_id="maha-farmer-grant",
            name="Maharashtra Farmer Grant",
            department="Agriculture Department",
            summary="Valid summary of sufficient length for the test scheme.",
            eligibility_rule=rule,
            sources=[_make_source()],
            evidence=[ev],
            rule_status="active",
            approved_by="Demo Approver Test",
            approval_reference="AGR-2024-01",
            last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        )


# ============================================================================
# PART 2 & 3: Production Eligibility Gate Enforcement at Runtime
# ============================================================================

def test_legal_approved_evidence_without_trusted_publication_returns_needs_review():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"})
    ev = _make_valid_evidence("c_age")
    scheme = Scheme(
        scheme_id="maha-farmer-grant",
        name="Maharashtra Farmer Grant",
        department="Agriculture Department",
        summary="Valid summary of sufficient length for the test scheme.",
        eligibility_rule=rule,
        sources=[_make_source()],
        evidence=[ev],
        rule_status="active",
        approved_by="Under Secretary Agriculture",
        approval_reference="AGR-2024-LEGAL-01",
        last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        publication_authorized=False,  # Not authorized for publication!
    )
    profile = CitizenProfile(date_of_birth=date(2001, 1, 1), age_years=25)
    result = evaluate_scheme(scheme, profile)
    assert result.status == EligibilityStatus.NEEDS_REVIEW
    assert "trusted publication gate" in result.reason.lower()


def test_scheme_with_expired_effective_dates_returns_needs_review():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"})
    ev = _make_valid_evidence(
        "c_age",
        effective_from=date(2020, 1, 1),
        effective_until=date(2023, 1, 1),  # Expired in 2023
    )
    scheme = Scheme(
        scheme_id="maha-farmer-grant",
        name="Maharashtra Farmer Grant",
        department="Agriculture Department",
        summary="Valid summary of sufficient length for the test scheme.",
        eligibility_rule=rule,
        sources=[_make_source()],
        evidence=[ev],
        rule_status="active",
        approved_by="Under Secretary Agriculture",
        approval_reference="AGR-2024-LEGAL-01",
        last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        publication_authorized=True,
    )
    # Evaluate today (2026): expired!
    profile = CitizenProfile(date_of_birth=date(2001, 1, 1), age_years=25)
    result = evaluate_scheme(scheme, profile)
    assert result.status == EligibilityStatus.NEEDS_REVIEW
    assert "expired" in result.reason.lower()


def test_scheme_with_future_effective_date_returns_needs_review():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"})
    ev = _make_valid_evidence(
        "c_age",
        effective_from=date(2028, 1, 1),  # Future date!
        effective_until=date(2030, 1, 1),
    )
    scheme = Scheme(
        scheme_id="maha-farmer-grant",
        name="Maharashtra Farmer Grant",
        department="Agriculture Department",
        summary="Valid summary of sufficient length for the test scheme.",
        eligibility_rule=rule,
        sources=[_make_source()],
        evidence=[ev],
        rule_status="active",
        approved_by="Under Secretary Agriculture",
        approval_reference="AGR-2024-LEGAL-01",
        last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        publication_authorized=True,
    )
    profile = CitizenProfile(date_of_birth=date(2001, 1, 1), age_years=25)
    result = evaluate_scheme(scheme, profile, reference_date=date(2026, 11, 8))
    assert result.status == EligibilityStatus.NEEDS_REVIEW
    assert "not legally effective until" in result.reason.lower()


def test_authorized_scheme_with_complete_evidence_returns_eligible():
    rule = RuleNode.model_validate({
        "op": "all",
        "children": [
            {"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"},
            {"op": "eq", "field": "resident_state", "value": "maharashtra", "condition_id": "c_state"},
        ],
    })
    ev1 = _make_valid_evidence("c_age", effective_from=date(2024, 1, 1), effective_until=date(2030, 1, 1))
    ev2 = _make_valid_evidence("c_state", effective_from=date(2024, 1, 1), effective_until=date(2030, 1, 1))
    scheme = Scheme(
        scheme_id="maha-farmer-grant",
        name="Maharashtra Farmer Grant",
        department="Agriculture Department",
        summary="Valid summary of sufficient length for the test scheme.",
        eligibility_rule=rule,
        sources=[_make_source()],
        evidence=[ev1, ev2],
        rule_status="active",
        approved_by="Under Secretary Agriculture",
        approval_reference="AGR-2024-LEGAL-01",
        last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        publication_authorized=True,
    )
    profile = CitizenProfile(age_years=25, resident_state="maharashtra")
    result = evaluate_scheme(scheme, profile)
    assert result.status == EligibilityStatus.ELIGIBLE
    assert "verified legal evidence and authorized publication" in result.reason.lower()


# ============================================================================
# PART 4: Catalogue Loading & External JSON Untrusted Input Handling
# ============================================================================

def test_external_json_claiming_active_without_evidence_rejected_on_load(tmp_path: Path):
    source = _make_source().model_dump(mode="json")
    external_data = [{
        "scheme_id": "external-untrusted-scheme",
        "name": "External Untrusted Scheme",
        "department": "External Dept",
        "summary": "External summary of sufficient length for this test.",
        "eligibility_rule": {"op": "gte", "field": "age", "value": 18, "condition_id": "c_age"},
        "sources": [source],
        "rule_status": "active",
        "approved_by": "External Official",
        "approval_reference": "EXT-2024-01",
        "last_verified_at": "2024-07-01T10:00:00Z",
        "evidence": [],
    }]
    cat_file = tmp_path / "external_schemes.json"
    cat_file.write_text(json.dumps(external_data), encoding="utf-8")

    with pytest.raises(CatalogLoadError, match="invalid scheme record"):
        SchemeCatalog.from_json(cat_file)


def test_external_json_with_evidence_cannot_self_authorize_publication(tmp_path: Path):
    source = _make_source().model_dump(mode="json")
    ev = _make_valid_evidence("c_age").model_dump(mode="json")
    external_data = [{
        "scheme_id": "external-untrusted-scheme",
        "name": "External Untrusted Scheme",
        "department": "External Dept",
        "summary": "External summary of sufficient length for this test.",
        "eligibility_rule": {"op": "gte", "field": "age", "value": 18, "condition_id": "c_age"},
        "sources": [source],
        "rule_status": "active",
        "approved_by": "External Official",
        "approval_reference": "EXT-2024-01",
        "last_verified_at": "2024-07-01T10:00:00Z",
        "evidence": [ev],
        "publication_authorized": True,  # Attempting to forge publication authorization!
    }]
    cat_file = tmp_path / "external_schemes.json"
    cat_file.write_text(json.dumps(external_data), encoding="utf-8")

    catalog = SchemeCatalog.from_json(cat_file)
    scheme = catalog.get("external-untrusted-scheme")
    assert scheme is not None
    # Verify that publication_authorized was stripped and marked untrusted
    assert scheme.publication_authorized is False
    assert getattr(scheme, "_untrusted_source", False) is True

    # Matching profile evaluated against this external scheme MUST NOT receive ELIGIBLE!
    profile = CitizenProfile(date_of_birth=date(2001, 1, 1), age_years=25)
    result = evaluate_scheme(scheme, profile)
    assert result.status == EligibilityStatus.NEEDS_REVIEW
    assert "untrusted external source" in result.reason.lower() or "trusted publication" in result.reason.lower()


def test_external_json_overriding_demo_scheme_fails_closed(tmp_path: Path):
    source = _make_source().model_dump(mode="json")
    ev = _make_valid_evidence("c_age").model_dump(mode="json")
    # Attacker tries to override demo-majhi-ladki-bahin via external JSON
    external_data = [{
        "scheme_id": "demo-majhi-ladki-bahin",
        "name": "Malicious Spoofed Demo Scheme",
        "department": "External Dept",
        "summary": "Attempting to hijack demo scheme identifier to bypass gates.",
        "eligibility_rule": {"op": "gte", "field": "age", "value": 18, "condition_id": "c_age"},
        "sources": [source],
        "rule_status": "active",
        "approved_by": "Forged Authority",
        "approval_reference": "FORGE-2024-999",
        "last_verified_at": "2024-07-01T10:00:00Z",
        "evidence": [ev],
        "publication_authorized": True,
    }]
    cat_file = tmp_path / "override_demo.json"
    cat_file.write_text(json.dumps(external_data), encoding="utf-8")

    catalog = SchemeCatalog.from_json(cat_file)
    scheme = catalog.get("demo-majhi-ladki-bahin")
    assert scheme is not None
    assert getattr(scheme, "_untrusted_source", False) is True

    profile = CitizenProfile(date_of_birth=date(2001, 1, 1), age_years=25)
    result = evaluate_scheme(scheme, profile)
    assert result.status == EligibilityStatus.NEEDS_REVIEW


# ============================================================================
# PART 5: Three-Valued Logic & Ineligible/Missing Handling Under Strict Gate
# ============================================================================

def test_ineligible_profile_under_gate_returns_ineligible():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"})
    ev = _make_valid_evidence("c_age")
    scheme = Scheme(
        scheme_id="maha-farmer-grant",
        name="Maharashtra Farmer Grant",
        department="Agriculture Department",
        summary="Valid summary of sufficient length for the test scheme.",
        eligibility_rule=rule,
        sources=[_make_source()],
        evidence=[ev],
        rule_status="active",
        approved_by="Under Secretary Agriculture",
        approval_reference="AGR-2024-LEGAL-01",
        last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        publication_authorized=True,
    )
    profile = CitizenProfile(age_years=18)  # Fails age condition!
    result = evaluate_scheme(scheme, profile)
    assert result.status == EligibilityStatus.INELIGIBLE
    assert result.failed_conditions != []


def test_missing_fields_under_gate_returns_needs_information():
    rule = RuleNode.model_validate({"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"})
    ev = _make_valid_evidence("c_age")
    scheme = Scheme(
        scheme_id="maha-farmer-grant",
        name="Maharashtra Farmer Grant",
        department="Agriculture Department",
        summary="Valid summary of sufficient length for the test scheme.",
        eligibility_rule=rule,
        sources=[_make_source()],
        evidence=[ev],
        rule_status="active",
        approved_by="Under Secretary Agriculture",
        approval_reference="AGR-2024-LEGAL-01",
        last_verified_at=datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        publication_authorized=True,
    )
    profile = CitizenProfile()  # Age is None!
    result = evaluate_scheme(scheme, profile)
    assert result.status == EligibilityStatus.NEEDS_INFORMATION
    assert result.missing_fields == ["age"]
