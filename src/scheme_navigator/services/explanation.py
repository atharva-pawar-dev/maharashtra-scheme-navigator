from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

from scheme_navigator.domain.models import (
    CitizenProfile,
    ConditionEvaluation,
    EligibilityResult,
    EligibilityStatus,
    ExtractedDocument,
    Language,
    RuleNode,
    Scheme,
    SourceReference,
)
from scheme_navigator.domain.evidence import (
    DocumentRequirement,
    MultilingualText,
    OfficialSourceType,
    RuleEvidence,
    RuleVerificationStatus,
)
from scheme_navigator.services.rule_engine import evaluate_node, evaluate_scheme


class ValueProvenance(StrEnum):
    SELF_REPORTED = "self_reported"
    DOCUMENT_EXTRACTED = "document_extracted"
    REVIEWER_VERIFIED = "reviewer_verified"
    MISSING = "missing"


class ConditionStatus(StrEnum):
    SATISFIED = "satisfied"
    UNMET = "unmet"
    UNKNOWN = "unknown"


class ExplainedCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    condition_id: str | None = None
    field: str | None = None
    operator: str | None = None
    required_value: Any = None
    actual_value: Any = None
    provenance: ValueProvenance = ValueProvenance.SELF_REPORTED
    status: ConditionStatus
    title: str
    requirement_description: str
    citizen_explanation: str
    evidence_id: str | None = None
    source_title: str | None = None
    official_reference: str | None = None
    effective_from: date | None = None
    page_or_section: str | None = None
    official_source_url: str | None = None
    verification_status: str | None = None
    is_rule_verified: bool = False


class ExplainedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    name: str
    issuing_authority: str
    rts_delivery_days: int | None = None
    verification_state: str = "document_verification_pending"
    notes: str | None = None


class ExplainedSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_title: str
    source_url: str
    source_kind: str
    official_reference: str | None = None
    page_or_section: str | None = None
    effective_from: date | None = None
    verification_status: str | None = None


class SchemeExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheme_id: str
    scheme_name: str
    language: str
    overall_status: str
    overall_status_label: str
    summary: str
    positive_conditions: list[ExplainedCondition] = Field(default_factory=list)
    unmet_conditions: list[ExplainedCondition] = Field(default_factory=list)
    missing_information: list[ExplainedCondition] = Field(default_factory=list)
    relevant_sources: list[ExplainedSource] = Field(default_factory=list)
    document_requirements: list[ExplainedDocument] = Field(default_factory=list)
    scheme_verification_status: str
    scheme_verification_label: str
    next_recommended_action: str
    trust_notices: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Static Reviewed Multilingual Dictionaries (English, Marathi, Hindi)
# ---------------------------------------------------------------------------

FIELD_TITLES: dict[str, dict[str, str]] = {
    "age": {
        "en": "Age Requirement",
        "mr": "वयाची अट",
        "hi": "आयु की आवश्यकता",
    },
    "gender": {
        "en": "Gender Requirement",
        "mr": "लिंग अट",
        "hi": "लिंग आवश्यकता",
    },
    "resident_state": {
        "en": "State Residency & Domicile",
        "mr": "महाराष्ट्र राज्य रहिवासी व अधिवास",
        "hi": "महाराष्ट्र राज्य निवास एवं अधिवास",
    },
    "annual_family_income": {
        "en": "Annual Family Income Limit",
        "mr": "कौटुंबिक वार्षिक उत्पन्न मर्यादा",
        "hi": "पारिवारिक वार्षिक आय सीमा",
    },
    "caste_category": {
        "en": "Caste & Social Category",
        "mr": "सामाजिक प्रवर्ग व जात",
        "hi": "सामाजिक वर्ग एवं जाति",
    },
    "is_student": {
        "en": "Student Enrollment Status",
        "mr": "विद्यार्थी नोंदणी स्थिती",
        "hi": "विद्यार्थी नामांकन स्थिति",
    },
    "education_level": {
        "en": "Education Level / Course Group",
        "mr": "शिक्षण स्तर / अभ्यासक्रम गट",
        "hi": "शिक्षा स्तर / पाठ्यक्रम समूह",
    },
    "has_disability": {
        "en": "Divyang / Disability Criteria",
        "mr": "दिव्यांगत्व अट",
        "hi": "दिव्यांगता की शर्त",
    },
    "disability_percentage": {
        "en": "Certified Disability Percentage",
        "mr": "प्रमाणित दिव्यांगत्व टक्केवारी",
        "hi": "प्रमाणित दिव्यांगता प्रतिशत",
    },
    "bpl": {
        "en": "Below Poverty Line (BPL) Registration",
        "mr": "दारिद्र्यरेषेखालील (BPL) नोंदणी",
        "hi": "गरीबी रेखा से नीचे (BPL) पंजीकरण",
    },
    "receiving_other_pension": {
        "en": "Other Social Security Pension Exclusion",
        "mr": "इतर सामाजिक सुरक्षा पेन्शन न घेण्याची अट",
        "hi": "अन्य सामाजिक सुरक्षा पेंशन न लेने की शर्त",
    },
    "aadhaar_linked_bank_account": {
        "en": "Aadhaar-Linked Bank Account for DBT",
        "mr": "DBT साठी आधार संलग्न बँक खाते",
        "hi": "डीबीटी हेतु आधार से जुड़ा बैंक खाता",
    },
    "has_land": {
        "en": "Agricultural Land Ceiling",
        "mr": "शेतीजमीन धारणा मर्यादा",
        "hi": "कृषि भूमि धारण सीमा",
    },
    "district": {
        "en": "District of Residence",
        "mr": "रहिवासी जिल्हा",
        "hi": "निवास ज़िला",
    },
}

COMMON_DOCUMENT_NAMES: dict[str, dict[str, str]] = {
    "income_certificate": {
        "en": "Income Certificate",
        "mr": "उत्पन्नाचा दाखला",
        "hi": "आय प्रमाण पत्र",
    },
    "caste_certificate": {
        "en": "Caste Certificate",
        "mr": "जातीचे प्रमाणपत्र",
        "hi": "जाति प्रमाण पत्र",
    },
    "domicile_certificate": {
        "en": "Domicile Certificate",
        "mr": "अधिवास प्रमाणपत्र",
        "hi": "अधिवास प्रमाण पत्र",
    },
    "aadhaar_card": {
        "en": "Aadhaar Card",
        "mr": "आधार कार्ड",
        "hi": "आधार कार्ड",
    },
    "ration_card": {
        "en": "Ration Card (Yellow/Orange)",
        "mr": "रेशन कार्ड (पिवळे/केशरी)",
        "hi": "राशन कार्ड (पीला/नारंगी)",
    },
    "bank_passbook": {
        "en": "Aadhaar-Seeded Bank Passbook",
        "mr": "आधार संलग्न बँक पासबुक",
        "hi": "आधार लिंक बैंक पासबुक",
    },
    "disability_certificate": {
        "en": "Disability Certificate (UDID / 40%+)",
        "mr": "दिव्यांगत्व प्रमाणपत्र (UDID / ४०%+)",
        "hi": "दिव्यांगता प्रमाण पत्र (UDID / ४०%+)",
    },
    "cap_allotment_letter": {
        "en": "CAP Allotment Letter",
        "mr": "केंद्रीभूत प्रवेश वाटप पत्र (CAP Allotment)",
        "hi": "केंद्रीकृत प्रवेश आवंटन पत्र (CAP Allotment)",
    },
    "self_declaration": {
        "en": "Self Declaration / Hamipatra",
        "mr": "हमीपत्र / स्वघोषणापत्र",
        "hi": "स्व-घोषणा पत्र / हामीपत्र",
    },
}

STATUS_LABELS: dict[str, dict[str, str]] = {
    "eligible": {
        "en": "Preliminary Eligible",
        "mr": "प्राथमिक दृष्ट्या पात्र",
        "hi": "प्रारंभिक रूप से पात्र",
    },
    "needs_review": {
        "en": "Scheme Rules Under Review",
        "mr": "योजनेचे नियम पुनरावलोकनाधीन",
        "hi": "योजना के नियम समीक्षाधीन",
    },
    "needs_information": {
        "en": "Additional Information Needed",
        "mr": "अधिक माहिती आवश्यक आहे",
        "hi": "अतिरिक्त जानकारी आवश्यक है",
    },
    "ineligible": {
        "en": "Preliminary Ineligible",
        "mr": "प्राथमिक दृष्ट्या अपात्र",
        "hi": "प्रारंभिक रूप से अपात्र",
    },
}

RECOMMENDED_ACTIONS: dict[str, dict[str, str]] = {
    "needs_information": {
        "en": "Provide the missing information in your profile or the interview to complete the preliminary eligibility check.",
        "mr": "प्राथमिक पात्रता तपासणी पूर्ण करण्यासाठी अपूर्ण माहिती प्रोफाइल किंवा मुलाखतीत भरा.",
        "hi": "प्रारंभिक पात्रता जांच पूरी करने के लिए अधूरी जानकारी प्रोफ़ाइल या साक्षात्कार में दर्ज करें।",
    },
    "needs_review": {
        "en": "This scheme's rules are unverified or in draft mode. Review official guidelines with the administering department before relying on this assessment.",
        "mr": "या योजनेचे नियम मसुदा स्वरूपात आहेत. या मूल्यांकनावर अवलंबून राहण्यापूर्वी संबंधित विभागाकडून अधिकृत मार्गदर्शक तत्त्वांची खात्री करा.",
        "hi": "इस योजना के नियम अभी प्रारूप में हैं। इस मूल्यांकन पर निर्भर होने से पहले संबंधित विभाग से आधिकारिक दिशानिर्देशों की पुष्टि करें।",
    },
    "ineligible": {
        "en": "Review the unmet conditions above. You may explore alternative government schemes suited to your profile.",
        "mr": "वरील अपूर्ण अटी तपासा. तुम्ही तुमच्या प्रोफाइलसाठी उपलब्ध इतर पर्यायी शासकीय योजना पाहू शकता.",
        "hi": "ऊपर दी गई अपूर्ण शर्तों की समीक्षा करें। आप अपनी प्रोफ़ाइल के अनुसार उपलब्ध अन्य सरकारी योजनाएं देख सकते हैं।",
    },
    "eligible": {
        "en": "Collect the required supporting documents and proceed to prepare your official application with the department.",
        "mr": "आवश्यक साहाय्यक कागदपत्रे गोळा करा आणि संबंधित विभागाकडे अधिकृत अर्ज सादर करण्याची तयारी करा.",
        "hi": "आवश्यक सहायक दस्तावेज़ एकत्र करें और संबंधित विभाग में आधिकारिक आवेदन जमा करने की तैयारी करें।",
    },
}

TRUST_NOTICES: dict[str, dict[str, str]] = {
    "based_on_answers": {
        "en": "Based on your answers: This preliminary evaluation is calculated strictly from self-reported answers or unverified extractions.",
        "mr": "तुमच्या उत्तरांवर आधारित: हे प्राथमिक मूल्यांकन केवळ तुम्ही दिलेल्या माहितीवर किंवा पडताळणी न झालेल्या मजकुरावर आधारित आहे.",
        "hi": "आपके उत्तरों पर आधारित: यह प्रारंभिक मूल्यांकन पूरी तरह से आपकी दी गई जानकारी या असत्यापित सामग्री पर आधारित है।",
    },
    "document_pending": {
        "en": "Document verification pending: Uploaded documents and self-declarations have not yet been verified by an authorized government official.",
        "mr": "कागदपत्र पडताळणी प्रलंबित: अपलोड केलेली कागदपत्रे किंवा स्वयंघोषणा अद्याप अधिकृत सरकारी अधिकाऱ्याकडून पडताळण्यात आलेली नाहीत.",
        "hi": "दस्तावेज़ सत्यापन लंबित: अपलोड किए गए दस्तावेज़ या स्व-घोषणा अभी किसी अधिकृत सरकारी अधिकारी द्वारा सत्यापित नहीं की गई है।",
    },
    "rules_under_review": {
        "en": "This scheme's eligibility conditions are under review (Draft candidate record; not officially activated).",
        "mr": "या योजनेच्या पात्रता अटी पुनरावलोकनाधीन आहेत (मसुदा नोंद; अद्याप अधिकृतपणे सक्रिय नाही).",
        "hi": "इस योजना की पात्रता शर्तें समीक्षाधीन हैं (प्रारूप रिकॉर्ड; आधिकारिक तौर पर सक्रिय नहीं है)।",
    },
    "not_government_approval": {
        "en": "This result is not a government approval: Meeting preliminary conditions does not constitute a legal right or government approval of benefits.",
        "mr": "हा निकाल म्हणजे सरकारी मंजुरी नाही: प्राथमिक अटींची पूर्तता झाली तरी तो कायदेशीर अधिकार किंवा सरकारी मंजुरी ठरत नाही.",
        "hi": "यह परिणाम सरकारी स्वीकृति नहीं है: प्रारंभिक शर्तों की पूर्ति से कोई कानूनी अधिकार या सरकारी मंज़ूरी नहीं मिलती।",
    },
}


def _lang_code(language: Language | str) -> str:
    if isinstance(language, Language):
        return language.value.lower()
    return str(language or "en").strip().lower()


def _format_inr(value: int | float | None) -> str:
    if value is None:
        return ""
    try:
        val_int = int(value)
        return f"{val_int:,}"
    except (ValueError, TypeError):
        return str(value)


def _get_field_title(field: str, lang: str) -> str:
    entry = FIELD_TITLES.get(field, {})
    return entry.get(lang) or entry.get("en") or field.replace("_", " ").title()


def _describe_requirement(node: RuleNode, lang: str) -> str:
    field = node.field or "requirement"
    op = node.op
    val = node.value

    if field == "age":
        if op == "gte":
            if lang == "mr":
                return f"वय किमान {val} वर्षे पूर्ण असणे आवश्यक आहे"
            if lang == "hi":
                return f"आयु कम से कम {val} वर्ष होनी चाहिए"
            return f"Must be at least {val} years of age"
        if op == "lte":
            if lang == "mr":
                return f"वय कमाल {val} वर्षे असणे आवश्यक आहे"
            if lang == "hi":
                return f"आयु अधिकतम {val} वर्ष होनी चाहिए"
            return f"Must be at most {val} years of age"
        if op == "lt":
            if lang == "mr":
                return f"वय {val} वर्षांखालील असणे आवश्यक आहे"
            if lang == "hi":
                return f"आयु {val} वर्ष से कम होनी चाहिए"
            return f"Must be under {val} years of age"
        if op == "gt":
            if lang == "mr":
                return f"वय {val} वर्षांपेक्षा जास्त असणे आवश्यक आहे"
            if lang == "hi":
                return f"आयु {val} वर्ष से अधिक होनी चाहिए"
            return f"Must be over {val} years of age"

    if field == "annual_family_income":
        fmt_val = _format_inr(val)
        if op == "lte":
            if lang == "mr":
                return f"कुटुंबाचे वार्षिक उत्पन्न रु. {fmt_val}/- पेक्षा जास्त नसावे"
            if lang == "hi":
                return f"पारिवारिक वार्षिक आय ₹{fmt_val}/- से अधिक नहीं होनी चाहिए"
            return f"Annual family income must not exceed ₹{fmt_val}"
        if op == "lt":
            if lang == "mr":
                return f"कुटुंबाचे वार्षिक उत्पन्न रु. {fmt_val}/- पेक्षा कमी असणे आवश्यक आहे"
            if lang == "hi":
                return f"पारिवारिक वार्षिक आय ₹{fmt_val}/- से कम होनी चाहिए"
            return f"Annual family income must be less than ₹{fmt_val}"

    if field == "resident_state":
        if lang == "mr":
            return "महाराष्ट्र राज्याचे रहिवासी असणे आवश्यक आहे"
        if lang == "hi":
            return "महाराष्ट्र राज्य का निवासी होना आवश्यक है"
        return "Must be a resident of Maharashtra state"

    if field == "gender":
        if str(val).lower() == "female":
            if lang == "mr":
                return "अर्जदार महिला असणे आवश्यक आहे"
            if lang == "hi":
                return "आवेदक महिला होनी चाहिए"
            return "Applicant must be female"
        if str(val).lower() == "male":
            if lang == "mr":
                return "अर्जदार पुरुष असणे आवश्यक आहे"
            if lang == "hi":
                return "आवेदक पुरुष होना चाहिए"
            return "Applicant must be male"

    if field == "bpl":
        if val is True:
            if lang == "mr":
                return "कुटुंब दारिद्र्यरेषेखालील (BPL) यादीत समाविष्ट असणे आवश्यक आहे"
            if lang == "hi":
                return "परिवार गरीबी रेखा से नीचे (BPL) सूची में होना चाहिए"
            return "Family must be registered under Below Poverty Line (BPL)"

    if field == "receiving_other_pension":
        if val is False:
            if lang == "mr":
                return "शासनाकडून इतर कोणतीही नियमित सामाजिक सुरक्षा पेन्शन घेत नसावी"
            if lang == "hi":
                return "शासन से कोई अन्य नियमित सामाजिक सुरक्षा पेंशन नहीं ले रहे होने चाहिए"
            return "Must not be receiving another government social security pension"

    if field == "aadhaar_linked_bank_account":
        if val is True:
            if lang == "mr":
                return "स्वतःचे आधार लिंक असलेले सक्रिय बँक खाते असणे आवश्यक आहे"
            if lang == "hi":
                return "स्वयं का आधार से जुड़ा सक्रिय बैंक खाता होना आवश्यक है"
            return "Must possess an active individual bank account seeded with Aadhaar"

    if field == "has_disability":
        if val is True:
            if lang == "mr":
                return "किमान ४०% प्रमाणित दिव्यांगत्व असणे आवश्यक आहे"
            if lang == "hi":
                return "कम से कम ४०% प्रमाणित दिव्यांगता होना आवश्यक है"
            return "Must have a certified disability (40% or above)"

    if field == "disability_percentage":
        if op == "gte":
            if int(val) >= 80:
                if lang == "mr":
                    return "किमान ८०% तीव्र दिव्यांगत्व (UDID) असणे आवश्यक आहे (वाढीव अनुदानासाठी)"
                if lang == "hi":
                    return "कम से कम ८०% गंभीर दिव्यांगता (UDID) होना आवश्यक है (बढ़ी हुई सहायता हेतु)"
                return "Must have at least 80% severe certified disability / UDID (for enhanced assistance)"
            else:
                if lang == "mr":
                    return f"किमान {val}% प्रमाणित दिव्यांगत्व (UDID) असणे आवश्यक आहे"
                if lang == "hi":
                    return f"कम से कम {val}% प्रमाणित दिव्यांगता (UDID) होना आवश्यक है"
                return f"Must have at least {val}% certified disability (UDID)"

    if field == "is_student":
        if val is True:
            if lang == "mr":
                return "मान्यताप्राप्त शिक्षण संस्थेत नियमित विद्यार्थी असणे आवश्यक आहे"
            if lang == "hi":
                return "मान्यता प्राप्त शिक्षण संस्थान में नियमित विद्यार्थी होना आवश्यक है"
            return "Must be actively enrolled as a regular student"

    if field == "caste_category":
        if isinstance(val, list):
            cats = ", ".join(str(v).upper() for v in val)
            if lang == "mr":
                return f"{cats} यापैकी एका प्रवर्गातील असणे आवश्यक आहे"
            if lang == "hi":
                return f"{cats} में से किसी एक वर्ग का होना आवश्यक है"
            return f"Must belong to one of these categories: {cats}"
        cat = str(val).upper()
        if lang == "mr":
            return f"{cat} प्रवर्गातील असणे आवश्यक आहे"
        if lang == "hi":
            return f"{cat} वर्ग से संबंधित होना आवश्यक है"
        return f"Must belong to {cat} category"

    # Clean fallback for any other condition without exposing raw AST
    field_title = _get_field_title(field, lang)
    if op == "eq":
        if lang == "mr":
            return f"{field_title}: {val} असणे आवश्यक"
        if lang == "hi":
            return f"{field_title}: {val} होना आवश्यक"
        return f"{field_title}: Must be {val}"

    return f"{field_title} requirement ({op} {val})"


def _explain_condition_result(
    node: RuleNode,
    actual: Any,
    status: ConditionStatus,
    provenance: ValueProvenance,
    lang: str,
) -> str:
    field = node.field or "requirement"
    val = node.value
    req_desc = _describe_requirement(node, lang)

    if status == ConditionStatus.UNKNOWN:
        if field == "age":
            if lang == "mr":
                return "वय नमूद केलेले नाही. कृपया पूर्ण वर्षे प्रविष्ट करा."
            if lang == "hi":
                return "आयु दर्ज नहीं की गई है। कृपया पूर्ण वर्ष दर्ज करें।"
            return "Age has not been provided. Please specify your completed age in years."
        if field == "annual_family_income":
            if lang == "mr":
                return "कौटुंबिक वार्षिक उत्पन्न नमूद केलेले नाही. कृपया रुपयांमध्ये अंदाजे उत्पन्न प्रविष्ट करा."
            if lang == "hi":
                return "पारिवारिक वार्षिक आय दर्ज नहीं की गई है। कृपया रुपये में अनुमानित आय दर्ज करें।"
            return "Family income has not been provided. Please provide an estimate of your annual income in INR."
        if field == "resident_state":
            if lang == "mr":
                return "रहिवासी राज्य निवडलेले नाही. कृपया आपले राज्य निवडा."
            if lang == "hi":
                return "निवास राज्य नहीं चुना गया है। कृपया अपना राज्य चुनें।"
            return "State of residence has not been specified. Please select your resident state."
        if field == "gender":
            if lang == "mr":
                return "लिंग निवडलेले नाही. कृपया आपले लिंग निवडा."
            if lang == "hi":
                return "लिंग नहीं चुना गया है। कृपया अपना लिंग चुनें।"
            return "Gender has not been selected. Please choose your gender."
        if field == "caste_category":
            if lang == "mr":
                return "सामाजिक प्रवर्ग निवडलेला नाही. कृपया आपला प्रवर्ग निवडा."
            if lang == "hi":
                return "सामाजिक वर्ग नहीं चुना गया है। कृपया अपना वर्ग चुनें।"
            return "Social category has not been provided. Please select your category."
        if field == "bpl":
            if lang == "mr":
                return "दारिद्र्यरेषेखालील (BPL) स्थिती नमूद केलेली नाही."
            if lang == "hi":
                return "गरीबी रेखा से नीचे (BPL) स्थिति दर्ज नहीं की गई है।"
            return "BPL registration status has not been specified."
        if field == "receiving_other_pension":
            if lang == "mr":
                return "इतर पेन्शन घेण्याबाबत माहिती दिलेली नाही."
            if lang == "hi":
                return "अन्य पेंशन के संबंध में जानकारी नहीं दी गई है।"
            return "Information regarding other pension benefits has not been provided."
        if field == "aadhaar_linked_bank_account":
            if lang == "mr":
                return "बँक खाते आधारशी जोडलेले आहे का ते नमूद केलेले नाही."
            if lang == "hi":
                return "बैंक खाता आधार से जुड़ा है या नहीं, यह दर्ज नहीं किया गया है।"
            return "Aadhaar-seeded bank account status has not been specified."

        field_title = _get_field_title(field, lang)
        if lang == "mr":
            return f"{field_title} ची माहिती उपलब्ध नाही. कृपया ही माहिती द्या."
        if lang == "hi":
            return f"{field_title} की जानकारी उपलब्ध नहीं है। कृपया यह जानकारी दें।"
        return f"{field_title} has not been provided. Please furnish this information."

    if status == ConditionStatus.SATISFIED:
        prov_prefix = (
            "Based on your answers: "
            if lang == "en"
            else "तुम्ही दिलेल्या माहितीनुसार: "
            if lang == "mr"
            else "आपकी दी गई जानकारी के अनुसार: "
        )
        if provenance == ValueProvenance.DOCUMENT_EXTRACTED:
            prov_prefix = (
                "Based on uploaded certificate (verification pending): "
                if lang == "en"
                else "अपलोड केलेल्या प्रमाणपत्रावर आधारित (पडताळणी प्रलंबित): "
                if lang == "mr"
                else "अपलोड किए गए प्रमाण पत्र के अनुसार (सत्यापन लंबित): "
            )
        elif provenance == ValueProvenance.REVIEWER_VERIFIED:
            prov_prefix = (
                "Verified by reviewer: "
                if lang == "en"
                else "समीक्षकाद्वारे पडताळणी पूर्ण: "
                if lang == "mr"
                else "समीक्षक द्वारा सत्यापित: "
            )

        if field == "annual_family_income":
            fmt_act = _format_inr(actual)
            fmt_req = _format_inr(val)
            if lang == "mr":
                return f"{prov_prefix}कौटुंबिक वार्षिक उत्पन्न रु. {fmt_act}/- असून ते विहित मर्यादा रु. {fmt_req}/- च्या आत असल्याने ही अट पूर्ण होते."
            if lang == "hi":
                return f"{prov_prefix}पारिवारिक वार्षिक आय ₹{fmt_act}/- है, जो ₹{fmt_req}/- की सीमा के भीतर होने से यह शर्त पूरी होती है।"
            return f"{prov_prefix}Your family annual income of ₹{fmt_act} is within the required limit of ₹{fmt_req}."

        if field == "age":
            if lang == "mr":
                return f"{prov_prefix}वय {actual} वर्षे असून वयाची अट पूर्ण होते ({req_desc})."
            if lang == "hi":
                return f"{prov_prefix}आयु {actual} वर्ष होने से आयु की शर्त पूरी होती है ({req_desc})।"
            return f"{prov_prefix}Your age of {actual} years satisfies the condition ({req_desc})."

        if field == "resident_state":
            if lang == "mr":
                return f"{prov_prefix}महाराष्ट्र राज्याचे रहिवासी असल्याने अधिवास अट पूर्ण होते."
            if lang == "hi":
                return f"{prov_prefix}महाराष्ट्र राज्य के निवासी होने से यह शर्त पूरी होती है।"
            return f"{prov_prefix}Residency in Maharashtra satisfies the state domicile requirement."

        if field == "gender":
            if lang == "mr":
                return f"{prov_prefix}महिला लाभार्थीची अट पूर्ण होते."
            if lang == "hi":
                return f"{prov_prefix}महिला लाभार्थी की शर्त पूरी होती है।"
            return f"{prov_prefix}Gender condition is satisfied."

        if field == "caste_category":
            if lang == "mr":
                return f"{prov_prefix}सामाजिक प्रवर्ग ({actual}) या योजनेच्या निकषांनुसार पात्र आहे."
            if lang == "hi":
                return f"{prov_prefix}सामाजिक वर्ग ({actual}) इस योजना के मानदंडों के अनुसार पात्र है।"
            return f"{prov_prefix}Your social category ({actual}) satisfies the scheme requirements."

        if field == "disability_percentage":
            if lang == "mr":
                return f"{prov_prefix}प्रमाणित दिव्यांगत्व {actual}% असून विहित अट पूर्ण होते ({req_desc})."
            if lang == "hi":
                return f"{prov_prefix}प्रमाणित दिव्यांगता {actual}% है और विहित शर्त पूरी होती है ({req_desc})।"
            return f"{prov_prefix}Certified disability of {actual}% satisfies the requirement ({req_desc})."

        if lang == "mr":
            return f"{prov_prefix}ही अट पूर्ण होते ({req_desc})."
        if lang == "hi":
            return f"{prov_prefix}यह शर्त पूरी होती है ({req_desc})।"
        return f"{prov_prefix}This condition appears satisfied ({req_desc})."

    # status == ConditionStatus.UNMET
    prov_prefix = (
        "Based on your answers: "
        if lang == "en"
        else "तुम्ही दिलेल्या माहितीनुसार: "
        if lang == "mr"
        else "आपकी दी गई जानकारी के अनुसार: "
    )
    if field == "annual_family_income":
        fmt_act = _format_inr(actual)
        fmt_req = _format_inr(val)
        if lang == "mr":
            return f"{prov_prefix}कौटुंबिक वार्षिक उत्पन्न रु. {fmt_act}/- हे योजनेच्या कमाल मर्यादा रु. {fmt_req}/- पेक्षा जास्त आहे."
        if lang == "hi":
            return f"{prov_prefix}पारिवारिक वार्षिक आय ₹{fmt_act}/- योजना की अधिकतम सीमा ₹{fmt_req}/- से अधिक है।"
        return f"{prov_prefix}Your family income of ₹{fmt_act} exceeds the allowable limit of ₹{fmt_req}."

    if field == "age":
        if lang == "mr":
            return f"{prov_prefix}दिलेले वय ({actual} वर्षे) या अटीची पूर्तता करत नाही ({req_desc})."
        if lang == "hi":
            return f"{prov_prefix}दी गई आयु ({actual} वर्ष) इस शर्त को पूरा नहीं करती ({req_desc})।"
        return f"{prov_prefix}Your reported age ({actual} years) does not satisfy the requirement ({req_desc})."

    if field == "resident_state":
        if lang == "mr":
            return f"{prov_prefix}ही योजना केवळ महाराष्ट्रातील रहिवाशांसाठी लागू आहे (दिलेले राज्य: {actual})."
        if lang == "hi":
            return f"{prov_prefix}यह योजना केवल महाराष्ट्र के निवासियों के लिए है (दर्ज राज्य: {actual})।"
        return f"{prov_prefix}This scheme is restricted to residents of Maharashtra (reported: {actual})."

    if field == "gender":
        if lang == "mr":
            return f"{prov_prefix}ही योजना केवळ महिला अर्जदारांसाठी लागू आहे."
        if lang == "hi":
            return f"{prov_prefix}यह योजना केवल महिला आवेदकों के लिए लागू है।"
        return f"{prov_prefix}This scheme is specifically restricted to female applicants."

    if field == "caste_category":
        if lang == "mr":
            return f"{prov_prefix}दिलेला प्रवर्ग ({actual}) या योजनेच्या प्रवर्गाशी जुळत नाही ({req_desc})."
        if lang == "hi":
            return f"{prov_prefix}दर्ज वर्ग ({actual}) इस योजना के वर्ग से मेल नहीं खाता ({req_desc})।"
        return f"{prov_prefix}Your social category ({actual}) does not match the scheme's target group ({req_desc})."

    if field == "disability_percentage":
        if lang == "mr":
            return f"{prov_prefix}प्रमाणित दिव्यांगत्व {actual}% असून ते विहित निकषाची पूर्तता करत नाही ({req_desc})."
        if lang == "hi":
            return f"{prov_prefix}प्रमाणित दिव्यांगता {actual}% है, जो विहित मानदंड को पूरा नहीं करती ({req_desc})।"
        return f"{prov_prefix}Certified disability of {actual}% does not satisfy the requirement ({req_desc})."

    if lang == "mr":
        return f"{prov_prefix}या अटीची पूर्तता होत नाही ({req_desc})."
    if lang == "hi":
        return f"{prov_prefix}यह शर्त पूरी नहीं होती है ({req_desc})।"
    return f"{prov_prefix}This requirement is not satisfied ({req_desc})."


# ---------------------------------------------------------------------------
# Core Traversal and Short-Circuit Reasoning Logic
# ---------------------------------------------------------------------------

def _determine_provenance(
    field: str,
    profile: CitizenProfile,
    extracted_documents: list[ExtractedDocument] | None,
    review_record: dict[str, Any] | None,
) -> ValueProvenance:
    actual = profile.value_for_rule(field)
    if actual is None:
        return ValueProvenance.MISSING

    if review_record is not None and review_record.get("status") == "review_completed":
        return ValueProvenance.REVIEWER_VERIFIED

    if extracted_documents:
        field_doc_map = {
            "annual_family_income": "income_certificate",
            "age": "aadhaar_card",
            "caste_category": "caste_certificate",
            "resident_state": "domicile_certificate",
        }
        target_doc_type = field_doc_map.get(field)
        if target_doc_type and any(d.document_type == target_doc_type for d in extracted_documents):
            return ValueProvenance.DOCUMENT_EXTRACTED

    return ValueProvenance.SELF_REPORTED


def _traverse_and_explain(
    node: RuleNode,
    profile: CitizenProfile,
    evidence_map: dict[str, RuleEvidence],
    lang: str,
    extracted_documents: list[ExtractedDocument] | None,
    review_record: dict[str, Any] | None,
    default_ref_date: date | None = None,
) -> tuple[list[ExplainedCondition], list[ExplainedCondition], list[ExplainedCondition]]:
    """
    Recursively evaluate and explain conditions while respecting short-circuit logic:
    - AND ('all'): All must pass.
    - OR ('any'): If any child passes, the OR condition is satisfied.
                 Irrelevant missing fields or failures from alternative branches
                 MUST NOT be exposed to the citizen once a branch is satisfied.
    """
    positive: list[ExplainedCondition] = []
    unmet: list[ExplainedCondition] = []
    missing: list[ExplainedCondition] = []

    if node.op == "all":
        for child in node.children:
            p, u, m = _traverse_and_explain(
                child, profile, evidence_map, lang, extracted_documents, review_record, default_ref_date
            )
            positive.extend(p)
            unmet.extend(u)
            missing.extend(m)
        return positive, unmet, missing

    if node.op == "any":
        child_evals = []
        for child in node.children:
            eval_res = evaluate_node(child, profile, default_reference_date=default_ref_date)
            p, u, m = _traverse_and_explain(
                child, profile, evidence_map, lang, extracted_documents, review_record, default_ref_date
            )
            child_evals.append((eval_res.value, p, u, m))

        # 1. If at least one branch is TRUE (matched):
        # The OR condition is satisfied! Only include the satisfied branches.
        # DO NOT expose irrelevant missing questions or failures from other branches!
        satisfied_branches = [item for item in child_evals if item[0] is True]
        if satisfied_branches:
            for _, p, _, _ in satisfied_branches:
                positive.extend(p)
            return positive, unmet, missing

        # 2. If ALL branches are FALSE (failed):
        # The OR condition failed completely. Expose the alternative failures.
        all_failed = all(item[0] is False for item in child_evals)
        if all_failed:
            for _, _, u, _ in child_evals:
                unmet.extend(u)
            return positive, unmet, missing

        # 3. Otherwise, it is UNKNOWN (missing information):
        # Expose missing information from branches that are still candidates.
        for val, _, _, m in child_evals:
            if val is None:
                missing.extend(m)
        return positive, unmet, missing

    if node.op == "not":
        child = node.children[0]
        eval_res = evaluate_node(child, profile, default_reference_date=default_ref_date)
        # If child is False, NOT is True (satisfied)
        if eval_res.value is False:
            p, _, _ = _traverse_and_explain(
                child, profile, evidence_map, lang, extracted_documents, review_record, default_ref_date
            )
            positive.extend(p)
        elif eval_res.value is True:
            _, u, _ = _traverse_and_explain(
                child, profile, evidence_map, lang, extracted_documents, review_record, default_ref_date
            )
            unmet.extend(u)
        else:
            _, _, m = _traverse_and_explain(
                child, profile, evidence_map, lang, extracted_documents, review_record, default_ref_date
            )
            missing.extend(m)
        return positive, unmet, missing

    # Atomic Leaf Node
    field = node.field or "unknown_field"
    ref_date = getattr(node, "as_of_date", None) or default_ref_date
    actual = profile.value_for_rule(field, reference_date=ref_date)
    eval_leaf = evaluate_node(node, profile, default_reference_date=default_ref_date)

    if eval_leaf.value is True:
        status = ConditionStatus.SATISFIED
    elif eval_leaf.value is False:
        status = ConditionStatus.UNMET
    else:
        status = ConditionStatus.UNKNOWN

    cid = getattr(node, "condition_id", None)
    ev = evidence_map.get(cid) if cid else None
    provenance = _determine_provenance(field, profile, extracted_documents, review_record)

    title = _get_field_title(field, lang)
    req_desc = _describe_requirement(node, lang)
    explanation = _explain_condition_result(node, actual, status, provenance, lang)

    is_verified = (
        ev is not None and ev.verification_status == RuleVerificationStatus.LEGAL_APPROVED
    )

    explained = ExplainedCondition(
        condition_id=cid,
        field=field,
        operator=node.op,
        required_value=node.value,
        actual_value=actual,
        provenance=provenance,
        status=status,
        title=title,
        requirement_description=req_desc,
        citizen_explanation=explanation,
        evidence_id=cid,
        source_title=ev.source_title if ev else None,
        official_reference=ev.official_reference if ev else None,
        effective_from=ev.effective_from if ev else None,
        page_or_section=ev.page_or_section if ev else None,
        official_source_url=ev.official_source_url if ev else None,
        verification_status=ev.verification_status.value if ev else "unsupported",
        is_rule_verified=is_verified,
    )

    if status == ConditionStatus.SATISFIED:
        positive.append(explained)
    elif status == ConditionStatus.UNMET:
        unmet.append(explained)
    else:
        missing.append(explained)

    return positive, unmet, missing


# ---------------------------------------------------------------------------
# Public Explanation Service APIs
# ---------------------------------------------------------------------------

def explain_eligibility(
    *,
    scheme_id: str,
    scheme_name: str,
    eligibility_status: EligibilityStatus | str,
    eligibility_reason: str,
    rule_root: RuleNode,
    profile: CitizenProfile,
    evidence_list: list[RuleEvidence] | None = None,
    document_requirements: list[DocumentRequirement] | list[str] | None = None,
    sources: list[SourceReference] | None = None,
    language: Language | str = Language.EN,
    publication_authorized: bool = False,
    rule_status: str = "draft",
    approved_by: str | None = None,
    extracted_documents: list[ExtractedDocument] | None = None,
    review_record: dict[str, Any] | None = None,
    reference_date: date | None = None,
) -> SchemeExplanation:
    """Pure explanation engine producing structured, multilingual, evidence-grounded citizen explanations."""
    lang = _lang_code(language)
    if lang not in {"en", "mr", "hi"}:
        lang = "en"

    # Map evidence by condition_id
    evidence_map: dict[str, RuleEvidence] = {}
    for item in evidence_list or []:
        ev = RuleEvidence.model_validate(item) if isinstance(item, dict) else item
        if ev.condition_id:
            evidence_map[ev.condition_id] = ev

    # Traverse AST and generate short-circuit-aware condition explanations
    positive, unmet, missing = _traverse_and_explain(
        node=rule_root,
        profile=profile,
        evidence_map=evidence_map,
        lang=lang,
        extracted_documents=extracted_documents,
        review_record=review_record,
        default_ref_date=reference_date,
    )

    status_str = (
        eligibility_status.value
        if isinstance(eligibility_status, EligibilityStatus)
        else str(eligibility_status).lower()
    )

    # Trust & Verification Classification
    is_fully_approved = (
        rule_status == "active"
        and publication_authorized is True
        and bool(approved_by)
        and "demo" not in (approved_by or "").casefold()
    )

    if not is_fully_approved:
        scheme_ver_status = "under_review"
        scheme_ver_label = TRUST_NOTICES["rules_under_review"].get(lang, TRUST_NOTICES["rules_under_review"]["en"])
    else:
        scheme_ver_status = "verified_active"
        scheme_ver_label = (
            "Officially verified and authorized scheme rules."
            if lang == "en"
            else "अधिकृतपणे पडताळलेले व मंजूर योजना नियम."
            if lang == "mr"
            else "आधिकारिक तौर पर सत्यापित एवं स्वीकृत योजना नियम।"
        )

    # Localized Overall Status Label
    overall_label = STATUS_LABELS.get(status_str, {}).get(lang) or STATUS_LABELS.get(status_str, {}).get("en") or status_str.replace("_", " ").title()

    # Localized Recommended Next Action
    next_action = RECOMMENDED_ACTIONS.get(status_str, {}).get(lang) or RECOMMENDED_ACTIONS.get(status_str, {}).get("en") or eligibility_reason

    # Trust Notices & Disclaimers
    trust_notices = [
        TRUST_NOTICES["based_on_answers"].get(lang, TRUST_NOTICES["based_on_answers"]["en"]),
        TRUST_NOTICES["document_pending"].get(lang, TRUST_NOTICES["document_pending"]["en"]),
        TRUST_NOTICES["not_government_approval"].get(lang, TRUST_NOTICES["not_government_approval"]["en"]),
    ]
    if not is_fully_approved:
        trust_notices.insert(1, scheme_ver_label)

    # Explained Sources
    explained_sources: list[ExplainedSource] = []
    for s in sources or []:
        src_obj = SourceReference.model_validate(s) if isinstance(s, dict) else s
        explained_sources.append(
            ExplainedSource(
                source_title=src_obj.source_name,
                source_url=src_obj.source_url,
                source_kind=src_obj.source_kind,
                page_or_section=src_obj.page_or_section,
                verification_status="unverified" if not is_fully_approved else "verified",
            )
        )

    # Explained Document Requirements
    explained_docs: list[ExplainedDocument] = []
    for doc in document_requirements or []:
        if isinstance(doc, DocumentRequirement):
            d_name = doc.display_name.for_language(lang)
            d_auth = doc.issuing_authority.for_language(lang)
            explained_docs.append(
                ExplainedDocument(
                    document_id=doc.canonical_document_id,
                    name=d_name,
                    issuing_authority=d_auth,
                    rts_delivery_days=doc.statutory_delivery_days,
                    verification_state="document_verification_pending",
                )
            )
        elif isinstance(doc, dict) and "canonical_document_id" in doc:
            doc_obj = DocumentRequirement.model_validate(doc)
            explained_docs.append(
                ExplainedDocument(
                    document_id=doc_obj.canonical_document_id,
                    name=doc_obj.display_name.for_language(lang),
                    issuing_authority=doc_obj.issuing_authority.for_language(lang),
                    rts_delivery_days=doc_obj.statutory_delivery_days,
                    verification_state="document_verification_pending",
                )
            )
        elif isinstance(doc, str):
            clean_str = doc.strip()
            # Check common static translations
            canon_key = clean_str.lower().replace(" ", "_").replace("/", "_")
            trans_entry = COMMON_DOCUMENT_NAMES.get(canon_key, {})
            doc_name = trans_entry.get(lang) or trans_entry.get("en") or clean_str
            auth_name = (
                "Competent Issuing Authority"
                if lang == "en"
                else "सक्षम प्राधिकारी"
                if lang == "mr"
                else "सक्षम प्राधिकारी"
            )
            explained_docs.append(
                ExplainedDocument(
                    document_id=canon_key,
                    name=doc_name,
                    issuing_authority=auth_name,
                    rts_delivery_days=None,
                    verification_state="document_verification_pending",
                )
            )

    # Citizen-facing Summary
    if status_str == "eligible":
        summary = (
            f"Based on your reported answers, you satisfy all {len(positive)} preliminary eligibility condition(s) for this scheme."
            if lang == "en"
            else f"तुम्ही दिलेल्या माहितीनुसार, तुम्ही या योजनेच्या सर्व {len(positive)} प्राथमिक पात्रता अटी पूर्ण करता."
            if lang == "mr"
            else f"आपकी दी गई जानकारी के अनुसार, आप इस योजना की सभी {len(positive)} प्रारंभिक पात्रता शर्तों को पूरा करते हैं।"
        )
    elif status_str == "ineligible":
        summary = (
            f"Based on your reported answers, {len(unmet)} condition(s) are not satisfied."
            if lang == "en"
            else f"तुम्ही दिलेल्या माहितीनुसार, {len(unmet)} अटी पूर्ण होत नाहीत."
            if lang == "mr"
            else f"आपकी दी गई जानकारी के अनुसार, {len(unmet)} शर्तें पूरी नहीं होती हैं।"
        )
    elif status_str == "needs_information":
        summary = (
            f"Additional information is needed to evaluate {len(missing)} condition(s) for this scheme."
            if lang == "en"
            else f"या योजनेसाठी {len(missing)} अटी तपासण्यासाठी अधिक माहिती आवश्यक आहे."
            if lang == "mr"
            else f"इस योजना की {len(missing)} शर्तों की जांच के लिए अतिरिक्त जानकारी की आवश्यकता है।"
        )
    else:  # needs_review
        summary = (
            f"This scheme's rules are under review. {len(positive)} condition(s) appear satisfied, {len(unmet)} unmet, and {len(missing)} unknown."
            if lang == "en"
            else f"या योजनेचे नियम पुनरावलोकनाधीन आहेत. {len(positive)} अटी जुळल्या, {len(unmet)} अपूर्ण आणि {len(missing)} अज्ञात आहेत."
            if lang == "mr"
            else f"इस योजना के नियम समीक्षाधीन हैं। {len(positive)} शर्तें पूरी हुईं, {len(unmet)} अपूर्ण और {len(missing)} अज्ञात हैं।"
        )

    return SchemeExplanation(
        scheme_id=scheme_id,
        scheme_name=scheme_name,
        language=lang,
        overall_status=status_str,
        overall_status_label=overall_label,
        summary=summary,
        positive_conditions=positive,
        unmet_conditions=unmet,
        missing_information=missing,
        relevant_sources=explained_sources,
        document_requirements=explained_docs,
        scheme_verification_status=scheme_ver_status,
        scheme_verification_label=scheme_ver_label,
        next_recommended_action=next_action,
        trust_notices=trust_notices,
    )


def generate_scheme_explanation(
    scheme: Scheme,
    profile: CitizenProfile,
    eligibility_result: EligibilityResult | None = None,
    *,
    language: Language | str = Language.EN,
    extracted_documents: list[ExtractedDocument] | None = None,
    review_record: dict[str, Any] | None = None,
    reference_date: date | None = None,
) -> SchemeExplanation:
    """Convenience wrapper accepting a Scheme and CitizenProfile, evaluating if needed."""
    effective_ref_date = reference_date or getattr(scheme, "eligibility_reference_date", None)
    res = eligibility_result or evaluate_scheme(scheme, profile, reference_date=effective_ref_date)

    doc_reqs = getattr(scheme, "document_requirements", None) or getattr(scheme, "required_documents", None) or []

    return explain_eligibility(
        scheme_id=scheme.scheme_id,
        scheme_name=scheme.name,
        eligibility_status=res.status,
        eligibility_reason=res.reason,
        rule_root=scheme.eligibility_rule,
        profile=profile,
        evidence_list=getattr(scheme, "evidence", []),
        document_requirements=doc_reqs,
        sources=scheme.sources,
        language=language,
        publication_authorized=scheme.publication_authorized,
        rule_status=scheme.rule_status,
        approved_by=scheme.approved_by,
        extracted_documents=extracted_documents,
        review_record=review_record,
        reference_date=effective_ref_date,
    )
