"""TRIMURTI / MSN-DV-001 Requirement Slots & DocType Profiles Engine (Annex A & ADR 001).

Implements:
- Top 5 Global DocType Profiles (`DOC-INCOME-CERT`, `DOC-DOMICILE-CERT`, etc.)
- Requirement Slots for 10 Pilot Schemes with official source evidence & trust tiers.
- Alternatives handling (one accepted document satisfies the slot).
- Denominator honesty counting logic (Formula: N of M needs covered, §4.3).
- Graceful non-pilot fallback (REQUIREMENT_UNCONFIRMED with official portal link).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from scheme_navigator.dv.models import (
    AcceptedDocType,
    DocTypeProfile,
    FieldSchemaItem,
    NeedsSummary,
    RequirementKind,
    RequirementSlot,
    RequirementTrustTier,
    SlotEvaluation,
    SlotState,
)


# -------------------------------------------------------------------------
# TOP 5 GLOBAL DOCTYPE PROFILES (ADR 001)
# -------------------------------------------------------------------------
TOP_5_DOCTYPES: Dict[str, DocTypeProfile] = {
    "DOC-INCOME-CERT": DocTypeProfile(
        id="DOC-INCOME-CERT",
        names={
            "en": "Income Certificate",
            "mr": "उत्पन्नाचा दाखला",
            "hi": "आय प्रमाण-पत्र",
        },
        plain_description={
            "en": "Official certificate issued by Tahsildar showing annual family income.",
            "mr": "तहसीलदार किंवा सेतू केंद्राकडून मिळणारा वार्षिक कौटुंबिक उत्पन्नाचा दाखला.",
            "hi": "तहसीलदार द्वारा जारी वार्षिक पारिवारिक आय प्रमाण-पत्र।",
        },
        where_to_get={
            "en": "Aaple Sarkar portal (aaplesarkar.mahaonline.gov.in) or nearest Tahsil / Setu Kendra. Fee: ₹33. Time: 15 days.",
            "mr": "आपले सरकार पोर्टल किंवा नजीकचे सेतू केंद्र / तहसील कार्यालय. शुल्क: ₹३३. मुदत: १५ दिवस.",
            "hi": "आपले सरकार पोर्टल या नज़दीकी सेतु केंद्र। शुल्क: ₹33, समय: 15 दिन।",
        },
        fields=[
            FieldSchemaItem("annual_income", "amount", "CONFIDENTIAL", "Annual Family Income", "वार्षिक कौटुंबिक उत्पन्न", "वार्षिक पारिवारिक आय"),
            FieldSchemaItem("financial_year", "string", "PUBLIC", "Financial Year", "आर्थिक वर्ष", "वित्तीय वर्ष"),
            FieldSchemaItem("beneficiary_name", "string", "CONFIDENTIAL", "Beneficiary Name", "लाभार्थ्याचे नाव", "लाभार्थी का नाम"),
            FieldSchemaItem("issued_date", "date", "PUBLIC", "Issued Date", "जारी केल्याचा दिनांक", "जारी करने की तिथि"),
            FieldSchemaItem("certificate_no", "string", "PUBLIC", "Certificate Number", "दाखला क्रमांक", "प्रमाण-पत्र संख्या"),
        ],
        version="1.0.0",
    ),
    "DOC-DOMICILE-CERT": DocTypeProfile(
        id="DOC-DOMICILE-CERT",
        names={
            "en": "Domicile Certificate",
            "mr": "अधिवास दाखला (रहिवासी दाखला)",
            "hi": "अधिवास प्रमाण-पत्र",
        },
        plain_description={
            "en": "Proof of 15 years continuous residence in Maharashtra.",
            "mr": "महाराष्ट्रात सलग १५ वर्षे वास्तव्याचा अधिकृत शासकीय दाखला.",
            "hi": "महाराष्ट्र में 15 वर्ष से निवास का आधिकारिक प्रमाण।",
        },
        where_to_get={
            "en": "Aaple Sarkar portal or Sub-Divisional Officer (SDO) / Tahsildar office. Fee: ₹33. Time: 15 days.",
            "mr": "आपले सरकार पोर्टल किंवा उपविभागीय अधिकारी (SDO) / तहसील कार्यालय. शुल्क: ₹३३. मुदत: १५ दिवस.",
            "hi": "आपले सरकार पोर्टल या एसडीओ/तहसील कार्यालय। शुल्क: ₹33, समय: 15 दिन।",
        },
        fields=[
            FieldSchemaItem("beneficiary_name", "string", "CONFIDENTIAL", "Beneficiary Name", "लाभार्थ्याचे नाव", "लाभार्थी का नाम"),
            FieldSchemaItem("residence_years", "number", "PUBLIC", "Years of Residence", "महाराष्ट्रातील वास्तव्याची वर्षे", "निवास के वर्ष"),
            FieldSchemaItem("issued_date", "date", "PUBLIC", "Issued Date", "जारी केल्याचा दिनांक", "जारी करने की तिथि"),
            FieldSchemaItem("certificate_no", "string", "PUBLIC", "Certificate Number", "दाखला क्रमांक", "प्रमाण-पत्र संख्या"),
        ],
        version="1.0.0",
    ),
    "DOC-RATION-CARD": DocTypeProfile(
        id="DOC-RATION-CARD",
        names={
            "en": "Ration Card",
            "mr": "शिधापत्रिका",
            "hi": "राशन कार्ड",
        },
        plain_description={
            "en": "Yellow (BPL), Orange (AAY/APL), or White ration card showing family members.",
            "mr": "पिवळे (दारिद्र्यरेषेखालील), केशरी किंवा पांढरे रेशन कार्ड.",
            "hi": "पीला, केसरी या सफेद राशन कार्ड जिसमें परिवार के सदस्यों के नाम हों।",
        },
        where_to_get={
            "en": "District Food & Civil Supplies Department / Aaple Sarkar. Fee: ₹20-50. Time: 30 days.",
            "mr": "अन्न व नागरी पुरवठा विभाग किंवा आपले सरकार. शुल्क: ₹२०-५०. मुदत: ३० दिवस.",
            "hi": "खाद्य एवं नागरिक आपूर्ति विभाग। शुल्क: ₹20-50, समय: 30 दिन।",
        },
        fields=[
            FieldSchemaItem("card_type", "enum", "PUBLIC", "Card Type (Yellow/Orange/White)", "शिधापत्रिका प्रकार", "राशन कार्ड प्रकार"),
            FieldSchemaItem("head_of_family", "string", "CONFIDENTIAL", "Head of Family", "कुटुंब प्रमुखाचे नाव", "मुखिया का नाम"),
            FieldSchemaItem("members_count", "number", "PUBLIC", "Family Members Count", "एकूण सदस्य", "कुल सदस्य"),
        ],
        version="1.0.0",
    ),
    "DOC-BANK-PASSBOOK": DocTypeProfile(
        id="DOC-BANK-PASSBOOK",
        names={
            "en": "Bank Passbook",
            "mr": "बँक पासबुक",
            "hi": "बैंक पासबुक",
        },
        plain_description={
            "en": "First page of bank passbook or cancelled cheque with clear IFSC and Account number.",
            "mr": "बँक खात्याचे पासबुक (पहिले पान) किंवा बँक स्टेटमेंट, ज्यावर खाते क्रमांक व IFSC कोड स्पष्ट दिसेल.",
            "hi": "बैंक पासबुक का पहला पृष्ठ या कैंसल्ड चेक जिस पर खाता संख्या और IFSC साफ़ दिखे।",
        },
        where_to_get={
            "en": "Your bank branch or downloaded account statement from mobile banking.",
            "mr": "तुमच्या बँक शाखेतून किंवा मोबाइल बँकिंगमधून.",
            "hi": "आपकी बैंक शाखा या मोबाइल बैंकिंग ऐप से।",
        },
        fields=[
            FieldSchemaItem("account_holder_name", "string", "CONFIDENTIAL", "Account Holder Name", "खातेदाराचे नाव", "खाताधारक का नाम"),
            FieldSchemaItem("account_number", "string", "STRICTLY_PRIVATE", "Account Number", "खाते क्रमांक", "खाता संख्या"),
            FieldSchemaItem("ifsc_code", "string", "PUBLIC", "IFSC Code", "आयएफएससी कोड", "आईएफएससी कोड"),
            FieldSchemaItem("bank_name", "string", "PUBLIC", "Bank Name", "बँकेचे नाव", "बैंक का नाम"),
        ],
        version="1.0.0",
    ),
    "DOC-AADHAAR-CARD": DocTypeProfile(
        id="DOC-AADHAAR-CARD",
        names={
            "en": "Aadhaar Card",
            "mr": "आधार कार्ड",
            "hi": "आधार कार्ड",
        },
        plain_description={
            "en": "UIDAI identity proof with masked 12-digit number (only last 4 digits stored).",
            "mr": "युआयडीएआय (UIDAI) कडून मिळणारे अधिकृत ओळखपत्र.",
            "hi": "यूआईडीएआई द्वारा जारी पहचान पत्र।",
        },
        where_to_get={
            "en": "Download masked e-Aadhaar from uidai.gov.in or nearest Aadhaar Seva Kendra.",
            "mr": "uidai.gov.in वरून मास्क केलेले ई-आधार किंवा आधार सेवा केंद्र.",
            "hi": "uidai.gov.in से मास्क किया हुआ ई-आधार डाउनलोड करें।",
        },
        fields=[
            FieldSchemaItem("name", "string", "CONFIDENTIAL", "Full Name", "पूर्ण नाव", "पूरा नाम"),
            FieldSchemaItem("dob", "date", "PUBLIC", "Date of Birth", "जन्मदिनांक", "जन्म तिथि"),
            FieldSchemaItem("gender", "enum", "PUBLIC", "Gender", "लिंग", "लिंग"),
            FieldSchemaItem("masked_aadhaar", "string", "STRICTLY_PRIVATE", "Masked Aadhaar Number", "मास्क आधार क्रमांक", "मास्क आधार संख्या"),
        ],
        version="1.0.0",
    ),
}


# -------------------------------------------------------------------------
# PILOT SCHEMES REQUIREMENT SLOTS (ADR 001)
# -------------------------------------------------------------------------
PILOT_SCHEME_SLOTS: Dict[str, List[RequirementSlot]] = {
    # 1. Namo Shetkari Maha Samman
    "scheme-namo-shetkari-maha-samman": [
        RequirementSlot(
            slot_id="SLOT-NSMS-IDENTITY",
            scheme_id="scheme-namo-shetkari-maha-samman",
            requirement_version="1.0.0",
            need_label={"en": "Identity Proof", "mr": "ओळख पुरावा", "hi": "पहचान प्रमाण"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-AADHAAR-CARD")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="GOVERNMENT_RESOLUTION",
            source_reference="GR-AGRI-2023-06-13",
            source_quote="Scheme applicants must authenticate via Aadhaar linked with agricultural land records.",
        ),
        RequirementSlot(
            slot_id="SLOT-NSMS-BANK",
            scheme_id="scheme-namo-shetkari-maha-samman",
            requirement_version="1.0.0",
            need_label={"en": "Bank Account Proof", "mr": "बँक खाते पुरावा", "hi": "बैंक खाता प्रमाण"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-BANK-PASSBOOK", constraints={"aadhaar_seeded": True})],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="GOVERNMENT_RESOLUTION",
            source_reference="GR-AGRI-2023-06-13",
            source_quote="Direct benefit transfer requires Aadhaar-seeded active bank account.",
        ),
    ],

    # 2. PM Kisan
    "scheme-pm-kisan": [
        RequirementSlot(
            slot_id="SLOT-PMK-IDENTITY",
            scheme_id="scheme-pm-kisan",
            requirement_version="1.0.0",
            need_label={"en": "Aadhaar Identity", "mr": "आधार ओळख", "hi": "आधार पहचान"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-AADHAAR-CARD")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://pmkisan.gov.in",
            source_quote="Aadhaar is mandatory for all landholding farmers under PM-KISAN.",
        ),
        RequirementSlot(
            slot_id="SLOT-PMK-BANK",
            scheme_id="scheme-pm-kisan",
            requirement_version="1.0.0",
            need_label={"en": "Bank Passbook", "mr": "बँक पासबुक", "hi": "बैंक पासबुक"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-BANK-PASSBOOK")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://pmkisan.gov.in",
        ),
    ],

    # 3. Mukhyamantri Vayoshri Yojana (Senior Citizens 65+)
    "scheme-mukhyamantri-vayoshri": [
        RequirementSlot(
            slot_id="SLOT-VAYO-AGE-IDENTITY",
            scheme_id="scheme-mukhyamantri-vayoshri",
            requirement_version="1.0.0",
            need_label={"en": "Proof of Age & Identity", "mr": "वय व ओळख पुरावा", "hi": "आयु एवं पहचान प्रमाण"},
            kind=RequirementKind.MANDATORY,
            # Alternatives: Aadhaar Card OR Domicile Certificate
            accepted=[
                AcceptedDocType("DOC-AADHAAR-CARD", constraints={"min_age": 65}),
                AcceptedDocType("DOC-DOMICILE-CERT"),
            ],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="GOVERNMENT_RESOLUTION",
            source_reference="GR-SJD-2024-02-05",
            source_quote="Applicant must be at least 65 years of age on 31 December of application year.",
        ),
        RequirementSlot(
            slot_id="SLOT-VAYO-INCOME",
            scheme_id="scheme-mukhyamantri-vayoshri",
            requirement_version="1.0.0",
            need_label={"en": "Proof of Income", "mr": "उत्पन्न पुरावा", "hi": "आय प्रमाण"},
            kind=RequirementKind.MANDATORY,
            # Alternatives: Income Certificate OR Yellow Ration Card
            accepted=[
                AcceptedDocType("DOC-INCOME-CERT", constraints={"max_annual_income": 200000}),
                AcceptedDocType("DOC-RATION-CARD", constraints={"card_type": "YELLOW"}),
            ],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="GOVERNMENT_RESOLUTION",
            source_reference="GR-SJD-2024-02-05",
            source_quote="Annual family income must not exceed ₹2,00,000, certified by Tahsildar or BPL Yellow card.",
        ),
        RequirementSlot(
            slot_id="SLOT-VAYO-DOMICILE",
            scheme_id="scheme-mukhyamantri-vayoshri",
            requirement_version="1.0.0",
            need_label={"en": "Proof of Residence", "mr": "रहिवासी पुरावा", "hi": "निवास प्रमाण"},
            kind=RequirementKind.MANDATORY,
            # Alternatives: Domicile Certificate OR Ration Card
            accepted=[
                AcceptedDocType("DOC-DOMICILE-CERT"),
                AcceptedDocType("DOC-RATION-CARD"),
            ],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="GOVERNMENT_RESOLUTION",
            source_reference="GR-SJD-2024-02-05",
        ),
        RequirementSlot(
            slot_id="SLOT-VAYO-BANK",
            scheme_id="scheme-mukhyamantri-vayoshri",
            requirement_version="1.0.0",
            need_label={"en": "Bank Account", "mr": "बँक खाते", "hi": "बैंक खाता"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-BANK-PASSBOOK")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="GOVERNMENT_RESOLUTION",
            source_reference="GR-SJD-2024-02-05",
        ),
        RequirementSlot(
            slot_id="SLOT-VAYO-DISABILITY",
            scheme_id="scheme-mukhyamantri-vayoshri",
            requirement_version="1.0.0",
            need_label={"en": "Disability Certificate", "mr": "दिव्यांगत्व प्रमाणपत्र", "hi": "दिव्यांगता प्रमाण-पत्र"},
            kind=RequirementKind.CONDITIONAL,
            applicability_condition={"is_divyang": True},
            accepted=[AcceptedDocType("DOC-INCOME-CERT", notes="UDID or Disability Medical Certificate")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="GOVERNMENT_RESOLUTION",
            source_reference="GR-SJD-2024-02-05",
            source_quote="Required only if claiming additional assistive devices for physical impairment.",
        ),
    ],

    # 4. IGNDPS Disability Pension
    "scheme-igndps-disability-pension": [
        RequirementSlot(
            slot_id="SLOT-IGNDPS-IDENTITY",
            scheme_id="scheme-igndps-disability-pension",
            requirement_version="1.0.0",
            need_label={"en": "Identity Proof", "mr": "ओळख पुरावा", "hi": "पहचान प्रमाण"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-AADHAAR-CARD")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://nsap.nic.in",
        ),
        RequirementSlot(
            slot_id="SLOT-IGNDPS-INCOME",
            scheme_id="scheme-igndps-disability-pension",
            requirement_version="1.0.0",
            need_label={"en": "BPL Proof", "mr": "दारिद्र्यरेषेचा पुरावा", "hi": "बीपीएल प्रमाण"},
            kind=RequirementKind.MANDATORY,
            accepted=[
                AcceptedDocType("DOC-RATION-CARD", constraints={"card_type": "YELLOW"}),
                AcceptedDocType("DOC-INCOME-CERT", constraints={"max_annual_income": 21000}),
            ],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://nsap.nic.in",
        ),
        RequirementSlot(
            slot_id="SLOT-IGNDPS-BANK",
            scheme_id="scheme-igndps-disability-pension",
            requirement_version="1.0.0",
            need_label={"en": "Bank Account", "mr": "बँक खाते", "hi": "बैंक खाता"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-BANK-PASSBOOK")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://nsap.nic.in",
        ),
    ],

    # 5. IGNWPS Widow Pension
    "scheme-ignwps-widow-pension": [
        RequirementSlot(
            slot_id="SLOT-IGNWPS-IDENTITY",
            scheme_id="scheme-ignwps-widow-pension",
            requirement_version="1.0.0",
            need_label={"en": "Identity Proof", "mr": "ओळख पुरावा", "hi": "पहचान प्रमाण"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-AADHAAR-CARD")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://nsap.nic.in",
        ),
        RequirementSlot(
            slot_id="SLOT-IGNWPS-INCOME",
            scheme_id="scheme-ignwps-widow-pension",
            requirement_version="1.0.0",
            need_label={"en": "BPL / Income Proof", "mr": "दारिद्र्यरेषेचा / उत्पन्नाचा पुरावा", "hi": "बीपीएल / आय प्रमाण"},
            kind=RequirementKind.MANDATORY,
            accepted=[
                AcceptedDocType("DOC-RATION-CARD", constraints={"card_type": "YELLOW"}),
                AcceptedDocType("DOC-INCOME-CERT", constraints={"max_annual_income": 21000}),
            ],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://nsap.nic.in",
        ),
        RequirementSlot(
            slot_id="SLOT-IGNWPS-BANK",
            scheme_id="scheme-ignwps-widow-pension",
            requirement_version="1.0.0",
            need_label={"en": "Bank Passbook", "mr": "बँक पासबुक", "hi": "बैंक पासबुक"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-BANK-PASSBOOK")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://nsap.nic.in",
        ),
    ],

    # 6. EBC Tuition Waiver
    "scheme-ebc-tuition-waiver": [
        RequirementSlot(
            slot_id="SLOT-EBC-DOMICILE",
            scheme_id="scheme-ebc-tuition-waiver",
            requirement_version="1.0.0",
            need_label={"en": "Domicile Certificate", "mr": "अधिवास दाखला", "hi": "अधिवास प्रमाण-पत्र"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-DOMICILE-CERT")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="GOVERNMENT_RESOLUTION",
            source_reference="GR-HED-2018-06-02",
        ),
        RequirementSlot(
            slot_id="SLOT-EBC-INCOME",
            scheme_id="scheme-ebc-tuition-waiver",
            requirement_version="1.0.0",
            need_label={"en": "Income Certificate (Under ₹8 Lakh)", "mr": "उत्पन्नाचा दाखला (८ लाखांच्या आत)", "hi": "आय प्रमाण-पत्र (8 लाख के भीतर)"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-INCOME-CERT", constraints={"max_annual_income": 800000})],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="GOVERNMENT_RESOLUTION",
            source_reference="GR-HED-2018-06-02",
        ),
        RequirementSlot(
            slot_id="SLOT-EBC-BANK",
            scheme_id="scheme-ebc-tuition-waiver",
            requirement_version="1.0.0",
            need_label={"en": "Student Bank Passbook", "mr": "विद्यार्थ्याचे बँक पासबुक", "hi": "विद्यार्थी बैंक पासबुक"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-BANK-PASSBOOK")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="GOVERNMENT_RESOLUTION",
            source_reference="GR-HED-2018-06-02",
        ),
        RequirementSlot(
            slot_id="SLOT-EBC-RATION",
            scheme_id="scheme-ebc-tuition-waiver",
            requirement_version="1.0.0",
            need_label={"en": "Ration Card (For Child Cap)", "mr": "शिधापत्रिका (अपत्य पडताळणी)", "hi": "राशन कार्ड (संतान सत्यापन)"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-RATION-CARD")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="GOVERNMENT_RESOLUTION",
            source_reference="GR-HED-2018-06-02",
        ),
    ],

    # 7. Post-Matric OBC Scholarship
    "candidate-post-matric-obc": [
        RequirementSlot(
            slot_id="SLOT-OBC-INCOME",
            scheme_id="candidate-post-matric-obc",
            requirement_version="1.0.0",
            need_label={"en": "Income Certificate", "mr": "उत्पन्नाचा दाखला", "hi": "आय प्रमाण-पत्र"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-INCOME-CERT", constraints={"max_annual_income": 150000})],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://mahadbt.maharashtra.gov.in",
        ),
        RequirementSlot(
            slot_id="SLOT-OBC-DOMICILE",
            scheme_id="candidate-post-matric-obc",
            requirement_version="1.0.0",
            need_label={"en": "Domicile Certificate", "mr": "अधिवास दाखला", "hi": "अधिवास प्रमाण-पत्र"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-DOMICILE-CERT")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://mahadbt.maharashtra.gov.in",
        ),
        RequirementSlot(
            slot_id="SLOT-OBC-BANK",
            scheme_id="candidate-post-matric-obc",
            requirement_version="1.0.0",
            need_label={"en": "Bank Account", "mr": "बँक खाते", "hi": "बैंक खाता"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-BANK-PASSBOOK")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://mahadbt.maharashtra.gov.in",
        ),
    ],

    # 8. CMEGP Self-Employment
    "scheme-cmegp-self-employment": [
        RequirementSlot(
            slot_id="SLOT-CMEGP-IDENTITY",
            scheme_id="scheme-cmegp-self-employment",
            requirement_version="1.0.0",
            need_label={"en": "Aadhaar Card", "mr": "आधार कार्ड", "hi": "आधार कार्ड"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-AADHAAR-CARD")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://cmegp.gov.in",
        ),
        RequirementSlot(
            slot_id="SLOT-CMEGP-DOMICILE",
            scheme_id="scheme-cmegp-self-employment",
            requirement_version="1.0.0",
            need_label={"en": "Domicile Certificate", "mr": "अधिवास दाखला", "hi": "अधिवास प्रमाण-पत्र"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-DOMICILE-CERT")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://cmegp.gov.in",
        ),
        RequirementSlot(
            slot_id="SLOT-CMEGP-BANK",
            scheme_id="scheme-cmegp-self-employment",
            requirement_version="1.0.0",
            need_label={"en": "Bank Passbook", "mr": "बँक पासबुक", "hi": "बैंक पासबुक"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-BANK-PASSBOOK")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://cmegp.gov.in",
        ),
    ],

    # 9. Annasaheb Patil IR2 (Credit Subsidy)
    "scheme-annasaheb-patil-ir2": [
        RequirementSlot(
            slot_id="SLOT-AP-IDENTITY",
            scheme_id="scheme-annasaheb-patil-ir2",
            requirement_version="1.0.0",
            need_label={"en": "Aadhaar Card", "mr": "आधार कार्ड", "hi": "आधार कार्ड"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-AADHAAR-CARD")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://apamv.maharashtra.gov.in",
        ),
        RequirementSlot(
            slot_id="SLOT-AP-DOMICILE",
            scheme_id="scheme-annasaheb-patil-ir2",
            requirement_version="1.0.0",
            need_label={"en": "Domicile Certificate", "mr": "अधिवास दाखला", "hi": "अधिवास प्रमाण-पत्र"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-DOMICILE-CERT")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://apamv.maharashtra.gov.in",
        ),
        RequirementSlot(
            slot_id="SLOT-AP-INCOME",
            scheme_id="scheme-annasaheb-patil-ir2",
            requirement_version="1.0.0",
            need_label={"en": "Income Certificate", "mr": "उत्पन्नाचा दाखला", "hi": "आय प्रमाण-पत्र"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-INCOME-CERT", constraints={"max_annual_income": 800000})],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://apamv.maharashtra.gov.in",
        ),
    ],

    # 10. Ramai Awas Yojana (Rural Housing)
    "scheme-ramai-awas-yojana": [
        RequirementSlot(
            slot_id="SLOT-RAMAI-IDENTITY",
            scheme_id="scheme-ramai-awas-yojana",
            requirement_version="1.0.0",
            need_label={"en": "Identity Proof", "mr": "ओळख पुरावा", "hi": "पहचान प्रमाण"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-AADHAAR-CARD")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://sjsa.maharashtra.gov.in",
        ),
        RequirementSlot(
            slot_id="SLOT-RAMAI-DOMICILE",
            scheme_id="scheme-ramai-awas-yojana",
            requirement_version="1.0.0",
            need_label={"en": "Domicile / Residence Proof", "mr": "रहिवासी दाखला", "hi": "निवास प्रमाण"},
            kind=RequirementKind.MANDATORY,
            accepted=[
                AcceptedDocType("DOC-DOMICILE-CERT"),
                AcceptedDocType("DOC-RATION-CARD"),
            ],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://sjsa.maharashtra.gov.in",
        ),
        RequirementSlot(
            slot_id="SLOT-RAMAI-INCOME",
            scheme_id="scheme-ramai-awas-yojana",
            requirement_version="1.0.0",
            need_label={"en": "Income Proof", "mr": "उत्पन्न पुरावा", "hi": "आय प्रमाण"},
            kind=RequirementKind.MANDATORY,
            accepted=[
                AcceptedDocType("DOC-INCOME-CERT", constraints={"max_annual_income": 100000}),
                AcceptedDocType("DOC-RATION-CARD", constraints={"card_type": "YELLOW"}),
            ],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://sjsa.maharashtra.gov.in",
        ),
        RequirementSlot(
            slot_id="SLOT-RAMAI-BANK",
            scheme_id="scheme-ramai-awas-yojana",
            requirement_version="1.0.0",
            need_label={"en": "Bank Account", "mr": "बँक खाते", "hi": "बैंक खाता"},
            kind=RequirementKind.MANDATORY,
            accepted=[AcceptedDocType("DOC-BANK-PASSBOOK")],
            trust_tier=RequirementTrustTier.SOURCE_VERIFIED,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://sjsa.maharashtra.gov.in",
        ),
    ],
}


def get_scheme_slots(scheme_id: str) -> List[RequirementSlot]:
    """Retrieve requirement slots for a scheme, or return honest unconfirmed fallback (§4.4)."""
    if scheme_id in PILOT_SCHEME_SLOTS:
        return PILOT_SCHEME_SLOTS[scheme_id]

    # Non-pilot scheme: honest fallback per ADR 001 and Law L1 & L12
    return [
        RequirementSlot(
            slot_id=f"SLOT-UNCONFIRMED-{scheme_id}",
            scheme_id=scheme_id,
            requirement_version="1.0.0",
            need_label={
                "en": "Official Document Requirements Pending Verification",
                "mr": "अधिकृत कागदपत्रांची यादी पडताळणी प्रक्रियेत आहे",
                "hi": "आधिकारिक दस्तावेज़ सूची सत्यापन प्रक्रिया में है",
            },
            kind=RequirementKind.MANDATORY,
            accepted=[],
            trust_tier=RequirementTrustTier.UNKNOWN,
            source_type="OFFICIAL_PORTAL",
            source_reference="https://aaplesarkar.mahaonline.gov.in",
            source_quote="Official document list is being verified against Government Resolutions. Please consult the nearest Setu / Tahsil Kendra.",
        )
    ]


def evaluate_slots_for_citizen(
    scheme_id: str,
    citizen_profile: Optional[Dict[str, Any]] = None,
    uploaded_docs: Optional[List[Dict[str, Any]]] = None,
) -> NeedsSummary:
    """Evaluate slots for a citizen and compute honest denominator (§4.3).
    
    Formula:
    'N of M needs covered'
    M = applicable mandatory slots + conditional slots whose applicability is True.
    A slot satisfied by one of several alternatives counts once.
    """
    profile = citizen_profile or {}
    docs = uploaded_docs or []
    slots = get_scheme_slots(scheme_id)

    evaluations: List[SlotEvaluation] = []
    applicable_count = 0
    satisfied_count = 0
    unknown_conditional_count = 0
    unconfirmed_count = 0

    # Index uploaded docs by doctype_id
    uploaded_by_doctype: Dict[str, Dict[str, Any]] = {}
    for doc in docs:
        dt = doc.get("doctype_id")
        if dt:
            uploaded_by_doctype[dt] = doc

    for slot in slots:
        # Check if non-pilot unconfirmed slot
        if slot.trust_tier == RequirementTrustTier.UNKNOWN:
            unconfirmed_count += 1
            evaluations.append(
                SlotEvaluation(
                    slot=slot,
                    state=SlotState.REQUIREMENT_UNCONFIRMED,
                    is_applicable=None,
                    explanation_key="advisory.official_authority_reminder",
                )
            )
            continue

        # Check applicability
        is_applicable: Optional[bool] = True
        if slot.kind == RequirementKind.CONDITIONAL:
            if not slot.applicability_condition:
                is_applicable = None
            else:
                # Simple condition check e.g. {"is_divyang": True}
                is_met = True
                has_unknown = False
                for k, expected_v in slot.applicability_condition.items():
                    if k not in profile:
                        has_unknown = True
                        break
                    if profile[k] != expected_v:
                        is_met = False
                        break
                
                if has_unknown:
                    is_applicable = None
                else:
                    is_applicable = is_met

        if is_applicable is None:
            unknown_conditional_count += 1
            evaluations.append(
                SlotEvaluation(
                    slot=slot,
                    state=SlotState.NOT_STARTED,
                    is_applicable=None,
                )
            )
            continue

        if is_applicable is False:
            evaluations.append(
                SlotEvaluation(
                    slot=slot,
                    state=SlotState.NOT_APPLICABLE,
                    is_applicable=False,
                )
            )
            continue

        # Slot is applicable -> increments denominator M
        applicable_count += 1

        # Check alternatives: does any uploaded doc satisfy one of the accepted doctypes?
        satisfied_doc = None
        satisfied_dt = None
        for accepted in slot.accepted:
            if accepted.doctype_id in uploaded_by_doctype:
                satisfied_doc = uploaded_by_doctype[accepted.doctype_id]
                satisfied_dt = accepted.doctype_id
                break

        if satisfied_doc:
            satisfied_count += 1
            evaluations.append(
                SlotEvaluation(
                    slot=slot,
                    state=SlotState.SATISFIED,
                    is_applicable=True,
                    satisfied_by_doc_id=satisfied_doc.get("doc_id"),
                    satisfied_by_doctype_id=satisfied_dt,
                    explanation_key="ladder.received",
                )
            )
        else:
            evaluations.append(
                SlotEvaluation(
                    slot=slot,
                    state=SlotState.NOT_STARTED,
                    is_applicable=True,
                )
            )

    pending_count = applicable_count - satisfied_count
    return NeedsSummary(
        total_applicable_needs_m=applicable_count,
        satisfied_needs_n=satisfied_count,
        pending_needs_count=pending_count,
        unknown_conditional_count=unknown_conditional_count,
        unconfirmed_requirements_count=unconfirmed_count,
        evaluations=evaluations,
    )
