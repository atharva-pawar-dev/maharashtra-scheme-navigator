"""Re-export of NLU services for backward-compatibility with agents.nlu imports."""

from scheme_navigator.services.nlu import (
    DEVANAGARI_DIGITS,
    InterpretationResult,
    _normalize_devanagari_digits,
    _normalize_text,
    interpret_answer,
    interpret_boolean_slot,
    interpret_gender_slot,
    interpret_number_slot,
    interpret_resident_state,
)

__all__ = [
    "DEVANAGARI_DIGITS",
    "InterpretationResult",
    "_normalize_devanagari_digits",
    "_normalize_text",
    "interpret_answer",
    "interpret_boolean_slot",
    "interpret_gender_slot",
    "interpret_number_slot",
    "interpret_resident_state",
]
