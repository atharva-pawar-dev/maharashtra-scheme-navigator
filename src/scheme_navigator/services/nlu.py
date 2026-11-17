from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from scheme_navigator.domain.models import Language

logger = logging.getLogger("scheme_navigator.nlu")

DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


@dataclass(frozen=True)
class InterpretationResult:
    """Structured result of natural language answer interpretation."""

    value: Any | None
    is_uncertain: bool
    semantic_confidence: float
    clarification_prompt: str | None = None
    canonical_representation: str | None = None


def _normalize_text(text: str) -> str:
    """Convert Devanagari numerals to ASCII, lowercase, and normalize whitespace."""
    ascii_text = text.translate(DEVANAGARI_DIGITS)
    return re.sub(r"\s+", " ", ascii_text.strip().casefold())


_normalize_devanagari_digits = _normalize_text


def _matches_pattern(pattern: str, text: str) -> bool:
    """Matches pattern respecting ASCII word boundaries and Indic Unicode script boundaries."""
    wrapped = rf"(?:^|[^\w\u0900-\u097F])(?:{pattern})(?:$|[^\w\u0900-\u097F])"
    return bool(re.search(wrapped, text))


def _has_uncertainty(text: str) -> bool:
    """Detect expressions of uncertainty, doubt, or lack of knowledge."""
    uncertainty_patterns = [
        # English
        r"maybe|perhaps|probably|could be|might be",
        r"i think|think so|i guess|guess so",
        r"not sure|im not sure|i'm not sure|not really sure|not certain|uncertain",
        r"dont know|don't know|dont remember|don't remember|cant say|can't say|cannot say",
        r"hard to say|who knows|no idea",
        # Marathi
        r"माहित नाही|माहीत नाही|नक्की सांगता येत नाही|नक्की माहित नाही|आठवत नाही",
        r"कदाचित|असेल कदाचित|शंका आहे|सांगू शकत नाही|खात्री नाही|माहीत नसावे",
        # Hindi
        r"पता नहीं|मालूम नहीं|याद नहीं|कह नहीं सकते|पक्का नहीं|निश्चित नहीं",
        r"शायद|हो सकता है|लगता तो है|संभवतः|संशय है|स्पष्ट नहीं",
    ]
    for pattern in uncertainty_patterns:
        if _matches_pattern(pattern, text):
            return True
    return False


def _has_contradiction(text: str) -> bool:
    """Detect conflicting statements in the same answer (e.g., 'yes no', 'yes wait no')."""
    patterns = [
        r"yes\s+no|no\s+yes",
        r"yes\s+but\s+no|no\s+wait\s+yes|yes\s+wait\s+no",
        r"हो\s+नाही|नाही\s+हो|होय\s+नाही",
        r"हाँ\s+नहीं|नहीं\s+हाँ|जी\s+हाँ\s+नहीं",
    ]
    for pattern in patterns:
        if _matches_pattern(pattern, text):
            return True
    return False


def _get_clarification_prompt(slot: str, language: str) -> str:
    prompts = {
        "resident_state": {
            "mr": "कृपया आपण महाराष्ट्रात राहता का ते स्पष्ट करा (हो किंवा नाही).",
            "hi": "कृपया स्पष्ट करें कि क्या आप महाराष्ट्र में रहते हैं (हाँ या नहीं)।",
            "en": "Could you please clarify whether you currently reside in Maharashtra (Yes or Other state)?",
        },
        "gender": {
            "mr": "कृपया आपले लिंग स्पष्ट करा (महिला, पुरुष किंवा इतर).",
            "hi": "कृपया अपना लिंग स्पष्ट करें (महिला, पुरुष या अन्य)।",
            "en": "Could you please clarify your gender (Female, Male, Other, or Prefer not to say)?",
        },
        "age_years": {
            "mr": "कृपया एक संख्या प्रविष्ट करा (उदा. २५).",
            "hi": "कृपया एक संख्या दर्ज करें (उदा. 25)।",
            "en": "Please provide a number (e.g. 25).",
        },
        "annual_family_income": {
            "mr": "कृपया कुटुंबाचे वार्षिक उत्पन्न आकड्यात सांगा (संख्या प्रविष्ट करा).",
            "hi": "कृपया परिवार की वार्षिक आय संख्या में बताएं (संख्या दर्ज करें)।",
            "en": "Please provide a valid annual income amount.",
        },
    }
    default_boolean_prompts = {
        "mr": "कृपया आपले उत्तर स्पष्ट करा (हो किंवा नाही).",
        "hi": "कृपया अपना उत्तर स्पष्ट करें (हाँ या नहीं)।",
        "en": "Could you please clarify your answer with Yes or No?",
    }
    if slot in prompts:
        return prompts[slot].get(language, prompts[slot]["en"])
    return default_boolean_prompts.get(language, default_boolean_prompts["en"])


def interpret_boolean_slot(text: str, slot: str, language: str = "en") -> InterpretationResult:
    """Context-aware interpretation of natural language Boolean answers."""
    norm = _normalize_text(text)

    # 1. Contradiction check
    if _has_contradiction(norm):
        return InterpretationResult(
            value=None,
            is_uncertain=True,
            semantic_confidence=0.3,
            clarification_prompt=_get_clarification_prompt(slot, language),
        )

    # 2. Uncertainty check (Three-valued logic protection: Never convert uncertain into true/false!)
    if _has_uncertainty(norm):
        return InterpretationResult(
            value=None,
            is_uncertain=True,
            semantic_confidence=0.2,
            clarification_prompt=_get_clarification_prompt(slot, language),
        )

    # 3. Definite Negation patterns (English, Marathi, Hindi)
    negation_patterns = [
        # Strong English negation
        r"definitely not|absolutely not|certainly not|not at all|never",
        r"i don't|i do not|i never do|i am not|we are not|we don't|i dont|we dont",
        r"no i am not|no i don't|no we don't|no i haven't|dont have|don't have",
        r"no|nope|nah|false",
        r"not",
        # Strong Marathi negation
        r"मुळीच नाही|कधीच नाही|बिलकुल नाही|नक्कीच नाही",
        r"मी विद्यार्थी नाही|जोडलेले नाही|मिळत नाही|नाही मिळत|नाही राहत|नाहीत|नव्हे",
        r"दारिद्र्यरेषेखाली नाही|माझ्याकडे नाही|नाही",
        # Strong Hindi negation
        r"बिल्कुल नहीं|बिलकुल नहीं|कतई नहीं|कभी नहीं|निश्चित रूप से नहीं",
        r"मैं छात्र नहीं हूँ|नहीं जुड़ा है|नहीं मिलती|नहीं है|नहीं रहता|नहीं हूँ",
        r"जी नहीं|नहीं|ना",
    ]
    for pattern in negation_patterns:
        if _matches_pattern(pattern, norm):
            return InterpretationResult(
                value=False,
                is_uncertain=False,
                semantic_confidence=0.95,
                canonical_representation="no",
            )

    # 4. Definite Affirmation patterns (English, Marathi, Hindi)
    affirmation_patterns = [
        # Strong English affirmation
        r"definitely|absolutely|certainly|of course|sure|surely|indeed",
        r"yup|yeah|yep|aye|correct|that's right|thats right",
        r"i do|i certainly do|i am|we are|we do|i have|it is|already done",
        r"yes i am|yes i have|yes we are|yes it is|yes i do",
        r"yes|true",
        # Strong Marathi affirmation
        r"नक्कीच|होय नक्कीच|नक्की|खात्रीने|अवश्य",
        r"मी विद्यार्थी आहे|खाते जोडलेले आहे|मिळते|होय मिळते|आहे|होय आहे",
        r"दारिद्र्यरेषेखाली आहे|माझ्याकडे आहे|आहोत|हो|होय",
        # Strong Hindi affirmation
        r"बिल्कुल|बिलकुल|ज़रूर|जरूर|निश्चित रूप से|हाँ बिल्कुल",
        r"मैं छात्र हूँ|खाता जुड़ा हुआ है|मिलती है|हाँ मिलती है|जुड़ा है|हाँ है",
        r"बीपीएल में हैं|हाँजी|जी हाँ|हाँ|जी",
    ]
    for pattern in affirmation_patterns:
        if _matches_pattern(pattern, norm):
            return InterpretationResult(
                value=True,
                is_uncertain=False,
                semantic_confidence=0.95,
                canonical_representation="yes",
            )

    # 5. Unrecognized / Ambiguous response
    return InterpretationResult(
        value=None,
        is_uncertain=True,
        semantic_confidence=0.2,
        clarification_prompt=_get_clarification_prompt(slot, language),
    )


def interpret_resident_state(text: str, language: str = "en") -> InterpretationResult:
    """Context-aware interpretation for Maharashtra residence question."""
    norm = _normalize_text(text)

    # Contradiction / Uncertainty
    if _has_contradiction(norm) or _has_uncertainty(norm):
        return InterpretationResult(
            value=None,
            is_uncertain=True,
            semantic_confidence=0.3,
            clarification_prompt=_get_clarification_prompt("resident_state", language),
        )

    # Negation of Maharashtra residence
    negation_of_mh = [
        r"definitely don't live in maharashtra|don't live in maharashtra|dont live in maharashtra",
        r"do not live in maharashtra|not in maharashtra|outside maharashtra",
        r"i live in (?!maharashtra)[a-z]+|i am from (?!maharashtra)[a-z]+",
        r"other state|another state|different state",
        r"नाही मी महाराष्ट्रात राहत नाही|महाराष्ट्रात राहत नाही|महाराष्ट्राबाहेर|इतर राज्य",
        r"नहीं मैं महाराष्ट्र में नहीं रहता|महाराष्ट्र में नहीं रहता|महाराष्ट्र के बाहर|अन्य राज्य",
    ]
    for pattern in negation_of_mh:
        if _matches_pattern(pattern, norm):
            return InterpretationResult(
                value="other state",
                is_uncertain=False,
                semantic_confidence=0.95,
                canonical_representation="Other state",
            )

    # Affirmation of Maharashtra residence
    affirmation_of_mh = [
        r"live in maharashtra|reside in maharashtra|in maharashtra|from maharashtra",
        r"yeah, absolutely, i live in maharashtra|absolutely i live in maharashtra",
        r"yes i live in maharashtra|yes i reside in maharashtra",
        r"maharashtra|mh",
        r"महाराष्ट्रात राहतो|महाराष्ट्रात राहते|होय मी महाराष्ट्रात|महाराष्ट्रात आहे|महाराष्ट्र",
        r"महाराष्ट्र में रहता हूँ|महाराष्ट्र में रहती हूँ|हाँ मैं महाराष्ट्र|महाराष्ट्र में हूँ",
    ]
    for pattern in affirmation_of_mh:
        if _matches_pattern(pattern, norm):
            return InterpretationResult(
                value="maharashtra",
                is_uncertain=False,
                semantic_confidence=0.95,
                canonical_representation="Maharashtra",
            )

    # Fallback to general boolean check (e.g. citizen answered "yes" or "no")
    bool_res = interpret_boolean_slot(text, "resident_state", language)
    if bool_res.value is True:
        return InterpretationResult(
            value="maharashtra",
            is_uncertain=False,
            semantic_confidence=bool_res.semantic_confidence,
            canonical_representation="Maharashtra",
        )
    if bool_res.value is False:
        return InterpretationResult(
            value="other state",
            is_uncertain=False,
            semantic_confidence=bool_res.semantic_confidence,
            canonical_representation="Other state",
        )

    return InterpretationResult(
        value=None,
        is_uncertain=True,
        semantic_confidence=0.2,
        clarification_prompt=_get_clarification_prompt("resident_state", language),
    )


def interpret_gender_slot(text: str, language: str = "en") -> InterpretationResult:
    """Context-aware interpretation for gender with Devanagari and English boundary support."""
    norm = _normalize_text(text)

    # 1. Uncertainty check (Three-valued logic protection: Uncertain answers remain unknown)
    if _has_uncertainty(norm):
        return InterpretationResult(
            value=None,
            is_uncertain=True,
            semantic_confidence=0.3,
            clarification_prompt=_get_clarification_prompt("gender", language),
        )

    # 2. Prefer not to say
    prefer_not_to_say_patterns = [
        r"prefer not to say|prefer_not_to_say|prefer to not say",
        r"dont want to say|don't want to say|rather not say|keep private|private|confidential",
        r"सांगू इच्छित नाही|सांगायचे नाही|सांगायचं नाही",
        r"बताना नहीं चाहते|बताना नहीं चाहती|नहीं बताना चाहते",
    ]
    for pattern in prefer_not_to_say_patterns:
        if _matches_pattern(pattern, norm):
            return InterpretationResult(
                value="prefer_not_to_say",
                is_uncertain=False,
                semantic_confidence=0.95,
                canonical_representation="prefer_not_to_say",
            )

    # 3. Female patterns (distinguished from male with explicit boundaries)
    female_patterns = [
        r"i am female|i am a female|i'm female|i'm a female|female citizen|female",
        r"i am a woman|i'm a woman|i am woman|a woman|woman|lady|girl",
        r"she|her|hers",
        r"मी महिला आहे|मी एक महिला आहे|मी महिला|महिला",
        r"मी स्त्री आहे|मी एक स्त्री आहे|मी स्त्री|स्त्री",
        r"मी मुलगी आहे|मी मुलगी|मुलगी|स्त्रीलिंग",
        r"मैं महिला हूँ|मैं एक महिला हूँ|मैं महिला हु|मैं महिला|महिला",
        r"मैं स्त्री हूँ|मैं एक स्त्री हूँ|मैं स्त्री हु|मैं स्त्री|स्त्री",
        r"मैं लड़की हूँ|मैं एक लड़की हूँ|लड़की|औरत|नारी|स्त्रीलिंग",
    ]
    for pattern in female_patterns:
        if _matches_pattern(pattern, norm):
            return InterpretationResult(
                value="female",
                is_uncertain=False,
                semantic_confidence=0.95,
                canonical_representation="female",
            )

    # 4. Male patterns (safe from substring overlap with female)
    male_patterns = [
        r"i am male|i am a male|i'm male|i'm a male|male citizen|male",
        r"i am a man|i'm a man|i am man|a man|man|gentleman|boy",
        r"he|him|his",
        r"मी पुरुष आहे|मी एक पुरुष आहे|मी पुरुष|पुरुष",
        r"मी मुलगा आहे|मी मुलगा|मुलगा|पुल्लिंग",
        r"मैं पुरुष हूँ|मैं एक पुरुष हूँ|मैं पुरुष हु|मैं पुरुष|पुरुष",
        r"मैं लड़का हूँ|मैं एक लड़का हूँ|लड़का|आदमी|मर्द|नर|पुल्लिंग",
    ]
    for pattern in male_patterns:
        if _matches_pattern(pattern, norm):
            return InterpretationResult(
                value="male",
                is_uncertain=False,
                semantic_confidence=0.95,
                canonical_representation="male",
            )

    # 5. Other gender identity
    other_patterns = [
        r"other|non-binary|non binary|transgender|trans|third gender|genderqueer",
        r"इतर|अन्य|तृतीयपंथी",
    ]
    for pattern in other_patterns:
        if _matches_pattern(pattern, norm):
            return InterpretationResult(
                value="other",
                is_uncertain=False,
                semantic_confidence=0.9,
                canonical_representation="other",
            )

    # 6. Ambiguous / Unrecognized response
    return InterpretationResult(
        value=None,
        is_uncertain=True,
        semantic_confidence=0.2,
        clarification_prompt=_get_clarification_prompt("gender", language),
    )


def interpret_number_slot(text: str, slot: str, language: str = "en") -> InterpretationResult:
    """Parse numeric quantities including Indian terminology, fractions, and digits."""
    norm = _normalize_text(text)

    if _has_uncertainty(norm):
        return InterpretationResult(
            value=None,
            is_uncertain=True,
            semantic_confidence=0.3,
            clarification_prompt=_get_clarification_prompt(slot, language),
        )

    # 1. Indian fractional lakh expressions for annual family income:
    fraction_map = {
        r"(?:two and a half|2\.5)\s*(?:lakh|lac|lakhs|lacs|लाख|लाख़)": 250000,
        r"(?:अडीच|ढाई)\s*(?:लाख|लाख़|lakh)": 250000,
        r"(?:one and a half|1\.5)\s*(?:lakh|lac|lakhs|lacs|लाख|लाख़)": 150000,
        r"(?:दीड|डेढ़)\s*(?:लाख|लाख़|lakh)": 150000,
        r"(?:three and a half|3\.5)\s*(?:lakh|lac|lakhs|lacs|लाख|लाख़)": 350000,
        r"(?:साडेतीन|साढ़े\s*तीन)\s*(?:लाख|लाख़|lakh)": 350000,
        r"(?:four and a half|4\.5)\s*(?:lakh|lac|lakhs|lacs|लाख|लाख़)": 450000,
        r"(?:साडेचार|साढ़े\s*चार)\s*(?:लाख|लाख़|lakh)": 450000,
    }
    if slot == "annual_family_income":
        for pattern, amount in fraction_map.items():
            if _matches_pattern(pattern, norm):
                return InterpretationResult(
                    value=amount,
                    is_uncertain=False,
                    semantic_confidence=0.95,
                    canonical_representation=str(amount),
                )

    # 2. General lakh / crore regex (e.g. "around 2.5 lakh", "3 crore", "१० करोड")
    clean_income = (
        norm.replace(",", "")
        .replace("₹", "")
        .replace("rs.", "")
        .replace("inr", "")
        .replace("रुपये", "")
        .replace("रु.", "")
        .replace("रु", "")
    )
    if slot == "annual_family_income":
        lakh_match = re.search(
            r"([0-9]+(?:\.[0-9]+)?)\s*(?:lakh|lac|lakhs|lacs|लाख|लाख़)(?:\s|$|[^\w\u0900-\u097F])",
            clean_income,
        )
        if lakh_match:
            try:
                val = int(float(lakh_match.group(1)) * 100_000)
                return InterpretationResult(
                    value=val,
                    is_uncertain=False,
                    semantic_confidence=0.95,
                    canonical_representation=str(val),
                )
            except ValueError:
                pass

        crore_match = re.search(
            r"([0-9]+(?:\.[0-9]+)?)\s*(?:crore|crores|cr|करोड़|करोड)(?:\s|$|[^\w\u0900-\u097F])",
            clean_income,
        )
        if crore_match:
            try:
                val = int(float(crore_match.group(1)) * 10_000_000)
                return InterpretationResult(
                    value=val,
                    is_uncertain=False,
                    semantic_confidence=0.95,
                    canonical_representation=str(val),
                )
            except ValueError:
                pass

    # 3. Direct numeric extraction (handles "२५", "६० वर्षे", "18 completed years", "१,५०,०००")
    digits_match = re.search(r"([0-9]{1,10})", clean_income.replace(",", ""))
    if digits_match:
        try:
            val = int(digits_match.group(1))
            return InterpretationResult(
                value=val,
                is_uncertain=False,
                semantic_confidence=0.95,
                canonical_representation=str(val),
            )
        except ValueError:
            pass

    # 4. If no numeric digits found in input (e.g., text like "वीस", "बीस", "अस्पष्ट"),
    # return uncertain with localized clarification prompt
    return InterpretationResult(
        value=None,
        is_uncertain=True,
        semantic_confidence=0.2,
        clarification_prompt=_get_clarification_prompt(slot, language),
    )


def interpret_answer(slot: str, answer_text: str, language: str = "en") -> tuple[str, Any]:
    """
    Main entry point for natural language answer interpretation.
    Returns (slot, canonical_value).
    Raises ValueError with a helpful clarification prompt if uncertain or invalid.
    """
    if not answer_text or not answer_text.strip():
        raise ValueError(_get_clarification_prompt(slot, language))

    # Boolean slots
    if slot in {
        "aadhaar_linked_bank_account",
        "bpl",
        "receiving_other_pension",
        "is_student",
        "has_disability",
        "has_land",
    }:
        res = interpret_boolean_slot(answer_text, slot, language)
        if res.is_uncertain or res.value is None:
            raise ValueError(res.clarification_prompt or _get_clarification_prompt(slot, language))
        return slot, res.value

    # Resident state
    if slot == "resident_state":
        res = interpret_resident_state(answer_text, language)
        if res.is_uncertain or res.value is None:
            raise ValueError(res.clarification_prompt or _get_clarification_prompt(slot, language))
        return slot, res.value

    # Gender
    if slot == "gender":
        res = interpret_gender_slot(answer_text, language)
        if res.is_uncertain or res.value is None:
            raise ValueError(res.clarification_prompt or _get_clarification_prompt(slot, language))
        return slot, res.value

    # Numeric slots
    if slot in {"age_years", "annual_family_income", "disability_percentage", "landholding_hectares"}:
        res = interpret_number_slot(answer_text, slot, language)
        if res.is_uncertain or res.value is None:
            raise ValueError(res.clarification_prompt or _get_clarification_prompt(slot, language))
        return slot, res.value

    # Fallback to normalized string
    return slot, answer_text.strip()
