from __future__ import annotations

import json
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
    return all_reqs.get(scheme_id)


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
        for doc in extracted_documents:
            # Name check
            doc_name = getattr(doc, "person_name", None)
            if doc_name and getattr(profile, "name", None):
                from scheme_navigator.documents.audit import compare_person_names
                comparison, score = compare_person_names(doc_name, profile.name)
                if comparison in ("mismatch", "phonetic_review", "cross_script"):
                    findings.append(
                        DocumentFinding(
                            code="PROFILE_DOCUMENT_NAME_MISMATCH",
                            severity="warning",
                            category="document_consistency",
                            message=(
                                f"Profile name '{profile.name}' differs from name on document '{doc_name}'."
                            ),
                            recommended_action="Update profile name or submit name change / gazette affidavit.",
                            document_ids=[doc.document_id],
                        )
                    )

            # Income check
            doc_income = getattr(doc, "annual_family_income", None)
            if doc_income is not None:
                if profile.annual_family_income is not None:
                    diff = abs(doc_income - profile.annual_family_income)
                    if diff > 5000:
                        findings.append(
                            DocumentFinding(
                                code="PROFILE_DOCUMENT_INCOME_MISMATCH",
                                severity="warning",
                                category="document_consistency",
                                message=(
                                    f"Declared annual income (₹{profile.annual_family_income:,}) differs from "
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
            rts_limit = r_spec.get("rts_statutory_days")
            alt_list = [alt["name"] if isinstance(alt, dict) else str(alt) for alt in r_spec.get("accepted_alternatives", [])]
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
                if matched_doc.confidence < 0.50:
                    m_status = DocumentMatchStatus.UNREADABLE
                    s_state = DocumentMatchStatus.UNREADABLE
                    if is_mandatory:
                        all_mand_satisfied = False
                    exp_text = (
                        f"Document '{doc_label}' appears unreadable or low resolution (confidence: {(matched_doc.confidence * 100):.0f}%)."
                        if lang_code == "en"
                        else f"कागदपत्र '{doc_label}' अस्पष्ट किंवा कमी गुणवत्तेचे आहे."
                    )
                    action_text = "Upload a clearer scan or photo."
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
                        f"Obtain a renewed certificate from {authority}."
                        if lang_code == "en"
                        else f"{authority} कडून नूतनीकृत प्रमाणपत्र मिळवा."
                        if lang_code == "mr"
                        else f"{authority} से नवीनीकृत प्रमाण पत्र प्राप्त करें।"
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
                        else f"वित्तीय वर्ष {target_financial_year} साठीचे उत्पन्न प्रमाणपत्र मिळवा."
                        if lang_code == "mr"
                        else f"वित्तीय वर्ष {target_financial_year} के लिए आय प्रमाण पत्र प्राप्त करें।"
                    )
                elif matched_doc.confidence < 0.75:
                    m_status = DocumentMatchStatus.MATCHED
                    s_state = DocumentMatchStatus.MANUAL_REVIEW_REQUIRED
                    exp_text = (
                        f"Document '{doc_label}' extracted with medium confidence. Caseworker review recommended."
                        if lang_code == "en"
                        else f"कागदपत्र '{doc_label}' चे निष्कर्षण मध्यम खात्रीने झाले आहे. पुनरावलोकन आवश्यक."
                    )
                    action_text = "Verify details during final submission."
                elif is_alt:
                    m_status = DocumentMatchStatus.ALTERNATIVE_MATCHED
                    s_state = DocumentMatchStatus.MATCHED_FOR_PREPARATION
                    exp_text = (
                        f"Officially accepted alternative '{alt_used_name}' identified and matched."
                        if lang_code == "en"
                        else (
                            f"अधिकृत पर्यायी कागदपत्र '{alt_used_name}' स्वीकारले गेले आहे."
                            if lang_code == "mr"
                            else f"आधिकारिक वैकल्पिक दस्तावेज़ '{alt_used_name}' स्वीकार किया गया है।"
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
                        f"Required document '{req_str}' successfully extracted and matched."
                        if lang_code == "en"
                        else (
                            f"आवश्यक कागदपत्र '{req_str}' यशस्वीरित्या पडताळले गेले आहे."
                            if lang_code == "mr"
                            else f"आवश्यक दस्तावेज़ '{req_str}' सफलतापूर्वक सत्यापित हो गया है।"
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
                if is_mandatory:
                    all_mand_satisfied = False
                alt_info = f" Permitted alternatives: {', '.join(alt_list)}." if alt_list else ""
                rts_info = f" Statutory RTS timeline: {rts_limit} days." if rts_limit else ""
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
                    f"Apply through {authority}."
                    if lang_code == "en"
                    else f"{authority} मार्फत अर्ज करा."
                    if lang_code == "mr"
                    else f"{authority} के माध्यम से आवेदन करें।"
                )

            req_statuses.append(
                DocumentRequirementStatus(
                    requirement_id=r_spec.get("requirement_id") or f"req_{idx}_{req_canon.replace(' ', '_')}",
                    document_name=req_str,
                    is_mandatory=is_mandatory,
                    match_status=m_status,
                    state=s_state,
                    requirement_type=req_type,
                    condition_description=cond_desc,
                    matched_document_id=matched_doc.document_id if matched_doc else None,
                    matched_document_type=matched_doc.document_type if matched_doc else None,
                    permitted_alternatives=alt_list,
                    alternative_used=alt_used_name,
                    issuing_authority=authority,
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
            alt_list = [alt["name"] for alt in OFFICIAL_ALTERNATIVE_DOCUMENTS.get(req_canon, [])]

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
                if matched_doc.valid_until and matched_doc.valid_until < now:
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
                        f"Obtain a renewed certificate from {authority}."
                        if lang_code == "en"
                        else f"{authority} कडून नूतनीकृत प्रमाणपत्र मिळवा."
                        if lang_code == "mr"
                        else f"{authority} से नवीनीकृत प्रमाण पत्र प्राप्त करें।"
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
                    exp_text = (
                        f"Officially accepted alternative '{alt_used_name}' identified and matched."
                        if lang_code == "en"
                        else (
                            f"अधिकृत पर्यायी कागदपत्र '{alt_used_name}' स्वीकारले गेले आहे."
                            if lang_code == "mr"
                            else f"आधिकारिक वैकल्पिक दस्तावेज़ '{alt_used_name}' स्वीकार किया गया है।"
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
                        f"Required document '{req_str}' successfully extracted and matched."
                        if lang_code == "en"
                        else (
                            f"आवश्यक कागदपत्र '{req_str}' यशस्वीरित्या पडताळले गेले आहे."
                            if lang_code == "mr"
                            else f"आवश्यक दस्तावेज़ '{req_str}' सफलतापूर्वक सत्यापित हो गया है।"
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
                alt_info = f" Permitted alternatives: {', '.join(alt_list)}." if alt_list else ""
                rts_info = f" Statutory RTS timeline: {rts_limit} days." if rts_limit else ""
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
                    f"Apply through {authority}."
                    if lang_code == "en"
                    else f"{authority} मार्फत अर्ज करा."
                    if lang_code == "mr"
                    else f"{authority} के माध्यम से आवेदन करें।"
                )

            req_statuses.append(
                DocumentRequirementStatus(
                    requirement_id=f"req_{idx}_{req_canon.replace(' ', '_')}",
                    document_name=req_str,
                    is_mandatory=True,
                    match_status=m_status,
                    state=s_state,
                    requirement_type="MANDATORY",
                    matched_document_id=matched_doc.document_id if matched_doc else None,
                    matched_document_type=matched_doc.document_type if matched_doc else None,
                    permitted_alternatives=alt_list,
                    alternative_used=alt_used_name,
                    issuing_authority=authority,
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
