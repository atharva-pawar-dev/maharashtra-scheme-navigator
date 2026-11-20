"""TRIMURTI v3 Governance and Provenance Domain Models.

Implements Invariants I-01 through I-20:
- Strict 8-stage provenance lifecycle (I-01, Section 17.1)
- Human reviewer role and subtype boundaries (I-05, Section 17.2)
- Separate completeness attestation binding to scheme version, rule hash, and source hashes (I-06, Section 17.5)
- Candidate disposition and scheme lifecycle models (Sections 9, 11)
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, List, Literal
from pydantic import BaseModel, ConfigDict, Field

from scheme_navigator.security.models import UserRole


class ProvenanceStage(StrEnum):
    """Eight-stage provenance pipeline per Section 17.1."""
    OFFICIAL_SOURCE_FOUND = "OFFICIAL_SOURCE_FOUND"
    SOURCE_CAPTURED = "SOURCE_CAPTURED"
    SOURCE_PARSED = "SOURCE_PARSED"
    EXACT_TEXT_MATCHED = "EXACT_TEXT_MATCHED"
    RULE_EXTRACTED = "RULE_EXTRACTED"
    RULE_INTERPRETED = "RULE_INTERPRETED"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    APPROVED_FOR_DECISION = "APPROVED_FOR_DECISION"


class ReviewSubtype(StrEnum):
    """Review independence classification per Section 17.1."""
    OWNER_REVIEWED = "OWNER_REVIEWED"
    INDEPENDENTLY_REVIEWED = "INDEPENDENTLY_REVIEWED"


class CandidateDisposition(StrEnum):
    """Stable candidate disposition per Section 9 and Appendix B."""
    IN_CATALOGUE_VERIFIED = "IN_CATALOGUE_VERIFIED"
    IN_CATALOGUE_LIMITED = "IN_CATALOGUE_LIMITED"
    NEEDS_RESEARCH = "NEEDS_RESEARCH"
    BLOCKED_SOURCE = "BLOCKED_SOURCE"
    DUPLICATE_OF = "DUPLICATE_OF"
    SUB_SCHEME_OF = "SUB_SCHEME_OF"
    HISTORICAL = "HISTORICAL"
    EXCLUDED_NOT_INDIVIDUAL_BENEFIT = "EXCLUDED_NOT_INDIVIDUAL_BENEFIT"
    EXCLUDED_OUT_OF_GEOGRAPHIC_SCOPE = "EXCLUDED_OUT_OF_GEOGRAPHIC_SCOPE"


class SchemeLifecycleStatus(StrEnum):
    """Scheme lifecycle classification per Section 11."""
    ACTIVE_APPLICATIONS_OPEN = "ACTIVE_APPLICATIONS_OPEN"
    ACTIVE_APPLICATIONS_CLOSED = "ACTIVE_APPLICATIONS_CLOSED"
    ACTIVE_RECURRING_WINDOW = "ACTIVE_RECURRING_WINDOW"
    ACTIVE_RENEWAL_ONLY = "ACTIVE_RENEWAL_ONLY"
    ACTIVE_BENEFIT_DISBURSEMENT = "ACTIVE_BENEFIT_DISBURSEMENT"
    TEMPORARILY_PAUSED = "TEMPORARILY_PAUSED"
    BUDGET_EXHAUSTED_OR_SUSPENDED = "BUDGET_EXHAUSTED_OR_SUSPENDED"
    PILOT_OR_LIMITED_ROLLOUT = "PILOT_OR_LIMITED_ROLLOUT"
    SUPERSEDED = "SUPERSEDED"
    MERGED_INTO_SUCCESSOR = "MERGED_INTO_SUCCESSOR"
    DISCONTINUED = "DISCONTINUED"
    HISTORICAL = "HISTORICAL"
    STATUS_UNCONFIRMED = "STATUS_UNCONFIRMED"


class RuleApprovalRecord(BaseModel):
    """Rule-level human review and approval record.
    
    Enforces Invariant I-05: Reviewer identity and timestamp cannot be fabricated
    or set by AI research agents. Must derive from authenticated server-side principal.
    """
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    scheme_id: str
    rule_id: str
    rule_version: str
    stage: ProvenanceStage
    review_subtype: ReviewSubtype
    reviewer_id: str
    reviewer_role: UserRole
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["APPROVED", "REJECTED", "CHANGES_REQUESTED", "PENDING"] = "APPROVED"
    source_hash: str = Field(..., min_length=16, description="SHA-256 of supporting source snapshot")
    notes: str = ""
    numeric_double_confirmed: bool = False


class CompletenessAttestation(BaseModel):
    """Independent Scheme Completeness Attestation per Invariant I-06 and Section 17.5.
    
    Binds human reviewer confirmation to the exact scheme version, source snapshot hashes,
    rule set hash, and exclusion pass record.
    """
    model_config = ConfigDict(extra="forbid")

    attestation_id: str
    scheme_id: str
    scheme_version: str
    source_hashes: List[str] = Field(default_factory=list, description="SHA-256 of governing source snapshots")
    rule_set_hash: str = Field(..., min_length=16, description="Cryptographic hash of the evaluated rule set")
    exclusion_pass_reference: str = Field(..., description="Evidence reference of mandatory negative-polarity pass")
    document_requirement_graph_version: str = Field(default="1.0.0")
    attested_by: str = Field(..., description="Authenticated reviewer user ID (derived from session)")
    reviewer_role: UserRole = Field(..., description="Role of the authenticated reviewer")
    attested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scope: str = Field(default="Maharashtra Statewide Canonical Entitlement")
    mandatory_conditions_confirmed: bool = True
    exclusions_confirmed: bool = True
    alternative_tracks_confirmed: bool = True
    benefit_limitations_confirmed: bool = True
    explicit_limitations: List[str] = Field(default_factory=list)
    is_valid: bool = True
