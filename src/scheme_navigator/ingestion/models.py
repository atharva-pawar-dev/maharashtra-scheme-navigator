from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class IngestionSourceKind(StrEnum):
    GOVERNMENT_RESOLUTION = "government_resolution"
    DEPARTMENTAL_PORTAL = "departmental_portal"
    MAHADBT_SCHEME_PAGE = "mahadbt_scheme_page"
    AAPLE_SARKAR_PAGE = "aaplesarkar_page"
    MYSCHEME_AGGREGATOR = "myscheme_aggregator"
    OFFICIAL_NOTIFICATION = "official_notification"
    GAZETTE_ORDER = "gazette_order"


class IngestionReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    UNDER_ANALYST_REVIEW = "under_analyst_review"
    READY_FOR_LEGAL_GATE = "ready_for_legal_gate"
    REJECTED = "rejected"
    DISPUTED = "disputed"


class AmendmentType(StrEnum):
    BASE_RESOLUTION = "base_resolution"
    AMENDMENT = "amendment"
    SHUDDHIPATRA = "shuddhipatra"
    CLARIFICATION = "clarification"
    BENEFIT_REVISION = "benefit_revision"
    DISABILITY_REVISION = "disability_revision"
    CONTINUATION_ORDER = "continuation_order"


class IngestedSnapshot(BaseModel):
    """Immutable snapshot of an ingested official government source document."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    snapshot_id: str = Field(min_length=8, max_length=64)
    source_url: str = Field(min_length=8, max_length=2000)
    final_url: str = Field(min_length=8, max_length=2000)
    source_kind: IngestionSourceKind
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_size: int = Field(ge=0)
    retrieved_at: str
    publication_date: str | None = None
    official_reference: str | None = None
    title: str = Field(max_length=500)
    extracted_text: str
    is_aggregator: bool = False
    etag: str | None = None
    last_modified: str | None = None
    notes: str | None = None


class DocumentChangeEvent(BaseModel):
    """Audit record capturing changes detected when re-retrieving an official source URL."""

    model_config = ConfigDict(extra="forbid")

    change_id: str
    source_url: str
    previous_sha256: str
    new_sha256: str
    detected_at: str
    previous_snapshot_id: str
    new_snapshot_id: str
    change_type: str = "content_updated"
    summary: str


class SchemeAlias(BaseModel):
    """Registered alias or vernacular name for a scheme in Maharashtra."""

    model_config = ConfigDict(extra="forbid")

    alias: str
    language: str = "en"
    alias_type: str = "vernacular_title"  # vernacular_title, acronym, portal_alias, department_title


class DuplicateCandidateMatch(BaseModel):
    """Potential duplicate match against an existing scheme record."""

    model_config = ConfigDict(extra="forbid")

    canonical_scheme_id: str
    canonical_name: str
    matched_term: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    reason: str
    is_distinct_branch: bool = False


class DuplicateDetectionReport(BaseModel):
    """Report inspecting whether a candidate scheme name or alias overlaps with existing records."""

    model_config = ConfigDict(extra="forbid")

    query_title: str
    department: str | None = None
    potential_duplicates: list[DuplicateCandidateMatch] = Field(default_factory=list)
    is_probable_duplicate: bool = False
    recommendation: str  # "create_new", "merge_with_existing", "requires_analyst_review"
    notes: list[str] = Field(default_factory=list)


class AmendmentRecord(BaseModel):
    """Chronological amendment entry in a scheme's legislative/GR lineage."""

    model_config = ConfigDict(extra="forbid")

    order_index: int
    gr_date: str
    gr_number: str
    title: str
    amendment_type: AmendmentType
    source_url: str
    source_sha256: str
    operative_clauses: list[str] = Field(default_factory=list)
    superseded_clauses: list[str] = Field(default_factory=list)
    verbatim_mr: str | None = None
    translation_en: str | None = None


class SupersededRuleNotice(BaseModel):
    """Record identifying a rule or eligibility condition superseded by a subsequent GR."""

    model_config = ConfigDict(extra="forbid")

    condition_id: str
    original_gr_reference: str
    superseding_gr_reference: str
    effective_date: str
    original_value: Any
    revised_value: Any
    description: str


class SchemeLineageReport(BaseModel):
    """Complete chronological lineage of a scheme across all operative and amending GRs."""

    model_config = ConfigDict(extra="forbid")

    scheme_id: str
    canonical_name: str
    administering_department: str
    base_resolution: AmendmentRecord | None = None
    amendments: list[AmendmentRecord] = Field(default_factory=list)
    superseded_rules: list[SupersededRuleNotice] = Field(default_factory=list)
    unresolved_conflicts: list[str] = Field(default_factory=list)
    current_operative_gr_references: list[str] = Field(default_factory=list)


class IngestionReviewItem(BaseModel):
    """Item in the human-review queue for newly ingested or updated scheme sources."""

    model_config = ConfigDict(extra="forbid")

    item_id: str
    source_url: str
    source_title: str
    source_kind: IngestionSourceKind
    sha256: str
    retrieved_at: str
    review_status: IngestionReviewStatus = IngestionReviewStatus.PENDING_REVIEW
    extracted_scheme_data: dict[str, Any] = Field(default_factory=dict)
    reviewer_id: str | None = None
    review_notes: str | None = None
    created_at: str
    updated_at: str
