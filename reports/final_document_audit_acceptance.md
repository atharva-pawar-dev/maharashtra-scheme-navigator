# Final Document Audit Acceptance Report (reports/final_document_audit_acceptance.md)
**Project:** Maharashtra Scheme Navigator  
**Mission ID:** MSN-FINAL-001  
**Generated:** 2026-11-21  
**Governing Standard:** TRIMURTI v4 — Ground-Truth Document Intelligence & Audit Invariance  

---

## 1. Document Extraction & OCR Pipeline

The application operates a multi-route extraction and audit pipeline:
1. **Searchable PDF Pipeline:** Direct stream text extraction using PyMuPDF (`fitz`), preserving text coordinates, fonts, and structured paragraphs.
2. **Scanned PDF Pipeline:** Multi-page rendering at 300 DPI with Tesseract OCR fallback (supporting Devanagari Marathi `mar` and Hindi `hin` language models).
3. **Photograph & Mobile Uploads:** Automatic EXIF camera rotation via `PIL.ImageOps.exif_transpose`, contrast normalization, and Laplacian blur detection.
4. **Image Quality Gating:** OpenCV Laplacian variance check rejecting blurred uploads ($< 45.0$) and low-resolution images ($< 250 	imes 250$ px).
5. **Vernacular Normalization:** Conversion of Devanagari numerals (`०-९`) to standard integers and parsing of Marathi date strings (`दिनांक १५ ऑगस्ट २०२४` $	o$ ISO `2024-08-15`).

---

## 2. Scheme-Specific Auditing & Mismatch Detection

The Document Auditor evaluates extracted fields strictly against the requested scheme's document rules:
- **`PROFILE_DOCUMENT_INCOME_MISMATCH`:** Triggered when extracted annual income exceeds profile ceiling or differs from declared amount.
- **`PROFILE_DOCUMENT_NAME_MISMATCH`:** String Levenshtein distance check flagging discrepancies while accommodating honorifics (Shri, Smt, Sau).
- **`EXPIRED_OR_STALE`:** Evaluates certificate validity period against current fiscal year.
- **`MISSING_PAGE_IN_SEQUENCE`:** Mathematical gap detection for multi-page documents (e.g., page 1 and 3 present without page 2).

---

## 3. Remediation & Monotonic Readiness Math

When an issue is identified, the citizen receives actionable vernacular guidance with non-destructive replacement:
- **Proportional Readiness Adjustment:** For a 5-document requirement, having 4 valid documents yields an 80% readiness score ($4/5$). Purging or rejecting one document monotonically drops the score to $80\%$ without collapsing to $0\%$.
- **Audit Lineage:** Every replacement is tracked as $v1 	o v2$ with immutable SQLite triggers preserving previous hashes and findings.
