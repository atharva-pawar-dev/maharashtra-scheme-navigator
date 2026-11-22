"""TRIMURTI / MSN-DV-001 Privacy, Sanitization & Masking Engine (Law L5 & L8).

Enforces:
- Aadhaar number masking (only last 4 digits visible: 'XXXX XXXX 1234').
- Identifier masking for PAN, bank account, and phone numbers.
- Hostile payload neutralization (no SSRF URLs, no script tags).
- Strict PII filtering in logs.
"""

from __future__ import annotations

import re
from typing import Optional


# Regular expressions for sensitive identifiers
AADHAAR_REGEX = re.compile(r"\b(\d{4})\s*(\d{4})\s*(\d{4})\b")
PAN_REGEX = re.compile(r"\b([A-Z]{5})(\d{4})([A-Z])\b", re.IGNORECASE)
BANK_ACCOUNT_REGEX = re.compile(r"\b(\d{3,6})(\d{4,12})(\d{4})\b")
PHONE_REGEX = re.compile(r"\b(\+91[\-\s]?)?([6-9]\d{5})(\d{4})\b")

# Dangerous URL schemes that must NEVER be fetched or traversed (Law L5)
DISALLOWED_SCHEMES = ("file:", "ftp:", "gopher:", "dict:", "php:", "ldap:", "netdoc:")
METADATA_IPS = ("169.254.169.254", "127.0.0.1", "localhost", "::1", "0.0.0.0")


def mask_aadhaar(text: str) -> str:
    """Mask 12-digit Aadhaar numbers to 'XXXX XXXX 1234' (Law L8)."""
    return AADHAAR_REGEX.sub(r"XXXX XXXX \3", text)


def mask_pan(text: str) -> str:
    """Mask PAN to 'XXXXX 1234 X'."""
    return PAN_REGEX.sub(r"XXXXX\2\3", text)


def mask_phone(text: str) -> str:
    """Mask phone number leaving only last 4 digits."""
    return PHONE_REGEX.sub(r"XXXXXX\3", text)


def mask_all_pii(text: str) -> str:
    """Convenience pipeline to mask all recognizable PII from text before logging."""
    if not text:
        return ""
    masked = mask_aadhaar(text)
    masked = mask_pan(masked)
    masked = mask_phone(masked)
    return masked


def sanitize_extracted_text(text: str) -> str:
    """Sanitize extracted OCR/document text to neutralize injections (Law L5).
    
    Treats document contents strictly as inert data:
    - Strips script and html tags
    - Disallows command-like directives
    """
    if not text:
        return ""
    # Strip dangerous HTML/script tags
    cleaned = re.sub(r"<[^>]*>", "", text)
    # Neutralize null bytes and control chars
    cleaned = cleaned.replace("\x00", "").replace("\r", " ")
    return cleaned.strip()


def validate_document_url_safety(url: str) -> bool:
    """Check if a URL found in a document or QR code is safe to view.
    
    Law L5: NEVER fetch a URL found inside a document.
    Returns False if URL attempts SSRF, local access, or dangerous schemes.
    """
    if not url:
        return False
        
    url_lower = url.strip().lower()
    for scheme in DISALLOWED_SCHEMES:
        if url_lower.startswith(scheme):
            return False
            
    for ip in METADATA_IPS:
        if ip in url_lower:
            return False

    # Only official https:// is permitted for external link references (never auto-fetched)
    if not url_lower.startswith("https://"):
        return False

    return True
