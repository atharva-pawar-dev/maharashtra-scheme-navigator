"""Tests for Supreme Master Capabilities:
Source Registry, Public Services (RTS), Application Channels, Citizen Tracking, and Lifecycle Monitoring.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app
from scheme_navigator.source_registry.models import ApplicationTrackStatus, ChannelType
from scheme_navigator.source_registry.registry import SourceRegistry
from scheme_navigator.source_registry.lifecycle_monitor import SourceLifecycleMonitor


@pytest.fixture
def client():
    return TestClient(app)


def test_source_registry_data_integrity():
    registry = SourceRegistry()
    sources = registry.list_sources()
    assert len(sources) >= 30

    # Ensure all required categories exist
    categories_found = set()
    for s in sources:
        assert s.source_id.startswith("SRC-")
        assert s.name
        assert s.url.startswith("https://") or s.url.startswith("http://")
        assert len(s.content_hash) == 64
        for cat in s.categories:
            categories_found.add(cat)

    assert any("MahaDBT" in c for c in categories_found)
    assert any("MahaSarathi" in c for c in categories_found)
    assert any("myScheme" in c for c in categories_found)
    assert any("Government Resolutions" in c for c in categories_found)
    assert any("State Departments" in c for c in categories_found)
    assert any("State Corporations" in c for c in categories_found)
    assert any("Central Schemes" in c for c in categories_found)
    assert any("Joint Central-State" in c for c in categories_found)


def test_public_services_registry_integrity():
    registry = SourceRegistry()
    services = registry.list_public_services()
    assert len(services) >= 7

    srv_map = {s.service_id: s for s in services}
    assert "SRV-RTS-DOMICILE" in srv_map
    assert "SRV-RTS-INCOME" in srv_map
    assert "SRV-RTS-CASTE" in srv_map
    assert "SRV-RTS-NCL" in srv_map
    assert "SRV-RTS-UDID" in srv_map

    domicile = srv_map["SRV-RTS-DOMICILE"]
    assert domicile.rts_statutory_limit_days == 15
    assert domicile.department == "Revenue Department"
    assert domicile.is_common_prerequisite is True
    assert len(domicile.required_documents) >= 3


def test_application_channels_registry_integrity():
    registry = SourceRegistry()
    channels = registry.list_channels()
    assert len(channels) >= 8

    ch_map = {c.scheme_id: c for c in channels}
    assert "demo-majhi-ladki-bahin" in ch_map
    assert "demo-indira-gandhi-old-age-pension" in ch_map

    ladki_ch = ch_map["demo-majhi-ladki-bahin"]
    assert ladki_ch.channel_type == ChannelType.DIRECT_OFFICIAL_PORTAL
    assert "ladkibahin.maharashtra.gov.in" in ladki_ch.portal_url
    assert len(ladki_ch.preparation_checklist) >= 3

    pension_ch = ch_map["demo-indira-gandhi-old-age-pension"]
    assert pension_ch.channel_type == ChannelType.OFFLINE_OFFICE_APPLICATION
    assert "Tehsildar" in pension_ch.offline_procedure or "Taluka" in pension_ch.offline_procedure


def test_api_source_registry_endpoints(client):
    # GET /source-registry/sources
    resp = client.get("/source-registry/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 30

    # Filter by department
    resp_wcd = client.get("/source-registry/sources?department=Women")
    assert resp_wcd.status_code == 200
    assert any("Women" in s["department"] for s in resp_wcd.json())

    # GET /source-registry/coverage
    resp_cov = client.get("/source-registry/coverage")
    assert resp_cov.status_code == 200
    cov_data = resp_cov.json()
    assert len(cov_data) == 10
    categories = [c["category"] for c in cov_data]
    assert "Maharashtra departments" in categories
    assert "State corporations/boards" in categories
    assert "MahaDBT" in categories
    assert "Government Resolutions" in categories

    # GET /public-services
    resp_pub = client.get("/public-services")
    assert resp_pub.status_code == 200
    assert len(resp_pub.json()) >= 7

    # GET /channels
    resp_ch = client.get("/channels")
    assert resp_ch.status_code == 200
    assert len(resp_ch.json()) >= 8

    # GET /channels/{scheme_id}
    resp_sch_ch = client.get("/channels/demo-majhi-ladki-bahin")
    assert resp_sch_ch.status_code == 200
    assert resp_sch_ch.json()["channel_type"] == "DIRECT_OFFICIAL_PORTAL"

    resp_404 = client.get("/channels/nonexistent-scheme-id")
    assert resp_404.status_code == 404


def test_api_application_tracking_lifecycle_and_invariants(client):
    thread_id = "test-track-thread-001"
    scheme_id = "demo-majhi-ladki-bahin"

    # Track portal opened
    resp_opened = client.post(
        "/application/track",
        json={
            "thread_id": thread_id,
            "scheme_id": scheme_id,
            "status": "official_portal_opened",
            "notes": "Citizen clicked external link to ladkibahin portal",
        },
    )
    assert resp_opened.status_code == 200
    data_opened = resp_opened.json()
    assert data_opened["status"] == "official_portal_opened"
    assert data_opened["is_citizen_reported"] is True
    assert data_opened["status_label_en"] == "Official Portal Opened"
    assert data_opened["status_label_mr"] == "अधिकृत पोर्टल उघडले"
    assert data_opened["status_label_hi"] == "आधिकारिक पोर्टल खोला गया"

    # Track citizen reported submission
    resp_sub = client.post(
        "/application/track",
        json={
            "thread_id": thread_id,
            "scheme_id": scheme_id,
            "status": "citizen_reported_submitted",
            "notes": "Citizen confirmed form submission on official portal",
        },
    )
    assert resp_sub.status_code == 200
    data_sub = resp_sub.json()
    assert data_sub["status"] == "citizen_reported_submitted"
    assert data_sub["is_citizen_reported"] is True
    assert "Citizen Reported" in data_sub["status_label_en"]

    # Retrieve tracking history
    resp_hist = client.get(f"/application/track/{thread_id}")
    assert resp_hist.status_code == 200
    history = resp_hist.json()
    assert len(history) == 2
    assert history[0]["status"] == "official_portal_opened"
    assert history[1]["status"] == "citizen_reported_submitted"


def test_lifecycle_monitor_and_publication_suspension():
    registry = SourceRegistry()
    monitor = SourceLifecycleMonitor(registry)

    # Record a detected GR amendment
    change = monitor.record_change(
        source_id="SRC-PORTAL-GR-MAHA",
        change_type="AMENDMENT",
        summary="New GR revising SGNAY medical board scrutiny guidelines",
        previous_hash="0" * 64,
        current_hash="1" * 64,
        affected_scheme_ids=["candidate-sanjay-gandhi-niradhar-anudan"],
        requires_human_approval=True,
    )
    assert change.change_id.startswith("CHG-")
    assert change.is_reviewed is False

    # Check pending changes
    pending = monitor.get_pending_changes()
    assert len(pending) == 1
    assert pending[0].change_id == change.change_id

    # Test scheme suspension
    scheme_id = "candidate-sanjay-gandhi-niradhar-anudan"
    assert monitor.is_suspended(scheme_id) is False
    monitor.suspend_scheme(scheme_id, "Pending verification of new GR")
    assert monitor.is_suspended(scheme_id) is True

    # Lift suspension
    monitor.lift_suspension(scheme_id)
    assert monitor.is_suspended(scheme_id) is False

    # Check monitor status payload
    status_payload = monitor.get_monitor_status()
    assert status_payload["status"] == "HEALTHY_MONITORING"
    assert status_payload["total_sources_monitored"] >= 30
    assert status_payload["pending_changes_count"] == 1


def test_canonical_schemes_inventory_integrity():
    registry = SourceRegistry()
    schemes = registry.list_canonical_schemes()
    assert len(schemes) >= 9

    # Separate active demo fixtures from draft quarantined candidates
    demo_fixtures = [s for s in schemes if s.publication_status in ("ACTIVE_DEMO_FIXTURE", "DEMO_ONLY")]
    draft_candidates = [s for s in schemes if s.publication_status in ("DRAFT_QUARANTINED", "REVIEW_REQUIRED", "POLICY_UNRESOLVED")]

    assert len(demo_fixtures) == 2
    assert len(draft_candidates) >= 7

    # Verify all records have unique IDs, official names, authorities, and mapped aliases
    seen_ids = set()
    for s in schemes:
        assert s.canonical_scheme_id not in seen_ids
        seen_ids.add(s.canonical_scheme_id)
        assert s.official_name_mr
        assert s.official_name_en
        assert s.responsible_authority
        assert len(s.source_references) >= 1
        assert s.application_portal_url.startswith("https://")
        assert len(s.duplicate_aliases_mapped) >= 1


def test_api_canonical_schemes_endpoints(client):
    # GET /canonical-schemes
    resp = client.get("/canonical-schemes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 9

    # GET /canonical-schemes/{scheme_id}
    resp_single = client.get("/canonical-schemes/demo-majhi-ladki-bahin")
    assert resp_single.status_code == 200
    item = resp_single.json()
    assert item["canonical_scheme_id"] == "demo-majhi-ladki-bahin"
    assert item["publication_status"] == "ACTIVE_DEMO_FIXTURE"

    # GET non-existent
    resp_404 = client.get("/canonical-schemes/nonexistent-scheme-999")
    assert resp_404.status_code == 404
