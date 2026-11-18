"""Contract and Invariant Tests for Catalogue v2 Data Model.

Enforces Prime Directives:
- Directive 1: No fabrication (verbatim quotes required).
- Directive 2: Never "ELIGIBLE" on incomplete data (< 2 substantive criteria auto-flagged incomplete).
- CI Guard: Verified schemes can NEVER have residency-only rules.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import pytest
from pydantic import ValidationError

from scheme_navigator.domain.catalogue_v2 import (
    SchemeV2,
    Criterion,
    CriterionEvidence,
    CriterionStatus,
    SourceTier,
    VerificationStatus,
    VerificationMeta,
    BenefitDetails,
    ApplicationDetails,
)


def _base_scheme_kwargs() -> dict:
    return {
        "scheme_id": "test-scheme",
        "name_en": "Test Welfare Scheme",
        "name_mr": "चाचणी कल्याणकारी योजना",
        "department": "Social Justice and Special Assistance",
        "implementing_body": "Directorate of Social Welfare",
        "benefit": BenefitDetails(
            type="cash_transfer",
            amount_text="₹1,500 per month",
            amount_value=1500.0,
            frequency="monthly",
        ),
        "description_en": "Provides financial assistance to eligible beneficiaries.",
        "description_mr": "पात्र लाभार्थ्यांना आर्थिक सहाय्य पुरवते.",
        "application": ApplicationDetails(
            mode="online",
            portal="Aaple Sarkar",
            url="https://aaplesarkar.mahaonline.gov.in",
        ),
    }


def _sample_evidence(quote: str = "महाराष्ट्र राज्याचा रहिवासी असणे आवश्यक आहे") -> CriterionEvidence:
    return CriterionEvidence(
        quote_original=quote,
        source_url="https://gr.maharashtra.gov.in/test.pdf",
        tier=SourceTier.TIER_1,
        gr_ref="GR-2024-TEST",
    )


def test_residency_only_is_flagged_eligibility_incomplete():
    """A scheme with only residency has substantive_criteria_count=0 and eligibility_incomplete=True."""
    scheme = SchemeV2(
        **_base_scheme_kwargs(),
        eligibility=[
            Criterion(
                criterion_id="c_res",
                field="resident_state",
                operator="eq",
                value="maharashtra",
                plain_en="Must be a resident of Maharashtra",
                plain_mr="महाराष्ट्र राज्याचा रहिवासी असणे आवश्यक आहे",
                evidence=_sample_evidence(),
                status=CriterionStatus.VERIFIED,
            )
        ],
    )

    assert scheme.substantive_criteria_count == 0
    assert scheme.eligibility_incomplete is True


def test_one_substantive_criterion_remains_incomplete():
    """A scheme with residency + only 1 substantive criterion remains eligibility_incomplete=True."""
    scheme = SchemeV2(
        **_base_scheme_kwargs(),
        eligibility=[
            Criterion(
                criterion_id="c_res",
                field="resident_state",
                operator="eq",
                value="maharashtra",
                plain_en="Must be a resident of Maharashtra",
                plain_mr="महाराष्ट्र राज्याचा रहिवासी असणे आवश्यक आहे",
                evidence=_sample_evidence(),
                status=CriterionStatus.VERIFIED,
            ),
            Criterion(
                criterion_id="c_age",
                field="age",
                operator="gte",
                value=60,
                unit="years",
                plain_en="Age must be 60 years or above",
                plain_mr="वय ६० वर्षे किंवा त्याहून अधिक असावे",
                evidence=_sample_evidence("वय ६० वर्षे पूर्ण असणे आवश्यक आहे"),
                status=CriterionStatus.VERIFIED,
            ),
        ],
    )

    assert scheme.substantive_criteria_count == 1
    assert scheme.eligibility_incomplete is True


def test_two_verified_substantive_criteria_completes_eligibility():
    """A scheme with >= 2 verified substantive criteria has eligibility_incomplete=False."""
    scheme = SchemeV2(
        **_base_scheme_kwargs(),
        eligibility=[
            Criterion(
                criterion_id="c_res",
                field="resident_state",
                operator="eq",
                value="maharashtra",
                plain_en="Resident of Maharashtra",
                plain_mr="महाराष्ट्राचा रहिवासी",
                evidence=_sample_evidence(),
                status=CriterionStatus.VERIFIED,
            ),
            Criterion(
                criterion_id="c_age",
                field="age",
                operator="gte",
                value=60,
                unit="years",
                plain_en="Age 60+",
                plain_mr="वय ६०+",
                evidence=_sample_evidence("वय ६० वर्षे पूर्ण"),
                status=CriterionStatus.VERIFIED,
            ),
            Criterion(
                criterion_id="c_income",
                field="annual_family_income",
                operator="lte",
                value=250000,
                unit="INR",
                plain_en="Income <= 2.5 Lakh",
                plain_mr="उत्पन्न २.५ लाखांपर्यंत",
                evidence=_sample_evidence("कौटुंबिक उत्पन्न रु. २,५०,००० पेक्षा जास्त नसावे"),
                status=CriterionStatus.VERIFIED,
            ),
        ],
        verification=VerificationMeta(
            status=VerificationStatus.VERIFIED_PRIMARY,
            confidence=0.98,
            last_verified_at=datetime.now(timezone.utc),
        ),
    )

    assert scheme.substantive_criteria_count == 2
    assert scheme.eligibility_incomplete is False


def test_ci_guard_fails_if_verified_scheme_has_residency_only():
    """CI Guard Test: Instantiating a verified scheme with only residency rules MUST fail validation."""
    with pytest.raises(ValidationError, match="has only 0 substantive criteria"):
        SchemeV2(
            **_base_scheme_kwargs(),
            eligibility=[
                Criterion(
                    criterion_id="c_res",
                    field="resident_state",
                    operator="eq",
                    value="maharashtra",
                    plain_en="Resident of Maharashtra",
                    plain_mr="महाराष्ट्राचा रहिवासी",
                    evidence=_sample_evidence(),
                    status=CriterionStatus.VERIFIED,
                )
            ],
            verification=VerificationMeta(
                status=VerificationStatus.VERIFIED_PRIMARY,
                confidence=1.0,
            ),
        )


def test_vocabulary_rejects_unregistered_field():
    """Fields not present in the Canonical Profile Vocabulary must be rejected."""
    with pytest.raises(ValidationError, match="Field 'invented_arbitrary_field' is not registered"):
        Criterion(
            criterion_id="c_fail",
            field="invented_arbitrary_field",
            operator="eq",
            value="something",
            plain_en="Invalid field",
            plain_mr="अवैध फील्ड",
        )


def test_quote_original_rejects_placeholder_text():
    """Evidence rejects dummy placeholder quotes."""
    with pytest.raises(ValidationError, match="quote_original must be a substantive verbatim quote"):
        CriterionEvidence(
            quote_original="n/a",
            source_url="https://example.gov.in",
            tier=SourceTier.TIER_1,
        )
