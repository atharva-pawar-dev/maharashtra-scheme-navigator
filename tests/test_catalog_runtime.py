from __future__ import annotations

import json

import pytest
from fastapi import HTTPException

import scheme_navigator.api.main as api_main
from scheme_navigator.core.config import Settings
from scheme_navigator.domain.models import CitizenProfile, InterviewStart
from scheme_navigator.services.catalog import CatalogLoadError, SchemeCatalog


def _single_demo_scheme_catalog(tmp_path) -> str:
    """Create a configured catalog from one existing demo record, without inventing policy data."""
    demo_scheme = SchemeCatalog.from_json().all()[0].model_dump(mode="json")
    catalog_file = tmp_path / "configured-schemes.json"
    catalog_file.write_text(json.dumps([demo_scheme]), encoding="utf-8")
    return str(catalog_file)


def _use_runtime_catalog(monkeypatch, *, configured_path: str | None, app_env: str):
    monkeypatch.setattr(api_main.settings, "scheme_catalog_path", configured_path)
    monkeypatch.setattr(api_main.settings, "app_env", app_env)
    runtime_catalog = api_main.load_runtime_catalog()
    monkeypatch.setattr(api_main, "catalog", runtime_catalog)
    return runtime_catalog


def test_settings_reads_scheme_catalog_path_from_environment(monkeypatch, tmp_path):
    catalog_path = tmp_path / "configured-schemes.json"
    monkeypatch.setenv("SCHEME_CATALOG_PATH", str(catalog_path))

    configured = Settings(_env_file=None)

    assert configured.scheme_catalog_path == str(catalog_path)


def test_configured_catalog_takes_precedence_over_demo(tmp_path):
    catalog_file = tmp_path / "schemes.json"
    catalog_file.write_text("[]", encoding="utf-8")

    catalog = SchemeCatalog.for_runtime(
        configured_path=catalog_file,
        demo_fixtures_enabled=True,
    )

    assert catalog.all() == []


def test_demo_catalog_loads_when_enabled_without_custom_path():
    catalog = SchemeCatalog.for_runtime(
        configured_path=None,
        demo_fixtures_enabled=True,
    )

    assert len(catalog.all()) == 2


def test_catalog_is_empty_when_demo_disabled_without_custom_path():
    catalog = SchemeCatalog.for_runtime(
        configured_path=None,
        demo_fixtures_enabled=False,
    )

    assert catalog.all() == []


def test_malformed_catalog_fails_closed(tmp_path):
    catalog_file = tmp_path / "malformed.json"
    catalog_file.write_text("{not valid JSON", encoding="utf-8")

    with pytest.raises(CatalogLoadError, match="invalid JSON"):
        SchemeCatalog.for_runtime(
            configured_path=catalog_file,
            demo_fixtures_enabled=True,
        )


def test_invalid_scheme_record_fails_closed(tmp_path):
    catalog_file = tmp_path / "invalid-record.json"
    catalog_file.write_text(
        json.dumps([{"scheme_id": "missing-required-policy-fields"}]),
        encoding="utf-8",
    )

    with pytest.raises(CatalogLoadError, match="invalid scheme record"):
        SchemeCatalog.for_runtime(
            configured_path=catalog_file,
            demo_fixtures_enabled=False,
        )


def test_duplicate_scheme_ids_are_rejected(tmp_path):
    record = SchemeCatalog.from_json().all()[0].model_dump(mode="json")
    catalog_file = tmp_path / "duplicates.json"
    catalog_file.write_text(json.dumps([record, record]), encoding="utf-8")

    with pytest.raises(CatalogLoadError, match="Duplicate scheme_id"):
        SchemeCatalog.for_runtime(
            configured_path=catalog_file,
            demo_fixtures_enabled=False,
        )


def test_api_handler_uses_configured_catalog_in_local_mode(monkeypatch, tmp_path):
    catalog_path = _single_demo_scheme_catalog(tmp_path)

    _use_runtime_catalog(
        monkeypatch,
        configured_path=catalog_path,
        app_env="local",
    )

    schemes = api_main.list_schemes()

    assert [item.scheme_id for item in schemes] == [
        "demo-majhi-ladki-bahin"
    ]


def test_api_handlers_use_configured_catalog_in_production(monkeypatch, tmp_path):
    catalog_path = _single_demo_scheme_catalog(tmp_path)

    _use_runtime_catalog(
        monkeypatch,
        configured_path=catalog_path,
        app_env="production",
    )

    schemes = api_main.list_schemes()
    eligibility = api_main.evaluate_eligibility(
        CitizenProfile(
            age_years=25,
            gender="female",
            resident_state="Maharashtra",
            annual_family_income=200000,
            aadhaar_linked_bank_account=True,
        )
    )

    assert len(schemes) == 1
    assert eligibility[0].status.value == "needs_review"


def test_api_handler_production_without_catalog_is_empty_and_blocks_interviews(monkeypatch):
    _use_runtime_catalog(
        monkeypatch,
        configured_path=None,
        app_env="production",
    )

    assert api_main.list_schemes() == []
    with pytest.raises(HTTPException) as raised:
        api_main.start_interview(
            InterviewStart(
                thread_id="catalog-runtime-production-empty",
            )
        )
    assert raised.value.status_code == 503


def test_api_handler_uses_demo_catalog_by_default_in_local_mode(monkeypatch):
    _use_runtime_catalog(
        monkeypatch,
        configured_path=None,
        app_env="local",
    )

    schemes = api_main.list_schemes()

    assert len(schemes) == 2


def test_canonical_catalog_cross_journey_consistency():
    """
    Verify Phase 1 Requirement 3.4:
    Prove that a scheme displayed in Explore is the exact same record
    evaluated by the interview, results, and application preparation flows.
    """
    from fastapi.testclient import TestClient
    from scheme_navigator.api.main import source_registry
    from scheme_navigator.services.catalog import canonical_catalog

    client = TestClient(api_main.app)

    # 1. Fetch Explore schemes from API
    explore_res = client.get("/canonical-schemes")
    assert explore_res.status_code == 200
    explore_schemes = explore_res.json()
    assert len(explore_schemes) >= 70, "Explore must serve the authoritative canonical catalogue"

    explore_ids = {s["canonical_scheme_id"] for s in explore_schemes}

    # 2. Verify all are loaded in canonical_catalog runtime service
    runtime_schemes = canonical_catalog.all()
    runtime_ids = {s.scheme_id for s in runtime_schemes}
    assert explore_ids == runtime_ids, "Explore schemes must identically match evaluation runtime schemes"

    # 3. Spot-check 5 diverse schemes across State, Municipal, Central, and Welfare categories
    sample_ids = [
        "scheme-pm-svanidhi",
        "candidate-majhi-ladki-bahin",
        "pmc-shahari-garib-arogya",
        "pcmc-mscit-women",
        "ulb-council-swachh-livelihood",
    ]

    for sid in sample_ids:
        # Explore detail endpoint
        detail_res = client.get(f"/canonical-schemes/{sid}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["canonical_scheme_id"] == sid

        # Channel preparation endpoint
        ch_res = client.get(f"/channels/{sid}")
        assert ch_res.status_code == 200
        ch = ch_res.json()
        assert ch["scheme_id"] == sid
        assert ch["portal_url"] or ch["offline_procedure"], f"Application channel must have official portal or offline office: {sid}"

        # Focused interview start consistency
        focused_start_res = client.post(
            "/interview/start",
            json={
                "thread_id": f"consistency-check-{sid}",
                "mode": "FOCUSED_SCHEME",
                "target_scheme_id": sid,
                "language": "en"
            }
        )
        assert focused_start_res.status_code == 200
        f_state = focused_start_res.json()
        assert f_state["mode"] == "FOCUSED_SCHEME"
        assert f_state["target_scheme_id"] == sid

