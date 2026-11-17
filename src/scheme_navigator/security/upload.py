from __future__ import annotations

import os
import re

MAX_PDF_BYTES = 15 * 1024 * 1024  # 15 MiB
MAX_IMAGE_BYTES = 12 * 1024 * 1024  # 12 MiB

DISALLOWED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".ps1", ".sh", ".php", ".phtml",
    ".asp", ".aspx", ".jsp", ".js", ".vbs", ".svg", ".html",
    ".htm", ".dll", ".so", ".dylib", ".jar", ".war", ".py",
}

SAFE_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and null byte injections."""
    if not filename or not isinstance(filename, str):
        return "unnamed_document.bin"

    # Remove null bytes
    clean = filename.replace("\x00", "").strip()

    # Get basename only
    base = os.path.basename(clean.replace("\\", "/"))

    # Remove dangerous characters
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", base)

    # Prevent hidden files
    if sanitized.startswith("."):
        sanitized = f"doc_{sanitized[1:]}"

    return sanitized or "document.bin"


def validate_uploaded_document_security(
    file_bytes: bytes,
    filename: str,
    content_type: str | None = None,
) -> tuple[str, str]:
    """Validate upload size, file extension, path safety, and magic byte headers.

    Returns (safe_filename, detected_mime_type).
    """
    if not file_bytes:
        raise ValueError("Upload security check failed: empty file payload.")

    size = len(file_bytes)
    safe_name = sanitize_filename(filename)
    _, ext = os.path.splitext(safe_name.lower())

    if ext in DISALLOWED_EXTENSIONS:
        raise ValueError(f"Upload security check failed: file extension '{ext}' is forbidden.")

    # Magic byte checks
    detected_mime: str | None = None

    if file_bytes.startswith(b"%PDF-"):
        detected_mime = "application/pdf"
        if size > MAX_PDF_BYTES:
            raise ValueError(f"Upload size exceeded: PDF is {size / 1024 / 1024:.1f} MiB (limit is 15 MiB).")
    elif file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_mime = "image/png"
        if size > MAX_IMAGE_BYTES:
            raise ValueError(f"Upload size exceeded: PNG image is {size / 1024 / 1024:.1f} MiB (limit is 12 MiB).")
    elif file_bytes.startswith(b"\xff\xd8\xff"):
        detected_mime = "image/jpeg"
        if size > MAX_IMAGE_BYTES:
            raise ValueError(f"Upload size exceeded: JPEG image is {size / 1024 / 1024:.1f} MiB (limit is 12 MiB).")
    elif file_bytes.startswith(b"RIFF") and len(file_bytes) > 12 and file_bytes[8:12] == b"WEBP":
        detected_mime = "image/webp"
        if size > MAX_IMAGE_BYTES:
            raise ValueError(f"Upload size exceeded: WEBP image is {size / 1024 / 1024:.1f} MiB (limit is 12 MiB).")
    else:
        raise ValueError(
            "Upload security check failed: unrecognized or forged file header. "
            "Only genuine PDF, PNG, JPEG, and WEBP documents are permitted."
        )

    # Cross-check declared MIME type if provided
    if content_type:
        clean_ct = content_type.split(";")[0].strip().casefold()
        if clean_ct and clean_ct in SAFE_MIME_TYPES:
            # If declared MIME is drastically different from magic byte
            if (clean_ct == "application/pdf" and detected_mime != "application/pdf") or \
               (clean_ct.startswith("image/") and not detected_mime.startswith("image/")):
                raise ValueError(
                    f"Upload security check failed: MIME type mismatch (declared '{content_type}', "
                    f"detected '{detected_mime}')."
                )

    return safe_name, detected_mime


MAX_AUDIO_BYTES = 15 * 1024 * 1024  # 15 MiB


def validate_uploaded_audio_security(
    file_bytes: bytes,
    filename: str,
    content_type: str | None = None,
) -> tuple[str, str]:
    """Validate audio upload size, filename safety, and genuine audio magic-byte headers.

    Supports WAV, MP3, OGG, FLAC, and WebM audio containers.
    Returns (safe_filename, detected_audio_format).
    """
    if not file_bytes:
        raise ValueError("Upload security check failed: empty audio payload.")

    size = len(file_bytes)
    if size > MAX_AUDIO_BYTES:
        raise ValueError(f"Audio upload size exceeded: {size / 1024 / 1024:.1f} MiB exceeds 15 MiB limit.")

    safe_name = sanitize_filename(filename)
    _, ext = os.path.splitext(safe_name.lower())

    if ext in DISALLOWED_EXTENSIONS:
        raise ValueError(f"Upload security check failed: file extension '{ext}' is forbidden.")

    detected_format: str | None = None

    if file_bytes.startswith(b"RIFF") and len(file_bytes) > 12 and file_bytes[8:12] == b"WAVE":
        detected_format = "audio/wav"
    elif file_bytes.startswith(b"ID3") or (len(file_bytes) >= 2 and file_bytes[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
        detected_format = "audio/mpeg"
    elif file_bytes.startswith(b"OggS"):
        detected_format = "audio/ogg"
    elif file_bytes.startswith(b"fLaC"):
        detected_format = "audio/flac"
    elif file_bytes.startswith(b"\x1a\x45\xdf\xa3"):
        detected_format = "audio/webm"
    else:
        raise ValueError(
            "Upload security check failed: unrecognized or forged audio header. "
            "Only genuine WAV, MP3, OGG, FLAC, and WebM audio files are permitted."
        )

    return safe_name, detected_format

