"""Tests for Aadhaar privacy and Verhoeff validation engine."""

import pytest
from scheme_navigator.security.aadhaar_privacy import (
    validate_verhoeff,
    mask_aadhaar,
    redact_aadhaar_text,
)


def test_verhoeff_validation_valid_and_invalid():
    # 15 is a valid Verhoeff number (digit 1 + check digit 5)
    assert validate_verhoeff("15") is True
    # 14 has an invalid check digit
    assert validate_verhoeff("14") is False
    # Arbitrary non-Verhoeff 12-digit number fails
    assert validate_verhoeff("123456789012") is False


def test_mask_aadhaar():
    assert mask_aadhaar("987654321098") == "XXXX-XXXX-1098"
    assert mask_aadhaar("9876 5432 1098") == "XXXX-XXXX-1098"
    assert mask_aadhaar("9876-5432-1098") == "XXXX-XXXX-1098"


def test_redact_aadhaar_text():
    sample_text = "Citizen Aadhaar number is 9876 5432 1098 and phone is 9820098200."
    redacted = redact_aadhaar_text(sample_text)
    assert "9876 5432 1098" not in redacted
    assert "XXXX-XXXX-1098" in redacted
    assert "9820098200" in redacted  # 10-digit phone number is not masked
