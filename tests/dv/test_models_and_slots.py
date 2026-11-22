"""TRIMURTI / MSN-DV-001 Models, Slots & Denominator Honesty Tests (Slice 1).

Tests:
- Top 5 Global DocType Profiles completeness (trilingual names, description, where_to_get).
- 10 Pilot Schemes Requirement Slots traceability and trust tiers.
- Alternatives handling (one accepted document satisfies slot; others not demanded).
- Denominator honesty counting logic (Formula: N of M needs covered, §4.3).
- Conditional applicability and non-pilot unconfirmed fallback.
"""

from __future__ import annotations

import pytest

from scheme_navigator.dv.models import (
    RequirementKind,
    RequirementTrustTier,
    SlotState,
)
from scheme_navigator.dv.slots import (
    PILOT_SCHEME_SLOTS,
    TOP_5_DOCTYPES,
    evaluate_slots_for_citizen,
    get_scheme_slots,
)


def test_top_5_doctypes_profiles_completeness():
    """Verify Top 5 DocType Profiles have complete trilingual metadata and field schemas."""
    expected_ids = {
        "DOC-INCOME-CERT",
        "DOC-DOMICILE-CERT",
        "DOC-RATION-CARD",
        "DOC-BANK-PASSBOOK",
        "DOC-AADHAAR-CARD",
    }
    assert set(TOP_5_DOCTYPES.keys()) == expected_ids

    for dt_id, profile in TOP_5_DOCTYPES.items():
        assert profile.id == dt_id
        # Trilingual names
        for lang in ("en", "mr", "hi"):
            assert lang in profile.names and len(profile.names[lang]) > 0
            assert lang in profile.plain_description and len(profile.plain_description[lang]) > 0
            assert lang in profile.where_to_get and len(profile.where_to_get[lang]) > 0
        assert len(profile.fields) >= 3


def test_10_pilot_schemes_slots_evidence():
    """Verify all 10 pilot schemes have requirement slots with valid source evidence (Law L1)."""
    expected_pilot_schemes = [
        "scheme-namo-shetkari-maha-samman",
        "scheme-pm-kisan",
        "scheme-mukhyamantri-vayoshri",
        "scheme-igndps-disability-pension",
        "scheme-ignwps-widow-pension",
        "scheme-ebc-tuition-waiver",
        "candidate-post-matric-obc",
        "scheme-cmegp-self-employment",
        "scheme-annasaheb-patil-ir2",
        "scheme-ramai-awas-yojana",
    ]
    assert len(PILOT_SCHEME_SLOTS) == 10
    for s_id in expected_pilot_schemes:
        assert s_id in PILOT_SCHEME_SLOTS, f"Missing pilot scheme {s_id}!"
        slots = PILOT_SCHEME_SLOTS[s_id]
        assert len(slots) >= 2, f"Scheme {s_id} has fewer than 2 slots!"

        for slot in slots:
            assert slot.scheme_id == s_id
            assert slot.source_type in ("GOVERNMENT_RESOLUTION", "OFFICIAL_PORTAL", "ACT", "GAZETTE")
            assert slot.source_reference and len(slot.source_reference.strip()) > 3
            assert slot.trust_tier in (RequirementTrustTier.SOURCE_VERIFIED, RequirementTrustTier.APPROVED)
            assert len(slot.accepted) >= 1


def test_alternatives_one_accepted_doctype_satisfies_slot():
    """Section 3 Assumption 1: One slot may accept several document types.
    Uploading one accepted alternative satisfies the slot; the others are NOT demanded.
    """
    scheme_id = "scheme-mukhyamantri-vayoshri"
    # SLOT-VAYO-AGE-IDENTITY accepts DOC-AADHAAR-CARD OR DOC-DOMICILE-CERT
    # Citizen provides ONLY Domicile Certificate (no Aadhaar)
    uploaded = [{"doc_id": "doc-001", "doctype_id": "DOC-DOMICILE-CERT"}]
    
    summary = evaluate_slots_for_citizen(scheme_id, citizen_profile={"is_divyang": False}, uploaded_docs=uploaded)
    
    age_slot_eval = next(e for e in summary.evaluations if e.slot.slot_id == "SLOT-VAYO-AGE-IDENTITY")
    assert age_slot_eval.state == SlotState.SATISFIED
    assert age_slot_eval.satisfied_by_doctype_id == "DOC-DOMICILE-CERT"


def test_single_document_can_satisfy_multiple_slots():
    """One document may satisfy multiple slots (e.g. Domicile satisfies Age & Residence)."""
    scheme_id = "scheme-mukhyamantri-vayoshri"
    # Domicile Certificate satisfies both SLOT-VAYO-AGE-IDENTITY and SLOT-VAYO-DOMICILE
    uploaded = [{"doc_id": "doc-domicile-99", "doctype_id": "DOC-DOMICILE-CERT"}]
    
    summary = evaluate_slots_for_citizen(scheme_id, citizen_profile={"is_divyang": False}, uploaded_docs=uploaded)
    
    satisfied_slots = [e for e in summary.evaluations if e.state == SlotState.SATISFIED]
    satisfied_ids = {e.slot.slot_id for e in satisfied_slots}
    assert "SLOT-VAYO-AGE-IDENTITY" in satisfied_ids
    assert "SLOT-VAYO-DOMICILE" in satisfied_ids
    assert summary.satisfied_needs_n == 2


def test_denominator_honesty_counting_formula():
    """Section 4.3 Counting rules: N of M needs covered.
    M = applicable mandatory slots + conditional slots where applicability is TRUE.
    Unknown conditional slots appear in separate bucket.
    """
    scheme_id = "scheme-mukhyamantri-vayoshri"
    # 4 mandatory slots + 1 conditional slot (SLOT-VAYO-DISABILITY)

    # Case A: Profile does NOT specify is_divyang (Unknown)
    # -> M = 4, unknown_conditional_count = 1
    summary_a = evaluate_slots_for_citizen(scheme_id, citizen_profile={}, uploaded_docs=[])
    assert summary_a.total_applicable_needs_m == 4
    assert summary_a.satisfied_needs_n == 0
    assert summary_a.unknown_conditional_count == 1

    # Case B: Profile specifies is_divyang = False
    # -> M = 4, unknown_conditional_count = 0
    summary_b = evaluate_slots_for_citizen(scheme_id, citizen_profile={"is_divyang": False}, uploaded_docs=[])
    assert summary_b.total_applicable_needs_m == 4
    assert summary_b.unknown_conditional_count == 0

    # Case C: Profile specifies is_divyang = True
    # -> M = 5 (4 mandatory + 1 conditional met)
    summary_c = evaluate_slots_for_citizen(scheme_id, citizen_profile={"is_divyang": True}, uploaded_docs=[])
    assert summary_c.total_applicable_needs_m == 5
    assert summary_c.unknown_conditional_count == 0

    # Test headline strings
    assert summary_b.get_headline_text("वयोश्री", lang="mr") == "वयोश्री साठी तुम्हाला 4 कागदपत्रे लागतील. तुमच्याकडे 0 तयार आहेत."
    assert summary_b.get_headline_text("Vayoshri", lang="en") == "To apply for Vayoshri you need 4 papers. You have 0."


def test_non_pilot_scheme_fallback_unconfirmed():
    """Non-pilot scheme returns unconfirmed requirement without fabricating fake checklist (Law L1 & L12)."""
    fake_scheme_id = "scheme-random-non-pilot-999"
    summary = evaluate_slots_for_citizen(fake_scheme_id, citizen_profile={}, uploaded_docs=[])
    
    assert summary.total_applicable_needs_m == 0
    assert summary.unconfirmed_requirements_count == 1
    assert len(summary.evaluations) == 1
    eval_item = summary.evaluations[0]
    assert eval_item.state == SlotState.REQUIREMENT_UNCONFIRMED
    assert eval_item.slot.trust_tier == RequirementTrustTier.UNKNOWN
    assert "aaplesarkar" in eval_item.slot.source_reference
