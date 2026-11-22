"""TRIMURTI / MSN-DV-001 Citizen Copy Linter.

Enforces:
- Law L10: 'Never blame, always explain' - no banned technical/blaming words.
- Law L9: 'No false green' - no bare word 'verified' in citizen-facing strings.
- Trilingual completeness: EN, MR, HI must all be present for every string.
- Sentence length: Average words per sentence <= 12, maximum <= 18 (English & romanized).
- Reporting: native_reviewed vs machine_drafted ratios.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add src to sys.path so we can import directly
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from scheme_navigator.dv.strings import BANNED_WORDS, CATALOGUE, CopyString


def check_banned_words(string_entry: CopyString) -> List[str]:
    """Check if any banned word appears in the copy string."""
    violations = []
    
    # English check (word boundaries, case insensitive)
    for banned in BANNED_WORDS["en"]:
        pattern = rf"\b{re.escape(banned)}\b"
        if re.search(pattern, string_entry.en, re.IGNORECASE):
            violations.append(f"[{string_entry.key}] EN contains banned word '{banned}': '{string_entry.en}'")
            
    # Marathi check (substring or token)
    for banned in BANNED_WORDS["mr"]:
        if banned in string_entry.mr:
            violations.append(f"[{string_entry.key}] MR contains banned word '{banned}': '{string_entry.mr}'")

    # Hindi check (substring or token)
    for banned in BANNED_WORDS["hi"]:
        if banned in string_entry.hi:
            violations.append(f"[{string_entry.key}] HI contains banned word '{banned}': '{string_entry.hi}'")

    return violations


def check_sentence_length(string_entry: CopyString) -> List[str]:
    """Check English sentence length limits (avg <= 12 words, max <= 18 words)."""
    violations = []
    text = string_entry.en.strip()
    if not text:
        return [f"[{string_entry.key}] EN text is empty."]
        
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if not sentences:
        return []

    word_counts = [len(s.split()) for s in sentences]
    max_words = max(word_counts)
    avg_words = sum(word_counts) / len(word_counts)

    if max_words > 18:
        violations.append(
            f"[{string_entry.key}] EN max sentence length {max_words} exceeds limit of 18 words: '{text}'"
        )
    if avg_words > 12:
        violations.append(
            f"[{string_entry.key}] EN avg sentence length {avg_words:.1f} exceeds limit of 12 words: '{text}'"
        )

    return violations


def check_trilingual_completeness(string_entry: CopyString) -> List[str]:
    """Check that all three languages (EN, MR, HI) are present and non-empty."""
    violations = []
    if not string_entry.en or not string_entry.en.strip():
        violations.append(f"[{string_entry.key}] Missing English translation.")
    if not string_entry.mr or not string_entry.mr.strip():
        violations.append(f"[{string_entry.key}] Missing Marathi translation.")
    if not string_entry.hi or not string_entry.hi.strip():
        violations.append(f"[{string_entry.key}] Missing Hindi translation.")
    return violations


def run_lint() -> Tuple[bool, Dict[str, any]]:
    """Run all lint rules across the catalogue and report summary."""
    all_violations = []
    native_count = 0
    machine_count = 0

    for key, entry in CATALOGUE.items():
        if entry.tag == "native_reviewed":
            native_count += 1
        elif entry.tag == "machine_drafted":
            machine_count += 1
            
        all_violations.extend(check_banned_words(entry))
        all_violations.extend(check_sentence_length(entry))
        all_violations.extend(check_trilingual_completeness(entry))

    total = len(CATALOGUE)
    passed = len(all_violations) == 0

    report = {
        "passed": passed,
        "total_strings": total,
        "native_reviewed": native_count,
        "machine_drafted": machine_count,
        "native_ratio": (native_count / total) if total > 0 else 0.0,
        "violation_count": len(all_violations),
        "violations": all_violations,
    }
    return passed, report


def main() -> int:
    passed, report = run_lint()
    print("=" * 60)
    print("MSN-DV-001 CITIZEN COPY LINT REPORT")
    print("=" * 60)
    print(f"Total Strings:    {report['total_strings']}")
    print(f"Native Reviewed:  {report['native_reviewed']} ({report['native_ratio']:.1%})")
    print(f"Machine Drafted:  {report['machine_drafted']}")
    print(f"Violations:       {report['violation_count']}")
    print("-" * 60)
    
    if not passed:
        print("VIOLATIONS FOUND:")
        for v in report["violations"]:
            print(f"  ❌ {v}")
        print("=" * 60)
        return 1

    print("✅ All copy strings passed banned-words, sentence-length and trilingual checks!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
