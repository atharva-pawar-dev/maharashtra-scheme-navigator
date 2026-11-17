from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
from hashlib import sha256
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Language(StrEnum):
    EN = "en"
    MR = "mr"
    HI = "hi"


class EligibilityStatus(StrEnum):
    ELIGIBLE = "eligible"
    PARTIAL = "partial"
    INELIGIBLE = "ineligible"
    NEEDS_INFORMATION = "needs_information"
    NEEDS_REVIEW = "needs_review"


class CitizenProfile(BaseModel):
    """Minimized profile used for eligibility checks; deliberately has no Aadhaar number field."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=120)
    date_of_birth: date | None = None
    age_years: int | None = Field(default=None, ge=0, le=120)
    gender: Literal["female", "male", "other", "prefer_not_to_say"] | None = None
    resident_state: str | None = Field(default=None, max_length=80)
    district: str | None = Field(default=None, max_length=80)
    annual_family_income: int | None = Field(default=None, ge=0, le=100_000_000)
    caste_category: str | None = Field(default=None, max_length=80)
    is_student: bool | None = None
    education_level: str | None = Field(default=None, max_length=80)
    has_disability: bool | None = None
    disability_percentage: int | None = Field(default=None, ge=0, le=100)
    bpl: bool | None = None
    receiving_other_pension: bool | None = None
    aadhaar_linked_bank_account: bool | None = None
    has_land: bool | None = None
    marital_status: Literal["single", "married", "widowed", "divorced", "abandoned", "prefer_not_to_say"] | None = None
    occupation: str | None = Field(default=None, max_length=100)
    landholding_hectares: float | None = Field(default=None, ge=0, le=100_000)
    ration_card_type: Literal["aay", "bpl_yellow", "apl_orange", "white", "none"] | None = None
    documents_available: list[str] = Field(default_factory=list, max_length=30)
    local_government_type: str | None = Field(default=None, max_length=80)
    municipal_corporation: str | None = Field(default=None, max_length=100)
    municipal_council: str | None = Field(default=None, max_length=100)
    nagar_panchayat: str | None = Field(default=None, max_length=100)
    gram_panchayat: str | None = Field(default=None, max_length=100)
    cantonment_board: str | None = Field(default=None, max_length=100)
    local_body_id: str | None = Field(default=None, max_length=100)
    ward: str | None = Field(default=None, max_length=100)
    locality: str | None = Field(default=None, max_length=120)
    residence_years: int | None = Field(default=None, ge=0, le=120)
    pin_code: str | None = Field(default=None, max_length=10)
    location_confirmed: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def strip_metadata_envelope(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # If wrapped in a response/envelope like {"session_id": ..., "profile": {...}, "provenance": ...}
            if "profile" in data and isinstance(data["profile"], dict):
                inner = dict(data["profile"])
                for k, v in data.items():
                    if k not in ("profile", "session_id", "provenance") and k not in inner:
                        inner[k] = v
                data = inner
            cleaned = {k: v for k, v in data.items() if k not in ("session_id", "provenance", "profile")}
            if "age" in cleaned and "age_years" not in cleaned:
                cleaned["age_years"] = cleaned.pop("age")
            elif "age" in cleaned and cleaned.get("age_years") is None:
                cleaned["age_years"] = cleaned.pop("age")
            allowed = set(CitizenProfile.model_fields.keys())
            return {k: val for k, val in cleaned.items() if k in allowed}
        return data

    @field_validator("name")
    @classmethod
    def name_is_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("name cannot be blank")
        return value

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip().casefold()
            if cleaned in {"prefer_not_to_say", "prefer not to say", "unspecified", "unknown", "don't know", "dont_know", ""}:
                return None
            return cleaned
        return value

    @field_validator("resident_state")
    @classmethod
    def normalize_state(cls, value: str | None) -> str | None:
        return value.strip().casefold() if value else value

    def age_at(self, reference_date: date | None = None) -> int | None:
        """Calculate age in whole years relative to an explicit reference cut-off date.

        If reference_date is None, date.today() is used.
        If date_of_birth is known, exact calendar age as of reference_date is computed.
        If date_of_birth is missing:
          - If reference_date is None or date.today(), age_years is returned.
          - If reference_date is a different cut-off date, returns None because age
            on that date cannot be calculated without date_of_birth.
        """
        target_date = reference_date or date.today()
        if self.date_of_birth is not None:
            return target_date.year - self.date_of_birth.year - (
                (target_date.month, target_date.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        if reference_date is None or reference_date == date.today():
            return self.age_years
        return None

    @property
    def age(self) -> int | None:
        return self.age_at(date.today())

    def value_for_rule(self, field_name: str, reference_date: date | None = None) -> Any:
        if field_name == "age":
            return self.age_at(reference_date)
        if field_name == "disability_percentage":
            if self.disability_percentage is not None:
                return self.disability_percentage
            if self.has_disability is False:
                return 0
            return None
        return getattr(self, field_name, None)


class RuleNode(BaseModel):
    """Safe, deliberately small JSON-Logic-like AST. It does not execute arbitrary code."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["all", "any", "not", "eq", "ne", "gt", "gte", "lt", "lte", "in", "exists"]
    children: list["RuleNode"] = Field(default_factory=list, max_length=50)
    field: str | None = Field(default=None, max_length=100)
    value: Any = None
    condition_id: str | None = Field(default=None, max_length=80)
    as_of_date: date | None = Field(default=None)
    is_hard_statutory: bool = Field(default=True)

    @model_validator(mode="after")
    def validate_shape(self) -> "RuleNode":
        logical = {"all", "any", "not"}
        comparison = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "exists"}
        if self.op in logical:
            if self.field is not None or self.value is not None or self.as_of_date is not None:
                raise ValueError(f"{self.op} nodes cannot have field/value/as_of_date")
            if self.op == "not" and len(self.children) != 1:
                raise ValueError("not requires exactly one child")
            if self.op in {"all", "any"} and not self.children:
                raise ValueError(f"{self.op} requires at least one child")
        elif self.op in comparison:
            if not self.field:
                raise ValueError(f"{self.op} requires a field")
            if self.as_of_date is not None and self.field != "age":
                raise ValueError("as_of_date can only be specified on 'age' conditions")
            if self.condition_id is not None and not re.match(r"^[a-z0-9_-]{2,80}$", self.condition_id):
                raise ValueError("condition_id must match '^[a-z0-9_-]{2,80}$'")
            allowed_fields = {
                "age", "gender", "resident_state", "district", "annual_family_income",
                "caste_category", "is_student", "education_level", "has_disability", "disability_percentage", "bpl",
                "receiving_other_pension", "aadhaar_linked_bank_account", "has_land",
                "marital_status", "occupation", "landholding_hectares", "ration_card_type",
                "local_government_type", "municipal_corporation", "municipal_council", "nagar_panchayat",
                "gram_panchayat", "ward", "locality", "residence_years", "pin_code",
            }
            if self.field not in allowed_fields:
                raise ValueError(f"Unsupported profile field: {self.field}")
            if self.children:
                raise ValueError(f"{self.op} cannot have children")
            if self.op != "exists" and self.value is None:
                raise ValueError(f"{self.op} requires a non-null value")
            scalar = (str, int, float, bool)
            if self.op in {"gt", "gte", "lt", "lte"} and (not isinstance(self.value, (int, float)) or isinstance(self.value, bool)):
                raise ValueError(f"{self.op} requires a numeric scalar")
            if self.op in {"eq", "ne"} and (not isinstance(self.value, scalar) or isinstance(self.value, (list, dict))):
                raise ValueError(f"{self.op} requires a scalar value")
            if self.op == "in" and not isinstance(self.value, list):
                raise ValueError("in requires a list value")
            if self.op == "in" and any(not isinstance(item, scalar) for item in self.value):
                raise ValueError("in list must contain scalar values only")
        # Reject deeply nested or oversized trees before evaluation to bound CPU and stack use.
        stack: list[tuple[RuleNode, int]] = [(self, 1)]
        total_nodes = 0
        while stack:
            current, depth = stack.pop()
            total_nodes += 1
            if depth > 12 or total_nodes > 256:
                raise ValueError("Rule AST exceeds the maximum depth (12) or node count (256)")
            stack.extend((child, depth + 1) for child in current.children)
        return self


RuleNode.model_rebuild()
class ConditionEvaluation(BaseModel):
    """Structured explanation of an individual rule or logical rule group."""

    model_config = ConfigDict(extra="forbid")

    operator: Literal["all", "any", "not"] | None = None
    condition: str | None = Field(default=None, max_length=500)
    result: Literal["matched", "failed", "unknown"]
    children: list["ConditionEvaluation"] = Field(
        default_factory=list,
        max_length=50,
    )

    @model_validator(mode="after")
    def validate_structure(self) -> "ConditionEvaluation":
        if self.operator is None:
            if not self.condition or self.children:
                raise ValueError(
                    "Leaf conditions require condition text and cannot have children."
                )
        else:
            if self.condition is not None or not self.children:
                raise ValueError(
                    "Logical groups require children and cannot have condition text."
                )
            if self.operator == "not" and len(self.children) != 1:
                raise ValueError("NOT groups require exactly one child.")

        return self


ConditionEvaluation.model_rebuild()

class SourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(min_length=2, max_length=160)
    source_url: str = Field(min_length=8, max_length=2000)
    source_kind: Literal["government_resolution", "official_scheme_page", "official_portal", "official_notification"]
    retrieved_at: datetime
    evidence_excerpt: str = Field(min_length=12, max_length=3000)
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    page_or_section: str | None = Field(default=None, max_length=300)

    @field_validator("source_url")
    @classmethod
    def require_https_source(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("Source URLs must use HTTPS")
        return value

    @model_validator(mode="after")
    def evidence_hash_matches_excerpt(self) -> "SourceReference":
        expected = sha256(self.evidence_excerpt.encode("utf-8")).hexdigest()
        if self.evidence_sha256 != expected:
            raise ValueError("evidence_sha256 must match the UTF-8 evidence_excerpt bytes")
        return self


class Scheme(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheme_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,79}$")
    name: str = Field(min_length=3, max_length=240)
    department: str = Field(min_length=2, max_length=200)
    summary: str = Field(min_length=10, max_length=3000)
    benefits: list[str] = Field(default_factory=list, max_length=30)
    required_documents: list[str] = Field(default_factory=list, max_length=30)
    eligibility_rule: RuleNode
    sources: list[SourceReference] = Field(min_length=1, max_length=20)
    rule_version: str = Field(default="0.1.0", max_length=40)
    rule_status: Literal["draft", "reviewed", "active", "retired"] = "draft"
    approved_by: str | None = Field(default=None, max_length=120)
    approval_reference: str | None = Field(default=None, max_length=200)
    last_verified_at: datetime | None = None
    languages: list[Language] = Field(default_factory=lambda: [Language.EN])
    evidence: list[Any] = Field(default_factory=list, max_length=50)
    document_requirements: list[Any] = Field(default_factory=list, max_length=50)
    eligibility_reference_date: date | None = None
    publication_authorized: bool = Field(default=False)
    jurisdiction_scope: str = Field(default="MAHARASHTRA_STATE", max_length=60)
    jurisdiction_ids: list[str] = Field(default_factory=list, max_length=50)
    included_local_bodies: list[str] = Field(default_factory=list, max_length=100)
    excluded_local_bodies: list[str] = Field(default_factory=list, max_length=100)
    required_residency_years: int | None = Field(default=None, ge=0, le=120)
    funding_type: str = Field(default="STATE_FUNDED", max_length=80)
    implementing_authority: str | None = Field(default=None, max_length=200)
    application_window_status: str = Field(default="APPLICATION_WINDOW_OPEN", max_length=80)

    @field_validator("evidence", mode="after")
    @classmethod
    def normalize_evidence_items(cls, items: list[Any]) -> list[Any]:
        from scheme_navigator.domain.evidence import RuleEvidence

        normalized = []
        for item in items:
            if isinstance(item, dict):
                normalized.append(RuleEvidence.model_validate(item))
            else:
                normalized.append(item)
        return normalized

    @model_validator(mode="after")
    def active_rule_needs_audit_trail(self) -> "Scheme":
        if self.rule_status == "active":
            if not self.approved_by or not self.approval_reference or not self.last_verified_at:
                raise ValueError("active rules require approved_by, approval_reference, and last_verified_at")

            is_demo = (
                self.scheme_id.startswith("demo-")
                or (self.approved_by or "").strip().casefold() == "local_demo_fixture_only"
                or "demo-fixture" in (self.approval_reference or "").casefold()
                or "not_for_production" in (self.approval_reference or "").casefold()
            )

            if not is_demo:
                disallowed = {"demo", "fixture", "synthetic", "placeholder", "unknown"}
                approver_lower = self.approved_by.casefold()
                ref_lower = self.approval_reference.casefold()
                if any(d in approver_lower for d in disallowed) or any(d in ref_lower for d in disallowed):
                    raise ValueError(
                        f"Active non-demo scheme cannot use placeholder approval metadata: '{self.approved_by}'"
                    )

                if not self.evidence:
                    raise ValueError("Active non-demo schemes require a non-empty evidence list.")

                from scheme_navigator.domain.evidence import (
                    RuleEvidence,
                    RuleVerificationStatus,
                    validate_rule_evidence_coverage,
                )

                typed_evidence: list[RuleEvidence] = []
                for item in self.evidence:
                    ev = RuleEvidence.model_validate(item) if isinstance(item, dict) else item
                    typed_evidence.append(ev)
                    if ev.verification_status != RuleVerificationStatus.LEGAL_APPROVED:
                        raise ValueError(
                            f"Evidence for condition '{ev.condition_id}' must have verification_status 'legal_approved', got '{ev.verification_status}'"
                        )
                    if ev.effective_until is not None and ev.effective_until < ev.effective_from:
                        raise ValueError(
                            f"Evidence for condition '{ev.condition_id}' has effective_until ({ev.effective_until}) before effective_from ({ev.effective_from})"
                        )

                coverage = validate_rule_evidence_coverage(
                    self.eligibility_rule,
                    typed_evidence,
                    require_all_leaves_have_ids=True,
                    require_legal_approval=True,
                )
                if not coverage.is_valid:
                    reasons = []
                    if coverage.missing_evidence_ids:
                        reasons.append(f"Missing evidence for: {coverage.missing_evidence_ids}")
                    if coverage.orphan_evidence_ids:
                        reasons.append(f"Orphan evidence for: {coverage.orphan_evidence_ids}")
                    if coverage.duplicate_ast_condition_ids:
                        reasons.append(f"Duplicate AST condition IDs: {coverage.duplicate_ast_condition_ids}")
                    if coverage.duplicate_evidence_condition_ids:
                        reasons.append(f"Duplicate evidence condition IDs: {coverage.duplicate_evidence_condition_ids}")
                    if coverage.unverified_condition_ids:
                        reasons.append(f"Unverified evidence conditions: {coverage.unverified_condition_ids}")
                    for note in coverage.notes:
                        if "STRICT MODE" in note or "do not declare a condition_id" in note:
                            reasons.append(note)
                    raise ValueError(f"Evidence validation failed: {'; '.join(reasons)}")

            elif self.evidence:
                from scheme_navigator.domain.evidence import validate_rule_evidence_coverage

                coverage = validate_rule_evidence_coverage(self.eligibility_rule, self.evidence)
                if not coverage.is_valid:
                    reasons = []
                    if coverage.missing_evidence_ids:
                        reasons.append(f"Missing evidence for: {coverage.missing_evidence_ids}")
                    if coverage.orphan_evidence_ids:
                        reasons.append(f"Orphan evidence for: {coverage.orphan_evidence_ids}")
                    if coverage.duplicate_ast_condition_ids:
                        reasons.append(f"Duplicate AST condition IDs: {coverage.duplicate_ast_condition_ids}")
                    if coverage.duplicate_evidence_condition_ids:
                        reasons.append(f"Duplicate evidence condition IDs: {coverage.duplicate_evidence_condition_ids}")
                    raise ValueError(f"Evidence validation failed: {'; '.join(reasons)}")

        return self


class EligibilityResult(BaseModel):
    scheme_id: str
    scheme_name: str
    status: EligibilityStatus
    reason: str
    missing_fields: list[str] = Field(default_factory=list)
    matched_conditions: list[str] = Field(default_factory=list)
    failed_conditions: list[str] = Field(default_factory=list)
    unknown_conditions: list[str] = Field(default_factory=list)
    condition_tree: ConditionEvaluation | None = None
    condition_evaluation_note: str = (
        "Condition lists describe individual rule checks. "
        "The all, any and not operators determine the overall result."
    )
    rule_version: str
    sources: list[SourceReference]
    explanation: Any | None = None
    pass_ratio: float | None = None
    is_partial: bool = False


class InterviewMode(StrEnum):
    DISCOVERY = "DISCOVERY"
    FOCUSED_SCHEME = "FOCUSED_SCHEME"


class InterviewRunContext(BaseModel):
    interview_run_id: str = Field(min_length=1, max_length=200)
    mode: InterviewMode = InterviewMode.DISCOVERY
    target_scheme_id: str | None = Field(default=None, max_length=80)
    target_jurisdiction_id: str | None = Field(default=None, max_length=80)
    citizen_profile_id: str | None = None
    catalogue_version: str = "2026.11"
    rule_version: str = "1.0.0"
    language: Language = Language.EN
    status: Literal["active", "completed", "abandoned"] = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class InterviewAnswer(BaseModel):
    thread_id: str = Field(min_length=1, max_length=200)
    answer: str = Field(min_length=1, max_length=2000)
    language: Language = Language.EN


class InterviewStart(BaseModel):
    thread_id: str = Field(min_length=1, max_length=200)
    language: Language = Language.EN
    profile: CitizenProfile = Field(default_factory=CitizenProfile)
    scheme_id: str | None = Field(default=None, max_length=80)
    mode: InterviewMode | None = None
    target_scheme_id: str | None = Field(default=None, max_length=80)
    target_jurisdiction_id: str | None = Field(default=None, max_length=80)
    scope: str | None = None

    @field_validator("profile", mode="before")
    @classmethod
    def sanitize_profile(cls, v: Any) -> Any:
        if isinstance(v, dict):
            if "profile" in v and isinstance(v["profile"], dict):
                inner = dict(v["profile"])
                for k, val in v.items():
                    if k not in ("profile", "session_id", "provenance") and k not in inner:
                        inner[k] = val
                v = inner
            cleaned = {k: val for k, val in v.items() if k not in ("session_id", "provenance", "profile")}
            if "age" in cleaned and "age_years" not in cleaned:
                cleaned["age_years"] = cleaned.pop("age")
            elif "age" in cleaned and cleaned.get("age_years") is None:
                cleaned["age_years"] = cleaned.pop("age")
            allowed = set(CitizenProfile.model_fields.keys())
            return {k: val for k, val in cleaned.items() if k in allowed}
        return v


class DocumentFinding(BaseModel):
    """Actionable, source-grounded finding from document pre-audit."""

    code: str
    severity: Literal["info", "warning", "error"]
    category: Literal[
        "document_extraction",
        "document_consistency",
        "document_validity",
        "scheme_eligibility",
    ] = "document_consistency"
    message: str
    recommended_action: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list, max_length=20)
    page_numbers: list[int] = Field(default_factory=list, max_length=20)



class ExtractedDocument(BaseModel):
    document_id: str

    document_type: Literal[
        "income_certificate",
        "seven_twelve_extract",
        "caste_certificate",
        "domicile_certificate",
        "aadhaar_card",
        "other",
        "unknown",
    ] = "unknown"

    # Personal information
    person_name: str | None = None
    date_of_birth: date | None = None

    # Certificate dates
    issue_date: date | None = None
    valid_until: date | None = None
    valid_financial_year: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}$",
    )

    # Financial information
    annual_family_income: int | None = Field(
        default=None,
        ge=0,
    )
    income_currency: Literal["INR"] | None = None

    # Document identity
    certificate_number_masked: str | None = None

    # Extraction evidence
    # Values should be exact, short excerpts visible in the document.
    field_evidence: dict[str, str] = Field(
        default_factory=dict,
        max_length=12,
    )

    # Model confidence (not an approval decision)
    confidence: float = Field(
        ge=0,
        le=1,
        default=0,
    )

    source_file_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$",
    )

    extraction_notes: list[str] = Field(
        default_factory=list,
        max_length=20,
    )



class DocumentAuditRequest(BaseModel):
    documents: list[ExtractedDocument] = Field(min_length=1, max_length=20)
    target_financial_year: str = Field(default="2026-27", pattern=r"^\d{4}-\d{2}$")


class DocumentAuditResponse(BaseModel):
    status: Literal["pass", "review_required", "issues_found"]
    findings: list[DocumentFinding]
    cross_document_name_match: float | None = None
    cross_document_dob_match: bool | None = None
    scheme_eligibility_evaluated: bool = False
    scope_note: str = (
        "This report checks extraction quality, document consistency, and selected document-validity "
        "signals only. It does not determine eligibility for any government scheme. Evaluate scheme "
        "eligibility separately using the approved, current scheme rules."
    )
    disclaimer: str = "Pre-audit only; not an official certificate verification or legal decision."


class DocumentFieldCorrections(BaseModel):
    """Reviewer-editable extraction fields. Source hashes and model metadata are immutable."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    document_type: Literal[
        "income_certificate",
        "seven_twelve_extract",
        "caste_certificate",
        "domicile_certificate",
        "aadhaar_card",
        "other",
        "unknown",
    ] | None = None
    person_name: str | None = Field(default=None, max_length=200)
    date_of_birth: date | None = None
    issue_date: date | None = None
    valid_until: date | None = None
    valid_financial_year: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    annual_family_income: int | None = Field(default=None, ge=0, le=100_000_000)
    income_currency: Literal["INR"] | None = None
    certificate_number_masked: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def require_at_least_one_correction(self) -> "DocumentFieldCorrections":
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to correct; use null to clear a field.")
        if self.person_name is not None and not self.person_name.strip():
            raise ValueError("person_name cannot be blank; use null to clear it.")
        if self.certificate_number_masked and re.fullmatch(
            r"\d{4}[- ]?\d{4}[- ]?\d{4}", self.certificate_number_masked
        ):
            raise ValueError("A full Aadhaar-like number must not be entered as a certificate number.")
        return self


class DocumentReviewCorrectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reviewer_id: str = Field(min_length=2, max_length=120)
    note: str = Field(min_length=3, max_length=1000)
    corrections: DocumentFieldCorrections


class DocumentReviewCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reviewer_id: str = Field(min_length=2, max_length=120)
    confirm_review_complete: bool = False
    note: str = Field(min_length=5, max_length=1000)


class PlanStep(BaseModel):
    step_id: str
    title: str
    step_type: Literal["obtain_document", "verify_document", "apply_scheme"]
    depends_on: list[str] = Field(default_factory=list)
    notified_limit_days: int | None = None
    timeline_source_url: str | None = None
    notes: str


class ApplicationPlan(BaseModel):
    scheme_id: str
    steps: list[PlanStep]
    estimated_notified_days_on_critical_path: int
    timeline_coverage: Literal["complete", "partial", "none"] = "none"
    unknown_timeline_step_ids: list[str] = Field(default_factory=list)
    timeline_note: str = (
        "Published RTS limits are service standards, not a guarantee of actual completion; confirm the current notified service and counting convention."
    )

class AssessmentAction(BaseModel):
    """A practical next action derived from an existing assessment component."""

    code: str
    source: Literal["eligibility", "document_audit", "planner"]
    priority: Literal["high", "medium", "low"]
    title: str
    detail: str


class ApplicantAssessmentRequest(BaseModel):
    """Input for a per-scheme consolidated applicant assessment."""

    model_config = ConfigDict(extra="forbid")

    profile: CitizenProfile = Field(default_factory=CitizenProfile)
    documents: list[ExtractedDocument] = Field(
        default_factory=list,
        max_length=20,
    )
    target_financial_year: str = Field(
        default="2026-27",
        pattern=r"^\d{4}-\d{2}$",
    )
    review_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
    )
    thread_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    language: Language = Field(default=Language.EN)


class ApplicantAssessmentResponse(BaseModel):
    """Combined eligibility, document pre-audit and application preparation report."""

    scheme_id: str
    scheme_name: str

    eligibility: EligibilityResult
    document_audit: DocumentAuditResponse | None = None
    application_plan: ApplicationPlan

    declared_available_documents: list[str] = Field(default_factory=list)
    document_availability_basis: Literal["applicant_reported"] = "applicant_reported"

    document_authenticity_status: Literal["not_verified"] = "not_verified"
    human_review_status: Literal[
        "not_linked",
        "pending_review",
        "review_completed",
    ] = "not_linked"

    human_review_id: str | None = None

    next_actions: list[AssessmentAction] = Field(default_factory=list)
    document_prep_report: Any | None = None
    portal_guidance: Any | None = None

    scope_note: str = (
    "This is a consolidated preliminary assessment, not a government decision. "
    "Eligibility depends on approved and current scheme rules. Document extraction "
    "and consistency checks do not establish certificate authenticity. Applicant-"
    "reported document availability is not proof of possession or verification. "
    "Human-review status records workflow progress only; it does not establish "
    "certificate authenticity or official verification."
)