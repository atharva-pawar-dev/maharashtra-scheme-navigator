from __future__ import annotations

import json
import re
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from scheme_navigator.documents.audit import (
    add_pdf_page_conflict_findings,
    audit_extracted_documents,
    compare_person_names,
)
from scheme_navigator.domain.models import (
    CitizenProfile,
    DocumentAuditResponse,
    DocumentFinding,
    ExtractedDocument,
    Language,
    Scheme,
)
from scheme_navigator.planner.dag import canonical_document


class DocumentMatchStatus(StrEnum):
    # Requirement-level State Machine (statutory & lifecycle states)
    NOT_PROVIDED = "NOT_PROVIDED"
    UPLOADED = "UPLOADED"
    EXTRACTION_PENDING = "EXTRACTION_PENDING"
    EXTRACTION_COMPLETE = "EXTRACTION_COMPLETE"
    NEEDS_USER_CONFIRMATION = "NEEDS_USER_CONFIRMATION"
    POSSIBLE_MATCH = "POSSIBLE_MATCH"
    MATCHED_FOR_PREPARATION = "MATCHED_FOR_PREPARATION"
    EXPIRED_OR_STALE = "EXPIRED_OR_STALE"
    UNREADABLE = "UNREADABLE"
    INCONSISTENT_INFORMATION = "INCONSISTENT_INFORMATION"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    REPLACEMENT_REQUIRED = "REPLACEMENT_REQUIRED"
    NOT_REQUIRED = "NOT_REQUIRED"

    # Backward-compatible legacy aliases (lowercase)
    MATCHED = "matched"
    ALTERNATIVE_MATCHED = "alternative_matched"
    EXPIRED = "expired"
    FY_MISMATCH = "fy_mismatch"
    MISSING = "missing"
    CONFLICTING = "conflicting"


# Alias for requirement-level lifecycle state machine
RequirementItemStatus = DocumentMatchStatus


class DocumentRequirementStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    requirement_id: str
    document_name: str
    is_mandatory: bool
    match_status: DocumentMatchStatus
    state: DocumentMatchStatus = DocumentMatchStatus.NOT_PROVIDED
    requirement_type: str = "MANDATORY"
    condition_description: str | None = None
    matched_document_id: str | None = None
    matched_document_type: str | None = None
    permitted_alternatives: list[str] = Field(default_factory=list)
    alternative_used: str | None = None
    issuing_authority: str
    rts_notified_days: int | None = None
    validity_conditions: str | None = None
    source_reference: str | None = None
    verification_status: str = "VERIFIED"
    explanation: str
    action_needed: str


class IntelligentDocumentPreparationReport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scheme_id: str
    all_mandatory_satisfied: bool
    requirements: list[DocumentRequirementStatus] = Field(default_factory=list)
    conflicts_detected: list[DocumentFinding] = Field(default_factory=list)
    duplicates_detected: list[str] = Field(default_factory=list)
    needs_human_audit: bool
    audit_summary: str
    readiness_percentage: int = 0
    mandatory_total: int = 0
    mandatory_satisfied: int = 0
    readiness_status: str = "MISSING"
    disclaimer: str = "Pre-check of readability, completeness, and consistency; the official department verifies authenticity upon application."


# Authoritative Maharashtra permitted alternative documents registry
OFFICIAL_ALTERNATIVE_DOCUMENTS: dict[str, list[dict[str, Any]]] = {
    "domicile certificate": [
        {
            "name": "15-year Ration Card",
            "type_alias": "ration_card",
            "statutory_basis": "Maharashtra GR No. Sankirna-2024/CR137/Karya-02 Para 2.2",
            "description": "Ration card issued at least 15 years prior in Maharashtra",
        },
        {
            "name": "Voter ID Card",
            "type_alias": "voter_id",
            "statutory_basis": "Maharashtra GR 3 July 2024 Amendment",
            "description": "Voter identity card with Maharashtra address",
        },
        {
            "name": "Birth Certificate (Maharashtra)",
            "type_alias": "birth_certificate",
            "statutory_basis": "Maharashtra GR 3 July 2024 Amendment",
            "description": "Birth certificate showing birthplace in Maharashtra",
        },
        {
            "name": "School Leaving Certificate",
            "type_alias": "school_leaving_certificate",
            "statutory_basis": "Maharashtra GR 3 July 2024 Amendment",
            "description": "School leaving certificate showing Maharashtra birthplace",
        },
    ],
    "income certificate": [
        {
            "name": "Yellow or Orange Ration Card",
            "type_alias": "ration_card",
            "statutory_basis": "Maharashtra GR No. Sankirna-2024/CR137/Karya-02 Para 2.2",
            "description": "Valid Yellow or Orange Ration Card (exempts separate income certificate for Majhi Ladki Bahin)",
        },
        {
            "name": "BPL Card / Certificate",
            "type_alias": "bpl_card",
            "statutory_basis": "Sanjay Gandhi Niradhar GR 20 August 2019",
            "description": "Family included in official BPL census survey list",
        },
    ],
    "caste certificate": [
        {
            "name": "Caste Validity Certificate",
            "type_alias": "caste_validity",
            "statutory_basis": "Maharashtra Act XXIII of 2001",
            "description": "Scrutiny committee validity certificate (mandatory for professional degree admissions/scholarships)",
        }
    ],
}

ISSUING_AUTHORITY_MAP: dict[str, tuple[str, int | None]] = {
    "domicile certificate": ("Tehsildar / Sub-Divisional Officer (SDO) via Aaple Sarkar", 15),
    "age nationality domicile certificate": ("Tehsildar / SDO via Aaple Sarkar", 15),
    "income certificate": ("Tehsildar / Nayab Tehsildar via Aaple Sarkar", 15),
    "caste certificate": ("Sub-Divisional Officer / Deputy Collector via Aaple Sarkar", 21),
    "non creamy layer certificate": ("Sub-Divisional Officer via Aaple Sarkar", 21),
    "7/12 extract": ("Talathi / Revenue Department (Mahabhulekh)", 7),
    "identity proof": ("Unique Identification Authority of India (UIDAI)", None),
    "aadhaar card": ("UIDAI", None),
    "bank account details": ("Scheduled Commercial Bank / Post Office", None),
    "disability certificate": ("District Civil Surgeon / UDID Portal (Department of EPwD)", 30),
    "affirmation letter": ("Applicant Self-Declaration / Hamipatra", None),
}

DOC_NAMES_TRILINGUAL: dict[str, dict[str, str]] = {
    "income certificate": {
        "en": "Income Certificate",
        "mr": "उत्पन्नाचा दाखला",
        "hi": "आय प्रमाण-पत्र",
    },
    "domicile certificate": {
        "en": "Domicile Certificate",
        "mr": "अधिवास दाखला (रहिवासी दाखला)",
        "hi": "अधिवास प्रमाण-पत्र",
    },
    "age nationality domicile certificate": {
        "en": "Age, Nationality & Domicile Certificate",
        "mr": "वय, अधिवास व राष्ट्रीयत्व दाखला",
        "hi": "आयु, अधिवास एवं राष्ट्रीयता प्रमाण-पत्र",
    },
    "caste certificate": {
        "en": "Caste Certificate",
        "mr": "जात प्रमाणपत्र",
        "hi": "जाति प्रमाण-पत्र",
    },
    "caste validity certificate": {
        "en": "Caste Validity Certificate",
        "mr": "जात वैधता प्रमाणपत्र",
        "hi": "जाति वैधता प्रमाण-पत्र",
    },
    "non creamy layer certificate": {
        "en": "Non-Creamy Layer Certificate",
        "mr": "नॉन-क्रिमीलेअर प्रमाणपत्र",
        "hi": "गैर-क्रीमी लेयर प्रमाण-पत्र",
    },
    "7/12 extract": {
        "en": "7/12 Land Extract",
        "mr": "७/१२ जमीन उतारा",
        "hi": "7/12 भूमि खतौनी",
    },
    "aadhaar card": {
        "en": "Aadhaar Card",
        "mr": "आधार कार्ड",
        "hi": "आधार कार्ड",
    },
    "identity proof": {
        "en": "Identity Proof",
        "mr": "ओळख पुरावा",
        "hi": "पहचान प्रमाण",
    },
    "bank passbook": {
        "en": "Bank Passbook",
        "mr": "बँक पासबुक",
        "hi": "बैंक पासबुक",
    },
    "bank account details": {
        "en": "Bank Passbook / Statement",
        "mr": "बँक पासबुक / बँक विवरण",
        "hi": "बैंक पासबुक / विवरण",
    },
    "ration card": {
        "en": "Ration Card",
        "mr": "शिधापत्रिका",
        "hi": "राशन कार्ड",
    },
    "disability certificate": {
        "en": "Disability Certificate",
        "mr": "दिव्यांगत्व प्रमाणपत्र",
        "hi": "दिव्यांगता प्रमाण-पत्र",
    },
    "affirmation letter": {
        "en": "Self-Declaration Letter",
        "mr": "स्वयंघोषणापत्र (हमीपत्र)",
        "hi": "स्व-घोषणा पत्र (हमीपत्र)",
    },
    "death certificate of husband": {
        "en": "Death Certificate of Husband",
        "mr": "पतीचा मृत्यू दाखला",
        "hi": "पति का मृत्यु प्रमाण-पत्र",
    },
    "previous year marksheet": {
        "en": "Previous Year Marksheet",
        "mr": "मागील वर्षाचे गुणपत्रक",
        "hi": "पिछले वर्ष की अंकतालिका",
    },
    "hostel certificate": {
        "en": "Hostel Certificate",
        "mr": "वसतिगृह प्रमाणपत्र",
        "hi": "छात्रावास प्रमाण-पत्र",
    },
    "fee receipt": {
        "en": "College Fee Receipt",
        "mr": "महाविद्यालयीन शुल्क पावती",
        "hi": "कॉलेज शुल्क रसीद",
    },
}

AUTHORITIES_TRILINGUAL: dict[str, dict[str, str]] = {
    "tehsildar / sub-divisional officer (sdo) via aaple sarkar": {
        "en": "Tehsildar / Sub-Divisional Officer (SDO) via Aaple Sarkar",
        "mr": "तहसीलदार / उपविभागीय अधिकारी (आपले सरकार मार्फत)",
        "hi": "तहसीलदार / एसडीओ (आपले सरकार द्वारा)",
    },
    "tehsildar / sdo via aaple sarkar": {
        "en": "Tehsildar / SDO via Aaple Sarkar",
        "mr": "तहसीलदार / उपविभागीय अधिकारी (आपले सरकार मार्फत)",
        "hi": "तहसीलदार / एसडीओ (आपले सरकार द्वारा)",
    },
    "tehsildar / nayab tehsildar via aaple sarkar": {
        "en": "Tehsildar / Nayab Tehsildar via Aaple Sarkar",
        "mr": "तहसीलदार / नायब तहसीलदार (आपले सरकार मार्फत)",
        "hi": "तहसीलदार / नायब तहसीलदार (आपले सरकार द्वारा)",
    },
    "sub-divisional officer / deputy collector via aaple sarkar": {
        "en": "Sub-Divisional Officer / Deputy Collector via Aaple Sarkar",
        "mr": "उपविभागीय अधिकारी / उपजिल्हाधिकारी (आपले सरकार मार्फत)",
        "hi": "अनुविभागीय अधिकारी / उपजिलाधिकारी (आपले सरकार द्वारा)",
    },
    "sub-divisional officer via aaple sarkar": {
        "en": "Sub-Divisional Officer via Aaple Sarkar",
        "mr": "उपविभागीय अधिकारी (आपले सरकार मार्फत)",
        "hi": "अनुविभागीय अधिकारी (आपले सरकार द्वारा)",
    },
    "talathi / revenue department (mahabhulekh)": {
        "en": "Talathi / Revenue Department (Mahabhulekh)",
        "mr": "तलाठी / महसूल विभाग (महाभूलेख)",
        "hi": "तलाठी / राजस्व विभाग (महाभूलेख)",
    },
    "unique identification authority of india (uidai)": {
        "en": "UIDAI",
        "mr": "युआयडीएआय (UIDAI)",
        "hi": "यूआईडीएआई (UIDAI)",
    },
    "uidai": {
        "en": "UIDAI",
        "mr": "युआयडीएआय (UIDAI)",
        "hi": "यूआईडीएआई (UIDAI)",
    },
    "scheduled commercial bank / post office": {
        "en": "Scheduled Commercial Bank / Post Office",
        "mr": "अनुसूचित बँक / पोस्ट ऑफिस",
        "hi": "अनुसूचित बैंक / डाकघर",
    },
    "district civil surgeon / udid portal (department of epwd)": {
        "en": "District Civil Surgeon / UDID Portal",
        "mr": "जिल्हा शल्यचिकित्सक / युडीआयडी पोर्टल",
        "hi": "जिला सिविल सर्जन / यूडीआईडी पोर्टल",
    },
    "applicant self-declaration / hamipatra": {
        "en": "Applicant Self-Declaration (Hamipatra)",
        "mr": "अर्जदाराचे स्वयंघोषणापत्र (हमीपत्र)",
        "hi": "आवेदक का स्व-घोषणा पत्र (हमीपत्र)",
    },
    "competent issuing authority": {
        "en": "Competent Issuing Authority",
        "mr": "सक्षम शासकीय प्राधिकारी",
        "hi": "सक्षम सरकारी प्राधिकारी",
    },
}

DOC_KEYWORD_PATTERNS: list[tuple[str, dict[str, str]]] = [
    (r'(?i)7/12.*8-?a|8-?a.*7/12', {'en': '7/12 & 8-A Land Extract', 'mr': '७/१२ आणि ८-अ जमीन उतारा', 'hi': '7/12 एवं 8-अ भूमि खतौनी'}),
    (r'(?i)7/12|seven twelve|सातबारा|जमीन उतारा', {'en': '7/12 Land Extract', 'mr': '७/१२ जमीन उतारा', 'hi': '7/12 भूमि खतौनी'}),
    (r'(?i)8-?a|holding extract', {'en': '8-A Holding Extract', 'mr': '८-अ जमीन धारणा उतारा', 'hi': '8-अ भूमि जोत खतौनी'}),
    (r'(?i)caste validity|जात वैधता', {'en': 'Caste Validity Certificate', 'mr': 'जात वैधता प्रमाणपत्र', 'hi': 'जाति वैधता प्रमाण-पत्र'}),
    (r'(?i)non-?creamy|ncl|नॉन-क्रिमी', {'en': 'Non-Creamy Layer Certificate', 'mr': 'नॉन-क्रिमीलेअर प्रमाणपत्र', 'hi': 'गैर-क्रीमी लेयर प्रमाण-पत्र'}),
    (r'(?i)caste|tribe|जात|जाति', {'en': 'Caste Certificate', 'mr': 'जात प्रमाणपत्र', 'hi': 'जाति प्रमाण-पत्र'}),
    (r'(?i)income|उत्पन्न|आय प्रमाण|proof.*2\.5l', {'en': 'Income Certificate', 'mr': 'उत्पन्नाचा दाखला', 'hi': 'आय प्रमाण-पत्र'}),
    (r'(?i)domicile|residence|resident|अधिवास|रहिवासी', {'en': 'Domicile Certificate', 'mr': 'अधिवास दाखला (रहिवासी दाखला)', 'hi': 'अधिवास प्रमाण-पत्र'}),
    (r'(?i)aadhaar.*slip|enrolment.*eid', {'en': 'Aadhaar Enrolment Slip (EID)', 'mr': 'आधार नोंदणी पावती (EID)', 'hi': 'आधार नामांकन पर्ची (ईआईडी)'}),
    (r'(?i)aadhaar|आधार', {'en': 'Aadhaar Card', 'mr': 'आधार कार्ड', 'hi': 'आधार कार्ड'}),
    (r'(?i)cancelled cheque|cheque', {'en': 'Cancelled Cheque', 'mr': 'रद्द केलेला धनादेश (Cancelled Cheque)', 'hi': 'रद्द चेक (Cancelled Cheque)'}),
    (r'(?i)bank statement', {'en': 'Bank Account Statement (Bank Stamped)', 'mr': 'बँक खाते विवरण (बँकेचा शिक्का असलेले)', 'hi': 'बैंक खाता विवरण (बैंक मुहर सहित)'}),
    (r'(?i)bank|passbook|पासबुक', {'en': 'Bank Account Passbook', 'mr': 'बँक खाते पासबुक', 'hi': 'बैंक खाता पासबुक'}),
    (r'(?i)15-?year ration', {'en': '15-year Ration Card', 'mr': '१५ वर्षांपूर्वीची जुनी शिधापत्रिका', 'hi': '15 वर्ष पुराना राशन कार्ड'}),
    (r'(?i)yellow.*ration|orange.*ration|antyodaya', {'en': 'Yellow or Orange Ration Card', 'mr': 'पिवळे किंवा केशरी रेशन कार्ड', 'hi': 'पीला या नारंगी राशन कार्ड'}),
    (r'(?i)ration|शिधापत्रिका|रेशन|राशन', {'en': 'Ration Card', 'mr': 'शिधापत्रिका', 'hi': 'राशन कार्ड'}),
    (r'(?i)disability|udid|divyang|दिव्यांग', {'en': 'Disability Certificate / UDID', 'mr': 'दिव्यांगत्व प्रमाणपत्र / युडीआयडी (UDID)', 'hi': 'दिव्यांगता प्रमाण-पत्र / यूडीआईडी (UDID)'}),
    (r'(?i)10th marksheet|ssc', {'en': '10th Marksheet (SSC)', 'mr': '१० वी गुणपत्रिका (SSC)', 'hi': '10वीं अंकतालिका (SSC)'}),
    (r'(?i)12th marksheet|hsc', {'en': '12th Marksheet (HSC)', 'mr': '१२ वी गुणपत्रिका (HSC)', 'hi': '12वीं अंकतालिका (HSC)'}),
    (r'(?i)marksheet|गुणपत्रिका|अंकतालिका', {'en': 'Marksheet', 'mr': 'गुणपत्रिका', 'hi': 'अंकतालिका'}),
    (r'(?i)bonafide|बोनाफाईड', {'en': 'School / College Bonafide Certificate', 'mr': 'शाळा / महाविद्यालय बोनाफाईड प्रमाणपत्र', 'hi': 'स्कूल / कॉलेज बोनाफाइड प्रमाण-पत्र'}),
    (r'(?i)birth certificate|जन्म दाखला', {'en': 'Birth Certificate', 'mr': 'जन्म दाखला', 'hi': 'जन्म प्रमाण-पत्र'}),
    (r'(?i)husband death|पतीचा मृत्यू', {'en': 'Death Certificate of Husband', 'mr': 'पतीचा मृत्यू दाखला', 'hi': 'पति का मृत्यु प्रमाण-पत्र'}),
    (r'(?i)death certificate|मृत्यू दाखला', {'en': 'Death Certificate', 'mr': 'मृत्यू दाखला', 'hi': 'मृत्यु प्रमाण-पत्र'}),
    (r'(?i)marriage|विवाह', {'en': 'Marriage Registration Certificate', 'mr': 'विवाह नोंदणी प्रमाणपत्र', 'hi': 'विवाह पंजीकरण प्रमाण-पत्र'}),
    (r'(?i)school leaving|tc|lc|शाळा सोडल्याचा', {'en': 'School Leaving Certificate (TC)', 'mr': 'शाळा सोडल्याचा दाखला (TC)', 'hi': 'स्कूल लीविंग सर्टिफिकेट (टीसी)'}),
    (r'(?i)fee receipt|शुल्क पावती', {'en': 'College Fee Receipt', 'mr': 'महाविद्यालयीन शुल्क पावती', 'hi': 'कॉलेज शुल्क रसीद'}),
    (r'(?i)hostel|वसतिगृह', {'en': 'Hostel Certificate', 'mr': 'वसतिगृह प्रमाणपत्र', 'hi': 'छात्रावास प्रमाण-पत्र'}),
    (r'(?i)voter|मतदार ओळखपत्र', {'en': 'Voter ID Card', 'mr': 'मतदार ओळखपत्र', 'hi': 'मतदाता पहचान पत्र'}),
    (r'(?i)bpl|दारिद्र्य', {'en': 'BPL Certificate / Survey List', 'mr': 'दारिद्र्यरेषेखालील (BPL) दाखला / सर्वेक्षण यादी', 'hi': 'बीपीएल प्रमाण-पत्र / सर्वेक्षण सूची'}),
    (r'(?i)self-?declaration|hamipatra|affidavit|हमीपत्र|स्वयंघोषणा', {'en': 'Self-Declaration / Hamipatra', 'mr': 'स्वयंघोषणापत्र (हमीपत्र)', 'hi': 'स्व-घोषणा पत्र (हमीपत्र)'}),
    (r'(?i)age proof|वयाचा पुरावा', {'en': 'Age Proof', 'mr': 'वयाचा पुरावा', 'hi': 'आयु प्रमाण'}),
    (r'(?i)photo|छायाचित्र', {'en': 'Passport Size Photograph', 'mr': 'पासपोर्ट आकाराचे छायाचित्र', 'hi': 'पासपोर्ट आकार फोटो'}),
    (r'(?i)business.*plan|project.*report|quotation', {'en': 'Business Project Proposal / Quotation', 'mr': 'व्यवसाय प्रकल्प प्रस्ताव व कोटेशन', 'hi': 'व्यवसाय परियोजना प्रस्ताव व कोटेशन'}),
    (r'(?i)ph\.?d|research.*synopsis', {'en': 'Ph.D. Registration / Research Synopsis', 'mr': 'पीएच.डी. नोंदणी / संशोधन रूपरेषा', 'hi': 'पीएचडी पंजीकरण / शोध रूपरेखा'}),
    (r'(?i)electricity|bill|वीज बिल', {'en': 'Electricity Bill / Consumer No.', 'mr': 'वीज बिल / ग्राहक क्रमांक', 'hi': 'बिजली बिल / उपभोक्ता संख्या'}),
    (r'(?i)job card|mgnregs|रोजगार हमी', {'en': 'MGNREGS Job Card', 'mr': 'मनरेगा रोजगार हमी जॉब कार्ड', 'hi': 'मनरेगा जॉब कार्ड'}),
    (r'(?i)identity|ओळख पुरावा', {'en': 'Identity Proof', 'mr': 'ओळख पुरावा', 'hi': 'पहचान प्रमाण'}),
    (r'(?i)address|पत्त्याचा पुरावा', {'en': 'Address Proof', 'mr': 'पत्त्याचा पुरावा', 'hi': 'पते का प्रमाण'}),
    (r'(?i)form 16|itr', {'en': 'Form 16 / ITR Acknowledgment', 'mr': 'फॉर्म १६ / आयकर विवरण पावती', 'hi': 'फॉर्म 16 / आईटीआर पावती'}),
]

AUTHORITIES_PATTERNS: list[tuple[str, dict[str, str]]] = [
    (r'(?i)uidai|unique identification authority', {
        'en': 'Unique Identification Authority of India (UIDAI)',
        'mr': 'भारतीय विशिष्ट ओळख प्राधिकरण (UIDAI)',
        'hi': 'भारतीय विशिष्ट पहचान प्राधिकरण (UIDAI)',
    }),
    (r'(?i)sub-?divisional officer.*deputy collector', {
        'en': 'Sub-Divisional Officer (SDO) / Deputy Collector via Aaple Sarkar',
        'mr': 'उपविभागीय अधिकारी (SDO) / उपजिल्हाधिकारी (आपले सरकार मार्फत)',
        'hi': 'उपविभागीय अधिकारी (एसडीओ) / उपजिलाधिकारी (आपले सरकार द्वारा)',
    }),
    (r'(?i)sub-?divisional officer.*tahsildar|sdo.*tahsildar', {
        'en': 'Sub-Divisional Officer (SDO) / Tahsildar via Aaple Sarkar',
        'mr': 'उपविभागीय अधिकारी (SDO) / तहसीलदार (आपले सरकार मार्फत)',
        'hi': 'उपविभागीय अधिकारी (एसडीओ) / तहसीलदार (आपले सरकार द्वारा)',
    }),
    (r'(?i)tahsildar.*nayab.*revenue|tehsildar.*revenue|tahsildar.*aaple|tehsildar.*aaple', {
        'en': 'Tahsildar / Nayab Tahsildar (Revenue Department) via Aaple Sarkar',
        'mr': 'तहसीलदार / नायब तहसीलदार (महसूल विभाग, आपले सरकार मार्फत)',
        'hi': 'तहसीलदार / नायब तहसीलदार (राजस्व विभाग, आपले सरकार द्वारा)',
    }),
    (r'(?i)talathi.*mahabhulekh|talathi.*revenue|mahabhumi', {
        'en': 'Talathi / Revenue Department (Mahabhulekh / Mahabhumi Portal)',
        'mr': 'तलाठी / महसूल विभाग (महाभूलेख / महाभूमी पोर्टल)',
        'hi': 'तलाठी / राजस्व विभाग (महाभूलेख / महाभूमि पोर्टल)',
    }),
    (r'(?i)district supply officer|food.*civil supplies', {
        'en': 'District Supply Officer / Tahsildar (Food, Civil Supplies & Consumer Protection Dept)',
        'mr': 'जिल्हा पुरवठा अधिकारी / तहसीलदार (अन्न, नागरी पुरवठा व ग्राहक संरक्षण विभाग)',
        'hi': 'जिला आपूर्ति अधिकारी / तहसीलदार (खाद्य, नागरिक आपूर्ति एवं उपभोक्ता संरक्षण विभाग)',
    }),
    (r'(?i)scheduled commercial bank|post office|payments bank|bank', {
        'en': 'Scheduled Commercial Bank / Regional Rural Bank / India Post Payments Bank',
        'mr': 'अनुसूचित व्यावसायिक बँक / प्रादेशिक ग्रामीण बँक / इंडिया पोस्ट पेमेंट्स बँक',
        'hi': 'अनुसूचित वाणिज्यिक बैंक / क्षेत्रीय ग्रामीण बैंक / इंडिया पोस्ट पेमेंट्स बैंक',
    }),
    (r'(?i)civil surgeon.*swavlamban|civil surgeon.*udid|medical board', {
        'en': 'District Civil Surgeon / Medical Board via Swavlamban UDID Portal',
        'mr': 'जिल्हा शल्यचिकित्सक / वैद्यकीय मंडळ (स्वावलंबन युडीआयडी पोर्टल मार्फत)',
        'hi': 'जिला सिविल सर्जन / चिकित्सा बोर्ड (स्वावलंबन यूडीआईडी पोर्टल द्वारा)',
    }),
    (r'(?i)school.*college.*university|examination board', {
        'en': 'Recognized School / College / University / State Examination Board',
        'mr': 'मान्यताप्राप्त शाळा / महाविद्यालय / विद्यापीठ / राज्य परीक्षा मंडळ',
        'hi': 'मान्यता प्राप्त विद्यालय / महाविद्यालय / विश्वविद्यालय / राज्य परीक्षा बोर्ड',
    }),
    (r'(?i)gram panchayat.*municipal corp|civil surgeon', {
        'en': 'Competent Authority (Gram Panchayat / Municipal Corp / Civil Surgeon)',
        'mr': 'सक्षम प्राधिकारी (ग्रामपंचायत / महानगरपालिका / जिल्हा शल्यचिकित्सक)',
        'hi': 'सक्षम प्राधिकारी (ग्राम पंचायत / नगर निगम / सिविल सर्जन)',
    }),
    (r'(?i)relevant administrative|departmental officer', {
        'en': 'Relevant Administrative Authority / Departmental Officer',
        'mr': 'संबंधित प्रशासकीय प्राधिकारी / विभागीय अधिकारी',
        'hi': 'संबंधित प्रशासनिक प्राधिकारी / विभागीय अधिकारी',
    }),
    (r'(?i)competent issuing authority|competent authority', {
        'en': 'Competent Issuing Authority',
        'mr': 'सक्षम शासकीय प्राधिकारी',
        'hi': 'सक्षम सरकारी प्राधिकारी',
    }),
]

def get_localized_doc_name(name: str | None, lang: str = "en") -> str:
    if not name:
        return ""
    if lang == "en":
        return name
    canon = canonical_document(name)
    entry = DOC_NAMES_TRILINGUAL.get(canon)
    if entry and entry.get(lang):
        return entry[lang]
    for k, v in DOC_NAMES_TRILINGUAL.items():
        if (k in canon or canon in k) and v.get(lang):
            return v[lang]
    for pat, trans in DOC_KEYWORD_PATTERNS:
        if re.search(pat, name):
            return trans.get(lang, name)
    if lang == "mr":
        return name.replace("Certificate", "प्रमाणपत्र").replace("certificate", "प्रमाणपत्र")
    elif lang == "hi":
        return name.replace("Certificate", "प्रमाण-पत्र").replace("certificate", "प्रमाण-पत्र")
    return name

def get_localized_authority(auth: str | None, lang: str = "en") -> str:
    if not auth:
        auth = "Competent Issuing Authority"
    if lang == "en":
        return auth
    key = auth.strip().lower()
    entry = AUTHORITIES_TRILINGUAL.get(key)
    if entry and entry.get(lang):
        return entry[lang]
    for pat, trans in AUTHORITIES_PATTERNS:
        if re.search(pat, auth):
            return trans.get(lang, auth)
    for k, v in AUTHORITIES_TRILINGUAL.items():
        if (k in key or key in k) and v.get(lang):
            return v[lang]
    return "सक्षम शासकीय प्राधिकारी" if lang == "mr" else "सक्षम सरकारी प्राधिकारी"

from scheme_navigator.source_registry.registry import CANONICAL_SCHEME_ALIAS_MAP

_SCHEME_REQ_CACHE: dict[str, dict[str, Any]] | None = None


def get_all_scheme_document_requirements() -> dict[str, dict[str, Any]]:
    global _SCHEME_REQ_CACHE
    if _SCHEME_REQ_CACHE is not None:
        return _SCHEME_REQ_CACHE

    reg_path = Path(__file__).resolve().parents[3] / "data" / "source_registry" / "scheme_document_requirements.json"
    if reg_path.exists():
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            _SCHEME_REQ_CACHE = {item["scheme_id"]: item for item in data if "scheme_id" in item}
            return _SCHEME_REQ_CACHE
        except Exception:
            pass
    return {}


def get_scheme_document_requirements(scheme_id: str) -> dict[str, Any] | None:
    all_reqs = get_all_scheme_document_requirements()
    if scheme_id in all_reqs:
        return all_reqs[scheme_id]
    alias_target = CANONICAL_SCHEME_ALIAS_MAP.get(scheme_id.upper())
    if alias_target and alias_target in all_reqs:
        return all_reqs[alias_target]
    return None


def _match_document_type(
    req_canon: str,
    doc: ExtractedDocument,
) -> tuple[bool, bool, str | None]:
    """Check if an extracted document matches a requirement directly or as an approved alternative."""
    d_type = (doc.document_type or "").casefold()

    # Direct mapping checks
    direct_types = {
        "income certificate": {"income_certificate"},
        "domicile certificate": {"domicile_certificate"},
        "age nationality domicile certificate": {"domicile_certificate"},
        "caste certificate": {"caste_certificate"},
        "non creamy layer certificate": {"caste_certificate"},
        "7/12 extract": {"seven_twelve_extract"},
        "identity proof": {"aadhaar_card"},
        "aadhaar card": {"aadhaar_card"},
        "bank passbook": {"bank_passbook", "other"},
        "bank account details": {"bank_passbook", "other"},
        "ration card": {"ration_card", "other"},
    }

    if d_type in direct_types.get(req_canon, set()):
        return True, False, None

    # Check evidence / title / notes for direct match
    text_haystack = " ".join([
        doc.field_evidence.get("document_title", ""),
        doc.field_evidence.get("title", ""),
        doc.field_evidence.get("doc_type", ""),
        doc.document_id,
        *doc.extraction_notes,
    ]).casefold()

    if req_canon in text_haystack or req_canon.replace(" ", "_") in text_haystack:
        return True, False, None

    # Robust semantic and keyword matching
    r_lower = req_canon.casefold()
    if ("income" in r_lower) and (d_type == "income_certificate" or "income" in text_haystack):
        return True, False, None
    if ("domicile" in r_lower or "residence" in r_lower) and (d_type == "domicile_certificate" or "domicile" in text_haystack):
        return True, False, None
    if ("aadhaar" in r_lower or "identity" in r_lower) and (d_type == "aadhaar_card" or "aadhaar" in text_haystack):
        return True, False, None
    if ("bank" in r_lower or "passbook" in r_lower) and (d_type in ("bank_passbook", "bank_account_details", "other") or "bank" in text_haystack or "passbook" in text_haystack):
        return True, False, None
    if ("caste" in r_lower or "creamy" in r_lower) and (d_type == "caste_certificate" or "caste" in text_haystack):
        return True, False, None
    if ("7/12" in r_lower or "seven twelve" in r_lower or "land" in r_lower) and (d_type == "seven_twelve_extract" or "7/12" in text_haystack):
        return True, False, None
    if ("ration" in r_lower) and (d_type in ("ration_card", "other") or "ration" in text_haystack):
        return True, False, None

    # Alternative checks
    alternatives = OFFICIAL_ALTERNATIVE_DOCUMENTS.get(req_canon, [])
    if not alternatives:
        if "domicile" in r_lower or "residence" in r_lower:
            alternatives = OFFICIAL_ALTERNATIVE_DOCUMENTS.get("domicile certificate", [])
        elif "income" in r_lower:
            alternatives = OFFICIAL_ALTERNATIVE_DOCUMENTS.get("income certificate", [])

    for alt in alternatives:
        if alt["name"].casefold() in text_haystack or alt["type_alias"] in text_haystack:
            return True, True, alt["name"]

    return False, False, None


def prepare_intelligent_document_audit(
    scheme: Scheme,
    extracted_documents: list[ExtractedDocument],
    profile: CitizenProfile | None = None,
    target_financial_year: str = "2026-27",
    language: Language = Language.EN,
    today: date | None = None,
    scheme_id: str | None = None,
) -> IntelligentDocumentPreparationReport:
    """Consolidate document classification, requirement matching, alternatives,

    expiry, and conflict detection into one actionable citizen report.
    """
    now = today or date.today()
    lang_code = language.value if isinstance(language, Language) else str(language).lower()

    # 1. Base audit
    findings: list[DocumentFinding] = []
    if extracted_documents:
        base_audit = audit_extracted_documents(
            extracted_documents,
            target_financial_year=target_financial_year,
            today=now,
        )
        findings.extend(base_audit.findings)

    duplicates: list[str] = []
    needs_human = False

    # 2. Duplicate document detection
    seen_hashes: dict[str, str] = {}
    for doc in extracted_documents:
        if doc.source_file_sha256:
            if doc.source_file_sha256 in seen_hashes:
                dup_msg = f"Duplicate document detected: file '{doc.document_id}' shares byte hash with '{seen_hashes[doc.source_file_sha256]}'."
                duplicates.append(dup_msg)
                findings.append(
                    DocumentFinding(
                        code="DUPLICATE_DOCUMENT_UPLOAD",
                        severity="warning",
                        message=dup_msg,
                        document_ids=[doc.document_id, seen_hashes[doc.source_file_sha256]],
                    )
                )
            else:
                seen_hashes[doc.source_file_sha256] = doc.document_id

        if doc.confidence < 0.75:
            needs_human = True

    # 2.5 Profile vs Document consistency and scheme threshold checks
    if profile:
        p_name = getattr(profile, "name", None) or (profile.get("name") if isinstance(profile, dict) else None)
        p_income = getattr(profile, "annual_family_income", None)
        if p_income is None and isinstance(profile, dict):
            p_income = profile.get("annual_family_income")

        for doc in extracted_documents:
            # Name check
            doc_name = getattr(doc, "person_name", None)
            if doc_name and p_name:
                from scheme_navigator.documents.audit import compare_person_names
                comparison, score = compare_person_names(doc_name, p_name)
                if comparison in ("mismatch", "phonetic_review", "cross_script"):
                    findings.append(
                        DocumentFinding(
                            code="PROFILE_DOCUMENT_NAME_MISMATCH",
                            severity="warning",
                            category="document_consistency",
                            message=(
                                f"Profile name '{p_name}' differs from name on document '{doc_name}'."
                            ),
                            recommended_action="Update profile name or submit name change / gazette affidavit.",
                            document_ids=[doc.document_id],
                        )
                    )

            # Income check
            doc_income = getattr(doc, "annual_family_income", None)
            if doc_income is not None:
                if p_income is not None:
                    diff = abs(doc_income - p_income)
                    if diff > 5000:
                        findings.append(
                            DocumentFinding(
                                code="PROFILE_DOCUMENT_INCOME_MISMATCH",
                                severity="warning",
                                category="document_consistency",
                                message=(
                                    f"Declared annual income (₹{p_income:,}) differs from "
                                    f"income certificate (₹{doc_income:,}). Please confirm."
                                ),
                                recommended_action="Confirm the exact income certified by the revenue authority.",
                                document_ids=[doc.document_id],
                            )
                        )
                if scheme and getattr(scheme, "eligibility_rule", None):
                    leaves = []
                    def _collect_leaves(node):
                        if not node:
                            return
                        if node.field:
                            leaves.append((node.field, node.op, node.value))
                        for ch in node.children:
                            _collect_leaves(ch)
                    _collect_leaves(scheme.eligibility_rule)
                    for f, op, val in leaves:
                        if f == "annual_family_income" and op in ("lte", "lt") and isinstance(val, (int, float)):
                            if doc_income > val:
                                findings.append(
                                    DocumentFinding(
                                        code="INCOME_EXCEEDS_SCHEME_THRESHOLD",
                                        severity="error",
                                        category="scheme_eligibility",
                                        message=(
                                            f"Certified income (₹{doc_income:,}) exceeds the maximum scheme limit of ₹{val:,}."
                                        ),
                                        recommended_action="Verify if family qualifies under an alternative sub-category.",
                                        document_ids=[doc.document_id],
                                    )
                                )
                                all_mand_satisfied = False

            # DOB / Age check
            if getattr(doc, "date_of_birth", None) is not None and profile.age_years is not None:
                calc_age = now.year - doc.date_of_birth.year - (
                    (now.month, now.day) < (doc.date_of_birth.month, doc.date_of_birth.day)
                )
                if abs(calc_age - profile.age_years) > 1:
                    findings.append(
                        DocumentFinding(
                            code="AGE_DOB_MISMATCH",
                            severity="warning",
                            category="document_consistency",
                            message=(
                                f"Document indicates age {calc_age} (DOB: {doc.date_of_birth.isoformat()}), "
                                f"while profile declared age {profile.age_years}."
                            ),
                            recommended_action="Confirm date of birth against official birth or school leaving certificate.",
                            document_ids=[doc.document_id],
                        )
                    )

            # Caste Category check
            doc_caste = getattr(doc, "caste_category", None)
            if doc_caste and profile.caste_category:
                if doc_caste.strip().casefold() != profile.caste_category.strip().casefold():
                    findings.append(
                        DocumentFinding(
                            code="CASTE_CATEGORY_MISMATCH",
                            severity="warning",
                            category="document_consistency",
                            message=(
                                f"Certificate declares category '{doc_caste}', while profile stated '{profile.caste_category}'."
                            ),
                            recommended_action="Update profile or verify competent issuing authority certificate.",
                            document_ids=[doc.document_id],
                        )
                    )

    # 3. Requirement matching against scheme-specific dataset or direct scheme requirements
    req_statuses: list[DocumentRequirementStatus] = []
    all_mand_satisfied = True

    target_sid = scheme_id or scheme.scheme_id

    # Check scheme-specific document requirements dataset
    scheme_spec = get_scheme_document_requirements(target_sid) or get_scheme_document_requirements(scheme.scheme_id)
    if scheme_spec and scheme_spec.get("requirements"):
        detailed_reqs = scheme_spec["requirements"]
    else:
        detailed_reqs = None

    if detailed_reqs:
        for idx, r_spec in enumerate(detailed_reqs):
            req_str = r_spec["document_name"]
            req_canon = canonical_document(req_str)
            authority = r_spec.get("issuing_authority") or "Competent Issuing Authority"
            loc_doc_name = get_localized_doc_name(req_str, lang_code)
            loc_authority = get_localized_authority(authority, lang_code)
            rts_limit = r_spec.get("rts_statutory_days")
            alt_list = [alt["name"] if isinstance(alt, dict) else str(alt) for alt in r_spec.get("accepted_alternatives", [])]
            loc_alts = [get_localized_doc_name(a, lang_code) for a in alt_list]
            is_mandatory = r_spec.get("is_mandatory", True)
            req_type = r_spec.get("requirement_type", "MANDATORY" if is_mandatory else "OPTIONAL")
            val_cond = r_spec.get("validity_conditions")
            src_ref = r_spec.get("source_reference")
            v_status = r_spec.get("verification_status", "VERIFIED")
            cond_desc = r_spec.get("condition_description")

            matched_doc: ExtractedDocument | None = None
            is_alt = False
            alt_used_name: str | None = None

            for doc in extracted_documents:
                match_ok, alt_ok, alt_name = _match_document_type(req_canon, doc)
                if match_ok:
                    matched_doc = doc
                    is_alt = alt_ok
                    alt_used_name = alt_name
                    break

            if matched_doc:
                doc_label = matched_doc.field_evidence.get("document_title") or matched_doc.document_type
                is_purged = (
                    getattr(matched_doc, "is_purged", False)
                    or getattr(matched_doc, "status", "") == "purged_expired"
                    or any("purged" in n.lower() for n in getattr(matched_doc, "extraction_notes", []))
                    or (matched_doc.document_id and matched_doc.document_id.startswith("purged_"))
                )
                if is_purged:
                    m_status = DocumentMatchStatus.EXPIRED_OR_STALE
                    s_state = DocumentMatchStatus.REPLACEMENT_REQUIRED
                    if is_mandatory:
                        all_mand_satisfied = False
                    exp_text = (
                        "Document evidence has expired under 24-hour privacy retention ceiling. Please re-upload current certificate."
                        if lang_code == "en"
                        else (
                            "२४ तासांच्या गोपनीयता मर्यादा संपल्यामुळे कागदपत्र पुरावा हटवला गेला आहे. कृपया पुन्हा अपलोड करा."
                            if lang_code == "mr"
                            else "२४ घंटे की गोपनीयता समयसीमा समाप्त होने के कारण दस्तावेज़ हटा दिया गया है। कृपया पुनः अपलोड करें।"
                        )
                    )
                    action_text = (
                        f"Re-upload valid document from {loc_authority}."
                        if lang_code == "en"
                        else (
                            f"{loc_authority} कडून मिळालेले वैध कागदपत्र पुन्हा अपलोड करा."
                            if lang_code == "mr"
                            else f"{loc_authority} से प्राप्त वैध दस्तावेज़ पुनः अपलोड करें।"
                        )
                    )
                    findings.append(
                        DocumentFinding(
                            code="RETENTION_PERIOD_EXPIRED",
                            severity="error",
                            category="document_validity",
                            message=exp_text,
                            recommended_action=action_text,
                            document_ids=[matched_doc.document_id],
                        )
                    )
                elif matched_doc.confidence < 0.50:
                    m_status = DocumentMatchStatus.UNREADABLE
                    s_state = DocumentMatchStatus.UNREADABLE
                    if is_mandatory:
                        all_mand_satisfied = False
                    exp_text = (
                        f"Document '{doc_label}' appears unreadable or low resolution (confidence: {(matched_doc.confidence * 100):.0f}%)."
                        if lang_code == "en"
                        else f"कागदपत्र '{doc_label}' अस्पष्ट किंवा कमी गुणवत्तेचे आहे."
                    )
                    action_text = (
                        "Upload a clearer scan or photo."
                        if lang_code == "en"
                        else ("अधिक स्पष्ट स्कॅन किंवा फोटो अपलोड करा." if lang_code == "mr" else "अधिक साफ़ स्कैन या फ़ोटो अपलोड करें।")
                    )
                elif matched_doc.valid_until and matched_doc.valid_until < now:
                    m_status = DocumentMatchStatus.EXPIRED
                    s_state = DocumentMatchStatus.EXPIRED_OR_STALE
                    if is_mandatory:
                        all_mand_satisfied = False
                    exp_text = (
                        f"Document '{doc_label}' expired on {matched_doc.valid_until.isoformat()}."
                        if lang_code == "en"
                        else (
                            f"कागदपत्र '{doc_label}' ची मुदत {matched_doc.valid_until.isoformat()} रोजी संपली आहे."
                            if lang_code == "mr"
                            else f"दस्तावेज़ '{doc_label}' की वैधता {matched_doc.valid_until.isoformat()} को समाप्त हो चुकी है।"
                        )
                    )
                    action_text = (
                        f"Obtain a renewed certificate from {loc_authority}."
                        if lang_code == "en"
                        else (
                            f"{loc_authority} कडून नूतनीकृत प्रमाणपत्र मिळवा."
                            if lang_code == "mr"
                            else f"{loc_authority} से नवीनीकृत प्रमाण पत्र प्राप्त करें।"
                        )
                    )
                elif (
                    ("income" in req_canon or getattr(matched_doc, "document_type", "") == "income_certificate")
                    and matched_doc.valid_financial_year
                    and matched_doc.valid_financial_year != target_financial_year
                ):
                    m_status = DocumentMatchStatus.FY_MISMATCH
                    s_state = DocumentMatchStatus.REPLACEMENT_REQUIRED
                    if is_mandatory:
                        all_mand_satisfied = False
                    exp_text = (
                        f"Income certificate is for FY {matched_doc.valid_financial_year}; target is FY {target_financial_year}."
                        if lang_code == "en"
                        else (
                            f"उत्पन्न प्रमाणपत्र वित्तीय वर्ष {matched_doc.valid_financial_year} चे आहे; लक्ष्य वर्ष {target_financial_year} आहे."
                            if lang_code == "mr"
                            else f"आय प्रमाण पत्र वित्तीय वर्ष {matched_doc.valid_financial_year} का है; लक्षित वर्ष {target_financial_year} है।"
                        )
                    )
                    action_text = (
                        f"Obtain income certificate for financial year {target_financial_year}."
                        if lang_code == "en"
                        else (
                            f"वित्तीय वर्ष {target_financial_year} साठीचे उत्पन्न प्रमाणपत्र मिळवा."
                            if lang_code == "mr"
                            else f"वित्तीय वर्ष {target_financial_year} के लिए आय प्रमाण पत्र प्राप्त करें।"
                        )
                    )
                elif matched_doc.confidence < 0.75:
                    m_status = DocumentMatchStatus.MATCHED
                    s_state = DocumentMatchStatus.MANUAL_REVIEW_REQUIRED
                    exp_text = (
                        f"Document '{doc_label}' extracted with medium confidence. Caseworker review recommended."
                        if lang_code == "en"
                        else f"कागदपत्र '{doc_label}' चे निष्कर्षण मध्यम खात्रीने झाले आहे. पुनरावलोकन आवश्यक."
                    )
                    action_text = (
                        "Verify details during final submission."
                        if lang_code == "en"
                        else ("अंतिम अर्ज सादर करताना माहिती तपासा." if lang_code == "mr" else "अंतिम आवेदन के समय विवरण सत्यापित करें।")
                    )
                elif is_alt:
                    m_status = DocumentMatchStatus.ALTERNATIVE_MATCHED
                    s_state = DocumentMatchStatus.MATCHED_FOR_PREPARATION
                    alt_label = get_localized_doc_name(alt_used_name, lang_code) if alt_used_name else ""
                    exp_text = (
                        f"Officially accepted alternative '{alt_label}' identified and matched."
                        if lang_code == "en"
                        else (
                            f"अधिकृत पर्यायी कागदपत्र '{alt_label}' स्वीकारले गेले आहे."
                            if lang_code == "mr"
                            else f"आधिकारिक वैकल्पिक दस्तावेज़ '{alt_label}' स्वीकार किया गया है।"
                        )
                    )
                    action_text = (
                        "Ready for application preparation."
                        if lang_code == "en"
                        else ("अर्ज तयारीसाठी तयार आहे." if lang_code == "mr" else "आवेदन तैयारी हेतु तैयार है।")
                    )
                else:
                    m_status = DocumentMatchStatus.MATCHED
                    s_state = DocumentMatchStatus.MATCHED_FOR_PREPARATION
                    exp_text = (
                        f"Required document '{loc_doc_name}' successfully extracted and matched."
                        if lang_code == "en"
                        else (
                            f"आवश्यक कागदपत्र '{loc_doc_name}' यशस्वीरित्या पडताळले गेले आहे."
                            if lang_code == "mr"
                            else f"आवश्यक दस्तावेज़ '{loc_doc_name}' सफलतापूर्वक सत्यापित हो गया है।"
                        )
                    )
                    action_text = (
                        "Ready for application preparation."
                        if lang_code == "en"
                        else ("अर्ज तयारीसाठी तयार आहे." if lang_code == "mr" else "आवेदन तैयारी हेतु तैयार है।")
                    )
            else:
                m_status = DocumentMatchStatus.MISSING
                s_state = DocumentMatchStatus.NOT_PROVIDED
                if is_mandatory:
                    all_mand_satisfied = False
                if loc_alts:
                    alt_info = (
                        f" Permitted alternatives: {', '.join(loc_alts)}."
                        if lang_code == "en"
                        else (
                            f" स्वीकार्य पर्यायी कागदपत्रे: {', '.join(loc_alts)}."
                            if lang_code == "mr"
                            else f" स्वीकार्य वैकल्पिक दस्तावेज़: {', '.join(loc_alts)}।"
                        )
                    )
                else:
                    alt_info = ""

                if rts_limit:
                    rts_info = (
                        f" Statutory RTS timeline: {rts_limit} days."
                        if lang_code == "en"
                        else (
                            f" लोकसेवा हमी कायदा (RTS) मुदत: {rts_limit} दिवस."
                            if lang_code == "mr"
                            else f" लोक सेवा गारंटी अधिनियम (RTS) समय सीमा: {rts_limit} दिन।"
                        )
                    )
                else:
                    rts_info = ""

                exp_text = (
                    f"Required document is missing.{alt_info}{rts_info}"
                    if lang_code == "en"
                    else (
                        f"आवश्यक कागदपत्र उपलब्ध नाही.{alt_info}{rts_info}"
                        if lang_code == "mr"
                        else f"आवश्यक दस्तावेज़ उपलब्ध नहीं है।{alt_info}{rts_info}"
                    )
                )
                action_text = (
                    f"Apply through {loc_authority}."
                    if lang_code == "en"
                    else (
                        f"{loc_authority} मार्फत अर्ज करा."
                        if lang_code == "mr"
                        else f"{loc_authority} के माध्यम से आवेदन करें।"
                    )
                )

            req_statuses.append(
                DocumentRequirementStatus(
                    requirement_id=r_spec.get("requirement_id") or f"req_{idx}_{req_canon.replace(' ', '_')}",
                    document_name=loc_doc_name,
                    is_mandatory=is_mandatory,
                    match_status=m_status,
                    state=s_state,
                    requirement_type=req_type,
                    condition_description=cond_desc,
                    matched_document_id=matched_doc.document_id if matched_doc else None,
                    matched_document_type=matched_doc.document_type if matched_doc else None,
                    permitted_alternatives=loc_alts,
                    alternative_used=get_localized_doc_name(alt_used_name, lang_code) if alt_used_name else None,
                    issuing_authority=loc_authority,
                    rts_notified_days=rts_limit,
                    validity_conditions=val_cond,
                    source_reference=src_ref,
                    verification_status=v_status,
                    explanation=exp_text,
                    action_needed=action_text,
                )
            )
    else:
        # Fallback to direct scheme.required_documents
        direct_reqs = list(dict.fromkeys(scheme.required_documents))
        for idx, req_str in enumerate(direct_reqs):
            req_canon = canonical_document(req_str)
            authority, rts_limit = ISSUING_AUTHORITY_MAP.get(
                req_canon, ("Competent Issuing Authority", None)
            )
            loc_doc_name = get_localized_doc_name(req_str, lang_code)
            loc_authority = get_localized_authority(authority, lang_code)
            alt_list = [alt["name"] for alt in OFFICIAL_ALTERNATIVE_DOCUMENTS.get(req_canon, [])]
            loc_alts = [get_localized_doc_name(a, lang_code) for a in alt_list]

            matched_doc = None
            is_alt = False
            alt_used_name = None

            for doc in extracted_documents:
                match_ok, alt_ok, alt_name = _match_document_type(req_canon, doc)
                if match_ok:
                    matched_doc = doc
                    is_alt = alt_ok
                    alt_used_name = alt_name
                    break

            if matched_doc:
                doc_label = matched_doc.field_evidence.get("document_title") or matched_doc.document_type
                is_purged = (
                    getattr(matched_doc, "is_purged", False)
                    or getattr(matched_doc, "status", "") == "purged_expired"
                    or any("purged" in n.lower() for n in getattr(matched_doc, "extraction_notes", []))
                    or (matched_doc.document_id and matched_doc.document_id.startswith("purged_"))
                )
                if is_purged:
                    m_status = DocumentMatchStatus.EXPIRED_OR_STALE
                    s_state = DocumentMatchStatus.REPLACEMENT_REQUIRED
                    all_mand_satisfied = False
                    exp_text = (
                        "Document evidence has expired under 24-hour privacy retention ceiling. Please re-upload current certificate."
                        if lang_code == "en"
                        else (
                            "२४ तासांच्या गोपनीयता मर्यादा संपल्यामुळे कागदपत्र पुरावा हटवला गेला आहे. कृपया पुन्हा अपलोड करा."
                            if lang_code == "mr"
                            else "२४ घंटे की गोपनीयता समयसीमा समाप्त होने के कारण दस्तावेज़ हटा दिया गया है। कृपया पुनः अपलोड करें।"
                        )
                    )
                    action_text = (
                        f"Re-upload valid document from {loc_authority}."
                        if lang_code == "en"
                        else f"{loc_authority} कडून मिळालेले वैध कागदपत्र पुन्हा अपलोड करा."
                        if lang_code == "mr"
                        else f"{loc_authority} से प्राप्त वैध दस्तावेज़ पुनः अपलोड करें।"
                    )
                    findings.append(
                        DocumentFinding(
                            code="RETENTION_PERIOD_EXPIRED",
                            severity="error",
                            category="document_validity",
                            message=exp_text,
                            recommended_action=action_text,
                            document_ids=[matched_doc.document_id],
                        )
                    )
                elif matched_doc.valid_until and matched_doc.valid_until < now:
                    m_status = DocumentMatchStatus.EXPIRED
                    s_state = DocumentMatchStatus.EXPIRED_OR_STALE
                    all_mand_satisfied = False
                    exp_text = (
                        f"Document '{doc_label}' expired on {matched_doc.valid_until.isoformat()}."
                        if lang_code == "en"
                        else (
                            f"कागदपत्र '{doc_label}' ची मुदत {matched_doc.valid_until.isoformat()} रोजी संपली आहे."
                            if lang_code == "mr"
                            else f"दस्तावेज़ '{doc_label}' की वैधता {matched_doc.valid_until.isoformat()} को समाप्त हो चुकी है।"
                        )
                    )
                    action_text = (
                        f"Obtain a renewed certificate from {loc_authority}."
                        if lang_code == "en"
                        else f"{loc_authority} कडून नूतनीकृत प्रमाणपत्र मिळवा."
                        if lang_code == "mr"
                        else f"{loc_authority} से नवीनीकृत प्रमाण पत्र प्राप्त करें।"
                    )
                elif (
                    ("income" in req_canon or getattr(matched_doc, "document_type", "") == "income_certificate")
                    and matched_doc.valid_financial_year
                    and matched_doc.valid_financial_year != target_financial_year
                ):
                    m_status = DocumentMatchStatus.FY_MISMATCH
                    s_state = DocumentMatchStatus.REPLACEMENT_REQUIRED
                    all_mand_satisfied = False
                    exp_text = (
                        f"Income certificate is for FY {matched_doc.valid_financial_year}; target is FY {target_financial_year}."
                        if lang_code == "en"
                        else (
                            f"उत्पन्न प्रमाणपत्र वित्तीय वर्ष {matched_doc.valid_financial_year} चे आहे; लक्ष्य वर्ष {target_financial_year} आहे."
                            if lang_code == "mr"
                            else f"आय प्रमाण पत्र वित्तीय वर्ष {matched_doc.valid_financial_year} का है; लक्षित वर्ष {target_financial_year} है।"
                        )
                    )
                    action_text = (
                        f"Obtain income certificate for financial year {target_financial_year}."
                        if lang_code == "en"
                        else f"वित्तीय वर्ष {target_financial_year} साठीचे उत्पन्न प्रमाणपत्र मिळवा."
                        if lang_code == "mr"
                        else f"वित्तीय वर्ष {target_financial_year} के लिए आय प्रमाण पत्र प्राप्त करें।"
                    )
                elif is_alt:
                    m_status = DocumentMatchStatus.ALTERNATIVE_MATCHED
                    s_state = DocumentMatchStatus.MATCHED_FOR_PREPARATION
                    loc_alt_used = get_localized_doc_name(alt_used_name, lang_code)
                    exp_text = (
                        f"Officially accepted alternative '{loc_alt_used}' identified and matched."
                        if lang_code == "en"
                        else (
                            f"अधिकृत पर्यायी कागदपत्र '{loc_alt_used}' स्वीकारले गेले आहे."
                            if lang_code == "mr"
                            else f"आधिकारिक वैकल्पिक दस्तावेज़ '{loc_alt_used}' स्वीकार किया गया है।"
                        )
                    )
                    action_text = (
                        "Ready for application preparation."
                        if lang_code == "en"
                        else "अर्ज तयारीसाठी तयार आहे."
                        if lang_code == "mr"
                        else "आवेदन तैयारी हेतु तैयार है।"
                    )
                else:
                    m_status = DocumentMatchStatus.MATCHED
                    s_state = DocumentMatchStatus.MATCHED_FOR_PREPARATION
                    exp_text = (
                        f"Required document '{loc_doc_name}' successfully extracted and matched."
                        if lang_code == "en"
                        else (
                            f"आवश्यक कागदपत्र '{loc_doc_name}' यशस्वीरित्या पडताळले गेले आहे."
                            if lang_code == "mr"
                            else f"आवश्यक दस्तावेज़ '{loc_doc_name}' सफलतापूर्वक सत्यापित हो गया है।"
                        )
                    )
                    action_text = (
                        "Ready for application preparation."
                        if lang_code == "en"
                        else "अर्ज तयारीसाठी तयार आहे."
                        if lang_code == "mr"
                        else "आवेदन तैयारी हेतु तैयार है।"
                    )
            else:
                m_status = DocumentMatchStatus.MISSING
                s_state = DocumentMatchStatus.NOT_PROVIDED
                all_mand_satisfied = False
                if loc_alts:
                    alt_info = (
                        f" Permitted alternatives: {', '.join(loc_alts)}."
                        if lang_code == "en"
                        else (
                            f" स्वीकार्य पर्यायी कागदपत्रे: {', '.join(loc_alts)}."
                            if lang_code == "mr"
                            else f" स्वीकार्य वैकल्पिक दस्तावेज़: {', '.join(loc_alts)}।"
                        )
                    )
                else:
                    alt_info = ""

                if rts_limit:
                    rts_info = (
                        f" Statutory RTS timeline: {rts_limit} days."
                        if lang_code == "en"
                        else (
                            f" लोकसेवा हमी कायदा (RTS) मुदत: {rts_limit} दिवस."
                            if lang_code == "mr"
                            else f" लोक सेवा गारंटी अधिनियम (RTS) समय सीमा: {rts_limit} दिन।"
                        )
                    )
                else:
                    rts_info = ""

                exp_text = (
                    f"Required document is missing.{alt_info}{rts_info}"
                    if lang_code == "en"
                    else (
                        f"आवश्यक कागदपत्र उपलब्ध नाही.{alt_info}{rts_info}"
                        if lang_code == "mr"
                        else f"आवश्यक दस्तावेज़ उपलब्ध नहीं है।{alt_info}{rts_info}"
                    )
                )
                action_text = (
                    f"Apply through {loc_authority}."
                    if lang_code == "en"
                    else (
                        f"{loc_authority} मार्फत अर्ज करा."
                        if lang_code == "mr"
                        else f"{loc_authority} के माध्यम से आवेदन करें।"
                    )
                )

            req_statuses.append(
                DocumentRequirementStatus(
                    requirement_id=f"req_{idx}_{req_canon.replace(' ', '_')}",
                    document_name=loc_doc_name,
                    is_mandatory=True,
                    match_status=m_status,
                    state=s_state,
                    requirement_type="MANDATORY",
                    matched_document_id=matched_doc.document_id if matched_doc else None,
                    matched_document_type=matched_doc.document_type if matched_doc else None,
                    permitted_alternatives=loc_alts,
                    alternative_used=get_localized_doc_name(alt_used_name, lang_code) if alt_used_name else None,
                    issuing_authority=loc_authority,
                    rts_notified_days=rts_limit,
                    explanation=exp_text,
                    action_needed=action_text,
                )
            )

    # 4. Overall readiness scoring & summary
    mand_reqs = [r for r in req_statuses if r.is_mandatory]
    mand_total = len(mand_reqs)
    mand_satisfied = sum(
        1 for r in mand_reqs
        if r.match_status in {DocumentMatchStatus.MATCHED, DocumentMatchStatus.ALTERNATIVE_MATCHED}
        or r.state == DocumentMatchStatus.MATCHED_FOR_PREPARATION
    )
    readiness_pct = int((mand_satisfied / mand_total * 100)) if mand_total > 0 else 100

    if all_mand_satisfied:
        summary = (
            f"All {mand_total} mandatory documents are present and validated. (Readiness: 100%)"
            if lang_code == "en"
            else (
                f"सर्व {mand_total} आवश्यक कागदपत्रे उपलब्ध व पडताळित आहेत. (पूर्वतयारी: १००%)"
                if lang_code == "mr"
                else f"सभी {mand_total} आवश्यक दस्तावेज़ उपलब्ध और सत्यापित हैं। (तैयारी: १००%)"
            )
        )
    else:
        summary = (
            f"{mand_satisfied} of {mand_total} mandatory documents matched ({readiness_pct}%). {mand_total - mand_satisfied} missing or requiring renewal."
            if lang_code == "en"
            else (
                f"{mand_total} पैकी {mand_satisfied} कागदपत्रे जुळली आहेत ({readiness_pct}%). {mand_total - mand_satisfied} प्रलंबित किंवा नूतनीकरण आवश्यक."
                if lang_code == "mr"
                else f"{mand_total} में से {mand_satisfied} दस्तावेज़ मिले ({readiness_pct}%)। {mand_total - mand_satisfied} लंबित या नवीनीकरण आवश्यक।"
            )
        )

    has_blocking_error = any(f.severity == "error" for f in findings)
    if all_mand_satisfied and not has_blocking_error and readiness_pct == 100:
        readiness_status = "READY"
    elif findings or readiness_pct > 0:
        readiness_status = "NEEDS_ATTENTION"
    else:
        readiness_status = "MISSING"

    return IntelligentDocumentPreparationReport(
        scheme_id=scheme.scheme_id,
        all_mandatory_satisfied=all_mand_satisfied,
        requirements=req_statuses,
        conflicts_detected=findings,
        duplicates_detected=duplicates,
        needs_human_audit=needs_human,
        audit_summary=summary,
        readiness_percentage=readiness_pct,
        mandatory_total=mand_total,
        mandatory_satisfied=mand_satisfied,
        readiness_status=readiness_status,
    )
