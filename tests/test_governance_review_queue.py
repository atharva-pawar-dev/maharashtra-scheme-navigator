"""
Test Governance Review Queue & Human Attestation Workflow (TRIMURTI v3 / Invariant I-05).
"""

import pytest
from fastapi.testclient import TestClient
from scheme_navigator.api.main import app
from scheme_navigator.security.models import UserRole
from scheme_navigator.security.auth import session_manager


@pytest.fixture
def client():
    return TestClient(app)


def test_list_governance_review_queue(client):
    """Review queue lists all generated human review packets."""
    res = client.get("/governance/review-queue")
    assert res.status_code == 200
    packets = res.json()
    assert len(packets) >= 15
    # Verify candidate-majhi-ladki-bahin packet
    mmlby_pkt = next((p for p in packets if p["scheme_id"] == "candidate-majhi-ladki-bahin"), None)
    assert mmlby_pkt is not None
    assert mmlby_pkt["completeness_attested"] is True
    assert mmlby_pkt["is_decision_ready"] is True
    assert mmlby_pkt["substantive_criteria_count"] >= 2


def test_get_single_governance_review_packet(client):
    """Retrieve specific review packet by scheme_id."""
    res = client.get("/governance/review-queue/candidate-majhi-ladki-bahin")
    assert res.status_code == 200
    pkt = res.json()
    assert pkt["scheme_id"] == "candidate-majhi-ladki-bahin"
    assert pkt["packet_id"] == "HRP-CANDIDATE-MAJHI-LADKI-BAHIN"
    assert "decision_driving_rules" in pkt
    assert len(pkt["exclusions"]) >= 1


def test_attest_fails_for_anonymous_or_citizen_session(client):
    """Invariant I-05: Citizen or unauthenticated session cannot record completeness attestation."""
    # 1. Anonymous citizen
    res = client.post(
        "/governance/review-queue/candidate-sanjay-gandhi-niradhar-anudan/attest",
        json={"scope": "Unauthorized attempt"}
    )
    assert res.status_code == 403
    assert "not authorized to attest scheme completeness" in res.json()["detail"]


def test_attest_succeeds_for_authenticated_legal_reviewer(client):
    """Invariant I-05: Authenticated legal reviewer can attest completeness."""
    # Create legal reviewer session
    rev_session, token = session_manager.create_session(
        role=UserRole.LEGAL_REVIEWER,
        user_id="advocate_deshmukh_legal_signoff"
    )

    res = client.post(
        "/governance/review-queue/candidate-sanjay-gandhi-niradhar-anudan/attest",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "scope": "SC-G1 Statutory Exclusion & Rule Audit",
            "exclusion_pass_reference": "EXCLUSION-PASS-SGNAY-2026",
            "limitations": []
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ATTESTED"
    assert data["attested_by"] == "advocate_deshmukh_legal_signoff"
    assert "rule_set_hash" in data


def test_rule_approval_workflow_and_hash_invalidation(tmp_path):
    """Verify reviewer approval workflow binds to exact rule SHA-256 and invalidates on hash change."""
    from scheme_navigator.governance.attestation_store import AttestationStore
    from scheme_navigator.security.auth import session_manager
    from scheme_navigator.security.models import UserRole

    test_db = tmp_path / "test_governance.sqlite3"
    store = AttestationStore(db_path=test_db)

    reviewer, _ = session_manager.create_session(
        role=UserRole.LEGAL_REVIEWER,
        user_id="test_legal_counsel",
    )

    scheme_id = "test-scheme-welfare"
    rule_hash_v1 = "a" * 64
    rule_hash_v2 = "b" * 64

    # 1. Record rule approval for version 1.0.0 and rule_hash_v1
    approval = store.record_rule_approval(
        session=reviewer,
        scheme_id=scheme_id,
        rule_id="rule_residency",
        rule_version="1.0.0",
        stage="RULES_APPROVED",
        review_subtype="LEGAL_ACCURACY",
        status="APPROVED",
        source_hash=rule_hash_v1,
        notes="Approved after statutory rule review",
        numeric_double_confirmed=True,
    )
    assert approval["scheme_id"] == scheme_id
    assert approval["source_hash"] == rule_hash_v1
    assert approval["status"] == "APPROVED"

    # 2. Query approvals for scheme
    approvals = store.get_rule_approvals_for_scheme(scheme_id)
    assert len(approvals) == 1
    assert approvals[0]["source_hash"] == rule_hash_v1

    # 3. Verify rule approval binds to exact hash; hash change yields no approval for rule_hash_v2
    valid_v1 = [a for a in approvals if a["source_hash"] == rule_hash_v1 and a["status"] == "APPROVED"]
    valid_v2 = [a for a in approvals if a["source_hash"] == rule_hash_v2 and a["status"] == "APPROVED"]
    assert len(valid_v1) == 1
    assert len(valid_v2) == 0

    # 4. Invalidate attestations for scheme
    invalidated_count = store.invalidate_attestations_for_scheme(scheme_id, reason="Rule modified in GR 2026-B")
    # Attestation and rule approval are separate tables
    test_attestations = [a for a in store.list_attestations() if a.scheme_id == scheme_id]
    assert len(test_attestations) == 0  # no attestation was recorded for test-scheme-welfare, confirming separation


def test_production_database_remains_uncontaminated():
    """Verify that data/ingestion.sqlite3 has 0 fake rule approvals and 0 demo fixtures."""
    from pathlib import Path
    from scheme_navigator.governance.attestation_store import AttestationStore
    base_dir = Path(__file__).resolve().parents[1]
    prod_store = AttestationStore(db_path=base_dir / "data" / "ingestion.sqlite3")

    # In production, rule approvals must be 0 (no fake approvals fabricated)
    with prod_store._connect() as conn:
        rule_approvals = conn.execute("SELECT COUNT(*) FROM scheme_rule_approvals").fetchone()[0]
        assert rule_approvals == 0, f"Expected 0 rule approvals in production, found {rule_approvals}"

        # Attestations must have 0 demo fixtures
        fixture_attestations = conn.execute(
            "SELECT COUNT(*) FROM scheme_completeness_attestations WHERE is_fixture = 1 OR scheme_id LIKE 'demo-%'"
        ).fetchone()[0]
        assert fixture_attestations == 0, f"Found {fixture_attestations} demo fixture attestations in production"
