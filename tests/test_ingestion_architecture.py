from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.ingestion.dedup import detect_scheme_duplicates
from scheme_navigator.ingestion.lineage import get_scheme_lineage, list_registered_lineages
from scheme_navigator.ingestion.models import (
    AmendmentType,
    IngestedSnapshot,
    IngestionReviewItem,
    IngestionReviewStatus,
    IngestionSourceKind,
)
from scheme_navigator.ingestion.pipeline import _check_url, _classify_source_kind
from scheme_navigator.ingestion.store import IngestionStore


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_store(tmp_path: Path) -> IngestionStore:
    db_file = tmp_path / "test_ingestion.sqlite3"
    return IngestionStore(db_path=db_file)


def test_allowlist_and_url_validation():
    # Valid allowlisted hosts
    _check_url("https://gr.maharashtra.gov.in/Site/Upload/GR/202406281814018230.pdf")
    _check_url("https://mahadbt.maharashtra.gov.in/SchemeData/SchemeData?str=abc")
    _check_url("https://myscheme.gov.in/schemes/mmlby")
    _check_url("https://aaplesarkar.mahaonline.gov.in/en/Services/Index")

    # Insecure HTTP must be rejected
    with pytest.raises(ValueError, match="Only HTTPS source URLs are accepted"):
        _check_url("http://gr.maharashtra.gov.in/test.pdf")

    # Non-allowlisted external host must be rejected
    with pytest.raises(ValueError, match="Host is not in the government-source allowlist"):
        _check_url("https://untrusted-blog.com/scheme-details")


def test_classify_source_kind():
    kind_gr, is_agg_gr = _classify_source_kind("https://gr.maharashtra.gov.in/Site/Upload/GR/test.pdf")
    assert kind_gr == IngestionSourceKind.GOVERNMENT_RESOLUTION
    assert not is_agg_gr

    kind_myscheme, is_agg_my = _classify_source_kind("https://myscheme.gov.in/schemes/test")
    assert kind_myscheme == IngestionSourceKind.MYSCHEME_AGGREGATOR
    assert is_agg_my  # Aggregators are marked as discovery pointers, not legal authority

    kind_mahadbt, _ = _classify_source_kind("https://mahadbt.maharashtra.gov.in/SchemeData")
    assert kind_mahadbt == IngestionSourceKind.MAHADBT_SCHEME_PAGE


def test_store_snapshot_and_change_detection(temp_store: IngestionStore):
    url = "https://gr.maharashtra.gov.in/Site/Upload/GR/sample.pdf"

    # Initial snapshot v1
    snap1 = IngestedSnapshot(
        snapshot_id="snap_1111111111111111",
        source_url=url,
        final_url=url,
        source_kind=IngestionSourceKind.GOVERNMENT_RESOLUTION,
        sha256="1" * 64,
        byte_size=1024,
        retrieved_at="2026-11-01T10:00:00Z",
        publication_date="2026-11-01",
        official_reference="SAMPLE-2026-01",
        title="Sample Government Resolution V1",
        extracted_text="Original text of the Government Resolution with initial rules.",
    )
    saved1, chg1 = temp_store.save_snapshot(snap1)
    assert saved1.snapshot_id == "snap_1111111111111111"
    assert chg1 is None  # First retrieval has no prior version

    # Updated snapshot v2 with modified content
    snap2 = IngestedSnapshot(
        snapshot_id="snap_2222222222222222",
        source_url=url,
        final_url=url,
        source_kind=IngestionSourceKind.GOVERNMENT_RESOLUTION,
        sha256="2" * 64,
        byte_size=1080,
        retrieved_at="2026-11-05T12:00:00Z",
        publication_date="2026-11-05",
        official_reference="SAMPLE-2026-02",
        title="Sample Government Resolution V2 (Amended)",
        extracted_text="Amended text with updated eligibility age and assistance rate.",
    )
    saved2, chg2 = temp_store.save_snapshot(snap2)
    assert saved2.snapshot_id == "snap_2222222222222222"
    assert chg2 is not None
    assert chg2.previous_sha256 == "1" * 64
    assert chg2.new_sha256 == "2" * 64
    assert chg2.change_type == "content_updated"
    assert "was modified" in chg2.summary

    # Verify change log list
    changes = temp_store.list_changes(url)
    assert len(changes) == 1
    assert changes[0].change_id == chg2.change_id


def test_human_review_queue_lifecycle(temp_store: IngestionStore):
    item = IngestionReviewItem(
        item_id="rev_sample_001",
        source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/mmlby.pdf",
        source_title="Mukhyamantri Majhi Ladki Bahin Yojana GR",
        source_kind=IngestionSourceKind.GOVERNMENT_RESOLUTION,
        sha256="a" * 64,
        retrieved_at="2026-11-09T08:00:00Z",
        review_status=IngestionReviewStatus.PENDING_REVIEW,
        extracted_scheme_data={"name": "Majhi Ladki Bahin", "income_limit": 250000},
        created_at="2026-11-09T08:00:00Z",
        updated_at="2026-11-09T08:00:00Z",
    )
    temp_store.enqueue_for_review(item)

    # List pending items
    queue = temp_store.list_review_queue(status=IngestionReviewStatus.PENDING_REVIEW)
    assert len(queue) == 1
    assert queue[0].item_id == "rev_sample_001"
    assert queue[0].review_status == IngestionReviewStatus.PENDING_REVIEW

    # Update review status
    updated = temp_store.update_review_status(
        item_id="rev_sample_001",
        status=IngestionReviewStatus.READY_FOR_LEGAL_GATE,
        reviewer_id="analyst_deshmukh",
        notes="Verified Marathi verbatim excerpts match GR clauses 1-4.",
    )
    assert updated

    retrieved = temp_store.get_review_item("rev_sample_001")
    assert retrieved is not None
    assert retrieved.review_status == IngestionReviewStatus.READY_FOR_LEGAL_GATE
    assert retrieved.reviewer_id == "analyst_deshmukh"
    assert "Verified Marathi verbatim" in (retrieved.review_notes or "")


def test_duplicate_scheme_and_alias_detection():
    # 1. Exact alias match for Majhi Ladki Bahin
    rep1 = detect_scheme_duplicates("मुख्यमंत्री माझी लाडकी बहीण योजना")
    assert rep1.is_probable_duplicate
    assert rep1.recommendation == "merge_with_existing"
    assert any(m.canonical_scheme_id == "candidate-majhi-ladki-bahin" for m in rep1.potential_duplicates)

    # 2. Acronym match
    rep2 = detect_scheme_duplicates("SGNAY Pension")
    assert any(m.canonical_scheme_id == "candidate-sanjay-gandhi-niradhar" for m in rep2.potential_duplicates)

    # 3. Known distinct branches are NOT flagged as duplicate merges
    rep_obc_girls = detect_scheme_duplicates(
        "Payment of Tuition Fees and Examination Fees to OBC Girls Pursuing Professional Courses",
        candidate_id="candidate-payment-tuition-exam-fees-obc-girls",
    )
    # Must identify the distinct branch relationship with standard OBC Post-Matric
    distinct_matches = [m for m in rep_obc_girls.potential_duplicates if m.is_distinct_branch]
    assert len(distinct_matches) >= 1
    assert any("Distinct Branch Verified" in m.reason for m in distinct_matches)

    # 4. Completely unrelated new scheme
    rep_new = detect_scheme_duplicates("Novel Maharashtra Solar Pump Agricultural Assistance Scheme")
    assert not rep_new.is_probable_duplicate
    assert rep_new.recommendation == "create_new"


def test_scheme_lineage_and_superseded_rules():
    # Majhi Ladki Bahin lineage
    lineage_mlb = get_scheme_lineage("candidate-majhi-ladki-bahin")
    assert lineage_mlb is not None
    assert lineage_mlb.base_resolution is not None
    assert lineage_mlb.base_resolution.gr_number == "202406281814018230"
    assert len(lineage_mlb.amendments) == 2  # Shuddhipatra + Clarification

    # Superseded rule detection
    assert len(lineage_mlb.superseded_rules) >= 1
    age_sup = lineage_mlb.superseded_rules[0]
    assert age_sup.original_value == 60
    assert age_sup.revised_value == 65
    assert age_sup.superseding_gr_reference == "202407031335114330"

    # Sanjay Gandhi Niradhar lineage
    lineage_sgnay = get_scheme_lineage("candidate-sanjay-gandhi-niradhar")
    assert lineage_sgnay is not None
    assert len(lineage_sgnay.superseded_rules) >= 2  # 1000->1500, 1500->2500 (divyang)
    assert any(r.revised_value == 2500 for r in lineage_sgnay.superseded_rules)


def test_ingestion_api_endpoints(client):
    # GET /ingestion/sources
    res_sources = client.get("/ingestion/sources")
    assert res_sources.status_code == 200
    assert isinstance(res_sources.json(), list)

    # GET /ingestion/changes
    res_changes = client.get("/ingestion/changes")
    assert res_changes.status_code == 200
    assert isinstance(res_changes.json(), list)

    # GET /ingestion/queue
    res_queue = client.get("/ingestion/queue")
    assert res_queue.status_code == 200
    assert isinstance(res_queue.json(), list)

    # POST /ingestion/detect-duplicates
    res_dup = client.post(
        "/ingestion/detect-duplicates",
        json={"title": "MMLBY Ladki Bahin Scheme"},
    )
    assert res_dup.status_code == 200
    dup_data = res_dup.json()
    assert dup_data["is_probable_duplicate"] is True
    assert dup_data["recommendation"] == "merge_with_existing"

    # GET /ingestion/lineages
    res_lineages = client.get("/ingestion/lineages")
    assert res_lineages.status_code == 200
    lineage_list = res_lineages.json()
    assert len(lineage_list) >= 4

    # GET /ingestion/lineage/{scheme_id}
    res_single = client.get("/ingestion/lineage/candidate-majhi-ladki-bahin")
    assert res_single.status_code == 200
    data_single = res_single.json()
    assert data_single["scheme_id"] == "candidate-majhi-ladki-bahin"
    assert len(data_single["superseded_rules"]) >= 1

    # Non-existent lineage returns 404
    res_404 = client.get("/ingestion/lineage/non-existent-scheme")
    assert res_404.status_code == 404
