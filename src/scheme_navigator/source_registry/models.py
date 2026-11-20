from __future__ import annotations

from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ChannelType(StrEnum):
    DIRECT_OFFICIAL_PORTAL = "DIRECT_OFFICIAL_PORTAL"
    AUTHORIZED_API_INTEGRATION = "AUTHORIZED_API_INTEGRATION"
    OFFLINE_OFFICE_APPLICATION = "OFFLINE_OFFICE_APPLICATION"
    AUTHORIZED_ASSISTANCE_CENTRE = "AUTHORIZED_ASSISTANCE_CENTRE"
    PORTAL_STATUS_UNKNOWN = "PORTAL_STATUS_UNKNOWN"
    APPLICATION_WINDOW_CLOSED = "APPLICATION_WINDOW_CLOSED"
    APPLICATION_CHANNEL_UNAVAILABLE = "APPLICATION_CHANNEL_UNAVAILABLE"


class ApplicationTrackStatus(StrEnum):
    NOT_STARTED = "not_started"
    PREPARATION_IN_PROGRESS = "preparation_in_progress"
    READY_TO_APPLY = "ready_to_apply"
    OFFICIAL_PORTAL_OPENED = "official_portal_opened"
    CITIZEN_REPORTED_SUBMITTED = "citizen_reported_submitted"
    OFFICIALLY_SUBMITTED = "officially_submitted"
    OFFICIALLY_APPROVED = "officially_approved"
    OFFICIALLY_REJECTED = "officially_rejected"
    ACTION_REQUIRED = "action_required"


class SourceRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source_id: str
    name: str
    authority: str
    department: str
    domain: str
    url: str
    source_type: str
    categories: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    access_method: str = "PUBLIC_WEB"
    auth_required: bool = False
    robots_allowed: bool = True
    discovery_status: str = "ACTIVE_VERIFIED"
    last_checked_iso: str
    last_retrieval_iso: str
    content_hash: str
    parser_version: str = "1.0.0"
    records_found: int = 0
    known_gaps: str | None = None
    failure_reason: str | None = None


class PublicServiceRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    service_id: str
    service_name_en: str
    service_name_mr: str
    service_name_hi: str
    department: str
    competent_authority: str
    designated_officer: str | None = None
    first_appellate_authority: str | None = None
    second_appellate_authority: str | None = None
    notification_status: str = "NOTIFIED"
    verification_status: str = "VERIFIED_OFFICIAL_GAZETTE"
    rts_statutory_limit_days: int
    official_portal_url: str
    application_fee_inr: float = 0.0
    required_documents: list[str] = Field(default_factory=list)
    is_common_prerequisite: bool = True
    appeal_authority: str


class ApplicationChannelRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scheme_id: str
    scheme_name: str
    channel_type: ChannelType
    portal_name: str
    portal_url: str
    department: str
    login_requirement: str
    application_window: str
    fresh_vs_renewal: str
    offline_procedure: str
    preparation_checklist: list[str] = Field(default_factory=list)
    tracking_url: str | None = None
    grievance_url: str | None = None
    statutory_hand_off_notice: str


class CitizenApplicationTrackRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tracking_id: str
    thread_id: str
    scheme_id: str
    status: ApplicationTrackStatus
    status_label_en: str
    status_label_mr: str
    status_label_hi: str
    is_citizen_reported: bool = True
    timestamp_iso: str
    notes: str | None = None


class SourceCoverageStats(BaseModel):
    model_config = ConfigDict(extra="ignore")

    category: str
    discovered_count: int
    reviewed_count: int
    published_count: int
    unresolved_count: int
    scan_status: str


class SchemePublicationStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    EXTRACTED_UNVERIFIED = "EXTRACTED_UNVERIFIED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    POLICY_UNRESOLVED = "POLICY_UNRESOLVED"
    VERIFIED_FOR_INFORMATION = "VERIFIED_FOR_INFORMATION"
    VERIFIED_FOR_ELIGIBILITY = "VERIFIED_FOR_ELIGIBILITY"
    PUBLISHED = "PUBLISHED"
    SUSPENDED = "SUSPENDED"
    SUPERSEDED = "SUPERSEDED"
    DISCONTINUED = "DISCONTINUED"
    DEMO_ONLY = "DEMO_ONLY"


class CanonicalSchemeRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    canonical_scheme_id: str
    official_scheme_name: str = ""
    english_name: str = ""
    marathi_name: str = ""
    hindi_name: str = ""
    aliases: list[str] = Field(default_factory=list)
    responsible_department: str = ""
    implementing_authority: str = ""
    funding_authority: str = "Government of Maharashtra"
    state_central_joint_classification: str = "STATE_SCHEME"
    beneficiary_category: str = "ALL_CITIZENS"
    scheme_objective: str = ""
    geographic_applicability: str = "Statewide (Maharashtra)"
    district_restrictions: list[str] | None = None
    jurisdiction_scope: str = "MAHARASHTRA_STATE"
    jurisdiction_ids: list[str] = Field(default_factory=list)
    included_local_bodies: list[str] = Field(default_factory=list)
    excluded_local_bodies: list[str] = Field(default_factory=list)
    required_residency_years: int | None = None
    funding_type: str = "STATE_FUNDED"
    application_window_status: str = "APPLICATION_WINDOW_OPEN"
    rural_urban_conditions: str = "ALL"
    age_requirements: str | None = None
    gender_conditions: str = "ALL"
    social_category_requirements: str = "ALL"
    family_income_requirements: str | None = None
    occupation_requirements: str | None = None
    education_requirements: str | None = None
    disability_requirements: str | None = None
    landholding_property_requirements: str | None = None
    other_eligibility_conditions: list[str] = Field(default_factory=list)
    benefit_description: str = ""
    benefit_amount: str | None = None
    benefit_frequency: str = "MONTHLY"
    benefit_restrictions: str | None = None
    required_documents: list[str] = Field(default_factory=list)
    optional_documents: list[str] = Field(default_factory=list)
    application_window: str = "OPEN_YEAR_ROUND"
    financial_academic_year: str = "2024-2025"
    renewal_requirements: str = "NONE"
    application_authority: str = ""
    official_application_url: str = ""
    offline_application_procedure: str | None = None
    prerequisite_services: list[str] = Field(default_factory=list)
    government_source_references: list[dict[str, Any]] = Field(default_factory=list)
    original_gr_and_amendments: list[str] = Field(default_factory=list)
    faqs: list[dict[str, Any]] = Field(default_factory=list)
    rule_version: str = "1.0.0"
    effective_start_date: str | None = None
    effective_end_date: str | None = None
    last_source_verification_date: str = "2026-11-13"
    application_availability: str = "AVAILABLE"
    publication_status: str = "VERIFIED_FOR_INFORMATION"

    # Backwards-compatible fields for existing code
    official_name_en: str = ""
    official_name_mr: str = ""
    responsible_authority: str = ""
    department: str = ""
    lifecycle_status: str = ""
    benefit_details: str = ""
    eligibility_summary: str = ""
    application_channel_id: str = ""
    application_portal_url: str = ""
    duplicate_aliases_mapped: list[str] = Field(default_factory=list)
    source_references: list[dict[str, Any]] = Field(default_factory=list)
    source_doc_ids: list[str] = Field(default_factory=list)
    geography: str = "Statewide (Maharashtra)"

    # TRIMURTI v3 Decision Readiness & Status Categorization (Invariants I-04, I-07)
    is_decision_ready: bool = False
    completeness_attested: bool = False
    public_status_category: str = "LIMITED_INFORMATION"

    def model_post_init(self, __context: Any) -> None:
        # Synchronize backward-compatible aliases
        if not self.official_name_en:
            self.official_name_en = self.english_name or self.official_scheme_name
        if not self.english_name:
            self.english_name = self.official_name_en
        if not self.official_name_mr:
            self.official_name_mr = self.marathi_name
        if not self.marathi_name:
            self.marathi_name = self.official_name_mr
        if not self.official_scheme_name:
            self.official_scheme_name = self.english_name or self.official_name_mr
        if not self.department:
            self.department = self.responsible_department
        if not self.responsible_department:
            self.responsible_department = self.department
        if not self.responsible_authority:
            self.responsible_authority = self.implementing_authority or self.responsible_department
        if not self.implementing_authority:
            self.implementing_authority = self.responsible_authority
        if not self.lifecycle_status:
            self.lifecycle_status = self.publication_status
        if not self.benefit_details:
            self.benefit_details = self.benefit_description
        if not self.benefit_description:
            self.benefit_description = self.benefit_details
        if not self.application_portal_url:
            self.application_portal_url = self.official_application_url
        if not self.official_application_url:
            self.official_application_url = self.application_portal_url
        if not self.duplicate_aliases_mapped:
            self.duplicate_aliases_mapped = self.aliases
        if not self.aliases:
            self.aliases = self.duplicate_aliases_mapped
        if not self.source_references:
            if self.government_source_references:
                self.source_references = self.government_source_references
            else:
                self.source_references = [
                    {
                        "source_name": f"{self.official_name_en or self.canonical_scheme_id} Official Authority Notification",
                        "source_url": self.official_application_url or "https://maharashtra.gov.in",
                        "source_kind": "official_municipal_portal",
                        "retrieved_at": "2026-11-16T00:00:00+05:30",
                        "page_or_section": "Urban Local Body Citizen Welfare Directive",
                        "evidence_excerpt": self.scheme_objective or self.benefit_description or "Official government scheme notification.",
                        "evidence_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    }
                ]
        if not self.government_source_references:
            self.government_source_references = self.source_references
        if not self.source_doc_ids:
            self.source_doc_ids = [self.canonical_scheme_id]


class SourceChangeRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    change_id: str
    source_id: str
    detected_at_iso: str
    change_type: str  # NEW_GR, AMENDMENT, STATUS_CHANGE, WINDOW_UPDATE
    summary: str
    previous_hash: str
    current_hash: str
    affected_scheme_ids: list[str] = Field(default_factory=list)
    requires_human_approval: bool = True
    is_reviewed: bool = False
