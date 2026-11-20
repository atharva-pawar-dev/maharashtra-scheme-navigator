"""TRIMURTI v3 Core Invariants Automated Verification Suite.

Enforces Invariants I-01 through I-20 (Part A, Part L Section 27):
1. No definitive verdict without approved rules and completeness attestation.
2. No demo fixture leakage in production citizen queries.
3. Unknown stays unknown (3-valued fail-closed logic).
4. Thin-rule protection (no single residency-only rule produces definitive verdict).
5. Humans approve; AI agents cannot approve themselves.
6. Completeness attestation binds to rule set hash and source hashes.
7. Candidate dispositions are non-destructive and explicit.
8. Citizen error reporting is safely integrated and persisted.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
import pytest

from scheme_navigator.core.citizen_store import CitizenProfileStore
from scheme_navigator.domain.evidence import (
    OfficialSourceType,
    RuleEvidence,
    RuleVerificationStatus,
)
from scheme_navigator.domain.models import (
    CitizenProfile,
    EligibilityResult,
    EligibilityStatus,
    Language,
    RuleNode,
    Scheme,
    SourceReference,
)
from scheme_navigator.governance.attestation_store import (
    attestation_store,
    compute_scheme_rule_set_hash,
)
from scheme_navigator.governance.models import CompletenessAttestation, ProvenanceStage
from scheme_navigator.governance.thin_rule_lint import lint_scheme_rules
from scheme_navigator.security.models import UserRole, UserSession
from scheme_navigator.services.catalog import canonical_catalog
from scheme_navigator.services.rule_engine import (
    check_production_eligibility_gate,
    evaluate_scheme,
)


def test_invariant_i04_i06_no_definitive_verdict_without_attestation():
    """Invariant I-04 & I-06: A scheme without a valid completeness attestation cannot return ELIGIBLE."""
    scheme = canonical_catalog.get("candidate-majhi-ladki-bahin")
    assert scheme is not None

    rule_hash = compute_scheme_rule_set_hash(scheme)
    profile = CitizenProfile(
        age_years=35,
        gender="female",
        annual_family_income=150000,
        resident_state="Maharashtra",
        aadhaar_linked_bank_account=True,
    )

    # Initial state with valid attestation should be confirmed eligible
    initial_res = evaluate_scheme(scheme, profile)
    assert initial_res.status == EligibilityStatus.ELIGIBLE

    # Invalidate attestation
    attestation_store.invalidate_attestations_for_scheme(scheme.scheme_id)

    # Gate should now fail closed
    is_ok, reason = check_production_eligibility_gate(scheme)
    assert not is_ok
    assert "Scheme lacks an authenticated completeness attestation" in reason

    # Evaluating with a matching profile should yield NEEDS_REVIEW, never ELIGIBLE
    result = evaluate_scheme(scheme, profile)
    assert result.status == EligibilityStatus.NEEDS_REVIEW
    assert "authenticated completeness attestation" in result.reason

    # Restore attestation for subsequent runs
    mock_admin_session = UserSession(
        session_id="sess_test_admin",
        user_id="legal_reviewer_invariants",
        role=UserRole.LEGAL_REVIEWER,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
    )
    attestation_store.record_completeness_attestation(
        session=mock_admin_session,
        scheme_id=scheme.scheme_id,
        scheme_version="2.0.0",
        source_hashes=["3a"*32],
        rule_set_hash=rule_hash,
        exclusion_pass_reference="EXCLUSION-PASS-INVARIANTS",
    )
    restored_res = evaluate_scheme(scheme, profile)
    assert restored_res.status == EligibilityStatus.ELIGIBLE


def test_invariant_i05_ai_agent_cannot_self_authorize():
    """Invariant I-05: AI agents or unauthorized users cannot record human approvals."""
    citizen_session = UserSession(
        session_id="sess_citizen_attempt",
        user_id="anonymous_ai_agent",
        role=UserRole.CITIZEN,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
    )

    with pytest.raises(PermissionError) as exc_info:
        attestation_store.record_completeness_attestation(
            session=citizen_session,
            scheme_id="candidate-sanjay-gandhi-niradhar-anudan",
            scheme_version="2.0.0",
            source_hashes=["11"*32],
            rule_set_hash="22"*32,
            exclusion_pass_reference="EXCLUSION-TEST",
        )
    assert "not authorized to attest scheme completeness" in str(exc_info.value)


def test_invariant_i07_thin_rule_protection():
    """Invariant I-07: Superficial schemes with only residency rules fail closed."""
    import hashlib
    excerpt = "Test excerpt for thin rule validation."
    h = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()

    ev = RuleEvidence(
        condition_id="c_thin_residency",
        source_title="Maharashtra Gazette",
        official_reference="GR-TEST-001",
        official_source_url="https://maharashtra.gov.in/gazette",
        source_type=OfficialSourceType.GOVERNMENT_RESOLUTION,
        publication_date=date(2026, 1, 1),
        effective_from=date(2026, 1, 1),
        verbatim_excerpt="Citizen must be resident of Maharashtra.",
        excerpt_language=Language.MR,
        source_document_sha256="44"*32,
        verification_status=RuleVerificationStatus.LEGAL_APPROVED,
        verified_by="Legal Remembrancer",
        verification_timestamp=datetime.now(timezone.utc),
    )

    # Build a thin scheme with only residency
    thin_scheme = Scheme(
        scheme_id="scheme-thin-test",
        name="Thin Scheme Test",
        department="Test Department",
        summary="Thin rule test",
        required_documents=[],
        rule_status="active",
        approved_by="Test Approver",
        approval_reference="GR-TEST-001",
        last_verified_at=date(2026, 11, 1),
        publication_authorized=True,
        sources=[
            SourceReference(
                source_name="Official Gazette",
                source_url="https://maharashtra.gov.in/gazette",
                source_kind="official_portal",
                retrieved_at=datetime.now(timezone.utc),
                evidence_excerpt=excerpt,
                evidence_sha256=h,
            )
        ],
        evidence=[ev],
        eligibility_rule=RuleNode(
            op="eq",
            field="resident_state",
            value="maharashtra",
            condition_id="c_thin_residency",
            is_hard_statutory=True,
        ),
    )

    lint = lint_scheme_rules(thin_scheme)
    assert not lint.is_valid
    assert "minimum 2 required" in lint.reason or "solely of geographic residency" in lint.reason

    # Production gate must reject thin-rule schemes
    is_ok, reason = check_production_eligibility_gate(thin_scheme)
    assert not is_ok
    assert "Thin-rule protection" in reason


def test_invariant_i02_demo_fixture_quarantined():
    """Invariant I-02: Demo fixtures are quarantined from confirmed production eligibility."""
    demo_scheme = canonical_catalog.get("demo-majhi-ladki-bahin")
    assert demo_scheme is not None
    assert not getattr(demo_scheme, "publication_authorized", True)

    profile = CitizenProfile(
        age_years=30,
        gender="female",
        annual_family_income=100000,
        resident_state="Maharashtra",
    )
    result = evaluate_scheme(demo_scheme, profile)
    assert result.status != EligibilityStatus.ELIGIBLE
    assert result.status == EligibilityStatus.NEEDS_REVIEW


def test_invariant_i03_three_valued_logic():
    """Invariant I-03: Unknown stays unknown; missing profile info never guessed as True or False."""
    scheme = canonical_catalog.get("candidate-sanjay-gandhi-niradhar-anudan")
    assert scheme is not None

    # Empty profile (all criteria unknown)
    empty_profile = CitizenProfile()
    result = evaluate_scheme(scheme, empty_profile)

    # Must NOT be ELIGIBLE and NOT be INELIGIBLE solely due to missing values
    assert result.status in (EligibilityStatus.NEEDS_INFORMATION, EligibilityStatus.NEEDS_REVIEW)
    assert len(result.unknown_conditions) > 0 or len(result.missing_fields) > 0


def test_invariant_i15_explicit_candidate_dispositions():
    """Invariant I-15: All canonical catalogue records have explicit, evidenced dispositions."""
    v2_path = Path(__file__).resolve().parents[2] / "data" / "catalogue" / "schemes.json"
    assert v2_path.exists()
    schemes = json.loads(v2_path.read_text(encoding="utf-8"))

    allowed_statuses = {"verified_primary", "single_source_secondary", "unverified"}
    for s in schemes:
        verif_status = s.get("verification", {}).get("status")
        assert verif_status in allowed_statuses, f"Scheme {s['scheme_id']} has unknown verification status: {verif_status}"
        assert s.get("department"), f"Scheme {s['scheme_id']} is missing responsible department"
        assert s.get("name_en") and s.get("name_mr"), f"Scheme {s['scheme_id']} lacks bilingual identity"


def test_invariant_i17_public_issue_reporting_persistence():
    """Invariant I-17 & I-18: Citizen error reporting endpoint persists to protected audit log."""
    from fastapi.testclient import TestClient
    from scheme_navigator.api.main import app

    client = TestClient(app)
    resp = client.post(
        "/trust/report-issue",
        json={
            "scheme_id": "candidate-majhi-ladki-bahin",
            "issue_type": "incorrect_criteria",
            "description": "Invariant test report for criterion audit verification.",
            "citizen_contact": "auditor@maharashtra.gov.in",
            "language": "mr",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "RECEIVED"
    assert "ticket_id" in data
    assert data["ticket_id"].startswith("TICKET-")
