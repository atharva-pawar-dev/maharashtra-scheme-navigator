from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.domain.models import Language, RuleNode, Scheme, SourceReference
from scheme_navigator.services.trust import (
    SchemeTrustReport,
    SchemeTrustStatus,
    determine_trust_status,
    generate_trust_report,
)


def _make_dummy_scheme(
    scheme_id: str = "test-scheme",
    rule_status: str = "draft",
    publication_authorized: bool = False,
    sources: list[SourceReference] | None = None,
    evidence: list[dict] | None = None,
    approved_by: str | None = None,
    approval_reference: str | None = None,
    last_verified_at: datetime | None = None,
) -> Scheme:
    from hashlib import sha256
    excerpt = "Test excerpt must be at least 12 characters"
    correct_hash = sha256(excerpt.encode("utf-8")).hexdigest()
    default_sources = [
        SourceReference(
            source_name="Maharashtra Government Resolution No. XYZ",
            source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/20240628.pdf",
            source_kind="government_resolution",
            retrieved_at=datetime(2024, 7, 1, tzinfo=timezone.utc),
            evidence_excerpt=excerpt,
            evidence_sha256=correct_hash,
            page_or_section="Para 1",
        )
    ]

    return Scheme(
        scheme_id=scheme_id,
        name="Test Welfare Scheme",
        department="Social Justice Department",
        summary="A test scheme summary description for validation.",
        benefits=["Financial grant of Rs. 1000"],
        required_documents=["Aadhaar Card"],
        eligibility_rule=RuleNode(
            op="eq",
            field="resident_state",
            value="maharashtra",
            condition_id="c_res",
        ),
        sources=sources or default_sources,
        rule_version="1.0.0",
        rule_status=rule_status,
        publication_authorized=publication_authorized,
        approved_by=approved_by,
        approval_reference=approval_reference,
        last_verified_at=last_verified_at,
        evidence=evidence or [],
    )


def test_determine_trust_status_lifecycle():
    # 1. Source verified draft
    s1 = _make_dummy_scheme(scheme_id="test-draft-verified", rule_status="draft")
    assert determine_trust_status(s1) == SchemeTrustStatus.SOURCE_VERIFIED

    # 2. Internally reviewed
    s2 = _make_dummy_scheme(scheme_id="test-reviewed", rule_status="reviewed")
    assert determine_trust_status(s2) == SchemeTrustStatus.INTERNALLY_REVIEWED

    # 3. Publication authorised but not active
    s3 = _make_dummy_scheme(
        scheme_id="test-auth",
        rule_status="reviewed",
        publication_authorized=True,
    )
    assert determine_trust_status(s3) == SchemeTrustStatus.PUBLICATION_AUTHORIZED

    # 4. Retired / expired
    s4 = _make_dummy_scheme(scheme_id="test-retired", rule_status="retired")
    assert determine_trust_status(s4) == SchemeTrustStatus.EXPIRED_OR_SUPERSEDED

    # 5. Demo scheme fixture treated as active for demo evaluation
    s5 = _make_dummy_scheme(
        scheme_id="demo-test",
        rule_status="active",
        approved_by="local_demo_fixture_only",
        approval_reference="demo-fixture-2026",
        last_verified_at=datetime.now(timezone.utc),
    )
    assert determine_trust_status(s5) == SchemeTrustStatus.ACTIVE


def test_candidate_schemes_trust_status_strictly_unauthorized():
    candidates_path = Path(__file__).resolve().parent.parent / "data" / "candidates"
    candidate_files = list(candidates_path.glob("*.json"))
    assert len(candidate_files) >= 7

    for cfile in candidate_files:
        if cfile.name == "candidate_schemes.json":
            continue
        data = json.loads(cfile.read_text(encoding="utf-8"))
        scheme = Scheme.model_validate(data)

        # Invariant: candidate schemes must never be active or authorized
        assert scheme.publication_authorized is False
        assert scheme.rule_status != "active"

        status = determine_trust_status(scheme)
        assert status in {
            SchemeTrustStatus.DRAFT_CANDIDATE,
            SchemeTrustStatus.UNDER_REVIEW,
            SchemeTrustStatus.SOURCE_VERIFIED,
            SchemeTrustStatus.INTERNALLY_REVIEWED,
        }
        assert status != SchemeTrustStatus.ACTIVE
        assert status != SchemeTrustStatus.PUBLICATION_AUTHORIZED


def test_generate_trust_report_multilingual():
    scheme = _make_dummy_scheme(
        scheme_id="test-report",
        rule_status="draft",
        last_verified_at=datetime(2024, 7, 12, 12, 0, tzinfo=timezone.utc),
    )

    # English
    rep_en = generate_trust_report(scheme, language=Language.EN)
    assert rep_en.trust_status == SchemeTrustStatus.SOURCE_VERIFIED
    assert "Source verified" in rep_en.badge_label
    assert rep_en.is_official_government_recommendation is False
    assert "preliminary eligibility assistance" in rep_en.trust_notice
    assert "2024-07-12" in (rep_en.last_verified_at or "")
    assert len(rep_en.official_sources) == 1
    assert rep_en.official_sources[0].source_url.startswith("https://")

    # Marathi
    rep_mr = generate_trust_report(scheme, language=Language.MR)
    assert "अधिकृत स्रोत पडताळित" in rep_mr.badge_label
    assert rep_mr.is_official_government_recommendation is False
    assert "स्कीम नेव्हिगेटर" in rep_mr.trust_notice
    assert "शासकीय मंजुरी" in rep_mr.trust_notice

    # Hindi
    rep_hi = generate_trust_report(scheme, language=Language.HI)
    assert "आधिकारिक स्रोत सत्यापित" in rep_hi.badge_label
    assert rep_hi.is_official_government_recommendation is False
    assert "स्कीम नेविगेटर" in rep_hi.trust_notice
    assert "सरकारी स्वीकृति" in rep_hi.trust_notice


def test_trust_api_endpoints():
    client = TestClient(app)

    # 1. Test get all trust reports
    resp_all = client.get("/schemes/trust/all?language=en")
    assert resp_all.status_code == 200
    reports = resp_all.json()
    assert isinstance(reports, list)
    if reports:
        first = reports[0]
        assert "scheme_id" in first
        assert "trust_status" in first
        assert "badge_label" in first
        assert first["is_official_government_recommendation"] is False
        assert "trust_notice" in first

    # 2. Test get single scheme trust report
    if reports:
        target_id = reports[0]["scheme_id"]
        resp_single = client.get(f"/schemes/{target_id}/trust?language=mr")
        assert resp_single.status_code == 200
        single_rep = resp_single.json()
        assert single_rep["scheme_id"] == target_id
        assert single_rep["is_official_government_recommendation"] is False
        assert len(single_rep["trust_notice"]) > 20

    # 3. Test non-existent scheme returns 404
    resp_404 = client.get("/schemes/non-existent-scheme-9999/trust")
    assert resp_404.status_code == 404
