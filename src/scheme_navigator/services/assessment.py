
from __future__ import annotations

from datetime import date
from typing import Any

from scheme_navigator.domain.models import (
    ApplicantAssessmentRequest,
    ApplicantAssessmentResponse,
    AssessmentAction,
    DocumentAuditResponse,
    DocumentFinding,
    EligibilityStatus,
    ExtractedDocument,
    Language,
    Scheme,
)
from scheme_navigator.documents.audit import (
    audit_extracted_documents,
    compare_person_names,
)
from scheme_navigator.planner.dag import (
    build_application_plan,
    canonical_document,
)
from scheme_navigator.services.document_prep import prepare_intelligent_document_audit
from scheme_navigator.services.portal_assistance import build_portal_application_package
from scheme_navigator.services.rule_engine import evaluate_scheme


# Maps Gemini's extracted document types to the planner's document names.
# Only explicit, recognised document types are mapped.
DOCUMENT_TYPE_TO_PLAN_NAME = {
    "income_certificate": "income certificate",
    "seven_twelve_extract": "7/12 extract",
    "caste_certificate": "caste certificate",
    "domicile_certificate": "domicile certificate",
    "aadhaar_card": "identity proof",
}


def _add_action(
    actions: list[AssessmentAction],
    action: AssessmentAction,
) -> None:
    """Prevent duplicate actions in the consolidated report."""
    if not any(item.code == action.code for item in actions):
        actions.append(action)


def _available_documents_for_plan(
    applicant_documents: list[str],
    extracted_documents: list[ExtractedDocument],
) -> list[str]:
    """
    Combine applicant-reported documents with recognised uploaded documents.

    Uploaded documents count as supplied for preparation planning.
    This does not establish authenticity, validity or official acceptance.
    Unknown document types are not automatically mapped.
    """
    available = list(applicant_documents)

    for document in extracted_documents:
        plan_name = DOCUMENT_TYPE_TO_PLAN_NAME.get(
            document.document_type
        )

        if plan_name:
            available.append(plan_name)

    # Canonicalise aliases and remove duplicate document entries.
    canonical_names = [
        canonical_document(item)
        for item in available
        if isinstance(item, str) and item.strip()
    ]

    return list(dict.fromkeys(canonical_names))


def _reconcile_profile_income(
    audit: DocumentAuditResponse,
    payload: ApplicantAssessmentRequest,
    documents: list[ExtractedDocument],
) -> DocumentAuditResponse:
    """
    Compare applicant-reported income with extracted INR income certificates.

    Differences create warnings only. Neither source automatically overrides
    the other.
    """
    reported_income = payload.profile.annual_family_income

    if reported_income is None:
        return audit

    mismatched_documents = [
        document
        for document in documents
        if (
            document.document_type == "income_certificate"
            and document.annual_family_income is not None
            and document.income_currency == "INR"
            and document.annual_family_income != reported_income
        )
    ]

    if not mismatched_documents:
        findings = [
            item
            for item in audit.findings
            if item.code != "PROFILE_DOCUMENT_INCOME_MISMATCH"
        ]

        if len(findings) != len(audit.findings):
            return audit.model_copy(
                update={"findings": findings}
            )

        return audit

    document_ids = sorted({
        document.document_id
        for document in mismatched_documents
    })

    finding = DocumentFinding(
        code="PROFILE_DOCUMENT_INCOME_MISMATCH",
        severity="warning",
        category="document_consistency",
        message=(
            "Applicant-reported annual family income differs from "
            "the annual income extracted from a supplied income certificate."
        ),
        recommended_action=(
            "Ask the applicant or reviewer to compare the original "
            "income certificate with the declared income. Confirm the "
            "correct value before proceeding. Do not automatically "
            "overwrite either value."
        ),
        document_ids=document_ids,
    )

    findings = [
        item
        for item in audit.findings
        if item.code != finding.code
    ]
    findings.append(finding)

    new_status = (
        "review_required"
        if audit.status == "pass"
        else audit.status
    )

    return audit.model_copy(
        update={
            "findings": findings,
            "status": new_status,
        }
    )


def _reconcile_profile_dob_and_age(
    audit: DocumentAuditResponse,
    payload: ApplicantAssessmentRequest,
    documents: list[ExtractedDocument],
) -> DocumentAuditResponse:
    """
    Compare applicant-reported DOB or age with DOB extracted from documents.

    If the applicant provides a DOB, compare exact dates.
    Otherwise, compare declared age with age calculated from document DOB.

    Differences create warnings only. Neither source automatically overrides
    the other.
    """
    profile_dob = payload.profile.date_of_birth
    profile_age = payload.profile.age_years
    today = date.today()

    dob_mismatches: list[ExtractedDocument] = []
    age_mismatches: list[tuple[ExtractedDocument, int]] = []

    for document in documents:
        document_dob = document.date_of_birth

        if document_dob is None:
            continue

        if profile_dob is not None:
            if document_dob != profile_dob:
                dob_mismatches.append(document)

        elif profile_age is not None:
            calculated_age = (
                today.year
                - document_dob.year
                - (
                    (today.month, today.day)
                    < (document_dob.month, document_dob.day)
                )
            )

            if calculated_age != profile_age:
                age_mismatches.append(
                    (document, calculated_age)
                )

    mismatch_codes = {
        "PROFILE_DOCUMENT_DOB_MISMATCH",
        "PROFILE_DOCUMENT_AGE_MISMATCH",
    }

    findings = [
        item
        for item in audit.findings
        if item.code not in mismatch_codes
    ]

    if dob_mismatches:
        findings.append(
            DocumentFinding(
                code="PROFILE_DOCUMENT_DOB_MISMATCH",
                severity="warning",
                category="document_consistency",
                message=(
                    "Applicant-reported date of birth differs from "
                    "the date of birth extracted from one or more documents."
                ),
                recommended_action=(
                    "Ask the applicant or reviewer to compare the original "
                    "document with the declared date of birth. Confirm the "
                    "correct value before proceeding. Do not automatically "
                    "overwrite either value."
                ),
                document_ids=sorted({
                    document.document_id
                    for document in dob_mismatches
                }),
                evidence=[
                    f"Applicant-reported DOB: {profile_dob.isoformat()}",
                    *[
                        (
                            f"{document.document_type} "
                            f"({document.document_id}): "
                            f"{document.date_of_birth.isoformat()}"
                        )
                        for document in dob_mismatches
                    ],
                ],
            )
        )

    if age_mismatches:
        findings.append(
            DocumentFinding(
                code="PROFILE_DOCUMENT_AGE_MISMATCH",
                severity="warning",
                category="document_consistency",
                message=(
                    "Applicant-reported age does not match the age "
                    "calculated from the DOB extracted from one or more documents."
                ),
                recommended_action=(
                    "Ask the applicant or reviewer to compare the declared "
                    "age with the original date-of-birth document. Confirm "
                    "the correct information before proceeding. Do not "
                    "automatically overwrite either value."
                ),
                document_ids=sorted({
                    document.document_id
                    for document, _ in age_mismatches
                }),
                evidence=[
                    f"Applicant-reported age: {profile_age}",
                    *[
                        (
                            f"{document.document_type} "
                            f"({document.document_id}): "
                            f"DOB {document.date_of_birth.isoformat()}, "
                            f"calculated age {calculated_age} "
                            f"as of {today.isoformat()}"
                        )
                        for document, calculated_age in age_mismatches
                    ],
                ],
            )
        )

    has_mismatch = bool(
        dob_mismatches or age_mismatches
    )

    new_status = audit.status

    if has_mismatch and audit.status == "pass":
        new_status = "review_required"

    return audit.model_copy(
        update={
            "findings": findings,
            "status": new_status,
        }
    )


def _reconcile_profile_name(
    audit: DocumentAuditResponse,
    payload: ApplicantAssessmentRequest,
    documents: list[ExtractedDocument],
) -> DocumentAuditResponse:
    """
    Compare applicant-reported name with names extracted from documents.

    Reuses the document auditor's name-comparison logic.
    Neither value is automatically overwritten.
    """
    profile_name = payload.profile.name

    mismatch_codes = {
        "PROFILE_DOCUMENT_NAME_MISMATCH",
        "PROFILE_DOCUMENT_NAME_REVIEW",
    }

    findings = [
        item
        for item in audit.findings
        if item.code not in mismatch_codes
    ]

    if not profile_name or not profile_name.strip():
        if len(findings) != len(audit.findings):
            return audit.model_copy(
                update={"findings": findings}
            )
        return audit

    for document in documents:
        document_name = document.person_name

        if not document_name or not document_name.strip():
            continue

        comparison, score = compare_person_names(
            profile_name,
            document_name,
        )

        if comparison == "match":
            continue

        if comparison == "cross_script":
            finding = DocumentFinding(
                code="PROFILE_DOCUMENT_NAME_REVIEW",
                severity="warning",
                category="document_consistency",
                message=(
                    "Applicant-reported name and document name use "
                    "different writing scripts. Automatic comparison "
                    "is unreliable."
                ),
                recommended_action=(
                    "Ask the applicant or reviewer to compare the original "
                    "document and confirm whether the names are equivalent "
                    "transliterations. Do not automatically overwrite either name."
                ),
                document_ids=[document.document_id],
                evidence=[
                    f"Applicant-reported name: {profile_name}",
                    f"Document name: {document_name}",
                ],
            )

        elif comparison == "phonetic_review":
            finding = DocumentFinding(
                code="PROFILE_DOCUMENT_NAME_REVIEW",
                severity="warning",
                category="document_consistency",
                message=(
                    f"Applicant and document names differ "
                    f"(Jaro-Winkler={score:.2f}), but their phonetic "
                    "forms are similar. Manual confirmation is required."
                ),
                recommended_action=(
                    "Compare the original document with the applicant's "
                    "declared name and manually confirm spelling or "
                    "transliteration. Do not automatically overwrite either name."
                ),
                document_ids=[document.document_id],
                evidence=[
                    f"Applicant-reported name: {profile_name}",
                    f"Document name: {document_name}",
                ],
            )

        else:
            finding = DocumentFinding(
                code="PROFILE_DOCUMENT_NAME_MISMATCH",
                severity="warning",
                category="document_consistency",
                message=(
                    "Applicant-reported name differs from the name "
                    f"extracted from a document "
                    f"(Jaro-Winkler={score:.2f})."
                ),
                recommended_action=(
                    "Ask the applicant or reviewer to compare the original "
                    "document with the declared name. Check spelling, name "
                    "order, initials and transliteration. Confirm the "
                    "correct information before proceeding. Do not "
                    "automatically overwrite either value."
                ),
                document_ids=[document.document_id],
                evidence=[
                    f"Applicant-reported name: {profile_name}",
                    f"Document name: {document_name}",
                ],
            )

        findings.append(finding)

    new_status = audit.status

    if (
        any(item.code in mismatch_codes for item in findings)
        and audit.status == "pass"
    ):
        new_status = "review_required"

    return audit.model_copy(
        update={
            "findings": findings,
            "status": new_status,
        }
    )


def build_applicant_assessment(
    scheme: Scheme,
    payload: ApplicantAssessmentRequest,
    *,
    review_record: dict[str, Any] | None = None,
) -> ApplicantAssessmentResponse:
    """Combine eligibility, document audit, review state and application plan."""

    # 1. Evaluate eligibility using the existing rules engine.
    eligibility = evaluate_scheme(
        scheme,
        payload.profile,
    )

    # 2. Choose the document source.
    # A linked review record provides current extracted/corrected values.
    if review_record is not None:
        documents_for_assessment = [
            ExtractedDocument.model_validate(item)
            for item in review_record["extracted_documents"]
        ]

        document_audit = DocumentAuditResponse.model_validate(
            review_record["audit"]
        )

        human_review_status = review_record["status"]
        human_review_id = review_record["review_id"]

        if human_review_status not in {
            "pending_review",
            "review_completed",
        }:
            raise ValueError(
                "Unsupported human-review status."
            )

    else:
        documents_for_assessment = payload.documents
        human_review_status = "not_linked"
        human_review_id = None

        document_audit = None

        if documents_for_assessment:
            document_audit = audit_extracted_documents(
                documents_for_assessment,
                payload.target_financial_year,
            )

    # 3. Reconcile applicant-reported information with extracted values.
    if document_audit is not None:
        document_audit = _reconcile_profile_income(
            document_audit,
            payload,
            documents_for_assessment,
        )

        document_audit = _reconcile_profile_dob_and_age(
            document_audit,
            payload,
            documents_for_assessment,
        )

        document_audit = _reconcile_profile_name(
            document_audit,
            payload,
            documents_for_assessment,
        )

    # 4. Combine applicant-reported and uploaded documents.
    # Uploaded documents count as supplied for planning purposes only.
    # They are not automatically accepted or authenticity-verified.
    available_for_plan = _available_documents_for_plan(
        applicant_documents=payload.profile.documents_available,
        extracted_documents=documents_for_assessment,
    )

    # 5. Build the application preparation plan.
    application_plan = build_application_plan(
        scheme,
        available_documents=available_for_plan,
    )

    # 6. Generate practical next actions.
    actions: list[AssessmentAction] = []

    if eligibility.status == EligibilityStatus.NEEDS_REVIEW:
        _add_action(
            actions,
            AssessmentAction(
                code="eligibility:manual-review",
                source="eligibility",
                priority="high",
                title="Review scheme eligibility rules",
                detail=eligibility.reason,
            ),
        )

    if eligibility.status == EligibilityStatus.NEEDS_INFORMATION:
        for field in eligibility.missing_fields:
            _add_action(
                actions,
                AssessmentAction(
                    code=f"eligibility:missing:{field}",
                    source="eligibility",
                    priority="high",
                    title=(
                        f"Provide information: "
                        f"{field.replace('_', ' ')}"
                    ),
                    detail=(
                        "The eligibility evaluator needs the applicant's "
                        f"{field.replace('_', ' ')}."
                    ),
                ),
            )

    if eligibility.status == EligibilityStatus.NEEDS_REVIEW:
        for field in eligibility.missing_fields:
            _add_action(
                actions,
                AssessmentAction(
                    code=f"eligibility:missing:{field}",
                    source="eligibility",
                    priority="medium",
                    title=(
                        f"Provide information: "
                        f"{field.replace('_', ' ')}"
                    ),
                    detail=(
                        "This information is still missing from the "
                        "preliminary assessment: "
                        f"{field.replace('_', ' ')}."
                    ),
                ),
            )

    if eligibility.status == EligibilityStatus.INELIGIBLE:
        _add_action(
            actions,
            AssessmentAction(
                code="eligibility:failed",
                source="eligibility",
                priority="high",
                title="Review failed eligibility conditions",
                detail=(
                    "At least one condition in the approved rule failed. "
                    "Review the condition breakdown before taking further action."
                ),
            ),
        )

    # 7. Convert document findings into actions.
    if document_audit is not None:
        severity_priority = {
            "error": "high",
            "warning": "medium",
            "info": "low",
        }

        for finding in document_audit.findings:
            _add_action(
                actions,
                AssessmentAction(
                    code=f"document-audit:{finding.code}",
                    source="document_audit",
                    priority=severity_priority[finding.severity],
                    title=finding.message,
                    detail=(
                        finding.recommended_action
                        or "Review this document-audit finding."
                    ),
                ),
            )

    # 8. Add human-review workflow actions.
    if human_review_status == "pending_review":
        _add_action(
            actions,
            AssessmentAction(
                code="human-review:pending",
                source="document_audit",
                priority="high",
                title="Complete the pending document review",
                detail=(
                    "Inspect the original document, extracted fields and "
                    "outstanding findings in the reviewer dashboard."
                ),
            ),
        )

    if human_review_status == "review_completed":
        _add_action(
            actions,
            AssessmentAction(
                code="human-review:completed",
                source="document_audit",
                priority="low",
                title="Human review completed",
                detail=(
                    "The local reviewer workflow is marked complete. "
                    "This does not establish official certificate authenticity."
                ),
            ),
        )

    # 9. Convert outstanding planner document steps into actions.
    if eligibility.status != EligibilityStatus.INELIGIBLE:
        for step in application_plan.steps:
            if step.step_type != "obtain_document":
                continue

            _add_action(
                actions,
                AssessmentAction(
                    code=f"planner:{step.step_id}",
                    source="planner",
                    priority="medium",
                    title=step.title,
                    detail=step.notes,
                ),
            )

    # 10. Prioritise actions.
    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    actions.sort(
        key=lambda item: priority_order[item.priority]
    )

    lang = getattr(payload, "language", Language.EN)
    doc_prep = prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=documents_for_assessment,
        profile=payload.profile,
        target_financial_year=payload.target_financial_year,
        language=lang,
        today=date.today(),
    )
    portal_pkg = build_portal_application_package(
        scheme=scheme,
        profile=payload.profile,
        extracted_documents=documents_for_assessment,
        language=lang,
    )

    return ApplicantAssessmentResponse(
        scheme_id=scheme.scheme_id,
        scheme_name=scheme.name,
        eligibility=eligibility,
        document_audit=document_audit,
        application_plan=application_plan,
        declared_available_documents=list(
            payload.profile.documents_available
        ),
        human_review_status=human_review_status,
        human_review_id=human_review_id,
        next_actions=actions,
        document_prep_report=doc_prep,
        portal_guidance=portal_pkg,
    )
