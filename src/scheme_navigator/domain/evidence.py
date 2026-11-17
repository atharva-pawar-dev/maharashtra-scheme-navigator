from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from scheme_navigator.domain.models import Language, RuleNode, SourceReference


class SchemeStatus(StrEnum):
    """Lifecycle status of a government scheme record in the catalogue."""

    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class RuleVerificationStatus(StrEnum):
    """Rigorous verification state of an individual eligibility rule condition.

    Note: Extraction by an automated tool or LLM does not constitute legal approval.
    """

    EXTRACTED_UNVERIFIED = "extracted_unverified"
    ANALYST_REVIEWED = "analyst_reviewed"
    LEGAL_APPROVED = "legal_approved"
    DISPUTED = "disputed"
    DEPRECATED = "deprecated"


class OfficialSourceType(StrEnum):
    """Authoritative official source classifications recognized in Scheme Navigator.

    Supports state Government Resolutions as well as central scheme guidelines,
    statutory legislation/rules, and gazetted departmental notifications.
    """

    GOVERNMENT_RESOLUTION = "government_resolution"
    CENTRAL_SCHEME_GUIDELINE = "central_scheme_guideline"
    STATE_SCHEME_GUIDELINE = "state_scheme_guideline"
    LEGISLATION_ACT_RULES = "legislation_act_rules"
    DEPARTMENTAL_NOTIFICATION = "departmental_notification"
    GAZETTE_NOTIFICATION = "gazette_notification"
    OFFICIAL_PORTAL = "official_portal"
    OFFICIAL_SCHEME_PAGE = "official_scheme_page"


class MultilingualText(BaseModel):
    """Standard multilingual text container for English, Marathi and Hindi text."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    en: str = Field(default="", max_length=2000)
    mr: str = Field(default="", max_length=2000)
    hi: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def at_least_one_language(self) -> "MultilingualText":
        if not (self.en or self.mr or self.hi):
            raise ValueError("MultilingualText requires at least one non-empty language text.")
        return self

    def for_language(self, language: Language | str) -> str:
        code = language.value if isinstance(language, Language) else str(language).lower()
        if code == "mr" and self.mr:
            return self.mr
        if code == "hi" and self.hi:
            return self.hi
        return self.en or self.mr or self.hi


class RuleEvidence(BaseModel):
    """Clause-level legal provenance linking an atomic eligibility condition to official sources.

    IMPORTANT LEGAL NOTE:
    The `source_document_sha256` checksum confirms data integrity and version identity of the
    retrieved source file against tampering or corruption. It does NOT independently establish
    legal validity, executive authority, or official government endorsement.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    condition_id: str = Field(
        pattern=r"^[a-z0-9_-]{2,80}$",
        description="Stable identifier linking this evidence to an atomic AST condition node.",
    )
    source_title: str = Field(
        min_length=2,
        max_length=240,
        description="Official title of the issuing source document.",
    )
    official_reference: str = Field(
        min_length=2,
        max_length=200,
        description="GR number, notification code, gazette issue, or statutory section citation.",
    )
    official_source_url: str = Field(
        min_length=8,
        max_length=2000,
        description="Authoritative HTTPS link to the primary government repository or portal.",
    )
    source_type: OfficialSourceType = OfficialSourceType.GOVERNMENT_RESOLUTION
    publication_date: date | None = None
    effective_from: date = Field(
        description="Date from which this condition legally took effect.",
    )
    effective_until: date | None = Field(
        default=None,
        description="Date when condition expired or was amended; None if currently operative.",
    )
    page_or_section: str | None = Field(
        default=None,
        max_length=300,
        description="Exact page, schedule, clause, or paragraph locator in the source document.",
    )
    verbatim_excerpt: str = Field(
        min_length=5,
        max_length=5000,
        description="Unaltered verbatim quote from the official government source.",
    )
    excerpt_language: Language = Language.MR
    translated_excerpt: str | None = Field(
        default=None,
        max_length=5000,
        description="Optional human-verified or official translation of the excerpt.",
    )
    translation_provenance: str | None = Field(
        default=None,
        max_length=200,
        description="Translation source (e.g. 'official_english_gazette', 'certified_translator').",
    )
    source_document_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$",
        description="SHA-256 hash verifying source content integrity and version identity.",
    )
    verification_status: RuleVerificationStatus = RuleVerificationStatus.EXTRACTED_UNVERIFIED
    verified_by: str | None = Field(
        default=None,
        max_length=120,
        description="Named human policy analyst or legal reviewer who verified this clause.",
    )
    verification_timestamp: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("official_source_url")
    @classmethod
    def require_https_source(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("Official source URLs must use secure HTTPS.")
        return value

    @model_validator(mode="after")
    def validate_verification_integrity(self) -> "RuleEvidence":
        if self.effective_until is not None and self.effective_until < self.effective_from:
            raise ValueError(
                f"effective_until ({self.effective_until}) cannot precede effective_from ({self.effective_from})."
            )
        if self.verification_status == RuleVerificationStatus.LEGAL_APPROVED:
            if not self.verified_by or not self.verified_by.strip():
                raise ValueError("Legally approved rule evidence requires an identified reviewer in verified_by.")
            if self.verification_timestamp is None:
                raise ValueError("Legally approved rule evidence requires a verification_timestamp.")
            reviewer_lower = self.verified_by.casefold()
            disallowed = {"demo", "test", "local", "synthetic", "placeholder", "unknown"}
            if any(term in reviewer_lower for term in disallowed):
                raise ValueError(
                    f"Reviewer '{self.verified_by}' is not recognized as a legitimate approving authority."
                )
        return self


class DocumentRequirement(BaseModel):
    """Authoritative document checklist linked to issuing authorities and RTS timelines."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    canonical_document_id: str = Field(pattern=r"^[a-z0-9_-]{2,80}$")
    display_name: MultilingualText
    issuing_authority: MultilingualText
    rts_service_name: str | None = None
    statutory_delivery_days: int | None = Field(default=None, ge=1, le=365)
    financial_year_sensitive: bool = False
    acceptable_alternatives: list[str] = Field(default_factory=list, max_length=20)
    evidence: list[RuleEvidence] = Field(default_factory=list, max_length=10)


class LegalApprovalMetadata(BaseModel):
    """Audit trail verifying human legal review and government authorization."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reviewer_id: str = Field(min_length=3, max_length=120)
    reviewer_role: Literal["legal_officer", "policy_analyst", "gazetted_officer", "system_maintainer"]
    approval_reference: str = Field(min_length=5, max_length=200)
    gazette_or_notification_reference: str = Field(min_length=5, max_length=200)
    approval_timestamp: datetime
    verification_checklist_confirmed: bool = False
    digital_signature_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_non_demo_approval(self) -> "LegalApprovalMetadata":
        ref = self.approval_reference.casefold()
        rev = self.reviewer_id.casefold()
        disallowed = {"demo", "fixture", "synthetic", "not_for_production", "test"}
        if any(term in ref for term in disallowed) or any(term in rev for term in disallowed):
            raise ValueError("Demo or synthetic references cannot constitute legal approval.")
        if not self.verification_checklist_confirmed:
            raise ValueError("All statutory criteria in the verification checklist must be confirmed.")
        return self


class EvidenceCoverageReport(BaseModel):
    """Detailed audit report inspecting whether an eligibility rule AST is fully grounded in evidence."""

    model_config = ConfigDict(extra="forbid")

    is_valid: bool
    ast_condition_ids: list[str]
    evidence_condition_ids: list[str]
    missing_evidence_ids: list[str]
    orphan_evidence_ids: list[str]
    duplicate_ast_condition_ids: list[str]
    duplicate_evidence_condition_ids: list[str]
    unverified_condition_ids: list[str]
    notes: list[str] = Field(default_factory=list)

    @property
    def coverage_ratio(self) -> float:
        if not self.ast_condition_ids:
            return 1.0
        covered = len(self.ast_condition_ids) - len(self.missing_evidence_ids)
        return max(0.0, min(1.0, covered / len(self.ast_condition_ids)))


def collect_ast_condition_ids(node: RuleNode) -> list[str]:
    """Recursively collect condition IDs declared on atomic leaf nodes in a RuleNode AST."""
    collected: list[str] = []
    if node.op in {"all", "any", "not"}:
        for child in node.children:
            collected.extend(collect_ast_condition_ids(child))
    else:
        cid = getattr(node, "condition_id", None)
        if cid:
            collected.append(cid)
    return collected


def validate_rule_evidence_coverage(
    rule: RuleNode,
    evidence_list: list[RuleEvidence],
    *,
    require_all_leaves_have_ids: bool = False,
    require_legal_approval: bool = False,
) -> EvidenceCoverageReport:
    """Validate cross-referencing between a rule AST and its condition-level evidence package.

    Detects:
    1. Missing evidence (AST condition declared with no evidence record).
    2. Orphan evidence (Evidence supplied for a condition ID not present in the AST).
    3. Duplicate condition IDs in AST or evidence list.
    4. Unverified evidence entries.
    """
    ast_ids: list[str] = []
    duplicate_ast_ids: list[str] = []
    seen_ast: set[str] = set()

    # Leaf audit
    leaves_missing_id = 0

    def traverse(curr: RuleNode):
        nonlocal leaves_missing_id
        if curr.op in {"all", "any", "not"}:
            for child in curr.children:
                traverse(child)
        else:
            cid = getattr(curr, "condition_id", None)
            if cid:
                if cid in seen_ast:
                    duplicate_ast_ids.append(cid)
                seen_ast.add(cid)
                ast_ids.append(cid)
            else:
                leaves_missing_id += 1

    traverse(rule)

    ev_ids: list[str] = []
    duplicate_ev_ids: list[str] = []
    unverified_ids: list[str] = []
    seen_ev: set[str] = set()

    for item in evidence_list:
        ev = RuleEvidence.model_validate(item) if isinstance(item, dict) else item
        cid = getattr(ev, "condition_id", None)
        if not cid:
            continue
        if cid in seen_ev:
            duplicate_ev_ids.append(cid)
        seen_ev.add(cid)
        ev_ids.append(cid)
        status = getattr(ev, "verification_status", None)
        if require_legal_approval and status != RuleVerificationStatus.LEGAL_APPROVED:
            unverified_ids.append(cid)

    missing_evidence = [cid for cid in ast_ids if cid not in seen_ev]
    orphan_evidence = [cid for cid in ev_ids if cid not in seen_ast]

    notes: list[str] = []
    if leaves_missing_id > 0:
        notes.append(f"{leaves_missing_id} atomic leaf rule(s) do not declare a condition_id.")
    if require_all_leaves_have_ids and leaves_missing_id > 0:
        notes.append("STRICT MODE: Every atomic condition must declare a stable condition_id.")

    is_valid = (
        len(missing_evidence) == 0
        and len(orphan_evidence) == 0
        and len(duplicate_ast_ids) == 0
        and len(duplicate_ev_ids) == 0
        and len(unverified_ids) == 0
        and (not require_all_leaves_have_ids or leaves_missing_id == 0)
    )

    return EvidenceCoverageReport(
        is_valid=is_valid,
        ast_condition_ids=ast_ids,
        evidence_condition_ids=ev_ids,
        missing_evidence_ids=missing_evidence,
        orphan_evidence_ids=orphan_evidence,
        duplicate_ast_condition_ids=duplicate_ast_ids,
        duplicate_evidence_condition_ids=duplicate_ev_ids,
        unverified_condition_ids=unverified_ids,
        notes=notes,
    )
