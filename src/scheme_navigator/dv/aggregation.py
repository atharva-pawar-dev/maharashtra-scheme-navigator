"""TRIMURTI / MSN-DV-001 Multidimensional Readiness Aggregator (Law L2 & L3).

Enforces:
- Law L2: 'Dimensions never merge.' Eligibility, paper coverage, content check,
  consistency, authenticity, prerequisites, and preparation-readiness are separate
  fields. NO composite score (e.g. '85% ready') is ever computed or returned.
- Law L3: 'Unknown stays unknown.' Results are PASS / FAIL / UNCERTAIN / NOT_APPLICABLE / NOT_CHECKED.
  UNCERTAIN and UNKNOWN never collapse into pass or fail in code, counts, or UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class CheckVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_CHECKED = "NOT_CHECKED"


class AuthenticityTier(str, Enum):
    TIER_0_UNVERIFIED = "TIER_0_UNVERIFIED"
    TIER_1_OCR_CONSISTENT = "TIER_1_OCR_CONSISTENT"
    TIER_2_QR_DECODED = "TIER_2_QR_DECODED"
    TIER_3_ISSUER_CONFIRMED = "TIER_3_ISSUER_CONFIRMED"
    NOT_CONFIGURED = "NOT_CONFIGURED"


@dataclass(frozen=True)
class CheckResult:
    check_name: str
    verdict: CheckVerdict
    summary_key: str
    details: Optional[str] = None


@dataclass(frozen=True)
class SchemeReadinessDimensions:
    """The 7 distinct dimensions defined by Law L2.
    
    CRUCIAL: No composite numeric score exists here.
    """
    eligibility_verdict: str                  # e.g. ELIGIBLE, CONDITIONAL, UNKNOWN
    paper_coverage_status: str                # e.g. COVERED, PARTIALLY_COVERED, MISSING_REQUIRED
    content_verdict: CheckVerdict             # Aggregate of content checks
    consistency_verdict: CheckVerdict         # Across-document cross-checks
    authenticity_tier: AuthenticityTier       # Default NOT_CONFIGURED or TIER_0
    prerequisites_met: bool                   # Whether scheme prerequisites are met
    preparation_action: str                   # Next discrete human action

    def has_composite_score(self) -> bool:
        """Tripwire helper: confirms no score field exists in object dictionary."""
        forbidden_keys = {"score", "readiness_score", "percentage", "percent", "readiness_percentage"}
        return any(k in self.__dict__ for k in forbidden_keys)


def aggregate_verdicts(verdicts: List[CheckVerdict]) -> CheckVerdict:
    """Aggregate a collection of check verdicts adhering strictly to Law L3.
    
    Rules:
    - If empty -> NOT_CHECKED
    - If any verdict is FAIL -> FAIL
    - If any verdict is UNCERTAIN -> UNCERTAIN (never collapsed to PASS or FAIL)
    - If all verdicts are NOT_APPLICABLE -> NOT_APPLICABLE
    - If all active verdicts are PASS -> PASS
    - If only NOT_CHECKED / NOT_APPLICABLE -> NOT_CHECKED
    """
    if not verdicts:
        return CheckVerdict.NOT_CHECKED

    unique = set(verdicts)

    # Hard failures take precedence
    if CheckVerdict.FAIL in unique:
        return CheckVerdict.FAIL

    # Crucial Law L3: UNCERTAIN must stay UNCERTAIN! Never collapse to PASS or FAIL
    if CheckVerdict.UNCERTAIN in unique:
        return CheckVerdict.UNCERTAIN

    # If only NOT_APPLICABLE and PASS
    active = {v for v in unique if v != CheckVerdict.NOT_APPLICABLE}
    if not active:
        return CheckVerdict.NOT_APPLICABLE

    if active == {CheckVerdict.PASS}:
        return CheckVerdict.PASS

    if active == {CheckVerdict.NOT_CHECKED}:
        return CheckVerdict.NOT_CHECKED

    if CheckVerdict.NOT_CHECKED in active:
        return CheckVerdict.NOT_CHECKED

    return CheckVerdict.UNCERTAIN
