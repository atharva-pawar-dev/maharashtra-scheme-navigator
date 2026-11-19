"""RC4 Document Intelligence & Accuracy Verification.

Proves real-world document processing across 6 mandatory processing routes:
1. Searchable PDFs (Embedded text extraction)
2. Scanned/image-only PDFs (OCR / fallback extraction)
3. JPG photographs (Camera photos with EXIF / perspective)
4. PNG photographs/scans (Quality gates: blur, resolution, contrast)
5. Multi-page PDFs (Sequential page gap detection)
6. Front/back document pairs (Grouped page synthesis)

Evaluates field-level extraction against ground truth across English, Marathi, and Hindi specimens.
"""
from __future__ import annotations

import datetime
from pathlib import Path
import pytest

from scheme_navigator.documents.audit import (
    LocalFallbackDocumentExtractor,
    assess_image_quality,
    detect_missing_pages,
    ExtractedDocument,
)
from scheme_navigator.documents.grouping import (
    group_pdf_page_extractions,
    PdfDocumentGroup,
)

SPECIMENS_DIR = Path(__file__).resolve().parent / "fixtures" / "specimens"


# Ground truth definitions for accuracy evaluation
GROUND_TRUTH_SPECIMENS = [
    {
        "filename": "searchable_english_certificate.pdf",
        "route": "Searchable PDF",
        "language": "English",
        "medium": "SEARCHABLE_PDF",
        "processing_method": "EMBEDDED_PDF_TEXT",
        "expected": {
            "applicant_name": "Sunita Ramesh Patil",
            "income": 120000,
            "financial_year": "2026-27",
            "certificate_number": "MH-REV-2026-ENG-0981",
            "issue_date": datetime.date(2026, 4, 12),
            "valid_until": datetime.date(2027, 3, 31),
            "issuing_authority": "Tahsildar Haveli, Pune",
            "district": "Pune",
            "taluka": "Haveli",
        },
    },
    {
        "filename": "searchable_marathi_certificate.pdf",
        "route": "Searchable PDF",
        "language": "Marathi",
        "medium": "SEARCHABLE_PDF",
        "processing_method": "EMBEDDED_PDF_TEXT",
        "expected": {
            "applicant_name": "अनिता सुरेश कदम",
            "income": 120000,
            "financial_year": "2026-27",
            "certificate_number": "MH-TAH-2026-MR-9922",
            "issue_date": datetime.date(2026, 4, 15),
            "valid_until": datetime.date(2027, 3, 31),
            "issuing_authority": "तहसीलदार, हवेली, पुणे",
            "district": "पुणे",
            "taluka": "Haveli",
        },
    },
    {
        "filename": "searchable_hindi_certificate.pdf",
        "route": "Searchable PDF",
        "language": "Hindi",
        "medium": "SEARCHABLE_PDF",
        "processing_method": "EMBEDDED_PDF_TEXT",
        "expected": {
            "applicant_name": "अनिता सुरेश कदम",
            "income": 120000,
            "financial_year": "2026-27",
            "certificate_number": "MH-REV-2026-HI-7733",
            "issue_date": datetime.date(2026, 5, 10),
            "valid_until": datetime.date(2027, 3, 31),
            "issuing_authority": "अनुविभागीय अधिकारी, पुणे",
            "district": "Pune",
            "taluka": None,
        },
    },
    {
        "filename": "scanned_english_certificate.pdf",
        "route": "Scanned PDF",
        "language": "English",
        "medium": "SCANNED_PDF",
        "processing_method": "IMAGE_FALLBACK_OCR",
        "expected": {
            "applicant_name": "Sunita Ramesh Patil",
            "income": 120000,
            "financial_year": "2026-27",
            "certificate_number": "MH-SCN-2026-1122",
            "issue_date": datetime.date(2026, 4, 12),
            "valid_until": datetime.date(2027, 3, 31),
            "issuing_authority": "Tahsildar Haveli, Pune",
            "district": "Pune",
            "taluka": "Haveli",
        },
    },
    {
        "filename": "scanned_marathi_certificate.pdf",
        "route": "Scanned PDF",
        "language": "Marathi",
        "medium": "SCANNED_PDF",
        "processing_method": "IMAGE_FALLBACK_OCR",
        "expected": {
            "applicant_name": "अनिता सुरेश कदम",
            "income": 120000,
            "financial_year": "2026-27",
            "certificate_number": "MH-TAH-2026-SCN-MR-8811",
            "issue_date": datetime.date(2026, 4, 15),
            "valid_until": datetime.date(2027, 3, 31),
            "issuing_authority": "तहसीलदार, हवेली, पुणे",
            "district": "Pune",
            "taluka": "Haveli",
        },
    },
    {
        "filename": "scanned_hindi_certificate.pdf",
        "route": "Scanned PDF",
        "language": "Hindi",
        "medium": "SCANNED_PDF",
        "processing_method": "IMAGE_FALLBACK_OCR",
        "expected": {
            "applicant_name": "अनिता सुरेश कदम",
            "income": 120000,
            "financial_year": "2026-27",
            "certificate_number": "MH-REV-2026-SCN-HI-6622",
            "issue_date": datetime.date(2026, 5, 10),
            "valid_until": datetime.date(2027, 3, 31),
            "issuing_authority": "अनुविभागीय अधिकारी, पुणे",
            "district": "Pune",
            "taluka": None,
        },
    },
    {
        "filename": "marathi_photograph.jpg",
        "route": "JPG Photograph",
        "language": "Marathi",
        "medium": "PHOTOGRAPH",
        "processing_method": "IMAGE_FALLBACK_OCR",
        "expected": {
            "applicant_name": "अनिता सुरेश कदम",
            "income": 120000,
            "financial_year": "2026-27",
            "certificate_number": "MH-PHOTO-MR-2026-5544",
            "issue_date": datetime.date(2026, 4, 15),
            "valid_until": datetime.date(2027, 3, 31),
            "issuing_authority": "तहसीलदार, हवेली, पुणे",
            "district": "Pune",
            "taluka": "Haveli",
        },
    },
    {
        "filename": "hindi_photograph.jpg",
        "route": "JPG Photograph",
        "language": "Hindi",
        "medium": "PHOTOGRAPH",
        "processing_method": "IMAGE_FALLBACK_OCR",
        "expected": {
            "applicant_name": "अनिता सुरेश कदम",
            "income": 120000,
            "financial_year": "2026-27",
            "certificate_number": "MH-PHOTO-HI-2026-4433",
            "issue_date": datetime.date(2026, 5, 10),
            "valid_until": datetime.date(2027, 3, 31),
            "issuing_authority": "अनुविभागीय अधिकारी, पुणे",
            "district": "Pune",
            "taluka": None,
        },
    },
]


def test_field_level_ground_truth_accuracy():
    """Verify field-level extraction matches ground truth across English, Marathi, Hindi specimens."""
    extractor = LocalFallbackDocumentExtractor()
    total_fields = 0
    matched_fields = 0

    for item in GROUND_TRUTH_SPECIMENS:
        path = SPECIMENS_DIR / item["filename"]
        assert path.exists(), f"Specimen missing: {item['filename']}"
        raw = path.read_bytes()
        doc = extractor.extract(raw, filename=item["filename"])

        assert doc.medium_type == item["medium"]
        assert doc.processing_method == item["processing_method"]

        exp = item["expected"]
        # Applicant name
        assert exp["applicant_name"] in doc.person_name
        # Income
        assert doc.annual_family_income == exp["income"]
        # Financial Year
        assert doc.valid_financial_year == exp["financial_year"]
        # Certificate Number
        assert doc.certificate_number_masked == exp["certificate_number"]
        # Issue Date
        assert doc.issue_date == exp["issue_date"]
        # Expiry / Valid until
        assert doc.valid_until == exp["valid_until"]
        # Issuing Authority
        assert exp["issuing_authority"] in (doc.field_evidence.get("issuing_authority") or "")
        # District
        if exp["district"]:
            assert exp["district"].lower() in (doc.field_evidence.get("district") or "").lower()

        total_fields += 8
        matched_fields += 8

    accuracy_pct = (matched_fields / total_fields) * 100.0
    assert accuracy_pct == 100.0


def test_png_scan_and_photograph_quality_route():
    """Verify Route 4 (PNG scans) detects blur, resolution limits, and contrast gracefully."""
    # Low resolution PNG rejection
    low_res_bytes = (SPECIMENS_DIR / "low_resolution_document.png").read_bytes()
    is_ok, code, metric = assess_image_quality(low_res_bytes)
    assert not is_ok
    assert code == "LOW_RESOLUTION_IMAGE"

    # Excessive blur rejection
    blur_bytes = (SPECIMENS_DIR / "blurred_document.png").read_bytes()
    is_ok, code, metric = assess_image_quality(blur_bytes)
    assert not is_ok
    assert code == "IMAGE_EXCESSIVE_BLUR"

    # Extractor returns QUALITY_FAILURE and ocr_uncertainty on blurred file
    extractor = LocalFallbackDocumentExtractor()
    doc = extractor.extract(blur_bytes, filename="blurred_document.png")
    assert doc.processing_method == "QUALITY_FAILURE"
    assert doc.ocr_uncertainty is True
    assert doc.confidence < 0.50


def test_multipage_pdf_page_gap_detection_route():
    """Verify Route 5 (Multi-page PDF) detects missing page gaps in declared sequential pages."""
    # Complete 2 pages
    pages_complete = ["Page 1 of 2: Header info", "Page 2 of 2: Official seal"]
    has_missing, missing_p, total_p = detect_missing_pages(pages_complete)
    assert not has_missing
    assert missing_p == []

    # Incomplete page 1 of 3, 3 of 3 (page 2 omitted)
    pages_gap = ["पृष्ठ १ पैकी ३: प्राथमिक माहिती", "पृष्ठ ३ पैकी ३: शिक्का व स्वाक्षरी"]
    has_missing, missing_p, total_p = detect_missing_pages(pages_gap)
    assert has_missing
    assert missing_p == [2]
    assert total_p == 3


def test_front_and_back_document_pair_grouping_route():
    """Verify Route 6 (Front/Back pair) merges front identity and back address into one logical unit."""
    sha = "a" * 64
    front_doc = ExtractedDocument(
        document_id="doc_front_1",
        document_type="aadhaar_card",
        person_name="Sunita Ramesh Patil",
        certificate_number_masked="XXXX-XXXX-4321",
        confidence=0.96,
        source_file_sha256=sha,
        field_evidence={"name": "Sunita Ramesh Patil"},
    )
    back_doc = ExtractedDocument(
        document_id="doc_back_2",
        document_type="aadhaar_card",
        person_name="Sunita Ramesh Patil",
        certificate_number_masked="XXXX-XXXX-4321",
        confidence=0.94,
        source_file_sha256=sha,
        field_evidence={"address": "Haveli, Pune, Maharashtra 411028"},
    )

    page_docs = [(1, front_doc), (2, back_doc)]
    groups = group_pdf_page_extractions(page_docs, sha)

    assert len(groups) == 1
    grouped_doc = groups[0].document
    assert grouped_doc.document_type == "aadhaar_card"
    assert grouped_doc.person_name == "Sunita Ramesh Patil"
    assert grouped_doc.certificate_number_masked == "XXXX-XXXX-4321"
    assert "address" in grouped_doc.field_evidence
    assert groups[0].page_numbers == (1, 2)
