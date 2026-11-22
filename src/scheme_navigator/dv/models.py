"""TRIMURTI / MSN-DV-001 Document Readiness Data Models (Annex A & §4.2–§4.4).

Defines:
- DocTypeProfile: Global definition of a document type.
- RequirementSlot: Scheme-specific requirement representing a need.
- RequirementTrustTier: Traceability and governance trust tiers.
- SlotEvaluation & NeedsSummary: Denominator honesty counting engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RequirementKind(str, Enum):
    MANDATORY = "MANDATORY"
    CONDITIONAL = "CONDITIONAL"
    OPTIONAL = "OPTIONAL"


class RequirementTrustTier(str, Enum):
    """Trust tiers for requirement slots (§4.4)."""
    APPROVED = "APPROVED"                    # Human-attested, bound to requirement hash
    SOURCE_VERIFIED = "SOURCE_VERIFIED"      # Official source quote + hash verified; human review pending
    SECONDARY_ONLY = "SECONDARY_ONLY"        # Not established by primary source
    UNDER_RESEARCH = "UNDER_RESEARCH"        # Active research in progress
    CONFLICTING = "CONFLICTING"              # Conflicting official sources
    UNKNOWN = "UNKNOWN"                      # Non-pilot or unconfirmed


class SlotState(str, Enum):
    """State of an individual slot for a given citizen (§A3)."""
    NOT_STARTED = "NOT_STARTED"
    CITIZEN_HAS_NONE = "CITIZEN_HAS_NONE"
    RECEIVED = "RECEIVED"
    NEEDS_FIXING = "NEEDS_FIXING"
    UNSURE = "UNSURE"
    SATISFIED = "SATISFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    REQUIREMENT_UNCONFIRMED = "REQUIREMENT_UNCONFIRMED"


@dataclass(frozen=True)
class FieldSchemaItem:
    field_id: str
    field_type: str                         # string, date, amount, number, enum
    sensitivity: str                        # PUBLIC, CONFIDENTIAL, STRICTLY_PRIVATE
    label_en: str
    label_mr: str
    label_hi: str


@dataclass(frozen=True)
class DocTypeProfile:
    """Global specification of what a document type IS and how to read it (§4.2)."""
    id: str                                  # e.g. DOC-INCOME-CERT
    names: Dict[str, str]                    # en, mr, hi
    plain_description: Dict[str, str]        # en, mr, hi
    where_to_get: Dict[str, str]             # en, mr, hi (where, fee, typical days)
    fields: List[FieldSchemaItem] = field(default_factory=list)
    version: str = "1.0.0"


@dataclass(frozen=True)
class AcceptedDocType:
    doctype_id: str
    constraints: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None


@dataclass(frozen=True)
class RequirementSlot:
    """Scheme-specific need that may be satisfied by one or more document types (§4.2)."""
    slot_id: str
    scheme_id: str
    requirement_version: str
    need_label: Dict[str, str]               # en, mr, hi
    kind: RequirementKind
    accepted: List[AcceptedDocType]          # Any one of these satisfies the slot (Alternatives)
    trust_tier: RequirementTrustTier
    source_type: str                         # GOVERNMENT_RESOLUTION, OFFICIAL_PORTAL, ACT, GAZETTE
    source_reference: str                    # GR number, circular date, portal URL
    source_quote: Optional[str] = None       # Verbatim excerpt from official document
    evidence_sha256: Optional[str] = None    # SHA-256 of the official source PDF/GR
    applicability_condition: Optional[Dict[str, Any]] = None  # JSON Logic or simple dict condition
    validity_months: Optional[int] = None    # Certificate validity duration in months
    how_to_get: Optional[Dict[str, str]] = None


@dataclass
class SlotEvaluation:
    slot: RequirementSlot
    state: SlotState
    is_applicable: Optional[bool]            # True, False, or None if UNKNOWN
    satisfied_by_doc_id: Optional[str] = None
    satisfied_by_doctype_id: Optional[str] = None
    explanation_key: str = "ladder.received"


@dataclass
class NeedsSummary:
    """Denominator Honesty counting result (§4.3).
    
    Formula:
    'N of M needs covered'
    M = applicable mandatory slots + conditional slots whose applicability is TRUE.
    Separate buckets for unknown conditional and unconfirmed requirements.
    """
    total_applicable_needs_m: int
    satisfied_needs_n: int
    pending_needs_count: int
    unknown_conditional_count: int
    unconfirmed_requirements_count: int
    evaluations: List[SlotEvaluation] = field(default_factory=list)

    @property
    def is_all_covered(self) -> bool:
        return self.total_applicable_needs_m > 0 and self.satisfied_needs_n >= self.total_applicable_needs_m

    def get_headline_text(self, scheme_name: str, lang: str = "mr") -> str:
        """Formatted trilingual headline per Annex C §C2."""
        if lang == "en":
            return f"To apply for {scheme_name} you need {self.total_applicable_needs_m} papers. You have {self.satisfied_needs_n}."
        elif lang == "hi":
            return f"{scheme_name} के लिए आपको {self.total_applicable_needs_m} कागज़ात चाहिए। आपके पास {self.satisfied_needs_n} तैयार हैं।"
        else: # mr
            return f"{scheme_name} साठी तुम्हाला {self.total_applicable_needs_m} कागदपत्रे लागतील. तुमच्याकडे {self.satisfied_needs_n} तयार आहेत."
