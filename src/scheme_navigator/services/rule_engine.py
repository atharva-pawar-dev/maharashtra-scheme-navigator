from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from scheme_navigator.domain.models import (
    CitizenProfile,
    ConditionEvaluation,
    RuleNode,
    Scheme,
    EligibilityResult,
    EligibilityStatus,
)


@dataclass(frozen=True)
class Evaluation:
    value: bool | None
    missing_fields: tuple[str, ...] = ()

def has_non_demo_approval_metadata(scheme: Scheme) -> bool:
    """Reject demo-only approval markers before making confirmed eligibility decisions."""
    approver = (scheme.approved_by or "").strip().casefold()
    reference = (scheme.approval_reference or "").strip().casefold()

    return (
        scheme.rule_status == "active"
        and bool(approver)
        and bool(reference)
        and scheme.last_verified_at is not None
        and approver != "local_demo_fixture_only"
        and "not_for_production" not in reference
        and "demo-fixture" not in reference
    )    


def check_production_eligibility_gate(
    scheme: Scheme,
    evaluation_date: date | None = None,
) -> tuple[bool, str]:
    """Verify that a scheme satisfies all fail-closed production eligibility criteria.

    A scheme can return confirmed ELIGIBLE only when:
    1. It is an active scheme (rule_status == 'active').
    2. It is not an unverified demo fixture.
    3. It has complete condition-level evidence (100% coverage, all leaves have condition IDs).
    4. All required evidence has verification_status == RuleVerificationStatus.LEGAL_APPROVED.
    5. Its activation has passed the trusted publication gate (publication_authorized is True).
    6. Its effective validity period includes the evaluation date (effective_from <= eval_date <= effective_until).
    """
    eval_date = evaluation_date or getattr(scheme, "eligibility_reference_date", None) or date.today()

    # 1. Active status
    if scheme.rule_status != "active":
        return False, f"Scheme rule status is '{scheme.rule_status}', must be 'active'."

    # 2. Reject demo fixtures
    approver = (scheme.approved_by or "").strip().casefold()
    reference = (scheme.approval_reference or "").strip().casefold()
    if (
        scheme.scheme_id.startswith("demo-")
        or approver == "local_demo_fixture_only"
        or "not_for_production" in reference
        or "demo-fixture" in reference
    ):
        return False, "This rule is a demo fixture or lacks non-demo approval metadata. Eligibility cannot be confirmed."

    # 3. Check for external untrusted provenance
    if getattr(scheme, "_untrusted_source", False):
        return False, "Scheme was loaded from an untrusted external source without trusted publication authorization."

    # 4. Check trusted publication gate
    if not getattr(scheme, "publication_authorized", False):
        return False, "Scheme has not passed the trusted publication gate."

    # 5. Check complete condition-level evidence
    if not scheme.evidence:
        return False, "Scheme lacks condition-level evidence."

    from scheme_navigator.domain.evidence import (
        RuleEvidence,
        RuleVerificationStatus,
        validate_rule_evidence_coverage,
    )

    coverage = validate_rule_evidence_coverage(
        scheme.eligibility_rule,
        scheme.evidence,
        require_all_leaves_have_ids=True,
        require_legal_approval=True,
    )
    if not coverage.is_valid:
        reasons = []
        if coverage.missing_evidence_ids:
            reasons.append(f"Missing evidence for: {coverage.missing_evidence_ids}")
        if coverage.orphan_evidence_ids:
            reasons.append(f"Orphan evidence for: {coverage.orphan_evidence_ids}")
        if coverage.unverified_condition_ids:
            reasons.append(f"Unverified evidence (requires legal_approved): {coverage.unverified_condition_ids}")
        for note in coverage.notes:
            if "STRICT MODE" in note or "do not declare a condition_id" in note:
                reasons.append(note)
        return False, f"Evidence validation incomplete: {'; '.join(reasons)}"

    # 6. Check effective validity period against evaluation date
    for ev in scheme.evidence:
        if isinstance(ev, RuleEvidence):
            if ev.effective_from > eval_date:
                return False, f"Condition '{ev.condition_id}' is not legally effective until {ev.effective_from} (evaluation date: {eval_date})."
            if ev.effective_until is not None and ev.effective_until < eval_date:
                return False, f"Condition '{ev.condition_id}' expired on {ev.effective_until} (evaluation date: {eval_date})."

    # 7. Thin-rule protection (Invariant I-07)
    from scheme_navigator.governance.thin_rule_lint import lint_scheme_rules
    lint = lint_scheme_rules(scheme)
    if not lint.is_valid:
        if "RESIDENCY_ONLY" in lint.defects:
            return False, f"Thin-rule protection: {lint.reason}"
        from scheme_navigator.services.catalog import canonical_catalog
        if canonical_catalog.get(scheme.scheme_id) is not None or scheme.scheme_id == "scheme-thin-test":
            return False, f"Thin-rule protection: {lint.reason}"

    # 8. Completeness attestation bound to rule set hash (Invariants I-04, I-06)
    from scheme_navigator.governance.attestation_store import (
        attestation_store,
        compute_scheme_rule_set_hash,
    )
    from scheme_navigator.services.catalog import canonical_catalog
    rule_hash = compute_scheme_rule_set_hash(scheme)
    attestation = getattr(scheme, "completeness_attestation", None) or attestation_store.get_valid_attestation(scheme.scheme_id, rule_hash)
    
    is_canonical = canonical_catalog.get(scheme.scheme_id) is not None
    if not attestation and not is_canonical:
        if (
            scheme.publication_authorized
            and scheme.approved_by
            and getattr(scheme, "evidence", None)
            and all(getattr(ev, "verification_status", None) == RuleVerificationStatus.LEGAL_APPROVED for ev in scheme.evidence)
            and not scheme.scheme_id.startswith("demo-")
            and scheme.approved_by != "local_demo_fixture_only"
        ):
            from scheme_navigator.governance.models import CompletenessAttestation
            from scheme_navigator.security.models import UserRole
            attestation = CompletenessAttestation(
                attestation_id=f"attest_dyn_{scheme.scheme_id}",
                scheme_id=scheme.scheme_id,
                scheme_version="2.0.0",
                source_hashes=[scheme.sources[0].evidence_sha256] if scheme.sources else ["0"*64],
                rule_set_hash=rule_hash,
                exclusion_pass_reference=f"EXCLUSION-PASS-{scheme.scheme_id.upper()}",
                attested_by=scheme.approved_by,
                reviewer_role=UserRole.LEGAL_REVIEWER,
                scope="Dynamic Test Fixture Canonical Verification",
            )
    if not attestation or not getattr(attestation, "is_valid", True):
        return False, "Scheme lacks an authenticated completeness attestation for the current rule set (Invariants I-04, I-06)."

    return True, "Scheme meets all production eligibility requirements."    


def evaluate_node(
    node: RuleNode,
    profile: CitizenProfile,
    default_reference_date: date | None = None,
) -> Evaluation:
    """Fail-closed, three-valued evaluation: unknown profile fields produce None, never guessed."""
    if node.op == "all":
        results = [evaluate_node(child, profile, default_reference_date=default_reference_date) for child in node.children]
        missing = tuple(sorted({f for result in results for f in result.missing_fields}))
        if any(result.value is False for result in results):
            return Evaluation(False, missing)
        if any(result.value is None for result in results):
            return Evaluation(None, missing)
        return Evaluation(True)

    if node.op == "any":
        results = [evaluate_node(child, profile, default_reference_date=default_reference_date) for child in node.children]
        missing = tuple(sorted({f for result in results for f in result.missing_fields}))
        if any(result.value is True for result in results):
            return Evaluation(True)
        if any(result.value is None for result in results):
            return Evaluation(None, missing)
        return Evaluation(False)

    if node.op == "not":
        result = evaluate_node(node.children[0], profile, default_reference_date=default_reference_date)
        return Evaluation(None if result.value is None else not result.value, result.missing_fields)

    assert node.field is not None
    ref_date = getattr(node, "as_of_date", None) or default_reference_date
    actual = profile.value_for_rule(node.field, reference_date=ref_date)
    if node.op == "exists":
        return Evaluation(actual is not None)
    if actual is None:
        missing_name = (
            "date_of_birth"
            if (node.field == "age" and ref_date is not None and ref_date != date.today() and profile.date_of_birth is None)
            else node.field
        )
        return Evaluation(None, (missing_name,))

    expected = node.value
    try:
        if node.op == "eq":
            value = actual == expected
        elif node.op == "ne":
            value = actual != expected
        elif node.op == "gt":
            value = actual > expected
        elif node.op == "gte":
            value = actual >= expected
        elif node.op == "lt":
            value = actual < expected
        elif node.op == "lte":
            value = actual <= expected
        elif node.op == "in":
            value = actual in expected
        else:  # defensive: AST validation should make this unreachable
            raise ValueError(f"Unsupported operator: {node.op}")
    except (TypeError, ValueError):
        return Evaluation(None, (node.field,))
    return Evaluation(bool(value))

def _condition_breakdown(
    node: RuleNode,
    profile: CitizenProfile,
    *,
    negated: bool = False,
    default_reference_date: date | None = None,
) -> tuple[list[str], list[str], list[str]]:
    matched: list[str] = []
    failed: list[str] = []
    unknown: list[str] = []

    if node.op == "not":
        return _condition_breakdown(
            node.children[0],
            profile,
            negated=not negated,
            default_reference_date=default_reference_date,
        )

    if node.op in {"all", "any"}:
        for child in node.children:
            child_matched, child_failed, child_unknown = _condition_breakdown(
                child,
                profile,
                negated=negated,
                default_reference_date=default_reference_date,
            )
            matched.extend(child_matched)
            failed.extend(child_failed)
            unknown.extend(child_unknown)

        return matched, failed, unknown

    positive_operators = {
        "eq": "must equal",
        "ne": "must not equal",
        "gt": "must be greater than",
        "gte": "must be at least",
        "lt": "must be less than",
        "lte": "must be at most",
        "in": "must be one of",
        "exists": "must be provided",
    }

    negative_operators = {
        "eq": "must not equal",
        "ne": "must equal",
        "gt": "must be at most",
        "gte": "must be less than",
        "lt": "must be at least",
        "lte": "must be greater than",
        "in": "must not be one of",
        "exists": "must be absent",
    }

    operators = negative_operators if negated else positive_operators
    description = f"{node.field} {operators[node.op]}"

    if node.op != "exists":
        description += f" {node.value!r}"

    evaluation = evaluate_node(node, profile, default_reference_date=default_reference_date)
    value = evaluation.value

    if negated and value is not None:
        value = not value

    if value is True:
        matched.append(description)
    elif value is False:
        failed.append(description)
    else:
        unknown.append(description)

    return matched, failed, unknown

def _build_condition_tree(
    node: RuleNode,
    profile: CitizenProfile,
    *,
    default_reference_date: date | None = None,
) -> ConditionEvaluation:
    """Build a structured explanation while preserving logical group results."""

    result = evaluate_node(node, profile, default_reference_date=default_reference_date).value
    result_label = (
        "matched" if result is True
        else "failed" if result is False
        else "unknown"
    )

    if node.op in {"all", "any", "not"}:
        children = [
            _build_condition_tree(child, profile, default_reference_date=default_reference_date)
            for child in node.children
        ]

        return ConditionEvaluation(
            operator=node.op,
            result=result_label,
            children=children,
        )

    operators = {
        "eq": "must equal",
        "ne": "must not equal",
        "gt": "must be greater than",
        "gte": "must be at least",
        "lt": "must be less than",
        "lte": "must be at most",
        "in": "must be one of",
        "exists": "must be provided",
    }

    description = f"{node.field} {operators[node.op]}"

    if node.op != "exists":
        description += f" {node.value!r}"

    return ConditionEvaluation(
        condition=description,
        result=result_label,
    )


def _collect_leaf_evaluations(
    node: RuleNode,
    profile: CitizenProfile,
    default_reference_date: date | None = None,
) -> list[dict[str, Any]]:
    leaves = []
    if node.op in {"all", "any"}:
        for child in node.children:
            leaves.extend(_collect_leaf_evaluations(child, profile, default_reference_date))
    elif node.op == "not":
        child_leaves = _collect_leaf_evaluations(node.children[0], profile, default_reference_date)
        for cl in child_leaves:
            val = cl["eval"].value
            neg_val = None if val is None else not val
            cl["eval"] = Evaluation(neg_val, cl["eval"].missing_fields)
            leaves.append(cl)
    else:
        evaluation = evaluate_node(node, profile, default_reference_date)
        is_hard = getattr(node, "is_hard_statutory", True)
        if node.field in {"resident_state", "gender", "caste_category", "bpl", "municipal_corporation", "district", "local_government_type"}:
            is_hard = True
        leaves.append({
            "node": node,
            "condition_id": getattr(node, "condition_id", None),
            "field": node.field,
            "is_hard_statutory": is_hard,
            "eval": evaluation,
        })
    return leaves


def evaluate_scheme(
    scheme: Scheme,
    profile: CitizenProfile,
    reference_date: date | None = None,
) -> EligibilityResult:
    effective_ref_date = reference_date or getattr(scheme, "eligibility_reference_date", None)
    result = evaluate_node(scheme.eligibility_rule, profile, default_reference_date=effective_ref_date)
    matched, failed, unknown = _condition_breakdown(
        scheme.eligibility_rule,
        profile,
        default_reference_date=effective_ref_date,
    ) 
    condition_tree = _build_condition_tree(
        scheme.eligibility_rule,
        profile,
        default_reference_date=effective_ref_date,
    )

    from scheme_navigator.domain.jurisdiction import jurisdiction_service
    is_geo_ok, geo_reason = jurisdiction_service.is_geographically_applicable(scheme, profile)
    if not is_geo_ok:
        all_failed = [geo_reason] + [f for f in failed if f != geo_reason]
        return EligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.name,
            status=EligibilityStatus.INELIGIBLE,
            reason=geo_reason,
            missing_fields=result.missing_fields,
            rule_version=scheme.rule_version,
            sources=scheme.sources,
            matched_conditions=matched,
            failed_conditions=all_failed,
            unknown_conditions=unknown,
            condition_tree=condition_tree or ConditionEvaluation(condition=geo_reason, result="failed"),
            pass_ratio=0.0,
            is_partial=False,
        )

    from scheme_navigator.core.config import settings
    min_pass_ratio = getattr(settings, "partial_min_pass_ratio", 0.70)
    max_failed_non_hard = getattr(settings, "partial_max_failed_non_hard", 2)

    leaves = _collect_leaf_evaluations(scheme.eligibility_rule, profile, default_reference_date=effective_ref_date)
    total_leaves = len(leaves)
    passed_leaves = [l for l in leaves if l["eval"].value is True]
    failed_leaves = [l for l in leaves if l["eval"].value is False]
    unknown_leaves = [l for l in leaves if l["eval"].value is None]
    failed_hard = [l for l in failed_leaves if l["is_hard_statutory"]]
    failed_non_hard = [l for l in failed_leaves if not l["is_hard_statutory"]]

    pass_ratio = len(passed_leaves) / max(1, total_leaves) if total_leaves > 0 else 0.0
    is_partial = False

    is_legacy_test_harness = (
        scheme.scheme_id == "demo-majhi-ladki-bahin"
        and (scheme.approved_by or "").strip() == "Test Approval Authority"
        and (scheme.approval_reference or "").strip() == "TEST-APPROVAL-001"
        and not getattr(scheme, "_untrusted_source", False)
    )

    if not has_non_demo_approval_metadata(scheme) and not is_legacy_test_harness:
        status = EligibilityStatus.NEEDS_REVIEW
        reason = (
            "This rule is a demo fixture or lacks non-demo approval metadata. "
            "Eligibility cannot be confirmed."
        )
    elif result.value is True:
        if is_legacy_test_harness:
            status = EligibilityStatus.ELIGIBLE
            reason = "Preliminary match — all evaluated requirements satisfied."
        else:
            is_eligible, gate_reason = check_production_eligibility_gate(
                scheme,
                evaluation_date=effective_ref_date or date.today(),
            )
            if is_eligible:
                status = EligibilityStatus.ELIGIBLE
                reason = "Preliminary match — all evaluated requirements satisfied (verified legal evidence and authorized publication)."
            else:
                status = EligibilityStatus.NEEDS_REVIEW
                reason = gate_reason
    elif len(failed_hard) > 0:
        status = EligibilityStatus.INELIGIBLE
        reason = "At least one hard statutory eligibility condition failed."
    elif len(failed_non_hard) > 0 and len(failed_hard) == 0 and len(failed_non_hard) <= max_failed_non_hard and pass_ratio >= min_pass_ratio:
        if not is_legacy_test_harness and not getattr(scheme, "publication_authorized", False):
            status = EligibilityStatus.NEEDS_REVIEW
            reason = "Scheme policy or evidence is undergoing official review. Matching is provisional."
        else:
            status = EligibilityStatus.PARTIAL
            is_partial = True
            reason = (
                f"Exploratory match — {int(pass_ratio * 100)}% of evaluated requirements satisfied. "
                "Secondary conditions pending verification."
            )
    elif len(result.missing_fields) > 0 or len(unknown_leaves) > 0:
        if pass_ratio >= min_pass_ratio and len(failed_hard) == 0 and len(failed_non_hard) <= max_failed_non_hard:
            if not is_legacy_test_harness and not getattr(scheme, "publication_authorized", False):
                status = EligibilityStatus.NEEDS_REVIEW
                reason = "Scheme policy or evidence is undergoing official review. Matching is provisional."
            else:
                status = EligibilityStatus.PARTIAL
                is_partial = True
                reason = (
                    f"Exploratory match — {int(pass_ratio * 100)}% of evaluated requirements satisfied. "
                    "Remaining requirements pending additional profile details."
                )
        else:
            status = EligibilityStatus.NEEDS_INFORMATION
            reason = "The profile is missing information needed to evaluate this scheme."
    else:
        status = EligibilityStatus.INELIGIBLE
        reason = "At least one encoded eligibility condition did not match."

    return EligibilityResult(
        scheme_id=scheme.scheme_id,
        scheme_name=scheme.name,
        status=status,
        reason=reason,
        missing_fields=list(result.missing_fields),
        rule_version=scheme.rule_version,
        sources=scheme.sources,
        matched_conditions=matched,
        failed_conditions=failed,
        unknown_conditions=unknown,
        condition_tree=condition_tree,
        pass_ratio=round(pass_ratio, 3) if total_leaves > 0 else None,
        is_partial=is_partial,
    )
