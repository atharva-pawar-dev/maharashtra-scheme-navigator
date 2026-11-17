from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from scheme_navigator.domain.models import CitizenProfile, ExtractedDocument, Language, Scheme


class PortalTarget(StrEnum):
    MAHADBT = "mahadbt"
    AAPLE_SARKAR = "aaplesarkar"
    OFFICIAL_DEPARTMENTAL = "official_departmental"


class FieldFillSource(StrEnum):
    DOCUMENT_EXTRACTED = "document_extracted"
    PROFILE_REPORTED = "profile_reported"
    MANUAL_ENTRY_MANDATORY = "manual_entry_mandatory"
    RESTRICTED_SECURITY_FIELD = "restricted_security_field"


class PortalFormFieldMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    portal_field_id: str
    portal_field_label: str
    suggested_value: str | None = None
    source: FieldFillSource
    is_sensitive: bool = False
    requires_user_confirmation: bool = True
    instructions_for_citizen: str


class ApplicationPreparationStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_number: int
    title: str
    instruction: str
    portal_url: str | None = None
    is_manual_step: bool = True
    security_warning: str | None = None


class PortalApplicationPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheme_id: str
    target_portal: PortalTarget
    portal_url: str
    department_name: str
    field_mappings: list[PortalFormFieldMapping] = Field(default_factory=list)
    preparation_steps: list[ApplicationPreparationStep] = Field(default_factory=list)
    pre_submission_checklist: list[str] = Field(default_factory=list)
    requires_explicit_citizen_confirmation: bool = True
    application_submission_status: str = "not_submitted_guidance_only"
    security_disclaimer: str


PORTAL_SECURITY_DISCLAIMERS: dict[str, str] = {
    "en": (
        "SAFE PORTAL ASSISTANCE GUARANTEE: Scheme Navigator is an independent guidance assistant. "
        "It NEVER stores passwords, biometric data, full Aadhaar numbers, or OTPs. "
        "It NEVER bypasses CAPTCHA, authentication checks, or portal restrictions. "
        "Scheme Navigator DOES NOT submit applications on your behalf; you must personally review every field, "
        "verify documents, and submit directly on the official government portal."
    ),
    "mr": (
        "सुरक्षित पोर्टल सहाय्यता हमी: स्कीम नेव्हिगेटर एक स्वतंत्र मार्गदर्शक प्रणाली आहे. "
        "हे पासवर्ड, बायोमेट्रिक माहिती, संपूर्ण आधार क्रमांक किंवा OTP कधीही साठवून ठेवत नाही. "
        "हे कॅप्चा किंवा पोर्टल सुरक्षा निर्बंध कधीही बायपास करत नाही. "
        "स्कीम नेव्हिगेटर स्वतः अर्ज सबमिट करत नाही; नागरिकांनी अधिकृत सरकारी पोर्टलवर स्वतः लॉगिन करून "
        "सर्व माहितीची खात्री करूनच प्रत्यक्ष अर्ज सादर करावा."
    ),
    "hi": (
        "सुरक्षित पोर्टल सहायता गारंटी: स्कीम नेविगेटर एक स्वतंत्र मार्गदर्शन प्रणाली है। "
        "यह पासवर्ड, बायोमेट्रिक डेटा, पूर्ण आधार नंबर या OTP कभी संग्रहित नहीं करता। "
        "यह कैप्चा या पोर्टल सुरक्षा प्रतिबंधों को कभी बाईपास नहीं करता। "
        "स्कीम नेविगेटर आपकी ओर से आवेदन जमा नहीं करता; नागरिकों को आधिकारिक सरकारी पोर्टल पर स्वयं लॉगिन कर, "
        "सभी फ़ील्ड की समीक्षा कर सीधे आवेदन जमा करना होगा।"
    ),
}

PORTAL_TARGET_URLS: dict[PortalTarget, tuple[str, str]] = {
    PortalTarget.MAHADBT: (
        "https://mahadbt.maharashtra.gov.in",
        "MahaDBT (Maharashtra Direct Benefit Transfer Portal)",
    ),
    PortalTarget.AAPLE_SARKAR: (
        "https://aaplesarkar.mahaonline.gov.in",
        "Aaple Sarkar (Right to Services Portal, Maharashtra)",
    ),
    PortalTarget.OFFICIAL_DEPARTMENTAL: (
        "https://www.maharashtra.gov.in",
        "Departmental Citizen Service Counter / Ward Office",
    ),
}


def _determine_target_portal(scheme: Scheme) -> PortalTarget:
    sid = scheme.scheme_id.casefold()
    dept = scheme.department.casefold()

    if "scholarship" in sid or "obc" in sid or "post-matric" in sid or "tuition" in sid:
        return PortalTarget.MAHADBT
    if "sanjay" in sid or "shravanbal" in sid or "revenue" in dept:
        return PortalTarget.AAPLE_SARKAR
    return PortalTarget.OFFICIAL_DEPARTMENTAL


def build_portal_application_package(
    scheme: Scheme,
    profile: CitizenProfile,
    extracted_documents: list[ExtractedDocument] | None = None,
    language: Language = Language.EN,
) -> PortalApplicationPackage:
    """Generate safe, prefilled field mappings and manual submission guidance for the citizen."""
    lang_code = language.value if isinstance(language, Language) else str(language).lower()
    if lang_code not in PORTAL_SECURITY_DISCLAIMERS:
        lang_code = "en"

    portal_type = _determine_target_portal(scheme)
    portal_url, portal_name = PORTAL_TARGET_URLS[portal_type]
    docs = extracted_documents or []

    # Find relevant document extractions
    income_doc = next((d for d in docs if d.document_type == "income_certificate"), None)
    caste_doc = next((d for d in docs if d.document_type == "caste_certificate"), None)
    domicile_doc = next((d for d in docs if d.document_type == "domicile_certificate"), None)
    aadhaar_doc = next((d for d in docs if d.document_type == "aadhaar_card"), None)

    # Resolve applicant name
    name_val = None
    name_src = FieldFillSource.MANUAL_ENTRY_MANDATORY
    if domicile_doc and domicile_doc.person_name:
        name_val = domicile_doc.person_name
        name_src = FieldFillSource.DOCUMENT_EXTRACTED
    elif aadhaar_doc and aadhaar_doc.person_name:
        name_val = aadhaar_doc.person_name
        name_src = FieldFillSource.DOCUMENT_EXTRACTED
    elif profile.name:
        name_val = profile.name
        name_src = FieldFillSource.PROFILE_REPORTED

    # Resolve income
    income_val = None
    income_src = FieldFillSource.MANUAL_ENTRY_MANDATORY
    if income_doc and income_doc.annual_family_income is not None:
        income_val = str(income_doc.annual_family_income)
        income_src = FieldFillSource.DOCUMENT_EXTRACTED
    elif profile.annual_family_income is not None:
        income_val = str(profile.annual_family_income)
        income_src = FieldFillSource.PROFILE_REPORTED

    # Build field mappings
    mappings: list[PortalFormFieldMapping] = [
        PortalFormFieldMapping(
            portal_field_id="applicant_full_name",
            portal_field_label=(
                "Applicant Full Name" if lang_code == "en" else ("अर्जदाराचे पूर्ण नाव" if lang_code == "mr" else "आवेदक का पूरा नाम")
            ),
            suggested_value=name_val,
            source=name_src,
            is_sensitive=False,
            requires_user_confirmation=True,
            instructions_for_citizen=(
                "Verify spelling against your Aadhaar card and SSC / Domicile certificate before entering."
                if lang_code == "en"
                else "दाखल करण्यापूर्वी आधार कार्ड व अधिवास प्रमाणपत्रावरील स्पेलिंग तपासा."
                if lang_code == "mr"
                else "प्रविष्ट करने से पहले आधार कार्ड और अधिवास प्रमाण पत्र पर नाम की वर्तनी जांचें।"
            ),
        ),
        PortalFormFieldMapping(
            portal_field_id="annual_family_income",
            portal_field_label=(
                "Annual Family Income (INR)" if lang_code == "en" else ("वार्षिक कौटुंबिक उत्पन्न (₹)" if lang_code == "mr" else "वार्षिक पारिवारिक आय (₹)")
            ),
            suggested_value=income_val,
            source=income_src,
            is_sensitive=False,
            requires_user_confirmation=True,
            instructions_for_citizen=(
                "Must match the exact amount on the Tehsildar Income Certificate attached."
                if lang_code == "en"
                else "जोडलेल्या तहसीलदार उत्पन्न प्रमाणपत्रावरील अचूक रकमेनुसार असावे."
                if lang_code == "mr"
                else "संलग्न तहसीलदार आय प्रमाण पत्र की सटीक राशि से मेल खाना चाहिए।"
            ),
        ),
        PortalFormFieldMapping(
            portal_field_id="resident_state",
            portal_field_label=(
                "Domicile / Residence State" if lang_code == "en" else ("रहिवासी राज्य" if lang_code == "mr" else "निवास का राज्य")
            ),
            suggested_value="Maharashtra",
            source=FieldFillSource.PROFILE_REPORTED,
            is_sensitive=False,
            requires_user_confirmation=True,
            instructions_for_citizen="Select 'Maharashtra' and attach valid Domicile proof.",
        ),
        PortalFormFieldMapping(
            portal_field_id="aadhaar_authentication",
            portal_field_label=(
                "Aadhaar OTP / Biometric Verification" if lang_code == "en" else ("आधार ओटीपी / बायोमेट्रिक प्रमाणीकरण" if lang_code == "mr" else "आधार ओटीपी / बायोमेट्रिक प्रमाणीकरण")
            ),
            suggested_value="[RESTRICTED - DO NOT ENTER IN THIRD PARTY APP]",
            source=FieldFillSource.RESTRICTED_SECURITY_FIELD,
            is_sensitive=True,
            requires_user_confirmation=True,
            instructions_for_citizen=(
                "Enter your Aadhaar and OTP ONLY on the official portal (https://mahadbt.maharashtra.gov.in or https://aaplesarkar.mahaonline.gov.in)."
                if lang_code == "en"
                else "आपला आधार व ओटीपी केवळ अधिकृत सरकारी पोर्टलवरच प्रविष्ट करा."
                if lang_code == "mr"
                else "अपना आधार और ओटीपी केवल आधिकारिक सरकारी पोर्टल पर ही दर्ज करें।"
            ),
        ),
    ]

    if profile.gender:
        mappings.append(
            PortalFormFieldMapping(
                portal_field_id="gender",
                portal_field_label="Gender / लिंग",
                suggested_value=profile.gender.title(),
                source=FieldFillSource.PROFILE_REPORTED,
                is_sensitive=False,
                requires_user_confirmation=True,
                instructions_for_citizen="Select your gender as per official identity document.",
            )
        )

    # Step-by-step guidance
    steps: list[ApplicationPreparationStep] = [
        ApplicationPreparationStep(
            step_number=1,
            title="Gather Audited Supporting Documents" if lang_code == "en" else "तपासलेली आवश्यक कागदपत्रे गोळा करा",
            instruction=(
                f"Ensure you have clear digital copies of: {', '.join(scheme.required_documents)}."
                if lang_code == "en"
                else f"पुढील कागदपत्रांच्या स्पष्ट डिजिटल प्रती जवळ ठेवा: {', '.join(scheme.required_documents)}."
            ),
            is_manual_step=True,
        ),
        ApplicationPreparationStep(
            step_number=2,
            title=f"Access Official Portal ({portal_name})",
            instruction=f"Open {portal_url} in your secure browser. Log in using your registered Citizen ID.",
            portal_url=portal_url,
            is_manual_step=True,
            security_warning="Never use unverified cyber-cafe autofill or share your password with anyone.",
        ),
        ApplicationPreparationStep(
            step_number=3,
            title="Authenticate via Aadhaar OTP directly on Portal",
            instruction="Complete OTP authentication directly on the official portal screen. Never share the OTP with any agent.",
            is_manual_step=True,
            security_warning="Government departments NEVER call to ask for OTPs.",
        ),
        ApplicationPreparationStep(
            step_number=4,
            title="Fill Form Using Scheme Navigator Suggested Guidance Values",
            instruction="Use the verified values provided in the field mapping table above. Verify all spelling before saving draft.",
            is_manual_step=True,
        ),
        ApplicationPreparationStep(
            step_number=5,
            title="Upload Supporting PDFs and Review Summary",
            instruction="Upload your certificates. Preview the complete application PDF before clicking Final Submit.",
            is_manual_step=True,
        ),
        ApplicationPreparationStep(
            step_number=6,
            title="Submit and Retain Acknowledgement Receipt",
            instruction="Click 'Submit Application'. Download and print the official Application Acknowledgement with Application Number.",
            is_manual_step=True,
        ),
    ]

    # Pre-submission checklist
    checklist = [
        "I have personally verified all spelling and certificate details.",
        "Annual family income matches the attached Tehsildar certificate.",
        "Bank account is active and seeded with Aadhaar for DBT transfer.",
        "I understand Scheme Navigator is not an official portal and does not submit applications.",
        "I will retain the official portal Application Acknowledgement Receipt.",
    ]
    if lang_code == "mr":
        checklist = [
            "मी स्वतः सर्व माहिती व प्रमाणपत्रांची अचूकता तपासली आहे.",
            "वार्षिक कौटुंबिक उत्पन्न जोडलेल्या तहसीलदार प्रमाणपत्राशी तंतोतंत जुळते.",
            "डीबीटी हस्तांतरणासाठी बँक खाते सक्रिय असून आधारशी जोडलेले आहे.",
            "स्कीम नेव्हिगेटर सरकारी पोर्टल नाही व अर्ज परस्पर भरत नाही याची मला जाणीव आहे.",
            "अधिकृत पोर्टलवरील अर्ज पोचपावती क्रमांक मी सुरक्षित जतन करेन.",
        ]
    elif lang_code == "hi":
        checklist = [
            "मैंने स्वयं सभी विवरणों और प्रमाण पत्रों की शुद्धता की पुष्टि की है।",
            "वार्षिक पारिवारिक आय संलग्न तहसीलदार प्रमाण पत्र से सटीक मेल खाती है।",
            "डीबीटी अंतरण हेतु बैंक खाता सक्रिय एवं आधार से जुड़ा हुआ है।",
            "स्कीम नेविगेटर सरकारी पोर्टल नहीं है और स्वतः आवेदन जमा नहीं करता, यह मुझे ज्ञात है।",
            "आधिकारिक पोर्टल से प्राप्त आवेदन पावती रसीद को सुरक्षित रखूंगा/रखूंगी।",
        ]

    return PortalApplicationPackage(
        scheme_id=scheme.scheme_id,
        target_portal=portal_type,
        portal_url=portal_url,
        department_name=scheme.department,
        field_mappings=mappings,
        preparation_steps=steps,
        pre_submission_checklist=checklist,
        requires_explicit_citizen_confirmation=True,
        application_submission_status="not_submitted_guidance_only",
        security_disclaimer=PORTAL_SECURITY_DISCLAIMERS[lang_code],
    )
