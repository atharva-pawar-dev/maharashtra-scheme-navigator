from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from scheme_navigator.domain.models import Language, Scheme, SourceReference


class SchemeTrustStatus(StrEnum):
    """Rigorous verification and lifecycle status of a scheme record."""

    DRAFT_CANDIDATE = "draft_candidate"
    UNDER_REVIEW = "under_review"
    SOURCE_VERIFIED = "source_verified"
    INTERNALLY_REVIEWED = "internally_reviewed"
    PUBLICATION_AUTHORIZED = "publication_authorized"
    ACTIVE = "active"
    EXPIRED_OR_SUPERSEDED = "expired_or_superseded"


class SourceCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str
    source_url: str
    source_kind: str
    official_reference: str | None = None
    page_or_section: str | None = None
    retrieved_at: str | None = None


class SchemeTrustReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheme_id: str
    trust_status: SchemeTrustStatus
    badge_label: str
    badge_color: str
    status_description: str
    last_verified_at: str | None = None
    effective_from: str | None = None
    effective_until: str | None = None
    effective_period_display: str
    official_sources: list[SourceCitation] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    is_official_government_recommendation: bool = False
    trust_notice: str
    provenance_disclaimer: str


TRUST_TRANSLATIONS: dict[str, dict[SchemeTrustStatus, dict[str, str]]] = {
    "en": {
        SchemeTrustStatus.DRAFT_CANDIDATE: {
            "label": "Draft candidate",
            "desc": "Preliminary draft record under initial compilation. Not authorized for official evaluation.",
            "color": "amber",
        },
        SchemeTrustStatus.UNDER_REVIEW: {
            "label": "Under review",
            "desc": "Under active policy analysis and departmental rule verification.",
            "color": "amber",
        },
        SchemeTrustStatus.SOURCE_VERIFIED: {
            "label": "Source verified",
            "desc": "Primary Government Resolution or guideline identified, excerpted, and cryptographic hash verified.",
            "color": "blue",
        },
        SchemeTrustStatus.INTERNALLY_REVIEWED: {
            "label": "Internally reviewed",
            "desc": "Internal policy rules reviewed by research team; pending administrative publication sign-off.",
            "color": "purple",
        },
        SchemeTrustStatus.PUBLICATION_AUTHORIZED: {
            "label": "Publication authorised",
            "desc": "Authorised by catalogue administration for eligibility testing.",
            "color": "teal",
        },
        SchemeTrustStatus.ACTIVE: {
            "label": "Active for eligibility evaluation",
            "desc": "Operative rule in active catalogue. Note: Preliminary results are not an official government entitlement.",
            "color": "green",
        },
        SchemeTrustStatus.EXPIRED_OR_SUPERSEDED: {
            "label": "Expired or superseded",
            "desc": "Rule superseded by later government resolution or financial year cycle ended.",
            "color": "slate",
        },
    },
    "mr": {
        SchemeTrustStatus.DRAFT_CANDIDATE: {
            "label": "मसुदा उमेदवार (अंतिम नाही)",
            "desc": "प्राथमिक मसुदा नोंद; प्राथमिक संकलन सुरू आहे. अधिकृत मूल्यांकनासाठी प्राधिकृत नाही.",
            "color": "amber",
        },
        SchemeTrustStatus.UNDER_REVIEW: {
            "label": "पुनरावलोकनाधीन (तपासणी सुरू)",
            "desc": "धोरण विश्लेषक व प्रशासकीय नियमांची सक्रिय पडताळणी सुरू आहे.",
            "color": "amber",
        },
        SchemeTrustStatus.SOURCE_VERIFIED: {
            "label": "अधिकृत स्रोत पडताळित",
            "desc": "मूळ शासन निर्णय/मार्गदर्शक तत्त्वे उपलब्ध असून डिजिटल परिच्छेद जुळला आहे.",
            "color": "blue",
        },
        SchemeTrustStatus.INTERNALLY_REVIEWED: {
            "label": "अंतर्गत पुनरावलोकन पूर्ण",
            "desc": "संशोधन चमूने अंतर्गत धोरण व अटी तपासल्या आहेत; अंतिम प्रकाशन स्वाक्षरी प्रलंबित.",
            "color": "purple",
        },
        SchemeTrustStatus.PUBLICATION_AUTHORIZED: {
            "label": "प्रकाशन प्राधिकृत",
            "desc": "पात्रता चाचणीसाठी सूची प्रशासनाने प्रकाशनास मान्यता दिली आहे.",
            "color": "teal",
        },
        SchemeTrustStatus.ACTIVE: {
            "label": "पात्रता मूल्यमापनासाठी सक्रिय",
            "desc": "सक्रिय सूचीतील लागू नियम. सूचना: प्राथमिक निकाल ही सरकारी मंजुरी नव्हे.",
            "color": "green",
        },
        SchemeTrustStatus.EXPIRED_OR_SUPERSEDED: {
            "label": "मुदत संपलेली किंवा अधिक्रमित",
            "desc": "पुढील शासन निर्णयाद्वारे नियम बदलला आहे किंवा कालावधी समाप्त झाला आहे.",
            "color": "slate",
        },
    },
    "hi": {
        SchemeTrustStatus.DRAFT_CANDIDATE: {
            "label": "प्रारूप उम्मीदवार (अंतिम नहीं)",
            "desc": "प्रारंभिक प्रारूप रिकॉर्ड; संकलन जारी है। आधिकारिक मूल्यांकन हेतु अधिकृत नहीं।",
            "color": "amber",
        },
        SchemeTrustStatus.UNDER_REVIEW: {
            "label": "समीक्षाधीन (जांच जारी)",
            "desc": "नीति विश्लेषक एवं विभागीय नियमों की सक्रिय जांच जारी है।",
            "color": "amber",
        },
        SchemeTrustStatus.SOURCE_VERIFIED: {
            "label": "आधिकारिक स्रोत सत्यापित",
            "desc": "मूल शासन निर्णय/दिशानिर्देश उपलब्ध हैं और डिजिटल अंश संरेखित है।",
            "color": "blue",
        },
        SchemeTrustStatus.INTERNALLY_REVIEWED: {
            "label": "आंतरिक समीक्षा पूर्ण",
            "desc": "अनुसंधान दल द्वारा नीति व शर्तों की समीक्षा पूर्ण; प्रकाशन अनुमोदन लंबित।",
            "color": "purple",
        },
        SchemeTrustStatus.PUBLICATION_AUTHORIZED: {
            "label": "प्रकाशन अधिकृत",
            "desc": "पात्रता परीक्षण हेतु कैटलॉग प्रशासन द्वारा प्रकाशन स्वीकृत।",
            "color": "teal",
        },
        SchemeTrustStatus.ACTIVE: {
            "label": "पात्रता मूल्यांकन हेतु सक्रिय",
            "desc": "सक्रिय कैटलॉग नियम। सूचना: प्रारंभिक परिणाम सरकारी स्वीकृति नहीं है।",
            "color": "green",
        },
        SchemeTrustStatus.EXPIRED_OR_SUPERSEDED: {
            "label": "अवधि समाप्त या अधिक्रमित",
            "desc": "परवर्ती शासन निर्णय द्वारा नियम संशोधित या वित्तीय समयावधि समाप्त।",
            "color": "slate",
        },
    },
}

TRUST_NOTICES: dict[str, str] = {
    "en": (
        "Scheme Navigator provides independent preliminary eligibility assistance. "
        "The presence of a Government Resolution reference verifies the legal source citations, "
        "but does NOT constitute official government endorsement, eligibility guarantee, or application approval. "
        "Final eligibility is determined exclusively by the competent government authority."
    ),
    "mr": (
        "सूचना: स्कीम नेव्हिगेटर सार्वजनिक शासन निर्णयांवर आधारित स्वतंत्र प्राथमिक मार्गदर्शन पुरवते. "
        "शासकीय संदर्भ दर्शविल्याने स्रोत सिद्ध होतो, परंतु ती अधिकृत शासकीय मंजुरी किंवा लाभाची हमी नाही. "
        "अंतिम पात्रता केवळ संबंधित सक्षम सरकारी प्राधिकरणाकडूनच निश्चित केली जाते."
    ),
    "hi": (
        "सूचना: स्कीम नेविगेटर सार्वजनिक शासन निर्णयों पर आधारित स्वतंत्र प्रारंभिक मार्गदर्शन प्रदान करता है। "
        "शासकीय संदर्भ स्रोत की प्रामाणिकता दर्शाता है, किंतु यह आधिकारिक सरकारी स्वीकृति या लाभ की गारंटी नहीं है। "
        "अंतिम पात्रता का निर्धारण केवल सक्षम सरकारी प्राधिकरण द्वारा किया जाता है।"
    ),
}

PROVENANCE_DISCLAIMERS: dict[str, str] = {
    "en": (
        "Rules are compiled from public Government Resolutions and official departmental portals. "
        "They are subject to administrative updates, circulars, and departmental discretion."
    ),
    "mr": (
        "नियम सार्वजनिक शासन निर्णय व अधिकृत विभागीय संकेतस्थळांवरून संकलित केले आहेत. "
        "ते शासकीय परिपत्रके व प्रशासकीय निर्णयांच्या अधीन आहेत."
    ),
    "hi": (
        "नियम सार्वजनिक शासन निर्णयों और आधिकारिक विभागीय पोर्टलों से संकलित हैं। "
        "वे सरकारी परिपत्रकों और प्रशासनिक निर्णयों के अधीन हैं।"
    ),
}


def determine_trust_status(scheme: Scheme, reference_date: date | None = None) -> SchemeTrustStatus:
    """Determine the trust and lifecycle verification status of a scheme record."""
    ref_date = reference_date or date.today()

    # 1. Expired / retired / superseded check
    if scheme.rule_status == "retired":
        return SchemeTrustStatus.EXPIRED_OR_SUPERSEDED

    # Check evidence dates if all conditions expired
    if scheme.evidence:
        all_expired = True
        has_dates = False
        for ev in scheme.evidence:
            eff_until = getattr(ev, "effective_until", None)
            if isinstance(ev, dict):
                eff_until = ev.get("effective_until")
            if eff_until is not None:
                has_dates = True
                if isinstance(eff_until, str):
                    try:
                        eff_until = date.fromisoformat(eff_until)
                    except ValueError:
                        pass
                if isinstance(eff_until, date) and eff_until >= ref_date:
                    all_expired = False
                    break
            else:
                all_expired = False
                break
        if has_dates and all_expired:
            return SchemeTrustStatus.EXPIRED_OR_SUPERSEDED

    # 2. Active non-demo requires publication_authorized and active rule_status
    if scheme.rule_status == "active":
        if scheme.publication_authorized:
            return SchemeTrustStatus.ACTIVE
        # Local demo fixture fallback
        is_demo = (
            scheme.scheme_id.startswith("demo-")
            or (scheme.approved_by or "").strip().casefold() == "local_demo_fixture_only"
            or "demo-fixture" in (scheme.approval_reference or "").casefold()
        )
        if is_demo:
            return SchemeTrustStatus.ACTIVE
        # If active status claimed without publication authorization, downgrade to under review
        return SchemeTrustStatus.UNDER_REVIEW

    # 3. Publication authorised
    if scheme.publication_authorized:
        return SchemeTrustStatus.PUBLICATION_AUTHORIZED

    # 4. Internally reviewed
    if scheme.rule_status == "reviewed":
        return SchemeTrustStatus.INTERNALLY_REVIEWED

    # 5. Check if sources have verified GRs / official guidelines
    has_gr_source = False
    for src in scheme.sources:
        if src.source_kind in {"government_resolution", "official_notification", "official_scheme_page"}:
            if src.evidence_sha256 and len(src.evidence_sha256) == 64:
                has_gr_source = True
                break

    has_verified_evidence = False
    for ev in scheme.evidence:
        ver_status = getattr(ev, "verification_status", None)
        if isinstance(ev, dict):
            ver_status = ev.get("verification_status")
        if ver_status in {"analyst_reviewed", "legal_approved"}:
            has_verified_evidence = True
            break

    if has_verified_evidence:
        return SchemeTrustStatus.INTERNALLY_REVIEWED

    if has_gr_source:
        return SchemeTrustStatus.SOURCE_VERIFIED

    if scheme.rule_status == "draft":
        return SchemeTrustStatus.DRAFT_CANDIDATE

    return SchemeTrustStatus.UNDER_REVIEW


def generate_trust_report(
    scheme: Scheme,
    language: Language | str = Language.EN,
    reference_date: date | None = None,
) -> SchemeTrustReport:
    """Generate a complete citizen-facing trust and verification report for a scheme."""
    lang_code = language.value if isinstance(language, Language) else str(language).lower()
    if lang_code not in TRUST_TRANSLATIONS:
        lang_code = "en"

    status = determine_trust_status(scheme, reference_date=reference_date)
    trans = TRUST_TRANSLATIONS[lang_code].get(
        status, TRUST_TRANSLATIONS["en"][status]
    )

    # Effective dates aggregation
    eff_from: date | None = None
    eff_until: date | None = None
    for ev in scheme.evidence:
        f = getattr(ev, "effective_from", None) or (ev.get("effective_from") if isinstance(ev, dict) else None)
        u = getattr(ev, "effective_until", None) or (ev.get("effective_until") if isinstance(ev, dict) else None)
        if f:
            if isinstance(f, str):
                try:
                    f = date.fromisoformat(f)
                except ValueError:
                    pass
            if isinstance(f, date):
                if eff_from is None or f < eff_from:
                    eff_from = f
        if u:
            if isinstance(u, str):
                try:
                    u = date.fromisoformat(u)
                except ValueError:
                    pass
            if isinstance(u, date):
                if eff_until is None or u > eff_until:
                    eff_until = u

    # Format effective period display
    if eff_from and eff_until:
        if lang_code == "mr":
            period_str = f"{eff_from.isoformat()} ते {eff_until.isoformat()} पर्यंत"
        elif lang_code == "hi":
            period_str = f"{eff_from.isoformat()} से {eff_until.isoformat()} तक"
        else:
            period_str = f"From {eff_from.isoformat()} to {eff_until.isoformat()}"
    elif eff_from:
        if lang_code == "mr":
            period_str = f"{eff_from.isoformat()} पासून लागू (चालू)"
        elif lang_code == "hi":
            period_str = f"{eff_from.isoformat()} से लागू (प्रभावी)"
        else:
            period_str = f"Effective from {eff_from.isoformat()} (Ongoing)"
    else:
        if lang_code == "mr":
            period_str = "वर्तमान आर्थिक वर्ष / शासकीय परिपत्रकानुसार"
        elif lang_code == "hi":
            period_str = "वर्तमान वित्तीय वर्ष / शासकीय परिपत्रक अनुसार"
        else:
            period_str = "Current financial cycle / operative circulars"

    # Format last verified date
    last_ver_str = None
    if scheme.last_verified_at:
        last_ver_str = scheme.last_verified_at.strftime("%Y-%m-%d %H:%M UTC")

    # Format official sources citations
    citations: list[SourceCitation] = []
    for src in scheme.sources:
        citations.append(
            SourceCitation(
                source_name=src.source_name,
                source_url=src.source_url,
                source_kind=src.source_kind,
                official_reference=getattr(src, "official_reference", None) or (src.source_name if "GR" in src.source_name else None),
                page_or_section=src.page_or_section,
                retrieved_at=src.retrieved_at.strftime("%Y-%m-%d") if src.retrieved_at else None,
            )
        )

    return SchemeTrustReport(
        scheme_id=scheme.scheme_id,
        trust_status=status,
        badge_label=trans["label"],
        badge_color=trans["color"],
        status_description=trans["desc"],
        last_verified_at=last_ver_str,
        effective_from=eff_from.isoformat() if eff_from else None,
        effective_until=eff_until.isoformat() if eff_until else None,
        effective_period_display=period_str,
        official_sources=citations,
        required_documents=scheme.required_documents,
        is_official_government_recommendation=False,
        trust_notice=TRUST_NOTICES.get(lang_code, TRUST_NOTICES["en"]),
        provenance_disclaimer=PROVENANCE_DISCLAIMERS.get(lang_code, PROVENANCE_DISCLAIMERS["en"]),
    )
