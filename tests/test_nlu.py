from __future__ import annotations

import pytest

from scheme_navigator.agents.interviewer import _parse_answer
from scheme_navigator.services.nlu import (
    InterpretationResult,
    interpret_answer,
    interpret_boolean_slot,
    interpret_gender_slot,
    interpret_number_slot,
    interpret_resident_state,
)


# --------------------------------------------------------------------------
# 1. Natural Affirmation Recognition (English, Marathi, Hindi)
# --------------------------------------------------------------------------

def test_natural_english_yes_recognition():
    affirmations = [
        "yes",
        "yup",
        "yeah",
        "definitely",
        "absolutely",
        "certainly",
        "of course",
        "that's right",
        "i do",
        "i certainly do",
    ]
    for text in affirmations:
        res = interpret_boolean_slot(text, "is_student", "en")
        assert res.value is True, f"Failed on '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("is_student", text, "en") == ("is_student", True)


def test_natural_marathi_yes_recognition():
    marathi_affirmations = [
        "हो",
        "होय",
        "नक्कीच",
        "आहे",
        "होय आहे",
        "मी विद्यार्थी आहे",
        "खाते जोडलेले आहे",
        "दारिद्र्यरेषेखाली आहे",
    ]
    for text in marathi_affirmations:
        res = interpret_boolean_slot(text, "is_student", "mr")
        assert res.value is True, f"Failed on '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("is_student", text, "mr") == ("is_student", True)


def test_natural_hindi_yes_recognition():
    hindi_affirmations = [
        "हाँ",
        "जी हाँ",
        "बिल्कुल",
        "ज़रूर",
        "जरूर",
        "हाँ बिल्कुल",
        "मैं छात्र हूँ",
        "खाता जुड़ा हुआ है",
    ]
    for text in hindi_affirmations:
        res = interpret_boolean_slot(text, "is_student", "hi")
        assert res.value is True, f"Failed on '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("is_student", text, "hi") == ("is_student", True)


# --------------------------------------------------------------------------
# 2. Natural Negation Understanding (English, Marathi, Hindi)
# --------------------------------------------------------------------------

def test_natural_english_no_recognition():
    negations = [
        "no",
        "nope",
        "nah",
        "definitely not",
        "absolutely not",
        "not at all",
        "never",
        "i don't",
        "i do not",
        "i never do",
        "i am not",
    ]
    for text in negations:
        res = interpret_boolean_slot(text, "is_student", "en")
        assert res.value is False, f"Failed on '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("is_student", text, "en") == ("is_student", True if False else False)


def test_natural_marathi_no_recognition():
    marathi_negations = [
        "नाही",
        "मुळीच नाही",
        "कधीच नाही",
        "नक्कीच नाही",
        "मी विद्यार्थी नाही",
        "जोडलेले नाही",
        "दारिद्र्यरेषेखाली नाही",
    ]
    for text in marathi_negations:
        res = interpret_boolean_slot(text, "is_student", "mr")
        assert res.value is False, f"Failed on '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("is_student", text, "mr") == ("is_student", False)


def test_natural_hindi_no_recognition():
    hindi_negations = [
        "नहीं",
        "जी नहीं",
        "बिल्कुल नहीं",
        "कतई नहीं",
        "कभी नहीं",
        "मैं छात्र नहीं हूँ",
        "नहीं जुड़ा है",
    ]
    for text in hindi_negations:
        res = interpret_boolean_slot(text, "is_student", "hi")
        assert res.value is False, f"Failed on '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("is_student", text, "hi") == ("is_student", False)


# --------------------------------------------------------------------------
# 3. Contextual Negation & Residence Slot Interpretation
# --------------------------------------------------------------------------

def test_resident_state_contextual_negation_and_affirmation():
    # Affirmatory residence statements
    assert _parse_answer("resident_state", "I definitely live in Maharashtra", "en") == ("resident_state", "maharashtra")
    assert _parse_answer("resident_state", "होय मी महाराष्ट्रात राहतो", "mr") == ("resident_state", "maharashtra")
    assert _parse_answer("resident_state", "हाँ मैं महाराष्ट्र में रहता हूँ", "hi") == ("resident_state", "maharashtra")

    # Negation of Maharashtra residence
    assert _parse_answer("resident_state", "I definitely don't live in Maharashtra", "en") == ("resident_state", "other state")
    assert _parse_answer("resident_state", "नाही मी महाराष्ट्रात राहत नाही", "mr") == ("resident_state", "other state")
    assert _parse_answer("resident_state", "नहीं मैं महाराष्ट्र में नहीं रहता", "hi") == ("resident_state", "other state")
    assert _parse_answer("resident_state", "other state", "en") == ("resident_state", "other state")
    assert _parse_answer("resident_state", "इतर राज्य", "mr") == ("resident_state", "other state")
    assert _parse_answer("resident_state", "अन्य राज्य", "hi") == ("resident_state", "other state")


# --------------------------------------------------------------------------
# 4. Uncertainty & Three-Valued Logic Protection
# --------------------------------------------------------------------------

def test_uncertainty_preservation_and_clarification():
    uncertain_answers = [
        ("maybe", "en"),
        ("I think so", "en"),
        ("I'm not sure", "en"),
        ("dont know", "en"),
        ("कदाचित", "mr"),
        ("माहित नाही", "mr"),
        ("सांगू शकत नाही", "mr"),
        ("शायद", "hi"),
        ("पता नहीं", "hi"),
        ("कह नहीं सकते", "hi"),
    ]
    for text, lang in uncertain_answers:
        res = interpret_boolean_slot(text, "bpl", lang)
        assert res.is_uncertain is True, f"Failed on '{text}'"
        assert res.value is None, f"Three-valued logic violated on '{text}' - value must be None"
        # Never convert uncertain speech to true or false
        with pytest.raises(ValueError):
            _parse_answer("bpl", text, lang)


def test_contradiction_detection():
    contradictions = [
        ("yes no", "en"),
        ("yes but no", "en"),
        ("हो नाही", "mr"),
        ("हाँ नहीं", "hi"),
    ]
    for text, lang in contradictions:
        res = interpret_boolean_slot(text, "has_disability", lang)
        assert res.is_uncertain is True, f"Failed to detect contradiction in '{text}'"
        assert res.value is None
        with pytest.raises(ValueError):
            _parse_answer("has_disability", text, lang)


# --------------------------------------------------------------------------
# 5. Numerals, Lakh/Crore, and Indian Fractional Amounts
# --------------------------------------------------------------------------

def test_indian_fractional_lakh_amounts():
    # 2.5 lakh
    assert _parse_answer("annual_family_income", "two and a half lakh", "en") == ("annual_family_income", 250000)
    assert _parse_answer("annual_family_income", "अडीच लाख", "mr") == ("annual_family_income", 250000)
    assert _parse_answer("annual_family_income", "ढाई लाख", "hi") == ("annual_family_income", 250000)

    # 1.5 lakh
    assert _parse_answer("annual_family_income", "one and a half lakh", "en") == ("annual_family_income", 150000)
    assert _parse_answer("annual_family_income", "दीड लाख", "mr") == ("annual_family_income", 150000)
    assert _parse_answer("annual_family_income", "डेढ़ लाख", "hi") == ("annual_family_income", 150000)

    # 3.5 lakh
    assert _parse_answer("annual_family_income", "three and a half lakh", "en") == ("annual_family_income", 350000)
    assert _parse_answer("annual_family_income", "साडेतीन लाख", "mr") == ("annual_family_income", 350000)
    assert _parse_answer("annual_family_income", "साढ़े तीन लाख", "hi") == ("annual_family_income", 350000)


def test_spoken_age_and_income_expressions():
    assert _parse_answer("age_years", "around 25 years old", "en") == ("age_years", 25)
    assert _parse_answer("age_years", "२५ वर्षे", "mr") == ("age_years", 25)
    assert _parse_answer("age_years", "पच्चीस साल - 25", "hi") == ("age_years", 25)
    assert _parse_answer("annual_family_income", "about 2.5 lakh annually", "en") == ("annual_family_income", 250000)
    assert _parse_answer("annual_family_income", "साधारण २.५ लाख", "mr") == ("annual_family_income", 250000)
    assert _parse_answer("annual_family_income", "लगभग ३ करोड़", "hi") == ("annual_family_income", 30000000)


# --------------------------------------------------------------------------
# 6. Gender Recognition and Transition Regression Tests
# --------------------------------------------------------------------------

def test_male_gender_recognition_english():
    male_cases = [
        "male",
        "I am male",
        "I'm male",
        "I'm a male",
        "I am a man",
        "Man",
        "boy",
        "male citizen",
        "he",
        "him",
    ]
    for text in male_cases:
        res = interpret_gender_slot(text, "en")
        assert res.value == "male", f"Failed to recognize male in '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("gender", text, "en") == ("gender", "male")


def test_male_gender_recognition_marathi_and_hindi():
    marathi_male = [
        "पुरुष",
        "मी पुरुष आहे",
        "मी एक पुरुष आहे",
        "मी पुरुष",
        "मी मुलगा आहे",
        "मुलगा",
    ]
    for text in marathi_male:
        res = interpret_gender_slot(text, "mr")
        assert res.value == "male", f"Failed on Marathi male '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("gender", text, "mr") == ("gender", "male")

    hindi_male = [
        "पुरुष",
        "मैं पुरुष हूँ",
        "मैं एक पुरुष हूँ",
        "मैं पुरुष",
        "आदमी",
        "लड़का",
        "मैं लड़का हूँ",
    ]
    for text in hindi_male:
        res = interpret_gender_slot(text, "hi")
        assert res.value == "male", f"Failed on Hindi male '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("gender", text, "hi") == ("gender", "male")


def test_female_gender_recognition_multilingual():
    english_female = [
        "female",
        "I am female",
        "I'm female",
        "I'm a female",
        "I am a woman",
        "woman",
        "lady",
        "girl",
        "she",
        "her",
    ]
    for text in english_female:
        res = interpret_gender_slot(text, "en")
        assert res.value == "female", f"Failed on English female '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("gender", text, "en") == ("gender", "female")

    marathi_female = [
        "महिला",
        "मी महिला आहे",
        "मी एक महिला आहे",
        "मी स्त्री आहे",
        "स्त्री",
        "मी मुलगी आहे",
        "मुलगी",
    ]
    for text in marathi_female:
        res = interpret_gender_slot(text, "mr")
        assert res.value == "female", f"Failed on Marathi female '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("gender", text, "mr") == ("gender", "female")

    hindi_female = [
        "महिला",
        "मैं महिला हूँ",
        "मैं एक महिला हूँ",
        "मैं स्त्री हूँ",
        "स्त्री",
        "औरत",
        "लड़की",
        "मैं लड़की हूँ",
    ]
    for text in hindi_female:
        res = interpret_gender_slot(text, "hi")
        assert res.value == "female", f"Failed on Hindi female '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("gender", text, "hi") == ("gender", "female")


def test_male_female_strict_distinction():
    # Boundary matcher check: "male" must NEVER match inside "female"
    assert interpret_gender_slot("female", "en").value == "female"
    assert interpret_gender_slot("female", "en").value != "male"
    assert interpret_gender_slot("female citizen", "en").value == "female"
    assert interpret_gender_slot("female citizen", "en").value != "male"

    assert interpret_gender_slot("male", "en").value == "male"
    assert interpret_gender_slot("male", "en").value != "female"
    assert interpret_gender_slot("male citizen", "en").value == "male"
    assert interpret_gender_slot("male citizen", "en").value != "female"


def test_other_gender_recognition():
    other_cases = [
        ("other", "en"),
        ("non-binary", "en"),
        ("transgender", "en"),
        ("third gender", "en"),
        ("इतर", "mr"),
        ("तृतीयपंथी", "mr"),
        ("अन्य", "hi"),
    ]
    for text, lang in other_cases:
        res = interpret_gender_slot(text, lang)
        assert res.value == "other", f"Failed on other '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("gender", text, lang) == ("gender", "other")


def test_prefer_not_to_say_preservation():
    pnts_cases = [
        ("prefer not to say", "en"),
        ("prefer_not_to_say", "en"),
        ("dont want to say", "en"),
        ("don't want to say", "en"),
        ("सांगू इच्छित नाही", "mr"),
        ("बताना नहीं चाहते", "hi"),
    ]
    for text, lang in pnts_cases:
        res = interpret_gender_slot(text, lang)
        assert res.value == "prefer_not_to_say", f"Failed on prefer not to say '{text}'"
        assert res.is_uncertain is False
        assert _parse_answer("gender", text, lang) == ("gender", "prefer_not_to_say")

    # Verify domain CitizenProfile model validator preserves prefer_not_to_say -> None
    from scheme_navigator.domain.models import CitizenProfile
    profile = CitizenProfile(gender="prefer_not_to_say")
    assert profile.gender is None
    profile2 = CitizenProfile(gender="prefer not to say")
    assert profile2.gender is None


def test_ambiguous_and_uncertain_gender_responses():
    ambiguous = [
        ("maybe", "en"),
        ("not sure", "en"),
        ("don't know", "en"),
        ("I think so", "en"),
        ("कदाचित", "mr"),
        ("नक्की माहित नाही", "mr"),
        ("शायद", "hi"),
        ("पता नहीं", "hi"),
    ]
    for text, lang in ambiguous:
        res = interpret_gender_slot(text, lang)
        assert res.is_uncertain is True, f"Failed to mark '{text}' as uncertain"
        assert res.value is None, f"Three-valued logic violated on '{text}': value must be None"
        with pytest.raises(ValueError):
            _parse_answer("gender", text, lang)


def test_successful_transition_to_next_question_after_gender():
    from fastapi.testclient import TestClient
    from scheme_navigator.api.main import app

    with TestClient(app) as client:
        thread_id = "test-gender-transition-thread"

        # Start an interview where gender is a candidate question
        start_res = client.post("/interview/start", json={
            "thread_id": thread_id,
            "language": "en",
            "profile": {
                "resident_state": "maharashtra",
                "age_years": 25,
                "annual_family_income": 120000,
            }
        })
        assert start_res.status_code == 200
        start_data = start_res.json()

        # The next question chosen should be gender or another slot
        current_q = start_data.get("question")
        assert current_q is not None

        if current_q["field"] != "gender":
            # Answer until gender is reached
            ans_res = client.post("/interview/answer", json={
                "thread_id": thread_id,
                "answer": "yes",
                "language": "en"
            })
            assert ans_res.status_code == 200
            current_q = ans_res.json().get("question")

        assert current_q is not None
        assert current_q["field"] == "gender"
        assert current_q.get("validation_error") is None

        # Now answer "male"
        gender_ans_res = client.post("/interview/answer", json={
            "thread_id": thread_id,
            "answer": "male",
            "language": "en"
        })
        assert gender_ans_res.status_code == 200
        data = gender_ans_res.json()

        # Gender must be saved in the profile as "male"
        assert data["profile"]["gender"] == "male"

        # The interview MUST advance: next question must NOT be "gender"
        next_q = data.get("question")
        if next_q is not None:
            assert next_q["field"] != "gender", "Answering male failed to advance past the gender question!"
        else:
            # Or interview completed successfully
            assert data["complete"] is True

