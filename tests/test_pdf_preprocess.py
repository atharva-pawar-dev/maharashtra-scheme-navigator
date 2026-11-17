from __future__ import annotations

import fitz

from scheme_navigator.documents.preprocess import render_pdf_pages


def test_pdf_pages_render_in_memory():
    pdf = fitz.open()
    page = pdf.new_page(width=595, height=842)
    page.insert_text((72, 72), "Maharashtra income certificate FY 2026-27")
    raw = pdf.tobytes()
    pdf.close()
    images = render_pdf_pages(raw)
    assert len(images) == 1
    assert images[0].startswith(b"\x89PNG\r\n\x1a\n")
