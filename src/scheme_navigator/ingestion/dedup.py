from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from scheme_navigator.ingestion.models import (
    DuplicateCandidateMatch,
    DuplicateDetectionReport,
    SchemeAlias,
)

# Authoritative registry of known aliases and distinct branches for Maharashtra schemes
KNOWN_MAHARASHTRA_SCHEME_ALIASES: dict[str, list[SchemeAlias]] = {
    "candidate-majhi-ladki-bahin": [
        SchemeAlias(alias="Mukhyamantri Majhi Ladki Bahin Yojana", language="en", alias_type="canonical_title"),
        SchemeAlias(alias="मुख्यमंत्री - माझी लाडकी बहीण योजना", language="mr", alias_type="vernacular_title"),
        SchemeAlias(alias="मुख्यमंत्री माझी लाडकी बहीण योजना", language="mr", alias_type="vernacular_title"),
        SchemeAlias(alias="माझी लाडकी बहीण", language="mr", alias_type="portal_alias"),
        SchemeAlias(alias="MMLBY", language="en", alias_type="acronym"),
        SchemeAlias(alias="Ladki Bahin Yojana", language="en", alias_type="portal_alias"),
    ],
    "candidate-sanjay-gandhi-niradhar": [
        SchemeAlias(alias="Sanjay Gandhi Niradhar Anudan Yojana", language="en", alias_type="canonical_title"),
        SchemeAlias(alias="संजय गांधी निराधार अनुदान योजना", language="mr", alias_type="vernacular_title"),
        SchemeAlias(alias="संजय गांधी निराधार योजना", language="mr", alias_type="portal_alias"),
        SchemeAlias(alias="SGNAY", language="en", alias_type="acronym"),
    ],
    "candidate-shravanbal-nivruttivetan": [
        SchemeAlias(alias="Shravanbal Seva Rajya Nivruttivetan Yojana", language="en", alias_type="canonical_title"),
        SchemeAlias(alias="श्रावणबाळ सेवा राज्य निवृत्तीवेतन योजना", language="mr", alias_type="vernacular_title"),
        SchemeAlias(alias="श्रावणबाळ योजना", language="mr", alias_type="portal_alias"),
        SchemeAlias(alias="Shravan Bal Yojana", language="en", alias_type="portal_alias"),
        SchemeAlias(alias="SSRNBY", language="en", alias_type="acronym"),
    ],
    "candidate-post-matric-sc": [
        SchemeAlias(alias="Centrally Sponsored Post-Matric Scholarship for SC Students", language="en", alias_type="canonical_title"),
        SchemeAlias(alias="Government of India Post-Matric Scholarship for SC Students", language="en", alias_type="portal_alias"),
        SchemeAlias(alias="भारत सरकार मॅट्रिकोत्तर शिष्यवृत्ती - अनुसूचित जाती", language="mr", alias_type="vernacular_title"),
        SchemeAlias(alias="Post Matric Scholarship to Scheduled Caste Students", language="en", alias_type="portal_alias"),
    ],
    "candidate-post-matric-obc": [
        SchemeAlias(alias="Post Matric Scholarship to OBC Students", language="en", alias_type="canonical_title"),
        SchemeAlias(alias="इतर मागासवर्गीय मॅट्रिकोत्तर शिष्यवृत्ती योजना", language="mr", alias_type="vernacular_title"),
        SchemeAlias(alias="OBC Post Matric Scholarship", language="en", alias_type="portal_alias"),
    ],
    "candidate-post-matric-obc-girls-professional": [
        SchemeAlias(alias="Post Matric Scholarship to the Girls Belonging to OBC taking admission in Professional Courses", language="en", alias_type="canonical_title"),
        SchemeAlias(alias="व्यावसायिक अभ्यासक्रमास प्रवेश घेणाऱ्या इतर मागास प्रवर्गातील मुलींना मॅट्रिकोत्तर शिष्यवृत्ती", language="mr", alias_type="vernacular_title"),
        SchemeAlias(alias="OBC Girls Professional Course Post Matric Scholarship", language="en", alias_type="portal_alias"),
    ],
    "candidate-payment-tuition-exam-fees-obc-girls": [
        SchemeAlias(alias="Payment of Tuition Fees and Examination Fees to OBC Girls Pursuing Professional Courses", language="en", alias_type="canonical_title"),
        SchemeAlias(alias="व्यावसायिक अभ्यासक्रमास प्रवेश घेणाऱ्या इतर मागास प्रवर्गातील मुलींना शिक्षण शुल्क व परीक्षा शुल्क प्रतिपूर्ती", language="mr", alias_type="vernacular_title"),
        SchemeAlias(alias="OBC Girls 100 Percent Tuition and Examination Fee Reimbursement", language="en", alias_type="portal_alias"),
        SchemeAlias(alias="GR 8 July 2024 Girls Fee Waiver", language="en", alias_type="portal_alias"),
    ],
}

# Known distinct pairs that must NEVER be collapsed or merged as duplicates
KNOWN_DISTINCT_BRANCH_PAIRS = {
    frozenset(["candidate-post-matric-obc", "candidate-post-matric-obc-girls-professional"]): (
        "Standard OBC Post-Matric covers all genders and all post-matric courses under OBC Bahujan Welfare Dept. "
        "Girls Professional is a dedicated separate intake track on MahaDBT for female students in professional disciplines."
    ),
    frozenset(["candidate-post-matric-obc-girls-professional", "candidate-payment-tuition-exam-fees-obc-girls"]): (
        "Post-Matric Scholarship provides maintenance allowance with ₹2.5L limit under OBC Bahujan Welfare Dept. "
        "Payment of Tuition/Exam Fees under GR 8 July 2024 provides 100% fees only with ₹8L limit under Higher & Tech Education Dept."
    ),
    frozenset(["candidate-post-matric-obc", "candidate-payment-tuition-exam-fees-obc-girls"]): (
        "Standard OBC Post-Matric has ₹1L-₹2.5L threshold with maintenance allowance; 8 July 2024 GR is ₹8L threshold fee-only."
    ),
    frozenset(["candidate-sanjay-gandhi-niradhar", "candidate-shravanbal-nivruttivetan"]): (
        "Sanjay Gandhi Niradhar applies to destitute individuals under 65 years. At age 65, beneficiaries transition to Shravanbal."
    ),
}


def _normalize_tokens(text: str) -> set[str]:
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    stop_words = {"yojana", "scheme", "shasan", "nirnay", "government", "of", "to", "for", "in", "and", "the", "योजना", "शासन", "निर्णय"}
    return {w for w in cleaned.split() if len(w) > 1 and w not in stop_words}


def _string_similarity(a: str, b: str) -> float:
    a_clean = re.sub(r"[^\w\s]", "", a.lower()).strip()
    b_clean = re.sub(r"[^\w\s]", "", b.lower()).strip()
    if a_clean == b_clean:
        return 1.0
    return SequenceMatcher(None, a_clean, b_clean).ratio()


def detect_scheme_duplicates(
    candidate_title: str,
    department: str | None = None,
    candidate_id: str | None = None,
) -> DuplicateDetectionReport:
    """Analyze a candidate scheme title against the registered Maharashtra alias database and known distinct branches."""
    matches: list[DuplicateCandidateMatch] = []
    notes: list[str] = []
    cand_tokens = _normalize_tokens(candidate_title)

    for scheme_id, aliases in KNOWN_MAHARASHTRA_SCHEME_ALIASES.items():
        if candidate_id and scheme_id == candidate_id:
            continue

        best_score = 0.0
        best_alias_match = ""

        for a in aliases:
            # 1. Exact match
            if candidate_title.strip().casefold() == a.alias.strip().casefold():
                best_score = 1.0
                best_alias_match = a.alias
                break

            # 2. Acronym match: if alias is acronym (e.g. "MMLBY", "SGNAY") and in cand_tokens
            if a.alias_type == "acronym" and a.alias.lower() in cand_tokens:
                if 0.90 > best_score:
                    best_score = 0.90
                    best_alias_match = a.alias

            # 3. Substring match for aliases (e.g. "ladki bahin", "संजय गांधी")
            alias_lower = a.alias.lower()
            cand_lower = candidate_title.lower()
            if len(alias_lower) >= 5 and (alias_lower in cand_lower or cand_lower in alias_lower):
                sub_score = 0.88
                if sub_score > best_score:
                    best_score = sub_score
                    best_alias_match = a.alias

            # 4. Sequence similarity
            score = _string_similarity(candidate_title, a.alias)
            if score > best_score:
                best_score = score
                best_alias_match = a.alias

            # 5. Token set Jaccard similarity
            alias_tokens = _normalize_tokens(a.alias)
            if cand_tokens and alias_tokens:
                jaccard = len(cand_tokens & alias_tokens) / len(cand_tokens | alias_tokens)
                if jaccard > best_score:
                    best_score = jaccard
                    best_alias_match = a.alias

        # Check if this pair is a registered distinct branch
        is_distinct = False
        distinct_reason = ""
        if candidate_id:
            pair_key = frozenset([candidate_id, scheme_id])
            if pair_key in KNOWN_DISTINCT_BRANCH_PAIRS:
                is_distinct = True
                distinct_reason = KNOWN_DISTINCT_BRANCH_PAIRS[pair_key]
                best_score = max(best_score, 0.70)
                if not best_alias_match:
                    best_alias_match = aliases[0].alias

        if best_score >= 0.50:
            match_reason = (
                f"Matched registered alias '{best_alias_match}' with score {best_score:.2f}."
            )
            if is_distinct:
                match_reason += f" Distinct Branch Verified: {distinct_reason}"

            matches.append(
                DuplicateCandidateMatch(
                    canonical_scheme_id=scheme_id,
                    canonical_name=aliases[0].alias,
                    matched_term=best_alias_match,
                    similarity_score=round(best_score, 3),
                    reason=match_reason,
                    is_distinct_branch=is_distinct,
                )
            )

    # Sort matches by similarity descending
    matches.sort(key=lambda m: m.similarity_score, reverse=True)

    # Determine recommendation
    high_confidence_matches = [m for m in matches if m.similarity_score >= 0.85 and not m.is_distinct_branch]
    distinct_matches = [m for m in matches if m.is_distinct_branch]

    if distinct_matches:
        notes.append("Recognized verified distinct statutory branch; must not be merged as a duplicate.")

    if high_confidence_matches:
        is_prob_dup = True
        recommendation = "merge_with_existing"
        notes.append(
            f"Candidate title closely matches existing registered scheme '{high_confidence_matches[0].canonical_scheme_id}'. "
            "Inspect amendment lineage to determine if this is a revision of that scheme."
        )
    elif matches and any(m.similarity_score >= 0.60 for m in matches if not m.is_distinct_branch):
        is_prob_dup = False
        recommendation = "requires_analyst_review"
        notes.append("Candidate shares overlapping terms with registered schemes; analyst review required to verify distinctness.")
    else:
        is_prob_dup = False
        recommendation = "create_new"
        notes.append("No conflicting duplicates found in registered Maharashtra schemes.")

    return DuplicateDetectionReport(
        query_title=candidate_title,
        department=department,
        potential_duplicates=matches,
        is_probable_duplicate=is_prob_dup,
        recommendation=recommendation,
        notes=notes,
    )
