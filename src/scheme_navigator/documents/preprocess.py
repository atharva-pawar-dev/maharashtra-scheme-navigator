from __future__ import annotations

from io import BytesIO

import cv2
import numpy as np
from PIL import Image

MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000


def preprocess_certificate_image(raw: bytes) -> bytes:
    """Decode safely and prepare a high-contrast image for local OCR/VLM inference."""
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("Image must be non-empty and at most 12 MiB")
    pil_image = Image.open(BytesIO(raw))
    if pil_image.width * pil_image.height > MAX_IMAGE_PIXELS:
        raise ValueError("Image exceeds 20 megapixels")
    pil_image.verify()
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unsupported or corrupt image")
    height, width = image.shape[:2]
    if min(height, width) < 31:
        raise ValueError("Image is too small to process as a certificate")
    if max(height, width) > 5000:
        scale = 5000 / max(height, width)
        image = cv2.resize(image, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Mild denoising and adaptive threshold preserve local certificate text without inventing pixels.
    gray = cv2.medianBlur(gray, 3)
    thresholded = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
    )
    ok, encoded = cv2.imencode(".png", thresholded)
    if not ok:
        raise ValueError("Unable to encode preprocessed image")
    return encoded.tobytes()


def render_pdf_pages(raw: bytes, *, max_pages: int = 10) -> list[bytes]:
    """Render bounded PDF pages to PNG bytes in memory for the local VLM path."""
    if not raw or len(raw) > 15 * 1024 * 1024:
        raise ValueError("PDF must be non-empty and at most 15 MiB")
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PDF rendering requires PyMuPDF; install the project dependencies.") from exc
    with fitz.open(stream=raw, filetype="pdf") as pdf:
        if pdf.needs_pass:
            raise ValueError("Password-protected PDFs are not supported")
        if pdf.page_count < 1 or pdf.page_count > max_pages:
            raise ValueError(f"PDF must have between 1 and {max_pages} pages")
        rendered: list[bytes] = []
        for page in pdf:
            rect = page.rect
            if rect.width <= 0 or rect.height <= 0:
                raise ValueError("PDF contains a page with invalid dimensions")
            scale = min(2.0, (MAX_IMAGE_PIXELS / (rect.width * rect.height)) ** 0.5)
            if scale < 0.25:
                raise ValueError("PDF page dimensions are too large to render safely")
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            if pixmap.width * pixmap.height > MAX_IMAGE_PIXELS:
                raise ValueError("Rendered PDF page exceeds 20 megapixels")
            rendered.append(pixmap.tobytes("png"))
        return rendered
