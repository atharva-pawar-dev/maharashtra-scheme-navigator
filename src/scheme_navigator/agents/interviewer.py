from __future__ import annotations

import math
import os
import re
from typing import Any, TypedDict

# Restrict deserialization of persisted checkpoint payloads.
os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

try:
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import Command as _LangGraphCommand, interrupt
    Command = _LangGraphCommand
    HAS_LANGGRAPH = True
except ImportError:  # deterministic local fallback for environments where dependencies cannot be installed
    HAS_LANGGRAPH = False

    class Command:
        def __init__(self, resume: str | None = None):
            self.resume = resume

    class _FakeInterrupt:
        def __init__(self, value: dict[str, Any]):
            self.value = value


from scheme_navigator.domain.models import CitizenProfile, Language, Scheme
from scheme_navigator.services.nlu import DEVANAGARI_DIGITS, _normalize_devanagari_digits, interpret_answer
from scheme_navigator.services.rule_engine import (
    evaluate_node,
    has_non_demo_approval_metadata,
)


class InterviewState(TypedDict, total=False):
    thread_id: str
    language: str
    mode: str
    target_scheme_id: str | None
    profile: dict[str, Any]
    candidate_schemes: list[dict[str, Any]]
    pending_answer: str | None
    next_question: dict[str, Any] | None
    asked_fields: list[str]
    events: list[dict[str, Any]]
    is_complete: bool
    result_summary: list[dict[str, Any]]
    error: dict[str, Any] | None


QUESTION_SPECS: dict[str, dict[str, Any]] = {
    "resident_state": {
        "kind": "text", "choices": ["Maharashtra", "Other state"],
        "labels": {"en": "Do you currently reside in Maharashtra?", "mr": "तुम्ही सध्या महाराष्ट्रात राहता का?", "hi": "क्या आप वर्तमान में महाराष्ट्र में रहते हैं?"},
        "choice_labels": {
            "mr": {"Maharashtra": "महाराष्ट्र", "Other state": "इतर राज्य"},
            "hi": {"Maharashtra": "महाराष्ट्र", "Other state": "अन्य राज्य"},
        },
    },
    "gender": {
        "kind": "enum", "choices": ["female", "male", "other", "prefer_not_to_say"],
        "labels": {"en": "What is your gender?", "mr": "तुमचे लिंग काय आहे?", "hi": "आपका लिंग क्या है?"},
        "choice_labels": {
            "mr": {"female": "महिला", "male": "पुरुष", "other": "इतर", "prefer_not_to_say": "सांगू इच्छित नाही"},
            "hi": {"female": "महिला", "male": "पुरुष", "other": "अन्य", "prefer_not_to_say": "बताना नहीं चाहते"},
        },
    },
    "age_years": {
        "kind": "integer", "choices": [],
        "labels": {"en": "How old are you (in completed years)?", "mr": "तुमचे पूर्ण वय किती वर्षे आहे?", "hi": "आपकी पूरी उम्र कितने वर्ष है?"},
    },
    "annual_family_income": {
        "kind": "integer", "choices": [],
        "labels": {"en": "What is your family's approximate annual income in INR?", "mr": "तुमच्या कुटुंबाचे अंदाजे वार्षिक उत्पन्न किती रुपये आहे?", "hi": "आपके परिवार की अनुमानित वार्षिक आय कितनी रुपये है?"},
    },
    "aadhaar_linked_bank_account": {
        "kind": "bool", "choices": ["yes", "no"],
        "labels": {"en": "Is your bank account Aadhaar-linked? Do not share your Aadhaar number.", "mr": "तुमचे बँक खाते आधारशी जोडलेले आहे का? आधार क्रमांक सांगू नका.", "hi": "क्या आपका बैंक खाता आधार से जुड़ा है? आधार नंबर साझा न करें।"},
        "choice_labels": {
            "mr": {"yes": "होय", "no": "नाही"},
            "hi": {"yes": "हाँ", "no": "नहीं"},
        },
    },
    "bpl": {
        "kind": "bool", "choices": ["yes", "no"],
        "labels": {"en": "Is your family officially listed as Below Poverty Line (BPL)?", "mr": "तुमचे कुटुंब अधिकृतपणे दारिद्र्यरेषेखाली (BPL) नोंदलेले आहे का?", "hi": "क्या आपका परिवार आधिकारिक रूप से गरीबी रेखा से नीचे (BPL) सूचीबद्ध है?"},
        "choice_labels": {
            "mr": {"yes": "होय", "no": "नाही"},
            "hi": {"yes": "हाँ", "no": "नहीं"},
        },
    },
    "receiving_other_pension": {
        "kind": "bool", "choices": ["yes", "no"],
        "labels": {"en": "Are you receiving a pension from another social-security scheme?", "mr": "तुम्हाला दुसऱ्या सामाजिक सुरक्षा योजनेतून पेन्शन मिळते का?", "hi": "क्या आपको किसी अन्य सामाजिक सुरक्षा योजना से पेंशन मिलती है?"},
        "choice_labels": {
            "mr": {"yes": "होय", "no": "नाही"},
            "hi": {"yes": "हाँ", "no": "नहीं"},
        },
    },
    "caste_category": {
        "kind": "text", "choices": ["SC", "ST", "OBC", "VJNT", "SBC", "Open", "Other", "Prefer not to say"],
        "labels": {"en": "Which caste category applies to you (or prefer not to say)?", "mr": "तुमच्यासाठी कोणता जात प्रवर्ग लागू होतो (किंवा सांगू इच्छित नाही)?", "hi": "आप पर कौन-सी जात श्रेणी लागू होती है (या बताना नहीं चाहते)?"},
        "choice_labels": {
            "mr": {"Open": "खुला", "Other": "इतर", "Prefer not to say": "सांगू इच्छित नाही"},
            "hi": {"Open": "सामान्य", "Other": "अन्य", "Prefer not to say": "बताना नहीं चाहते"},
        },
    },
    "is_student": {
        "kind": "bool", "choices": ["yes", "no"],
        "labels": {"en": "Are you currently a student?", "mr": "तुम्ही सध्या विद्यार्थी आहात का?", "hi": "क्या आप वर्तमान में विद्यार्थी हैं?"},
        "choice_labels": {
            "mr": {"yes": "होय", "no": "नाही"},
            "hi": {"yes": "हाँ", "no": "नहीं"},
        },
    },
    "has_disability": {
        "kind": "bool", "choices": ["yes", "no"],
        "labels": {"en": "Do you have a disability certificate or officially recognized disability?", "mr": "तुमच्याकडे दिव्यांग प्रमाणपत्र किंवा अधिकृत दिव्यांगत्व मान्यता आहे का?", "hi": "क्या आपके पास दिव्यांगता प्रमाणपत्र या आधिकारिक मान्यता है?"},
        "choice_labels": {
            "mr": {"yes": "होय", "no": "नाही"},
            "hi": {"yes": "हाँ", "no": "नहीं"},
        },
    },
    "has_land": {
        "kind": "bool", "choices": ["yes", "no"],
        "labels": {"en": "Do you or your family own agricultural land in Maharashtra?", "mr": "तुमच्या किंवा तुमच्या कुटुंबाच्या नावावर महाराष्ट्रात शेतजमीन आहे का?", "hi": "क्या आपके या आपके परिवार के नाम पर महाराष्ट्र में कृषि भूमि है?"},
        "choice_labels": {
            "mr": {"yes": "होय", "no": "नाही"},
            "hi": {"yes": "हाँ", "no": "नहीं"},
        },
    },
    "disability_percentage": {
        "kind": "integer", "choices": [],
        "labels": {"en": "What is your certified disability percentage (e.g. 40)?", "mr": "तुमच्या दिव्यांग प्रमाणपत्रातील टक्केवारी किती आहे (उदा. ४०)?", "hi": "आपके दिव्यांगता प्रमाणपत्र में प्रतिशत कितना है (उदा. 40)?"},
    },
    "marital_status": {
        "kind": "enum", "choices": ["single", "married", "widowed", "divorced"],
        "labels": {"en": "What is your marital status?", "mr": "तुमची वैवाहिक स्थिती काय आहे?", "hi": "आपकी वैवाहिक स्थिति क्या है?"},
        "choice_labels": {
            "mr": {"single": "अविवाहित", "married": "विवाहित", "widowed": "विधवा किंवा विधुर", "divorced": "घटस्फोटित"},
            "hi": {"single": "अविवाहित", "married": "विवाहित", "widowed": "विधवा या विधुर", "divorced": "तलाकशुदा"},
        },
    },
    "ration_card_type": {
        "kind": "enum", "choices": ["aay", "bpl_yellow", "apl_orange", "white", "none"],
        "labels": {"en": "What type of ration card does your family hold?", "mr": "तुमच्या कुटुंबाकडे कोणत्या प्रकारची शिधापत्रिका आहे?", "hi": "आपके परिवार के पास किस प्रकार का राशन कार्ड है?"},
        "choice_labels": {
            "mr": {"aay": "अंत्योदय (AAY)", "bpl_yellow": "पिवळे (BPL)", "apl_orange": "केशरी (APL)", "white": "पांढरे", "none": "नाही"},
            "hi": {"aay": "अंत्योदय (AAY)", "bpl_yellow": "पीला (BPL)", "apl_orange": "केसरिया (APL)", "white": "सफेद", "none": "नहीं"},
        },
    },
    "occupation": {
        "kind": "enum", "choices": ["farmer", "student", "salaried", "self_employed", "unemployed", "other"],
        "labels": {"en": "What is your primary occupation?", "mr": "आपला मुख्य व्यवसाय कोणता आहे?", "hi": "आपका मुख्य व्यवसाय क्या है?"},
        "choice_labels": {
            "mr": {"farmer": "शेतकरी", "student": "विद्यार्थी", "salaried": "वेतनधारक नोकरदार", "self_employed": "स्वयंरोजगार / व्यावसायिक", "unemployed": "बेरोजगार", "other": "इतर"},
            "hi": {"farmer": "किसान", "student": "विद्यार्थी", "salaried": "वेतनभोगी", "self_employed": "स्वरोजगार", "unemployed": "बेरोजगार", "other": "अन्य"},
        },
    },
    "landholding_hectares": {
        "kind": "float", "choices": [],
        "labels": {"en": "How many hectares of agricultural land do you or your family hold?", "mr": "आपल्या किंवा आपल्या कुटुंबाच्या नावावर किती हेक्टर शेतजमीन आहे?", "hi": "आपके या आपके परिवार के नाम पर कितने हेक्टेयर कृषि भूमि है?"},
    },
    "district": {
        "kind": "text", "choices": ["Pune", "Mumbai", "Thane", "Nagpur", "Nashik", "Chhatrapati Sambhajinagar", "Kolhapur", "Solapur", "Amravati", "Other"],
        "labels": {"en": "Which district of Maharashtra do you reside in?", "mr": "तुम्ही महाराष्ट्रातील कोणत्या जिल्ह्यात राहता?", "hi": "आप महाराष्ट्र के किस जिले में रहते हैं?"},
        "choice_labels": {
            "mr": {"Pune": "पुणे", "Mumbai": "मुंबई", "Thane": "ठाणे", "Nagpur": "नागपूर", "Nashik": "नाशिक", "Chhatrapati Sambhajinagar": "छत्रपती संभाजीनगर", "Kolhapur": "कोल्हापूर", "Solapur": "सोलापूर", "Amravati": "अमरावती", "Other": "इतर"},
            "hi": {"Pune": "पुणे", "Mumbai": "मुंबई", "Thane": "ठाणे", "Nagpur": "नागपुर", "Nashik": "नासिक", "Chhatrapati Sambhajinagar": "छत्रपति संभाजीनगर", "Kolhapur": "कोल्हापुर", "Solapur": "सोलापूर", "Amravati": "अमरावती", "Other": "अन्य"},
        },
    },
    "local_government_type": {
        "kind": "enum", "choices": ["municipal_corporation", "municipal_council", "nagar_panchayat", "gram_panchayat"],
        "labels": {"en": "What type of local government covers your place of residence?", "mr": "तुमचे निवासस्थान कोणत्या स्थानिक स्वराज्य संस्थेच्या हद्दीत येते?", "hi": "आपका निवास स्थान किस स्थानीय स्वशासन निकाय के अंतर्गत आता है?"},
        "choice_labels": {
            "mr": {"municipal_corporation": "महानगरपालिका (Municipal Corporation)", "municipal_council": "नगरपरिषद (Municipal Council)", "nagar_panchayat": "नगरपंचायत", "gram_panchayat": "ग्रामपंचायत (Rural / Gram Panchayat)"},
            "hi": {"municipal_corporation": "नगर निगम (Municipal Corporation)", "municipal_council": "नगर परिषद (Municipal Council)", "nagar_panchayat": "नगर पंचायत", "gram_panchayat": "ग्राम पंचायत (ग्रामीण)"},
        },
    },
    "municipal_corporation": {
        "kind": "text", "choices": ["mc-pune", "mc-pimpri-chinchwad", "mc-brihanmumbai", "mc-thane", "mc-navi-mumbai", "mc-nashik", "mc-nagpur", "other"],
        "labels": {"en": "Which Municipal Corporation do you legally reside in?", "mr": "तुम्ही कोणत्या महानगरपालिकेच्या हद्दीत राहता?", "hi": "आप किस नगर निगम के अधिकार क्षेत्र में रहते हैं?"},
        "choice_labels": {
            "mr": {"mc-pune": "पुणे महानगरपालिका (PMC)", "mc-pimpri-chinchwad": "पिंपरी चिंचवड महानगरपालिका (PCMC)", "mc-brihanmumbai": "बृहन्मुंबई महानगरपालिका (BMC)", "mc-thane": "ठाणे महानगरपालिका (TMC)", "mc-navi-mumbai": "नवी मुंबई महानगरपालिका (NMMC)", "mc-nashik": "नाशिक महानगरपालिका", "mc-nagpur": "नागपूर महानगरपालिका", "other": "इतर महानगरपालिका"},
            "hi": {"mc-pune": "पुणे नगर निगम (PMC)", "mc-pimpri-chinchwad": "पिंपरी चिंचवड़ नगर निगम (PCMC)", "mc-brihanmumbai": "बृहन्मुंबई नगर निगम (BMC)", "mc-thane": "ठाणे नगर निगम (TMC)", "mc-navi-mumbai": "नवी मुंबई नगर निगम (NMMC)", "mc-nashik": "नासिक नगर निगम", "mc-nagpur": "नागपुर नगर निगम", "other": "अन्य नगर निगम"},
        },
    },
    "residence_years": {
        "kind": "integer", "choices": [],
        "labels": {"en": "How many years have you resided continuously in your current city / municipality?", "mr": "तुम्ही तुमच्या सध्याच्या शहरात / महापालिका हद्दीत सलग किती वर्षांपासून राहत आहात?", "hi": "आप अपने वर्तमान शहर / नगर पालिका क्षेत्र में लगातार कितने वर्षों से रह रहे हैं?"},
    },
    "ward": {
        "kind": "text", "choices": [],
        "labels": {"en": "What is your municipal ward name or number (optional)?", "mr": "तुमचा प्रभाग किंवा वॉर्ड क्रमांक कोणता आहे (ऐच्छिक)?", "hi": "आपका वार्ड नाम या संख्या क्या है (वैकल्पिक)?"},
    },
}


def _walk_rules(node: dict[str, Any], out: list[tuple[str, str, Any]]) -> None:
    if node.get("field"):
        out.append((node["field"], node["op"], node.get("value")))
    for child in node.get("children", []):
        _walk_rules(child, out)


def _entropy(counts: list[int]) -> float:
    total = sum(counts)
    if total <= 0:
        return 0.0
    return -sum((count / total) * math.log2(count / total) for count in counts if count > 0)


def _slot_rule_field(slot: str) -> str:
    return "age" if slot == "age_years" else slot


def _hypotheses(slot: str, candidate_schemes: list[Scheme]) -> list[Any]:
    if slot in {"aadhaar_linked_bank_account", "bpl", "receiving_other_pension", "is_student", "has_disability", "has_land"}:
        return [True, False]
    if slot == "occupation":
        return ["farmer", "student", "salaried", "self_employed", "unemployed", "other"]
    if slot == "landholding_hectares":
        return [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
    if slot == "gender":
        return ["female", "male", "other"]
    if slot == "resident_state":
        return ["maharashtra", "other state"]
    if slot == "marital_status":
        return ["single", "married", "widowed", "divorced"]
    if slot == "ration_card_type":
        return ["aay", "bpl_yellow", "apl_orange", "white", "none"]
    if slot == "local_government_type":
        return ["municipal_corporation", "municipal_council", "nagar_panchayat", "gram_panchayat"]
    if slot == "municipal_corporation":
        return ["mc-pune", "mc-pimpri-chinchwad", "mc-brihanmumbai", "mc-thane", "mc-navi-mumbai", "mc-nashik", "mc-nagpur", "other"]
    if slot == "residence_years":
        return [1, 3, 5, 10, 15]
    if slot == "district":
        return ["pune", "mumbai", "thane", "nagpur", "nashik", "kolhapur", "solapur", "amravati"]
    if slot == "caste_category":
        values = {"SC", "ST", "OBC", "VJNT", "SBC", "Open", "Other"}
        for scheme in candidate_schemes:
            for field, op, value in _collect_predicates(scheme):
                if field == slot and op == "eq" and isinstance(value, str):
                    values.add(value)
                if field == slot and op == "in" and isinstance(value, list):
                    values.update(str(item) for item in value)
        return list(values)
    if slot in {"age_years", "annual_family_income"}:
        rule_field = _slot_rule_field(slot)
        threshold_values: set[float] = {0, 18, 21, 30, 60, 65} if slot == "age_years" else {0, 100000, 250000, 500000, 800000, 1000000}
        for scheme in candidate_schemes:
            for field, op, value in _collect_predicates(scheme):
                if field == rule_field and op in {"gt", "gte", "lt", "lte", "eq"} and isinstance(value, (int, float)):
                    threshold_values.update({max(0, value - 1), value, value + 1})
        return sorted(int(v) for v in threshold_values if 0 <= v <= (120 if slot == "age_years" else 100_000_000))
    return []


def _collect_predicates(scheme: Scheme) -> list[tuple[str, str, Any]]:
    out: list[tuple[str, str, Any]] = []
    _walk_rules(scheme.eligibility_rule.model_dump(mode="json"), out)
    return out


def information_gain(slot: str, profile: CitizenProfile, schemes: list[Scheme]) -> float:
    """Expected reduction in uncertainty over candidate schemes for a question slot."""
    if profile.value_for_rule(_slot_rule_field(slot)) is not None:
        return 0.0
    applicable = [s for s in schemes if any(field == _slot_rule_field(slot) for field, _, _ in _collect_predicates(s))]
    if len(applicable) < 2:
        # A single scheme can still benefit from a required criterion, but ask it after broader discriminators.
        if len(applicable) == 1 and schemes:
            applicable = schemes
        else:
            return 0.0
    prior_entropy = math.log2(max(1, len(schemes)))
    values = _hypotheses(slot, schemes)
    if len(values) < 2:
        return 0.0
    remaining_entropies: list[float] = []
    for value in values:
        update_field = slot
        updated = profile.model_copy(update={update_field: value})
        if slot == "resident_state":
            updated = profile.model_copy(update={"resident_state": "maharashtra" if str(value).casefold() == "maharashtra" else "other state"})
        survivors = []
        for scheme in schemes:
            result = evaluate_node(scheme.eligibility_rule, updated)

            # Unapproved/demo schemes remain provisional candidates.
            # Only rules with non-demo approval metadata can eliminate them.
            if (
                result.value is not False
                or not has_non_demo_approval_metadata(scheme)
            ):
                survivors.append(scheme.scheme_id)
        remaining_entropies.append(math.log2(max(1, len(survivors))))
    expected = sum(remaining_entropies) / len(remaining_entropies)
    return max(0.0, prior_entropy - expected)


DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _normalize_devanagari_digits(text: str) -> str:
    return text.translate(DEVANAGARI_DIGITS)


def _parse_answer(slot: str, answer: str, language: str = "en") -> tuple[str, Any]:
    return interpret_answer(slot, answer, language=language)


def _apply_answer(state: InterviewState) -> dict[str, Any]:
    answer = state.get("pending_answer")
    question = state.get("next_question")
    profile = CitizenProfile.model_validate(state.get("profile", {}))
    asked = list(state.get("asked_fields", []))
    events = list(state.get("events", []))
    if not answer or not question:
        return {"profile": profile.model_dump(mode="json"), "pending_answer": None}
    field = question["field"]
    try:
        lang = state.get("language", Language.EN.value)
        key, value = _parse_answer(field, answer, language=lang)
        updated = profile.model_dump(mode="python")
        updated[key] = value
        validated = CitizenProfile.model_validate(updated)
        events.append({"type": "slot_filled", "field": key, "ok": True})
        profile = validated
        if key not in asked:
            asked.append(key)
    except (ValueError, TypeError) as exc:
        events.append({"type": "slot_filled", "field": field, "ok": False, "message": str(exc)})
        # Re-ask the same slot with the validation feedback; the answer is cleared to avoid replay.
        question = {**question, "validation_error": str(exc)}
    return {
        "profile": profile.model_dump(mode="json"),
        "asked_fields": asked,
        "events": events[-100:],
        "pending_answer": None,
        "next_question": question,
    }


def _rank_schemes(state: InterviewState) -> dict[str, Any]:
    profile = CitizenProfile.model_validate(state.get("profile", {}))
    schemes = [Scheme.model_validate(item) for item in state.get("candidate_schemes", [])]
    from scheme_navigator.services.rule_engine import evaluate_scheme

    results = [evaluate_scheme(scheme, profile).model_dump(mode="json") for scheme in schemes]
    return {"result_summary": results}



def _generate_question_reason(slot: str, viable_schemes: list[Scheme], mode: str, language: str) -> str:
    scheme_name = None
    if viable_schemes and (mode == "FOCUSED_SCHEME" or len(viable_schemes) == 1):
        scheme_name = getattr(viable_schemes[0], "name", None) or getattr(viable_schemes[0], "official_name", None)
    
    reasons = {
        "annual_family_income": {
            "en": f"We ask about your annual family income because {f'the {scheme_name} scheme' if scheme_name else 'government schemes'} has an income eligibility ceiling to ensure benefits reach qualifying households.",
            "mr": f"शासकीय योजनांचे लाभ पात्र कुटुंबांपर्यंत पोहोचवण्यासाठी {f'{scheme_name} योजनेचे' if scheme_name else 'योजनांचे'} उत्पन्नाचे निकष तपासणे आवश्यक असते.",
            "hi": f"योजनाओं के लाभ पात्र परिवारों तक पहुँचाने के लिए {f'{scheme_name} योजना' if scheme_name else 'सरकारी योजनाओं'} में आय सीमा निर्धारित होती है।",
        },
        "resident_state": {
            "en": f"We ask about your residence because {scheme_name or 'most state schemes'} require Maharashtra domicile or residency.",
            "mr": f"{scheme_name or 'महाराष्ट्र शासनाच्या योजना'} केवळ महाराष्ट्रातील रहिवाशांसाठी लागू असतात.",
            "hi": f"{scheme_name or 'महाराष्ट्र शासन की योजनाएं'} केवल महाराष्ट्र के निवासियों के लिए लागू होती हैं।",
        },
        "age_years": {
            "en": f"We ask about your age because {f'{scheme_name}' if scheme_name else 'schemes'} have specific statutory age limits.",
            "mr": f"{scheme_name or 'योजनांसाठी'} शासन निर्णयानुसार वयाची विशिष्ट मर्यादा निश्चित केलेली असते.",
            "hi": f"{scheme_name or 'योजनाओं के लिए'} नियमों के अनुसार विशिष्ट आयु सीमा निर्धारित होती है।",
        },
        "gender": {
            "en": "We ask about your gender because certain welfare schemes are specifically targeted for women or specialized beneficiary groups.",
            "mr": "काही कल्याणकारी योजना विशेषतः महिला किंवा विशिष्ट लाभार्थी गटांसाठी आखलेल्या असतात.",
            "hi": "कुछ कल्याणकारी योजनाएं विशेष रूप से महिलाओं या विशिष्ट वर्गों के लिए बनाई गई हैं।",
        },
        "caste_category": {
            "en": "We ask about your caste category because dedicated benefits, fee waivers, and quotas are reserved for specific social categories.",
            "mr": "विशिष्ट सामाजिक प्रवर्गांसाठी राखीव सवलती व शुल्क माफी तपासण्यासाठी जात प्रवर्ग विचारला जातो.",
            "hi": "विशिष्ट सामाजिक श्रेणियों के लिए आरक्षित छूट और लाभों की जांच के लिए जाति श्रेणी पूछी जाती है।",
        },
        "is_student": {
            "en": "Educational schemes and scholarships are specifically tailored for active students.",
            "mr": "शैक्षणिक शिष्यवृत्ती योजना केवळ सध्या शिक्षण घेत असलेल्या विद्यार्थ्यांसाठी असतात.",
            "hi": "शैक्षिक छात्रवृत्ति योजनाएं केवल अध्ययनरत विद्यार्थियों के लिए होती हैं।",
        },
        "has_disability": {
            "en": "Disability welfare programmes require verified disability status to provide targeted financial assistance.",
            "mr": "दिव्यांग कल्याणकारी योजनांचे लाभ देण्यासाठी अधिकृत दिव्यांगत्वाची नोंद आवश्यक असते.",
            "hi": "दिव्यांग कल्याण योजनाओं के लाभ के लिए दिव्यांगता की आधिकारिक स्थिति आवश्यक होती है।",
        },
        "disability_percentage": {
            "en": "Statutory disability schemes require a certified disability of 40% or higher.",
            "mr": "दिव्यांग योजनांसाठी किमान ४०% किंवा त्याहून अधिक दिव्यांगत्वाचे प्रमाणपत्र आवश्यक असते.",
            "hi": "दिव्यांगता योजनाओं के लिए न्यूनतम 40% या अधिक का प्रमाणपत्र आवश्यक होता है।",
        },
        "has_land": {
            "en": "Agricultural subsidy schemes are exclusively for farmers owning cultivable land.",
            "mr": "कृषी योजना व सन्मान निधीचे लाभ शेतजमीनधारक शेतकऱ्यांसाठी उपलब्ध असतात.",
            "hi": "कृषि योजनाएं केवल कृषि भूमि धारक किसानों के लिए उपलब्ध होती हैं।",
        },
        "landholding_hectares": {
            "en": "Small and marginal farmer schemes apply to landholdings up to 2.0 hectares.",
            "mr": "अल्प व अल्पभूधारक शेतकरी योजना २.० हेक्टरपर्यंत जमीन असणाऱ्या शेतकऱ्यांसाठी लागू असतात.",
            "hi": "लघु और सीमांत किसान योजनाएं 2.0 हेक्टेयर तक की भूमि वाले किसानों के लिए लागू होती हैं।",
        },
        "bpl": {
            "en": "Poverty alleviation programmes require official Below Poverty Line (BPL) status.",
            "mr": "दारिद्र्य निर्मूलन योजना अधिकृत दारिद्र्यरेषेखालील (BPL) कुटुंबांसाठी असतात.",
            "hi": "गरीबी उन्मूलन योजनाएं आधिकारिक बीपीएल परिवारों के लिए होती हैं।",
        },
        "ration_card_type": {
            "en": "Food security and subsidized medical schemes depend on your family ration card color.",
            "mr": "अन्न सुरक्षा व आरोग्य योजना शिधापत्रिकेच्या प्रकारावर आधारित असतात.",
            "hi": "खाद्य सुरक्षा और स्वास्थ्य योजनाएं राशन कार्ड के प्रकार पर निर्भर करती हैं।",
        },
        "marital_status": {
            "en": "Special support schemes provide assistance to destitute or widowed citizens.",
            "mr": "विशेष सहाय्य योजना निराधार किंवा विधवा नागरिकांच्या संरक्षणासाठी असतात.",
            "hi": "विशेष सहायता योजनाएं निराश्रित या विधवा नागरिकों के कल्याण के लिए होती हैं।",
        },
        "receiving_other_pension": {
            "en": "Certain pension schemes cannot be combined with existing government pensions.",
            "mr": "एकाच वेळी दोन शासकीय निवृत्तीवेतन योजनांचा लाभ घेण्यावर कायदेशीर निर्बंध असतात.",
            "hi": "एक साथ दो सरकारी पेंशन योजनाओं का लाभ लेने पर कानूनी प्रतिबंध होते हैं।",
        },
        "aadhaar_linked_bank_account": {
            "en": "Direct Benefit Transfer (DBT) requires an Aadhaar-seeded bank account for payout disbursement.",
            "mr": "थेट लाभ हस्तांतरणासाठी (DBT) बँक खाते आधारशी जोडलेले असणे आवश्यक असते.",
            "hi": "प्रत्यक्ष लाभ अंतरण (DBT) के लिए बैंक खाता आधार से जुड़ा होना आवश्यक है।",
        },
        "occupation": {
            "en": "Specific employment generation and welfare schemes apply to particular occupations.",
            "mr": "विशिष्ट व्यवसाय किंवा रोजगारावर आधारित योजनांचे निकष तपासण्यासाठी व्यवसाय विचारला जातो.",
            "hi": "विशिष्ट रोजगार या व्यवसाय पर आधारित योजनाओं के लिए व्यवसाय पूछा जाता है।",
        },
        "district": {
            "en": "District and regional welfare programmes require residency in designated districts of Maharashtra.",
            "mr": "जिल्हास्तरीय कल्याणकारी योजनांचे लाभ मिळण्यासाठी विशिष्ट जिल्ह्यातील रहिवासी असणे आवश्यक असते.",
            "hi": "जिला स्तरीय कल्याणकारी योजनाओं के लिए विशिष्ट जिले का निवासी होना अनिवार्य है।",
        },
        "local_government_type": {
            "en": "Local welfare schemes depend on whether you reside within a Municipal Corporation, Municipal Council, or Gram Panchayat.",
            "mr": "स्थानिक योजनांचे स्वरूप तुम्ही महानगरपालिका, नगरपरिषद की ग्रामपंचायत क्षेत्रात राहता यावर अवलंबून असते.",
            "hi": "स्थानीय योजनाएं इस बात पर निर्भर करती हैं कि आप नगर निगम, नगर परिषद या ग्राम पंचायत क्षेत्र में रहते हैं।",
        },
        "municipal_corporation": {
            "en": "Municipal welfare grants and scholarships are exclusively funded for residents of the specific Municipal Corporation.",
            "mr": "महानगरपालिकांच्या कल्याणकारी योजना केवळ त्या विशिष्ट महापालिकेच्या हद्दीतील करदात्या/रहिवासी नागरिकांसाठी असतात.",
            "hi": "नगर निगम की कल्याणकारी योजनाएं केवल उस विशिष्ट नगर निगम के निवासियों के लिए उपलब्ध होती हैं।",
        },
        "residence_years": {
            "en": "Certain municipal welfare schemes require a minimum continuous period of local residency (e.g. 3 or 5 years).",
            "mr": "स्थानिक स्वराज्य संस्थांच्या योजनांसाठी शहरात सलग किमान वास्तव्याची कायदेशीर अट (उदा. ३ किंवा ५ वर्षे) असते.",
            "hi": "स्थानीय नगर निकाय योजनाओं के लिए न्यूनतम निरंतर निवास अवधि की वैधानिक शर्त होती है।",
        },
        "ward": {
            "en": "Ward-level verification determines your local civic administrative jurisdiction and facilitation office.",
            "mr": "स्थानिक नागरिक सुविधा केंद्र व क्षेत्रीय कार्यालय निश्चित करण्यासाठी प्रभाग माहिती उपयुक्त ठरते.",
            "hi": "स्थानीय नागरिक सुविधा केंद्र और वार्ड कार्यालय के निर्धारण के लिए वार्ड की जानकारी आवश्यक होती है।",
        },
    }
    slot_reasons = reasons.get(slot, {})
    return slot_reasons.get(language, slot_reasons.get("en", "This information is required by official government scheme eligibility criteria."))


def _choose_question(state: InterviewState) -> dict[str, Any]:
    """Choose a useful question for schemes not yet ruled out."""
    profile = CitizenProfile.model_validate(
        state.get("profile", {})
    )
    raw_schemes = state.get("candidate_schemes", [])
    schemes = [Scheme.model_validate(item) for item in raw_schemes]
    language = state.get("language", Language.EN.value)
    asked = set(state.get("asked_fields", []))
    mode = state.get("mode", "DISCOVERY")
    target_scheme_id = state.get("target_scheme_id")

    # In FOCUSED_SCHEME mode, restrict candidate schemes strictly to target scheme
    if (mode == "FOCUSED_SCHEME" or target_scheme_id) and target_scheme_id:
        focused = [s for s in schemes if s.scheme_id == target_scheme_id]
        if focused:
            schemes = focused

    # Exclude schemes that are definitively ineligible.
    viable_schemes = []
    unresolved_fields = set()

    from scheme_navigator.domain.jurisdiction import jurisdiction_service

    for scheme in schemes:
        is_geo_ok, _ = jurisdiction_service.is_geographically_applicable(scheme, profile)
        if not is_geo_ok:
            continue

        evaluation = evaluate_node(
            scheme.eligibility_rule,
            profile,
        )

        # Never eliminate a scheme using an unapproved/demo rule.
        if (
            evaluation.value is False
            and has_non_demo_approval_metadata(scheme)
        ):
            continue

        viable_schemes.append(scheme)
        unresolved_fields.update(evaluation.missing_fields)

    if not viable_schemes:
        return {
            "next_question": None,
            "is_complete": True,
        }

    # Ask only for fields that remain necessary to evaluate
    # schemes that have not already been ruled out.
    slots = set()

    for rule_field in unresolved_fields:
        slot = (
            "age_years"
            if rule_field == "age"
            else rule_field
        )

        if slot in QUESTION_SPECS:
            slots.add(slot)

    candidates = []

    for slot in slots:
        rule_field = _slot_rule_field(slot)

        if slot in asked:
            continue

        if profile.value_for_rule(rule_field) is not None:
            continue

        if mode == "FOCUSED_SCHEME" or target_scheme_id:
            # For focused scheme, ask required missing fields directly
            candidates.append((1.0, slot))
        else:
            gain = information_gain(
                slot,
                profile,
                viable_schemes,
            )

            coverage = sum(
                any(
                    field == rule_field
                    for field, _, _ in _collect_predicates(scheme)
                )
                for scheme in viable_schemes
            ) / len(viable_schemes)

            # Keep the displayed score between 0 and 1.
            score = min(1.0, gain + 0.05 * coverage)
            candidates.append((score, slot))

    if not candidates:
        unmapped_missing = [
            f for f in unresolved_fields 
            if (_slot_rule_field(f) not in QUESTION_SPECS and f not in QUESTION_SPECS)
        ]
        if unmapped_missing and not all(profile.value_for_rule(_slot_rule_field(f)) is not None for f in unresolved_fields):
            return {
                "next_question": None,
                "is_complete": True,
                "error": {
                    "code": "QUESTION_SELECTION_UNRESOLVED",
                    "missing_fields": list(unresolved_fields),
                    "message": "Some required statutory criteria cannot be collected through standard interview questions and require manual caseworker review."
                }
            }
        return {
            "next_question": None,
            "is_complete": True,
        }

    # Highest information gain first; deterministic tie-break.
    candidates.sort(
        key=lambda item: (item[0], item[1]),
        reverse=True,
    )

    score, slot = candidates[0]
    spec = QUESTION_SPECS[slot]

    prev_q = state.get("next_question") or {}
    prev_err = prev_q.get("validation_error") if prev_q.get("field") == slot else None

    reason = _generate_question_reason(slot, viable_schemes, mode, language)

    question = {
        "question_id": f"q_{slot}",
        "field": slot,
        "text": spec["labels"].get(
            language,
            spec["labels"]["en"],
        ),
        "choices": spec["choices"],
        "choice_labels": spec.get("choice_labels", {}).get(language, {}),
        "kind": spec["kind"],
        "required": True,
        "reason": reason,
        "information_gain": round(score, 4),
        "validation_error": prev_err,
        "language": language,
    }

    return {
        "next_question": question,
        "is_complete": False,
    }



def _ask_user(state: InterviewState) -> dict[str, Any]:
    question = state.get("next_question")
    if question is None:
        return {"is_complete": True}
    answer = interrupt({
        "type": "clarifying_question",
        "thread_id": state.get("thread_id"),
        "question": question,
        "mode": state.get("mode", "DISCOVERY"),
        "target_scheme_id": state.get("target_scheme_id"),
        "candidate_scheme_count": len(state.get("candidate_schemes", [])),
        "privacy_note": "Share only what is needed; never share a full Aadhaar number or OTP.",
    })
    return {"pending_answer": str(answer), "is_complete": False}


def _route_after_question(state: InterviewState) -> str:
    return "ask_user" if state.get("next_question") is not None else "end"


class _FallbackInterviewGraph:
    """Small in-memory compatible runner for local smoke tests; use LangGraph in deployed environments."""

    def __init__(self):
        self._states: dict[str, dict[str, Any]] = {}

    def get_state(self, config):
        class Snapshot:
            def __init__(self, values):
                self.values = values
        thread_id = config.get("configurable", {}).get("thread_id", "")
        return Snapshot(self._states.get(thread_id, {}))

    def invoke(self, input_state, config):
        thread_id = config.get("configurable", {}).get("thread_id", "")
        if hasattr(input_state, "resume"):
            if thread_id not in self._states:
                raise ValueError("Unknown interview thread")
            state = dict(self._states[thread_id])
            state["pending_answer"] = input_state.resume
        else:
            state = dict(input_state)
        state.update(_apply_answer(state))
        state.update(_rank_schemes(state))
        state.update(_choose_question(state))
        self._states[thread_id] = state
        question = state.get("next_question")
        if question is None:
            state["is_complete"] = True
            self._states[thread_id] = state
            return state
        interrupt_value = {
            "type": "clarifying_question",
            "thread_id": thread_id,
            "question": question,
            "mode": state.get("mode", "DISCOVERY"),
            "target_scheme_id": state.get("target_scheme_id"),
            "candidate_scheme_count": len(state.get("candidate_schemes", [])),
            "privacy_note": "Share only what is needed; never share a full Aadhaar number or OTP.",
        }
        return {**state, "__interrupt__": [_FakeInterrupt(interrupt_value)]}


def build_interviewer_graph(checkpointer: Any | None = None):
    if not HAS_LANGGRAPH:
        return _FallbackInterviewGraph()
    builder = StateGraph(InterviewState)
    builder.add_node("apply_answer", _apply_answer)
    builder.add_node("rank_schemes", _rank_schemes)
    builder.add_node("choose_question", _choose_question)
    builder.add_node("ask_user", _ask_user)
    builder.add_edge(START, "apply_answer")
    builder.add_edge("apply_answer", "rank_schemes")
    builder.add_edge("rank_schemes", "choose_question")
    builder.add_conditional_edges("choose_question", _route_after_question, {"ask_user": "ask_user", "end": END})
    builder.add_edge("ask_user", "apply_answer")  # cyclic loop: ask -> update profile -> re-rank -> next best question
    saver = checkpointer if checkpointer is not None else MemorySaver()
    return builder.compile(checkpointer=saver)
