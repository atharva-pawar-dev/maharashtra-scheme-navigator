from __future__ import annotations

import json
from pathlib import Path
import pytest

from scheme_navigator.core.citizen_store import CitizenProfileStore
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import pytest

from scheme_navigator.core.citizen_store import CitizenProfileStore
from scheme_navigator.domain.models import ExtractedDocument, RuleNode, Scheme, SourceReference
from scheme_navigator.services.document_prep import (
    CANONICAL_SCHEME_ALIAS_MAP,
    DocumentMatchStatus,
    get_all_scheme_document_requirements,
    get_scheme_document_requirements,
    prepare_intelligent_document_audit,
)
from scheme_navigator.source_registry.registry import SourceRegistry


REPRESENTATIVE_SCHEME_FAMILIES = [
    ("MHA-S-0001", "candidate-sanjay-gandhi-niradhar-anudan", "Income-tested Pension"),
    ("MHA-S-0002", "demo-indira-gandhi-old-age-pension", "National Old Age Pension"),
    ("MHA-S-0003", "candidate-majhi-ladki-bahin", "Women Direct Benefit Transfer (ANY_OF)"),
    ("MHA-S-0004", "candidate-shravanbal-sewa-rajya-nivruttivetan", "State Senior Citizen Pension"),
    ("MHA-S-0007", "scheme-divyang-motorized-tricycle", "Disability Welfare & Assistive Devices"),
    ("MHA-S-0008", "candidate-post-matric-sc", "Caste / Category Post-Matric Scholarship"),
    ("MHA-S-0010", "scheme-ebc-tuition-waiver", "Higher Education Tuition Fee Waiver (EBC)"),
    ("MHA-S-0015", "scheme-bhausaheb-fundkar-phalbag", "Farmer Landholding & Horticulture Support"),
    ("MHA-S-0016", "scheme-ramai-awas-yojana", "Rural / Urban Housing Assistance"),
    ("MHA-S-0017", "scheme-mjpjay-ayushman-bharat", "Healthcare & Universal Health Insurance"),
    ("MHA-S-0018", "scheme-annasaheb-patil-ir2", "Self-Employment & Enterprise Interest Reimbursement"),
    ("MHA-S-0006", "scheme-igndps-disability-pension", "Severe Disability Social Security"),
]


def _make_dummy_scheme(scheme_id: str, name: str, department: str, req_docs: list[str]) -> Scheme:
    excerpt = "Official statutory guidelines for Maharashtra state scheme administration."
    h = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
    return Scheme(
        scheme_id=scheme_id,
        name=name,
        department=department,
        summary="Official statutory scheme summary",
        required_documents=req_docs,
        eligibility_rule=RuleNode(
            op="all",
            children=[RuleNode(op="gte", field="age", value=18, condition_id="c_age_dummy")],
        ),
        sources=[
            SourceReference(
                source_name="Maharashtra Government Gazette",
                source_url="https://maharashtra.gov.in/gazette",
                source_kind="official_scheme_page",
                retrieved_at=datetime.now(timezone.utc),
                evidence_excerpt=excerpt,
                evidence_sha256=h,
            )
        ],
    )


def test_representative_12_scheme_families_exist_in_registry():
    """Verify that all 12 representative scheme families have verified document requirements."""
    registry = SourceRegistry()
    all_reqs = get_all_scheme_document_requirements()

    for mha_alias, canonical_id, description in REPRESENTATIVE_SCHEME_FAMILIES:
        reqs_canon = get_scheme_document_requirements(canonical_id)
        assert reqs_canon is not None, f"Requirements missing for {canonical_id} ({description})"
        assert len(reqs_canon.get("requirements", [])) > 0, f"Requirements list empty for {canonical_id}"

        reqs_alias = get_scheme_document_requirements(mha_alias)
        assert reqs_alias is not None, f"Requirements missing for alias {mha_alias}"
        assert reqs_alias["scheme_id"] == reqs_canon["scheme_id"]

        scheme_rec = registry.get_canonical_scheme(mha_alias)
        assert scheme_rec is not None, f"Source registry lookup failed for {mha_alias}"


def test_readiness_computation_for_all_12_schemes():
    """Verify readiness engine accurately computes baseline missing state and satisfaction for all 12 schemes."""
    for mha_alias, canonical_id, description in REPRESENTATIVE_SCHEME_FAMILIES:
        req_data = get_scheme_document_requirements(canonical_id)
        scheme_obj = _make_dummy_scheme(
            scheme_id=canonical_id,
            name=req_data.get("scheme_name", canonical_id),
            department=req_data.get("department", "Government of Maharashtra"),
            req_docs=[r["document_name"] for r in req_data.get("requirements", [])],
        )

        # Baseline: 0 documents uploaded -> 0% readiness
        report_empty = prepare_intelligent_document_audit(
            scheme=scheme_obj,
            extracted_documents=[],
            scheme_id=mha_alias,
        )
        assert report_empty.readiness_percentage == 0
        assert not report_empty.all_mandatory_satisfied
        assert len(report_empty.requirements) == len(req_data["requirements"])


def test_any_of_alternative_document_satisfaction():
    """Verify ANY_OF alternatives (e.g. 15-year Ration Card satisfying Domicile) work correctly."""
    req_data = get_scheme_document_requirements("candidate-majhi-ladki-bahin")
    scheme_obj = _make_dummy_scheme(
        scheme_id="candidate-majhi-ladki-bahin",
        name="Mukhyamantri Majhi Ladki Bahin Yojana",
        department="Women and Child Development Department",
        req_docs=[r["document_name"] for r in req_data.get("requirements", [])],
    )

    alt_ration_card = ExtractedDocument(
        document_id="doc_ration_alt_01",
        document_type="domicile_certificate",
        person_name="Sunita Ramesh Patil",
        confidence=0.95,
        source_file_sha256="c" * 64,
        field_evidence={"document_title": "15-year Ration Card / Domicile Proof"},
    )

    report = prepare_intelligent_document_audit(
        scheme=scheme_obj,
        extracted_documents=[alt_ration_card],
        scheme_id="MHA-S-0003",
    )

    domicile_req = next(
        r for r in report.requirements
        if "domicile" in r.document_name.lower() or "residence" in r.document_name.lower()
    )
    assert domicile_req.match_status in (
        DocumentMatchStatus.MATCHED,
        DocumentMatchStatus.ALTERNATIVE_MATCHED,
    )
    assert domicile_req.state == DocumentMatchStatus.MATCHED_FOR_PREPARATION


def test_farmer_scheme_landholding_document_requirement():
    """Verify farmer scheme MHA-S-0015 requires 7/12 land extract and matches correctly."""
    req_data = get_scheme_document_requirements("scheme-bhausaheb-fundkar-phalbag")
    scheme_obj = _make_dummy_scheme(
        scheme_id="scheme-bhausaheb-fundkar-phalbag",
        name="Bhausaheb Fundkar Phalbag Lagwad Yojana",
        department="Agriculture Department",
        req_docs=[r["document_name"] for r in req_data.get("requirements", [])],
    )

    req_names = [r["document_name"].lower() for r in req_data["requirements"]]
    assert any("7/12" in r or "land" in r for r in req_names)

    seven_twelve_doc = ExtractedDocument(
        document_id="doc_712_01",
        document_type="seven_twelve_extract",
        person_name="Ramesh Govind Patil",
        confidence=0.96,
        source_file_sha256="d" * 64,
        field_evidence={"document_title": "Mahabhulekh 7/12 Extract"},
    )

    report = prepare_intelligent_document_audit(
        scheme=scheme_obj,
        extracted_documents=[seven_twelve_doc],
        scheme_id="MHA-S-0015",
    )

    matched_712 = next(r for r in report.requirements if "7/12" in r.document_name)
    assert matched_712.match_status == DocumentMatchStatus.MATCHED


def test_sqlite_persistence_across_multiple_schemes(tmp_path):
    """Verify SQLite citizen_scheme_documents persists attachments across backend restarts for diverse schemes."""
    db_file = tmp_path / "diverse_citizen.sqlite3"
    store = CitizenProfileStore(db_path=db_file)
    session_id = "test_session_diverse_01"

    # Attach documents for 3 different scheme families
    doc_income = {
        "document_type": "income_certificate",
        "person_name": "Sunita Patil",
        "annual_family_income": 120000,
        "valid_financial_year": "2026-27",
    }
    doc_712 = {
        "document_type": "seven_twelve_extract",
        "person_name": "Ramesh Patil",
    }
    doc_caste = {
        "document_type": "caste_certificate",
        "person_name": "Sunita Patil",
        "caste_category": "SC",
    }

    # Save to MHA-S-0001 (Income Pension)
    store.save_scheme_document(session_id, "MHA-S-0001", doc_income, "income.pdf", "1" * 64)
    # Save to MHA-S-0015 (Farmer Land)
    store.save_scheme_document(session_id, "MHA-S-0015", doc_712, "712.pdf", "2" * 64)
    # Save to MHA-S-0008 (Post-Matric Caste)
    store.save_scheme_document(session_id, "MHA-S-0008", doc_caste, "caste.pdf", "3" * 64)

    # Simulate backend restart with new store instance pointing to same file
    restart_store = CitizenProfileStore(db_path=db_file)

    docs_0001 = restart_store.get_scheme_documents(session_id, "MHA-S-0001")
    assert len(docs_0001) == 1
    assert docs_0001[0]["document_type"] == "income_certificate"
    assert docs_0001[0]["source_file_sha256"] == "1" * 64

    docs_0015 = restart_store.get_scheme_documents(session_id, "MHA-S-0015")
    assert len(docs_0015) == 1
    assert docs_0015[0]["document_type"] == "seven_twelve_extract"

    docs_0008 = restart_store.get_scheme_documents(session_id, "MHA-S-0008")
    assert len(docs_0008) == 1
    assert docs_0008[0]["document_type"] == "caste_certificate"
