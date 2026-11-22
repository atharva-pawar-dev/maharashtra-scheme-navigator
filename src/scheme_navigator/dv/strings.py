"""TRIMURTI / MSN-DV-001 String Catalogue & Plain-Language Copy Engine.

Provides human-reviewable, three-language (EN, MR, HI) citizen-facing copy.
Enforces Law L10 ('Never blame, always explain'), grade-6 reading level,
and respectful, supportive phrasing (Aaji Test).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class VocabularyLadder(str, Enum):
    """The six distinct verification steps defined by Section 4.5."""
    RECEIVED = "RECEIVED"
    READABLE = "READABLE"
    UNDERSTOOD = "UNDERSTOOD"
    LOOKS_CONSISTENT = "LOOKS_CONSISTENT"
    REVIEWED_BY_TEAM = "REVIEWED_BY_TEAM"
    CONFIRMED_BY_ISSUER = "CONFIRMED_BY_ISSUER"


@dataclass(frozen=True)
class CopyString:
    key: str
    en: str
    mr: str
    hi: str
    tag: str  # 'native_reviewed' or 'machine_drafted'
    explanation: str


# Banned words in citizen-facing text (Annex C §C4)
BANNED_WORDS = {
    "en": [
        "invalid", "rejected", "failed", "error code", "ocr", "parse",
        "validate", "payload", "null", "exception", "token", "verified"
    ],
    "mr": [
        "अवैध", "नाकारले", "अयशस्वी", "त्रुटी कोड", "ओसीआर", "पार्स",
        "व्हॅलिडेट", "पेलोड", "नल", "अपवाद", "टोकन", "व्हेरिफाईड"
    ],
    "hi": [
        "अवैध", "अस्वीकृत", "असफल", "त्रुटि कोड", "ओसीआर", "पार्स",
        "वैलिडेट", "पेलोड", "नल", "अपवाद", "टोकन", "वेरिफाइड"
    ]
}


CATALOGUE: Dict[str, CopyString] = {
    # Vocabulary ladder badges (Law L9)
    "ladder.received": CopyString(
        key="ladder.received",
        en="Received",
        mr="कागद मिळाला",
        hi="कागज़ मिला",
        tag="native_reviewed",
        explanation="We have received your document safely.",
    ),
    "ladder.readable": CopyString(
        key="ladder.readable",
        en="Readable",
        mr="वाचता येत आहे",
        hi="पढ़ा जा सकता है",
        tag="native_reviewed",
        explanation="The photo or document is clear to read.",
    ),
    "ladder.understood": CopyString(
        key="ladder.understood",
        en="Understood",
        mr="माहिती समजली",
        hi="जानकारी समझी",
        tag="native_reviewed",
        explanation="We read the important details from the paper.",
    ),
    "ladder.consistent": CopyString(
        key="ladder.consistent",
        en="Looks consistent",
        mr="माहिती जुळत आहे",
        hi="जानकारी मेल खाती है",
        tag="native_reviewed",
        explanation="The details match what you shared with us.",
    ),
    "ladder.reviewed_by_team": CopyString(
        key="ladder.reviewed_by_team",
        en="Reviewed by our team",
        mr="आमच्या चमूने तपासले",
        hi="हमारी टीम ने देखा",
        tag="native_reviewed",
        explanation="A team reviewer checked this paper manually.",
    ),
    "ladder.confirmed_by_issuer": CopyString(
        key="ladder.confirmed_by_issuer",
        en="Confirmed by issuer",
        mr="शासकीय यंत्रणेने पुष्टी केली",
        hi="विभाग द्वारा पुष्टि",
        tag="native_reviewed",
        explanation="Directly confirmed by the issuing authority.",
    ),

    # Capture Guidance
    "capture.blur_warning": CopyString(
        key="capture.blur_warning",
        en="The photo is a little blurry. Please move to good light, hold steady, and try again.",
        mr="फोटो थोडा अस्पष्ट आहे. कृपया चांगल्या उजेडात, हात स्थिर ठेवून पुन्हा फोटो काढा.",
        hi="फ़ोटो थोड़ा धुंधला है। कृपया अच्छी रोशनी में, हाथ स्थिर रखकर दोबारा फ़ोटो लें।",
        tag="native_reviewed",
        explanation="Guidance when camera blur is detected.",
    ),
    "capture.dark_warning": CopyString(
        key="capture.dark_warning",
        en="The photo is a little dark. Please move to the light and try again.",
        mr="फोटोमध्ये थोडा अंधार दिसत आहे. कृपया उजेडात जाऊन पुन्हा फोटो काढा.",
        hi="फ़ोटो में थोड़ा अंधेरा है। कृपया रोशनी में जाकर दोबारा फ़ोटो लें।",
        tag="native_reviewed",
        explanation="Guidance when photo is underexposed.",
    ),
    "capture.glare_warning": CopyString(
        key="capture.glare_warning",
        en="There is bright reflection on the paper. Please tilt slightly away from the light.",
        mr="कागदावर प्रकाश चमकत आहे. कृपया फोन थोडा तिरका धरून फोटो काढा.",
        hi="कागज़ पर चमक आ रही है। कृपया फ़ोन को रोशनी से थोड़ा तिरछा करके फ़ोटो लें।",
        tag="native_reviewed",
        explanation="Guidance when glare obscures text.",
    ),
    "capture.human_check_prompt": CopyString(
        key="capture.human_check_prompt",
        en="Can you read every word clearly on this screen?",
        mr="तुम्हाला या फोटोतील सर्व अक्षरे स्पष्ट वाचता येत आहेत का?",
        hi="क्या आप इस फ़ोटो के सभी शब्द साफ़ पढ़ पा रहे हैं?",
        tag="native_reviewed",
        explanation="Aaji human confirmation beats heuristics.",
    ),

    # Confirm with Crop
    "confirm.title": CopyString(
        key="confirm.title",
        en="Check what we read from your paper",
        mr="आम्ही वाचलेली माहिती बरोबर आहे का ते तपासा",
        hi="कागज़ से पढ़ी गई जानकारी जाँचें",
        tag="native_reviewed",
        explanation="Header for side-by-side confirm with crop.",
    ),
    "confirm.is_correct": CopyString(
        key="confirm.is_correct",
        en="Yes, correct",
        mr="होय, बरोबर आहे",
        hi="हाँ, सही है",
        tag="native_reviewed",
        explanation="Button to confirm an extracted value.",
    ),
    "confirm.edit": CopyString(
        key="confirm.edit",
        en="Change this",
        mr="बदल करा",
        hi="बदलें",
        tag="native_reviewed",
        explanation="Button to manually correct a field.",
    ),
    "confirm.not_sure": CopyString(
        key="confirm.not_sure",
        en="Not sure",
        mr="नक्की माहिती नाही",
        hi="पक्का पता नहीं",
        tag="native_reviewed",
        explanation="Button when citizen is uncertain.",
    ),

    # Name matching questions (Law L10)
    "name.mismatch_question": CopyString(
        key="name.mismatch_question",
        en="The name on this paper looks a little different from your details. Is this you?",
        mr="या कागदावरील नाव तुमच्या माहितीपेक्षा थोडे वेगळे दिसते. हे तुमचेच नाव आहे का?",
        hi="इस कागज़ पर नाम आपकी जानकारी से थोड़ा अलग दिखता है। क्या यह आपका ही नाम है?",
        tag="native_reviewed",
        explanation="Friendly question on name difference.",
    ),
    "name.marriage_question": CopyString(
        key="name.marriage_question",
        en="Did your surname or middle name change after marriage?",
        mr="लग्नानंतर तुमचे आडनाव किंवा मधले नाव बदलले आहे का?",
        hi="क्या शादी के बाद आपका उपनाम या बीच का नाम बदला है?",
        tag="native_reviewed",
        explanation="Respectful question for married women in Maharashtra.",
    ),

    # Income remediation
    "income.over_limit_advisory": CopyString(
        key="income.over_limit_advisory",
        en="This certificate shows income above the scheme limit. You can still apply if this changed recently.",
        mr="या दाखल्यावरील उत्पन्न योजनेच्या मर्यादेपेक्षा अधिक दिसते. यात बदल झाला असल्यास तुम्ही अर्ज करू शकता.",
        hi="इस प्रमाण-पत्र में आय योजना की सीमा से अधिक दिखती है। हाल में बदलाव हुआ हो तो आप आगे बढ़ सकते हैं।",
        tag="native_reviewed",
        explanation="Advisory explanation for income check.",
    ),
    "income.missing_year": CopyString(
        key="income.missing_year",
        en="We could not tell which financial year this income is for. Please choose the year or add a clearer copy.",
        mr="हे उत्पन्न कोणत्या आर्थिक वर्षाचे आहे ते समजले नाही. कृपया वर्ष निवडा किंवा अधिक स्पष्ट प्रत जोडा.",
        hi="यह आय किस वित्तीय वर्ष की है, यह स्पष्ट नहीं है। कृपया वर्ष चुनें या साफ़ प्रति जोड़ें।",
        tag="native_reviewed",
        explanation="Friendly request when financial year is unclear.",
    ),

    # Honest Privacy Promise (Annex C §C5)
    "privacy.promise_line1": CopyString(
        key="privacy.promise_line1",
        en="We only read details needed for this scheme.",
        mr="आम्ही फक्त या योजनेसाठी लागणारी माहिती वाचतो.",
        hi="हम केवल इस योजना के लिए ज़रूरी जानकारी पढ़ते हैं।",
        tag="native_reviewed",
        explanation="Privacy promise point 1.",
    ),
    "privacy.promise_line2": CopyString(
        key="privacy.promise_line2",
        en="Your papers are private and never shared with anyone.",
        mr="तुमचे कागदपत्र सुरक्षित राहतात आणि कोणाशीही सामायिक केले जात नाहीत.",
        hi="आपके दस्तावेज़ सुरक्षित हैं और किसी से साझा नहीं किए जाते।",
        tag="native_reviewed",
        explanation="Privacy promise point 2.",
    ),
    "privacy.promise_line3": CopyString(
        key="privacy.promise_line3",
        en="You can delete everything anytime with one tap.",
        mr="तुम्ही एका बटनावर सर्व माहिती कधीही कायमची हटवू शकता.",
        hi="आप एक क्लिक में अपनी सारी जानकारी कभी भी हटा सकते हैं।",
        tag="native_reviewed",
        explanation="Privacy promise point 3.",
    ),

    # Official authority reminder (Law L7)
    "advisory.official_authority_reminder": CopyString(
        key="advisory.official_authority_reminder",
        en="This is a helper check we did for you. The government office makes the final decision.",
        mr="ही आम्ही केलेली पूर्वतयारी तपासणी आहे. अंतिम निर्णय संबंधित शासकीय कार्यालयच घेते.",
        hi="यह आपकी सुविधा के लिए की गई पूर्व-जाँच है। अंतिम निर्णय सरकारी कार्यालय ही करता है।",
        tag="native_reviewed",
        explanation="Crucial truth disclaimer shown on readiness screen.",
    ),

    # Help & accessibility
    "help.read_aloud": CopyString(
        key="help.read_aloud",
        en="Read aloud",
        mr="मोठ्याने वाचा",
        hi="बोलकर सुनाएं",
        tag="native_reviewed",
        explanation="Screen reader trigger button.",
    ),
    "help.someone_helping": CopyString(
        key="help.someone_helping",
        en="Someone is helping me",
        mr="मला कोणीतरी मदत करत आहे",
        hi="कोई मेरी मदद कर रहा है",
        tag="native_reviewed",
        explanation="Assisted mode banner toggle.",
    ),
    "help.clear_device": CopyString(
        key="help.clear_device",
        en="Clear this phone",
        mr="या फोनवरील माहिती पुसा",
        hi="इस फ़ोन से जानकारी हटाएं",
        tag="native_reviewed",
        explanation="Wipe local session for cyber cafes and shared devices.",
    ),
}


def get_string(key: str, lang: str = "mr", **kwargs: Any) -> str:
    """Retrieve localized string with safe parameter formatting."""
    cs = CATALOGUE.get(key)
    if not cs:
        return f"[{key}]"

    lang_code = lang.lower()
    if lang_code in ("mr", "marathi"):
        text = cs.mr
    elif lang_code in ("hi", "hindi"):
        text = cs.hi
    else:
        text = cs.en

    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
