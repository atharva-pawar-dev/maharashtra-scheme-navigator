from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from scheme_navigator.api.main import app, catalog
from scheme_navigator.domain.evidence import (
    OfficialSourceType,
    RuleEvidence,
    RuleVerificationStatus,
)
from scheme_navigator.domain.models import (
    CitizenProfile,
    EligibilityResult,
    EligibilityStatus,
    ExtractedDocument,
    Language,
    RuleNode,
    Scheme,
)
from scheme_navigator.services.catalog import SchemeCatalog
from scheme_navigator.services.explanation import (
    ConditionStatus,
    ExplainedCondition,
    SchemeExplanation,
    ValueProvenance,
    explain_eligibility,
    generate_scheme_explanation,
)
from scheme_navigator.services.rule_engine import evaluate_scheme


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def candidates_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / "data" / "candidates"


@pytest.fixture
def majhi_ladki_bahin_candidate(candidates_dir) -> Scheme:
    path = candidates_dir / "mukhyamantri-majhi-ladki-bahin.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Scheme.model_validate(data)


def test_english_explanation(majhi_ladki_bahin_candidate):
    profile = CitizenProfile(
        age_years=25,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=150000,
        aadhaar_linked_bank_account=True,
        receiving_other_pension=False,
    )
    exp = generate_scheme_explanation(majhi_ladki_bahin_candidate, profile, language=Language.EN)

    assert exp.language == "en"
    assert exp.overall_status == "needs_review"
    assert "under review" in exp.scheme_verification_label.lower()
    assert len(exp.positive_conditions) >= 5
    assert len(exp.unmet_conditions) == 0

    titles = [c.title for c in exp.positive_conditions]
    assert "Age Requirement" in titles
    assert "Gender Requirement" in titles
    assert "Annual Family Income Limit" in titles

    explanations = [c.citizen_explanation for c in exp.positive_conditions]
    assert any("Based on your answers:" in text for text in explanations)
    assert any("25 years satisfies" in text for text in explanations)


def test_marathi_explanation(majhi_ladki_bahin_candidate):
    profile = CitizenProfile(
        age_years=30,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=200000,
        aadhaar_linked_bank_account=True,
        receiving_other_pension=False,
    )
    exp = generate_scheme_explanation(majhi_ladki_bahin_candidate, profile, language=Language.MR)

    assert exp.language == "mr"
    assert exp.overall_status == "needs_review"
    assert "पुनरावलोकनाधीन" in exp.overall_status_label

    titles = [c.title for c in exp.positive_conditions]
    assert "वयाची अट" in titles
    assert "कौटुंबिक वार्षिक उत्पन्न मर्यादा" in titles
    assert "महाराष्ट्र राज्य रहिवासी व अधिवास" in titles

    explanations = [c.citizen_explanation for c in exp.positive_conditions]
    assert any("तुम्ही दिलेल्या माहितीनुसार:" in text for text in explanations)
    assert any("पूर्ण होते" in text for text in explanations)

    assert any("सरकारी मंजुरी नाही" in notice for notice in exp.trust_notices)
    assert any("कागदपत्र पडताळणी प्रलंबित" in notice for notice in exp.trust_notices)


def test_hindi_explanation(majhi_ladki_bahin_candidate):
    profile = CitizenProfile(
        age_years=28,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=180000,
        aadhaar_linked_bank_account=True,
        receiving_other_pension=False,
    )
    exp = generate_scheme_explanation(majhi_ladki_bahin_candidate, profile, language=Language.HI)

    assert exp.language == "hi"
    assert exp.overall_status == "needs_review"
    assert "समीक्षाधीन" in exp.overall_status_label

    titles = [c.title for c in exp.positive_conditions]
    assert "आयु की आवश्यकता" in titles
    assert "पारिवारिक वार्षिक आय सीमा" in titles
    assert "महाराष्ट्र राज्य निवास एवं अधिवास" in titles

    explanations = [c.citizen_explanation for c in exp.positive_conditions]
    assert any("आपकी दी गई जानकारी के अनुसार:" in text for text in explanations)
    assert any("पूरी होती है" in text for text in explanations)

    assert any("सरकारी स्वीकृति नहीं है" in notice for notice in exp.trust_notices)
    assert any("दस्तावेज़ सत्यापन लंबित" in notice for notice in exp.trust_notices)


def test_missing_translation_fallback(majhi_ladki_bahin_candidate):
    profile = CitizenProfile(age_years=25, gender="female", resident_state="Maharashtra")
    exp = generate_scheme_explanation(majhi_ladki_bahin_candidate, profile, language="unsupported_lang")

    assert exp.language == "en"
    assert exp.overall_status == "needs_review"
    assert len(exp.positive_conditions) > 0
    assert "Age Requirement" in [c.title for c in exp.positive_conditions]


def test_true_false_and_unknown_conditions():
    rule = RuleNode.model_validate({
        "op": "all",
        "children": [
            {"op": "gte", "field": "age", "value": 21, "condition_id": "c_age"},
            {"op": "lte", "field": "annual_family_income", "value": 250000, "condition_id": "c_income"},
            {"op": "eq", "field": "resident_state", "value": "maharashtra", "condition_id": "c_state"},
        ],
    })

    # Age 25 (True), Income 400,000 (False), Resident state None (Unknown)
    profile = CitizenProfile(age_years=25, annual_family_income=400000, resident_state=None)

    exp = explain_eligibility(
        scheme_id="test-three-valued",
        scheme_name="Test Three-Valued Scheme",
        eligibility_status="ineligible",
        eligibility_reason="Income exceeded limit.",
        rule_root=rule,
        profile=profile,
        language="en",
    )

    assert len(exp.positive_conditions) == 1
    assert exp.positive_conditions[0].field == "age"
    assert exp.positive_conditions[0].status == ConditionStatus.SATISFIED
    assert exp.positive_conditions[0].actual_value == 25

    assert len(exp.unmet_conditions) == 1
    assert exp.unmet_conditions[0].field == "annual_family_income"
    assert exp.unmet_conditions[0].status == ConditionStatus.UNMET
    assert exp.unmet_conditions[0].actual_value == 400000
    assert "exceeds the allowable limit" in exp.unmet_conditions[0].citizen_explanation

    assert len(exp.missing_information) == 1
    assert exp.missing_information[0].field == "resident_state"
    assert exp.missing_information[0].status == ConditionStatus.UNKNOWN
    assert "has not been specified" in exp.missing_information[0].citizen_explanation


def test_and_or_short_circuit_explanation_consistency():
    rule = RuleNode.model_validate({
        "op": "all",
        "children": [
            {"op": "gte", "field": "age", "value": 65, "condition_id": "c_age"},
            {
                "op": "any",
                "children": [
                    {"op": "eq", "field": "bpl", "value": True, "condition_id": "c_bpl"},
                    {"op": "lte", "field": "annual_family_income", "value": 21000, "condition_id": "c_income"},
                ],
            },
        ],
    })

    # Case 1: bpl = True, income = None. Age 70.
    # The OR branch succeeds via BPL! Missing income must NOT be exposed as missing!
    prof1 = CitizenProfile(age_years=70, bpl=True, annual_family_income=None)
    exp1 = explain_eligibility(
        scheme_id="test-pension",
        scheme_name="Test Pension",
        eligibility_status="eligible",
        eligibility_reason="Matched BPL pension track.",
        rule_root=rule,
        profile=prof1,
        language="en",
    )
    assert len(exp1.positive_conditions) == 2
    pos_fields = [c.field for c in exp1.positive_conditions]
    assert "age" in pos_fields
    assert "bpl" in pos_fields
    assert len(exp1.missing_information) == 0
    assert not any(c.field == "annual_family_income" for c in exp1.missing_information)

    # Case 2: bpl = False, income = 15000 (<= 21000). Age 70.
    # The OR branch succeeds via income! BPL failure does not fail the scheme.
    prof2 = CitizenProfile(age_years=70, bpl=False, annual_family_income=15000)
    exp2 = explain_eligibility(
        scheme_id="test-pension",
        scheme_name="Test Pension",
        eligibility_status="eligible",
        eligibility_reason="Matched non-BPL pension track.",
        rule_root=rule,
        profile=prof2,
        language="en",
    )
    assert len(exp2.positive_conditions) == 2
    pos_fields = [c.field for c in exp2.positive_conditions]
    assert "age" in pos_fields
    assert "annual_family_income" in pos_fields
    assert len(exp2.unmet_conditions) == 0

    # Case 3: bpl = False, income = None. Age 70.
    # BPL failed, but income is unknown. Income is needed to see if the applicant can qualify.
    prof3 = CitizenProfile(age_years=70, bpl=False, annual_family_income=None)
    exp3 = explain_eligibility(
        scheme_id="test-pension",
        scheme_name="Test Pension",
        eligibility_status="needs_information",
        eligibility_reason="Income information needed.",
        rule_root=rule,
        profile=prof3,
        language="en",
    )
    assert len(exp3.positive_conditions) == 1  # age is satisfied
    assert len(exp3.missing_information) == 1
    assert exp3.missing_information[0].field == "annual_family_income"

    # Case 4: bpl = False, income = 50000 (> 21000). Age 70.
    # Both alternatives failed. Both are listed under unmet conditions.
    prof4 = CitizenProfile(age_years=70, bpl=False, annual_family_income=50000)
    exp4 = explain_eligibility(
        scheme_id="test-pension",
        scheme_name="Test Pension",
        eligibility_status="ineligible",
        eligibility_reason="Neither BPL nor income limit met.",
        rule_root=rule,
        profile=prof4,
        language="en",
    )
    unmet_fields = [c.field for c in exp4.unmet_conditions]
    assert "bpl" in unmet_fields
    assert "annual_family_income" in unmet_fields


def test_source_reference_preservation(majhi_ladki_bahin_candidate):
    profile = CitizenProfile(age_years=25, gender="female", resident_state="Maharashtra")
    exp = generate_scheme_explanation(majhi_ladki_bahin_candidate, profile, language=Language.EN)

    for cond in exp.positive_conditions:
        assert cond.condition_id is not None
        assert cond.evidence_id is not None
        assert cond.source_title is not None
        assert cond.official_reference is not None
        assert cond.official_source_url is not None
        assert cond.official_source_url.startswith("https://")
        assert cond.verification_status == "extracted_unverified"
        assert not cond.is_rule_verified

    for src in exp.relevant_sources:
        assert src.source_title is not None
        assert src.source_url.startswith("https://")


def test_citizen_reported_versus_document_verified_values():
    rule = RuleNode.model_validate({
        "op": "lte",
        "field": "annual_family_income",
        "value": 250000,
        "condition_id": "c_inc",
    })

    # Case 1: Self-reported
    prof_self = CitizenProfile(annual_family_income=180000)
    exp_self = explain_eligibility(
        scheme_id="test",
        scheme_name="Test",
        eligibility_status="eligible",
        eligibility_reason="Eligible",
        rule_root=rule,
        profile=prof_self,
        language="en",
    )
    assert exp_self.positive_conditions[0].provenance == ValueProvenance.SELF_REPORTED
    assert "Based on your answers:" in exp_self.positive_conditions[0].citizen_explanation

    # Case 2: Document extracted
    doc = ExtractedDocument(
        document_id="doc-inc-1",
        source_file_sha256="a" * 64,
        document_type="income_certificate",
        annual_family_income=180000,
        income_currency="INR",
    )
    exp_doc = explain_eligibility(
        scheme_id="test",
        scheme_name="Test",
        eligibility_status="eligible",
        eligibility_reason="Eligible",
        rule_root=rule,
        profile=prof_self,
        extracted_documents=[doc],
        language="en",
    )
    assert exp_doc.positive_conditions[0].provenance == ValueProvenance.DOCUMENT_EXTRACTED
    assert "verification pending" in exp_doc.positive_conditions[0].citizen_explanation

    # Case 3: Reviewer verified
    review_record = {
        "status": "review_completed",
        "review_id": "rev-123",
        "reviewer_id": "gov_officer_42",
    }
    exp_rev = explain_eligibility(
        scheme_id="test",
        scheme_name="Test",
        eligibility_status="eligible",
        eligibility_reason="Eligible",
        rule_root=rule,
        profile=prof_self,
        extracted_documents=[doc],
        review_record=review_record,
        language="en",
    )
    assert exp_rev.positive_conditions[0].provenance == ValueProvenance.REVIEWER_VERIFIED
    assert "Verified by reviewer:" in exp_rev.positive_conditions[0].citizen_explanation


def test_unverified_scheme_status_wording(majhi_ladki_bahin_candidate):
    profile = CitizenProfile(age_years=25, gender="female", resident_state="Maharashtra")
    exp = generate_scheme_explanation(majhi_ladki_bahin_candidate, profile, language=Language.EN)

    assert exp.scheme_verification_status == "under_review"
    assert "conditions are under review" in exp.scheme_verification_label
    assert any("not a government approval" in notice.lower() for notice in exp.trust_notices)
    assert any("document verification pending" in notice.lower() for notice in exp.trust_notices)
    assert any("based on your answers" in notice.lower() for notice in exp.trust_notices)


def test_no_raw_ast_terms_in_citizen_facing_output(majhi_ladki_bahin_candidate):
    profile = CitizenProfile(
        age_years=25,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=500000,  # Exceeds limit
    )
    for lang in [Language.EN, Language.MR, Language.HI]:
        exp = generate_scheme_explanation(majhi_ladki_bahin_candidate, profile, language=lang)
        all_texts = [
            exp.summary,
            exp.next_recommended_action,
            exp.scheme_verification_label,
            *exp.trust_notices,
        ]
        for c in exp.positive_conditions + exp.unmet_conditions + exp.missing_information:
            all_texts.extend([c.title, c.requirement_description, c.citizen_explanation])

        forbidden = ["op:", "'op'", "RuleNode", "gte", "lte", "must equal", "must be at most", "must be at least"]
        for text in all_texts:
            for term in forbidden:
                assert term not in text, f"Found raw AST term '{term}' in user-facing text: '{text}'"


def test_no_claim_of_government_approval(majhi_ladki_bahin_candidate):
    profile = CitizenProfile(
        age_years=25,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=150000,
        aadhaar_linked_bank_account=True,
        receiving_other_pension=False,
    )
    for lang in [Language.EN, Language.MR, Language.HI]:
        exp = generate_scheme_explanation(majhi_ladki_bahin_candidate, profile, language=lang)
        full_text = " ".join(exp.trust_notices + [exp.summary, exp.next_recommended_action])
        assert "not a government approval" in full_text.lower() or "सरकारी मंजुरी नाही" in full_text or "सरकारी स्वीकृति नहीं" in full_text
        assert "grant guaranteed" not in full_text.lower()


def test_all_seven_candidate_schemes_remain_under_review(candidates_dir):
    files = sorted(candidates_dir.glob("*.json"))
    candidate_files = [f for f in files if "candidate_schemes" not in f.name]
    assert len(candidate_files) == 7

    profile = CitizenProfile(
        age_years=25,
        gender="female",
        resident_state="Maharashtra",
        annual_family_income=50000,
        caste_category="OBC",
        is_student=True,
        education_level="post_matric",
        bpl=True,
        receiving_other_pension=False,
        aadhaar_linked_bank_account=True,
    )

    for filepath in candidate_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        scheme = Scheme.model_validate(data)

        # 1. Status is draft
        assert scheme.rule_status == "draft"
        assert not scheme.publication_authorized
        assert scheme.approved_by is None

        # 2. Evaluation fails closed
        res = evaluate_scheme(scheme, profile)
        assert res.status == EligibilityStatus.NEEDS_REVIEW

        # 3. Explanation confirms under review
        exp = generate_scheme_explanation(scheme, profile, res, language=Language.EN)
        assert exp.scheme_verification_status == "under_review"
        assert "under review" in exp.scheme_verification_label.lower()


def test_api_explain_endpoint(client):
    demo_schemes = catalog.all()
    assert len(demo_schemes) >= 1
    target_id = demo_schemes[0].scheme_id

    # Test GET/POST /schemes/{scheme_id}/explain with Marathi
    res = client.post(
        f"/schemes/{target_id}/explain?language=mr",
        json={"age_years": 25, "gender": "female", "resident_state": "Maharashtra"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["scheme_id"] == target_id
    assert data["language"] == "mr"
    assert "positive_conditions" in data
    assert "trust_notices" in data

    # Test /eligibility/evaluate with language parameter
    eval_res = client.post(
        "/eligibility/evaluate?language=hi",
        json={"age_years": 25, "gender": "female", "resident_state": "Maharashtra"},
    )
    assert eval_res.status_code == 200
    eval_list = eval_res.json()
    assert len(eval_list) >= 1
    first = eval_list[0]
    assert first["explanation"] is not None
    assert first["explanation"]["language"] == "hi"
