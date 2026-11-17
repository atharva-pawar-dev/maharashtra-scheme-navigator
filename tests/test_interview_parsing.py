import pytest
from scheme_navigator.agents.interviewer import _parse_answer


def test_income_parser_supports_lakh_and_commas():
    assert _parse_answer("annual_family_income", "2.5 lakh") == ("annual_family_income", 250000)
    assert _parse_answer("annual_family_income", "₹1,50,000") == ("annual_family_income", 150000)
    assert _parse_answer("annual_family_income", "3 crore") == ("annual_family_income", 30000000)


def test_devanagari_and_indian_number_formatting_regression():
    # Required Phase 3 regression cases:
    # २५ → 25
    assert _parse_answer("age_years", "२५") == ("age_years", 25)
    # १,५०,००० → 150000
    assert _parse_answer("annual_family_income", "१,५०,०००") == ("annual_family_income", 150000)
    # २.५ लाख → 250000
    assert _parse_answer("annual_family_income", "२.५ लाख") == ("annual_family_income", 250000)
    # ३ करोड़ → 30000000
    assert _parse_answer("annual_family_income", "३ करोड़") == ("annual_family_income", 30000000)
    # 2.5 lakh → 250000
    assert _parse_answer("annual_family_income", "2.5 lakh") == ("annual_family_income", 250000)


def test_yes_no_parser_supports_marathi_and_hindi():
    assert _parse_answer("bpl", "हो") == ("bpl", True)
    assert _parse_answer("bpl", "होय") == ("bpl", True)
    assert _parse_answer("bpl", "हाँ") == ("bpl", True)
    assert _parse_answer("bpl", "जी") == ("bpl", True)
    assert _parse_answer("bpl", "नाही") == ("bpl", False)
    assert _parse_answer("bpl", "नहीं") == ("bpl", False)


def test_gender_and_residence_marathi_hindi():
    assert _parse_answer("gender", "महिला") == ("gender", "female")
    assert _parse_answer("gender", "स्त्री") == ("gender", "female")
    assert _parse_answer("gender", "औरत") == ("gender", "female")
    assert _parse_answer("gender", "पुरुष") == ("gender", "male")
    assert _parse_answer("gender", "इतर") == ("gender", "other")
    assert _parse_answer("resident_state", "महाराष्ट्र") == ("resident_state", "maharashtra")


def test_multilingual_validation_error_messages():
    with pytest.raises(ValueError, match="हो किंवा नाही"):
        _parse_answer("bpl", "कदाचित", language="mr")
    with pytest.raises(ValueError, match="हाँ या नहीं"):
        _parse_answer("bpl", "शायद", language="hi")
    with pytest.raises(ValueError, match="संख्या प्रविष्ट करा"):
        _parse_answer("age_years", "वीस", language="mr")
    with pytest.raises(ValueError, match="संख्या दर्ज करें"):
        _parse_answer("age_years", "बीस", language="hi")

def test_question_picker_skips_ruled_out_scheme_fields():
    from scheme_navigator.agents.interviewer import _choose_question
    from scheme_navigator.services.catalog import SchemeCatalog

    schemes = SchemeCatalog.from_json().all()
    candidate_schemes = []

    for scheme in schemes:
        if scheme.scheme_id == "demo-indira-gandhi-old-age-pension":
            # Synthetic metadata for testing only.
            scheme = scheme.model_copy(update={
                "approved_by": "Test Approval Authority",
                "approval_reference": "TEST-INTERVIEW-001",
            })

        candidate_schemes.append(scheme.model_dump(mode="json"))

    state = {
        "language": "en",
        "profile": {"age_years": 24},
        "candidate_schemes": candidate_schemes,
        "asked_fields": ["age_years"],
    }

    result = _choose_question(state)
    question = result["next_question"]

    assert question is not None
    assert question["field"] not in {
        "bpl",
        "receiving_other_pension",
    }
    from scheme_navigator.agents.interviewer import _choose_question
    from scheme_navigator.services.catalog import SchemeCatalog

    schemes = SchemeCatalog.from_json().all()

    state = {
        "language": "en",
        "profile": {"age_years": 24},
        "candidate_schemes": [
            scheme.model_dump(mode="json")
            for scheme in schemes
        ],
        "asked_fields": ["age_years"],
    }

    result = _choose_question(state)
    question = result["next_question"]

    assert question is not None
    assert question["field"] not in {
        "bpl",
        "receiving_other_pension",
    }
    assert 0 <= question["information_gain"] <= 1

def test_question_picker_keeps_demo_scheme_when_known_condition_fails():
    from scheme_navigator.agents.interviewer import _choose_question
    from scheme_navigator.services.catalog import SchemeCatalog

    scheme = next(
        s for s in SchemeCatalog.from_json().all()
        if s.scheme_id == "demo-indira-gandhi-old-age-pension"
    )

    state = {
        "language": "en",
        "profile": {"age_years": 24},
        "candidate_schemes": [
            scheme.model_dump(mode="json")
        ],
        "asked_fields": ["age_years"],
    }

    result = _choose_question(state)

    # Age fails the demo rule, but the scheme must remain provisional.
    # The interview should continue asking for other missing information.
    assert result["next_question"] is not None
    assert result["is_complete"] is False