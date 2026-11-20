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
