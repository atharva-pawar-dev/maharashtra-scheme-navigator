"""Catalogue v2 Data Model for Maharashtra Scheme Navigator.

Strict Pydantic v2 domain schemas implementing verified provenance,
canonical profile vocabulary enforcement, substantive criteria guards,
and JSON Schema export.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Dict, List, Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
    computed_field,
)

from scheme_navigator.domain.profile_vocabulary import (
    CANONICAL_PROFILE_VOCABULARY,
    is_field_substantive,
)


class SchemeLevel(StrEnum):
    STATE = "state"
    CENTRALLY_SPONSORED = "centrally_sponsored_implemented_in_MH"
    CENTRAL_APPLICABLE = "central_applicable"


class SchemeStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    PAUSED = "paused"
    MERGED = "merged"
    UNKNOWN = "unknown"


class SourceTier(StrEnum):
    TIER_1 = "tier_1"  # Authoritative state/central portals, official GRs, MahaDBT
    TIER_2 = "tier_2"  # Official aggregators (myScheme, India.gov.in, central ministries)
    TIER_3 = "tier_3"  # Cross-check/discovery ONLY (PublicServicesMap, news, third party)


class VerificationStatus(StrEnum):
    VERIFIED_PRIMARY = "verified_primary"          # All mandatory criteria sourced from Tier 1 with quotes
    VERIFIED_CROSS = "verified_cross"              # Tier 2 verified + second independent agreement
    SINGLE_SOURCE_SECONDARY = "single_source_secondary" # Single secondary source, confidence <= 0.6
    UNVERIFIED = "unverified"                      # Lacking verbatim quotes or conflicting


class CriterionStatus(StrEnum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"


class DocGroupMode(StrEnum):
    ALL_OF = "ALL_OF"
    ANY_OF = "ANY_OF"


class SourceEvidence(BaseModel):
    """Provenance tracking for official source materials cached under data/raw/."""
    model_config = ConfigDict(extra="forbid")

    url: str = Field(..., description="Canonical URL of government document or portal")
    tier: SourceTier = Field(..., description="Source authority tier (Tier 1, 2, or 3)")
    retrieved_at: datetime = Field(..., description="Timestamp when raw content was crawled")
    sha256: str = Field(..., min_length=64, max_length=64, description="Cryptographic SHA-256 of raw file")
    title: str = Field(..., description="Official title of page, notification, or GR")
    language: Literal["mr", "en", "hi"] = Field(default="mr")
    raw_path: str = Field(..., description="Relative path under data/raw/ where content is cached")


class CriterionEvidence(BaseModel):
    """Verbatim quote and provenance supporting a single eligibility criterion."""
    model_config = ConfigDict(extra="forbid")

    quote_original: str = Field(..., min_length=3, description="Exact verbatim text snippet from source")
    source_url: str = Field(..., description="URL of source")
    tier: SourceTier = Field(..., description="Tier of source")
    gr_ref: str | None = Field(default=None, description="Government Resolution (GR) number and date")

    @field_validator("quote_original")
    @classmethod
    def quote_must_not_be_placeholder(cls, v: str) -> str:
        s = v.strip().casefold()
        if s in {"none", "n/a", "placeholder", "tbd", "unknown", ""}:
            raise ValueError("quote_original must be a substantive verbatim quote")
        return v


class Criterion(BaseModel):
    """Individual eligibility condition evaluated by the deterministic rule engine."""
    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(..., description="Unique criterion identifier, e.g. c_ladki_age_min")
    field: str = Field(..., description="Field name from Canonical Profile Vocabulary")
    operator: Literal["eq", "ne", "gt", "gte", "lt", "lte", "in", "exists"]
    value: Any = Field(..., description="Target comparison value")
    unit: str | None = Field(default=None, description="Unit of measurement, e.g. INR, years, ha")
    mandatory: bool = Field(default=True, description="True for hard statutory rules; False for advisory")
    applies_if: Dict[str, Any] | None = Field(default=None, description="Conditional evaluation guard")
    plain_en: str = Field(..., description="Human-readable condition in English")
    plain_mr: str = Field(..., description="Human-readable condition in Marathi")
    evidence: CriterionEvidence | None = Field(default=None, description="Verbatim source evidence")
    verifiable_by_doc_types: List[str] = Field(default_factory=list, description="Associated document types")
    interview_question_id: str | None = Field(default=None, description="Target slot-filling question")
    status: CriterionStatus = Field(default=CriterionStatus.UNVERIFIED)

    @field_validator("field")
    @classmethod
    def field_must_be_in_vocabulary(cls, v: str) -> str:
        if v not in CANONICAL_PROFILE_VOCABULARY:
            raise ValueError(f"Field '{v}' is not registered in the Canonical Profile Vocabulary")
        return v

    @property
    def is_substantive(self) -> bool:
        return is_field_substantive(self.field)


class DocGroup(BaseModel):
    group_id: str
    mode: DocGroupMode = DocGroupMode.ANY_OF


class DocRequirement(BaseModel):
    """Scheme-specific document requirement mapped to multimodal extraction rules."""
    model_config = ConfigDict(extra="forbid")

    doc_type: str = Field(..., description="Canonical document type (income_certificate, domicile_certificate, etc.)")
    label_en: str
    label_mr: str
    mandatory: bool = Field(default=True)
    condition: str | None = Field(default=None, description="Condition description if conditional")
    group: DocGroup | None = Field(default=None, description="Alternative grouping (ALL_OF or ANY_OF)")
    validity_rule: str | None = Field(default=None, description="Sourced validity constraint; null if unsourced")
    issuing_authority: str | None = Field(default=None)
    where_to_obtain: str | None = Field(default=None, description="Official portal/service e.g. Aaple Sarkar")
    evidence: CriterionEvidence | None = Field(default=None)


class LegalBasis(BaseModel):
    """Government Resolution (GR), Gazette notification, or Act governing the scheme."""
    model_config = ConfigDict(extra="forbid")

    gr_number: str
    date: date
    title: str
    url: str | None = None
    supersedes: str | None = Field(default=None, description="Prior GR number superseded by this instrument")


class BenefitDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["cash_transfer", "subsidy", "scholarship", "in_kind", "insurance", "loan", "other"]
    amount_text: str
    amount_value: float | None = None
    frequency: Literal["one_time", "monthly", "quarterly", "annual", "academic_year", "incident_based", "unknown"] = "unknown"
    duration: str | None = None


class ApplicationDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["online", "offline", "hybrid", "csc_only"]
    portal: str | None = None
    url: str | None = None
    window_open: date | None = None
    window_close: date | None = None
    rolling: bool = True
    fee: float | None = Field(default=0.0)


class VerificationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    last_verified_at: datetime | None = None
    conflicts: List[str] = Field(default_factory=list)
    reviewer_notes: str | None = None


class SchemeV2(BaseModel):
    """Verified Catalogue v2 Canonical Scheme Schema."""
    model_config = ConfigDict(extra="forbid")

    scheme_id: str = Field(..., pattern=r"^[a-z0-9-]+$", description="Stable lowercase slug")
    name_en: str
    name_mr: str
    department: str
    implementing_body: str
    level: SchemeLevel = SchemeLevel.STATE
    categories: List[str] = Field(default_factory=list)
    status: SchemeStatus = SchemeStatus.ACTIVE
    benefit: BenefitDetails
    description_en: str
    description_mr: str
    translation_method: Dict[str, Literal["source", "machine"]] = Field(
        default_factory=lambda: {"name": "source", "description": "source"}
    )
    application: ApplicationDetails
    eligibility: List[Criterion] = Field(default_factory=list)
    exclusions: List[Criterion] = Field(default_factory=list)
    eligibility_notes: str | None = None
    required_documents: List[DocRequirement] = Field(default_factory=list)
    how_to_apply_steps: List[str] = Field(default_factory=list)
    grievance_helpline: str | None = None
    legal_basis: List[LegalBasis] = Field(default_factory=list)
    sources: List[SourceEvidence] = Field(default_factory=list)
    verification: VerificationMeta = Field(default_factory=VerificationMeta)
    catalogue_version: str = "2.0.0"
    jurisdiction_scope: str | None = None
    jurisdiction_ids: List[str] = Field(default_factory=list)
    included_local_bodies: List[str] = Field(default_factory=list)
    excluded_local_bodies: List[str] = Field(default_factory=list)
    required_residency_years: int | None = None
    funding_type: str | None = None
    application_window_status: str | None = None

    @computed_field
    @property
    def substantive_criteria_count(self) -> int:
        """Count substantive criteria excluding residency and nationality."""
        return sum(1 for c in self.eligibility if c.is_substantive)

    @computed_field
    @property
    def eligibility_incomplete(self) -> bool:
        """Hard Validator: Auto-flag incomplete if fewer than 2 sourced substantive criteria exist.
        
        Under Prime Directive 2:
        A scheme whose only substantive rule is residency/nationality, or that has fewer than
        2 sourced substantive criteria, or has any mandatory criterion marked unverified,
        can never produce an ELIGIBLE result.
        """
        # Fewer than 2 substantive criteria
        if self.substantive_criteria_count < 2:
            return True
        # Any mandatory criterion is unverified or lacks evidence
        for c in self.eligibility:
            if c.mandatory:
                if c.status != CriterionStatus.VERIFIED or c.evidence is None:
                    return True
        return False

    @model_validator(mode="after")
    def validate_verified_invariants(self) -> "SchemeV2":
        """CI / Runtime Invariant: A scheme marked verified cannot have residency-only rules."""
        is_verified = self.verification.status in (
            VerificationStatus.VERIFIED_PRIMARY,
            VerificationStatus.VERIFIED_CROSS,
        )
        if is_verified:
            if self.substantive_criteria_count < 2:
                raise ValueError(
                    f"Scheme '{self.scheme_id}' is marked {self.verification.status} "
                    f"but has only {self.substantive_criteria_count} substantive criteria! "
                    "A verified scheme must have at least 2 substantive criteria."
                )
            if self.eligibility_incomplete:
                raise ValueError(
                    f"Scheme '{self.scheme_id}' is marked {self.verification.status} "
                    "but has eligibility_incomplete=True. Verified schemes cannot be incomplete."
                )
        return self
