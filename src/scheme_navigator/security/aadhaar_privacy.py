"""Statutory Aadhaar Privacy, Verhoeff Checksum Validation, and Redaction Engine.

Implements Prime Directive 6:
- Zero Aadhaar leakage into logs, LLM calls, or long-term persistence.
- Strict Verhoeff dihedral D5 checksum verification.
- Masking all 12-digit Aadhaar sequences to 'XXXX-XXXX-1234' (last 4 digits only).
"""

from __future__ import annotations

import re

# Dihedral group D5 multiplication table for Verhoeff algorithm
_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

# Permutation table p for Verhoeff algorithm
_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

# Inverse table inv
_VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

_AADHAAR_REGEX = re.compile(r"\b([2-9]\d{3})[ -]?(\d{4})[ -]?(\d{4})\b")


def validate_verhoeff(number_str: str) -> bool:
    """Validate a numeric string against the Verhoeff check digit algorithm.
    
    A valid 12-digit Aadhaar number satisfies: c == 0 where c is computed over reversed digits.
    """
    cleaned = re.sub(r"\D", "", number_str)
    if not cleaned.isdigit() or len(cleaned) < 2:
        return False

    c = 0
    # Process digits from right to left (index 0 is check digit at rightmost position)
    for i, char in enumerate(reversed(cleaned)):
        digit = int(char)
        p_val = _VERHOEFF_P[i % 8][digit]
        c = _VERHOEFF_D[c][p_val]

    return c == 0


def mask_aadhaar(number_str: str) -> str:
    """Format an Aadhaar number to standard masked form: XXXX-XXXX-1234."""
    cleaned = re.sub(r"\D", "", number_str)
    if len(cleaned) >= 4:
        last4 = cleaned[-4:]
        return f"XXXX-XXXX-{last4}"
    return "XXXX-XXXX-XXXX"


def redact_aadhaar_text(text: str) -> str:
    """Scan text and redact all 12-digit Aadhaar sequences to XXXX-XXXX-last4.
    
    Applies to both standard 12-digit strings and segmented XXXX-XXXX-XXXX representations.
    """
    if not text:
        return ""

    def _replace_match(match: re.Match) -> str:
        raw_number = "".join(match.groups())
        # Always mask any 12-digit sequence matching Aadhaar structural pattern
        return mask_aadhaar(raw_number)

    return _AADHAAR_REGEX.sub(_replace_match, text)
