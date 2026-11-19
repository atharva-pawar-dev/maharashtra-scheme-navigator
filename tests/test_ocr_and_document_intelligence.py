from __future__ import annotations

from pathlib import Path
import pytest

from scheme_navigator.documents.audit import (
    LocalFallbackDocumentExtractor,
    assess_image_quality,
    audit_extracted_documents,
    devanagari_to_arabic_numerals,
)
from scheme_navigator.domain.models import ExtractedDocument

SPECIMENS_DIR = Path(__file__).parent / "fixtures" / "specimens"


def test_devanagari_numeral_conversion():
    """Verify Devanagari numerals are accurately normalized to Arabic numerals."""
    assert devanagari_to_arabic_numerals("०१२३४५६७८९") == "0123456789"
    assert devanagari_to_arabic_numerals("₹ १,२०,०००") == "₹ 1,20,000"
    assert devanagari_to_arabic_numerals("२०२६-२७") == "2026-27"
    assert devanagari_to_arabic_numerals("१५/०८/२०२६") == "15/08/2026"


def test_image_quality_assessment_blur_and_resolution():
    """Verify low resolution and blur are mathematically detected and rejected."""
    low_res_bytes = (SPECIMENS_DIR / "low_resolution_document.png").read_bytes()
    is_ok, code, metric = assess_image_quality(low_res_bytes)
    assert not is_ok
    assert code == "LOW_RESOLUTION_IMAGE"
    assert metric < 250.0

    blurred_bytes = (SPECIMENS_DIR / "blurred_document.png").read_bytes()
    is_ok, code, metric = assess_image_quality(blurred_bytes)
    assert not is_ok
    assert code == "IMAGE_EXCESSIVE_BLUR"
    assert metric < 45.0

    sharp_photo_bytes = (SPECIMENS_DIR / "marathi_photograph.jpg").read_bytes()
    is_ok, code, metric = assess_image_quality(sharp_photo_bytes)
    assert is_ok
    assert code is None
    assert metric >= 45.0


def test_searchable_english_pdf_extraction():
    """Verify searchable English PDF extracts embedded text without OCR uncertainty."""
    pdf_bytes = (SPECIMENS_DIR / "searchable_english_certificate.pdf").read_bytes()
    extractor = LocalFallbackDocumentExtractor()
    extracted = extractor.extract(pdf_bytes, filename="searchable_english_certificate.pdf")

    assert extracted.medium_type == "SEARCHABLE_PDF"
    assert extracted.processing_method == "EMBEDDED_PDF_TEXT"
    assert not extracted.ocr_uncertainty
    assert extracted.document_type == "income_certificate"
    assert extracted.annual_family_income == 120000
    assert extracted.valid_financial_year == "2026-27"


def test_scanned_english_pdf_extraction():
    """Verify scanned English PDF without text layer is classified as SCANNED_PDF with fallback OCR."""
    pdf_bytes = (SPECIMENS_DIR / "scanned_english_certificate.pdf").read_bytes()
    extractor = LocalFallbackDocumentExtractor()
    extracted = extractor.extract(pdf_bytes, filename="scanned_english_certificate.pdf")

    assert extracted.medium_type == "SCANNED_PDF"
    assert extracted.processing_method == "IMAGE_FALLBACK_OCR"
    assert extracted.annual_family_income == 120000
    assert extracted.valid_financial_year == "2026-27"


def test_searchable_marathi_pdf_extraction_devanagari():
    """Verify searchable Marathi PDF parses Devanagari text, numerals, name, income, and FY."""
    pdf_bytes = (SPECIMENS_DIR / "searchable_marathi_certificate.pdf").read_bytes()
    extractor = LocalFallbackDocumentExtractor()
    extracted = extractor.extract(pdf_bytes, filename="searchable_marathi_certificate.pdf")

    assert extracted.medium_type == "SEARCHABLE_PDF"
    assert extracted.processing_method == "EMBEDDED_PDF_TEXT"
    assert extracted.document_type == "income_certificate"
    assert extracted.annual_family_income == 120000
    assert extracted.valid_financial_year == "2026-27"
    assert "अनिता सुरेश कदम" in extracted.person_name


def test_scanned_marathi_pdf_extraction():
    """Verify scanned Marathi PDF parses recovered text from scanner metadata."""
    pdf_bytes = (SPECIMENS_DIR / "scanned_marathi_certificate.pdf").read_bytes()
    extractor = LocalFallbackDocumentExtractor()
    extracted = extractor.extract(pdf_bytes, filename="scanned_marathi_certificate.pdf")

    assert extracted.medium_type == "SCANNED_PDF"
    assert extracted.processing_method == "IMAGE_FALLBACK_OCR"
    assert extracted.document_type == "income_certificate"
    assert extracted.annual_family_income == 120000
    assert extracted.valid_financial_year == "2026-27"
    assert "अनिता सुरेश कदम" in extracted.person_name


def test_searchable_hindi_pdf_extraction_devanagari():
    """Verify searchable Hindi PDF parses Hindi text and Devanagari numerals."""
    pdf_bytes = (SPECIMENS_DIR / "searchable_hindi_certificate.pdf").read_bytes()
    extractor = LocalFallbackDocumentExtractor()
    extracted = extractor.extract(pdf_bytes, filename="searchable_hindi_certificate.pdf")

    assert extracted.medium_type == "SEARCHABLE_PDF"
    assert extracted.processing_method == "EMBEDDED_PDF_TEXT"
    assert extracted.document_type == "income_certificate"
    assert extracted.annual_family_income == 120000
    assert extracted.valid_financial_year == "2026-27"
    assert "अनिता सुरेश कदम" in extracted.person_name


def test_scanned_hindi_pdf_extraction():
    """Verify scanned Hindi PDF classification and field extraction."""
    pdf_bytes = (SPECIMENS_DIR / "scanned_hindi_certificate.pdf").read_bytes()
    extractor = LocalFallbackDocumentExtractor()
    extracted = extractor.extract(pdf_bytes, filename="scanned_hindi_certificate.pdf")

    assert extracted.medium_type == "SCANNED_PDF"
    assert extracted.processing_method == "IMAGE_FALLBACK_OCR"
    assert extracted.document_type == "income_certificate"
    assert extracted.annual_family_income == 120000
    assert extracted.valid_financial_year == "2026-27"


def test_photograph_marathi_document():
    """Verify camera photograph of Marathi document is classified as PHOTOGRAPH with correct extraction."""
    jpg_bytes = (SPECIMENS_DIR / "marathi_photograph.jpg").read_bytes()
    extractor = LocalFallbackDocumentExtractor()
    extracted = extractor.extract(jpg_bytes, filename="marathi_photograph.jpg")

    assert extracted.medium_type == "PHOTOGRAPH"
    assert extracted.processing_method == "IMAGE_FALLBACK_OCR"
    assert extracted.document_type == "income_certificate"
    assert extracted.annual_family_income == 120000
    assert extracted.valid_financial_year == "2026-27"


def test_photograph_hindi_document():
    """Verify camera photograph of Hindi document is classified as PHOTOGRAPH with correct extraction."""
    jpg_bytes = (SPECIMENS_DIR / "hindi_photograph.jpg").read_bytes()
    extractor = LocalFallbackDocumentExtractor()
    extracted = extractor.extract(jpg_bytes, filename="hindi_photograph.jpg")

    assert extracted.medium_type == "PHOTOGRAPH"
    assert extracted.processing_method == "IMAGE_FALLBACK_OCR"
    assert extracted.document_type == "income_certificate"
    assert extracted.annual_family_income == 120000
    assert extracted.valid_financial_year == "2026-27"


def test_low_resolution_image_rejection_in_audit():
    """Verify low resolution image is flagged as QUALITY_FAILURE and produces LOW_RESOLUTION_IMAGE finding."""
    png_bytes = (SPECIMENS_DIR / "low_resolution_document.png").read_bytes()
    extractor = LocalFallbackDocumentExtractor()
    extracted = extractor.extract(png_bytes, filename="low_resolution_document.png")

    assert extracted.processing_method == "QUALITY_FAILURE"
    assert extracted.ocr_uncertainty

    audit_res = audit_extracted_documents([extracted])
    assert audit_res.status == "issues_found"
    codes = [f.code for f in audit_res.findings]
    assert "LOW_RESOLUTION_IMAGE" in codes


def test_blurred_image_rejection_in_audit():
    """Verify excessively blurred image produces IMAGE_EXCESSIVE_BLUR finding with error severity."""
    png_bytes = (SPECIMENS_DIR / "blurred_document.png").read_bytes()
    extractor = LocalFallbackDocumentExtractor()
    extracted = extractor.extract(png_bytes, filename="blurred_document.png")

    assert extracted.processing_method == "QUALITY_FAILURE"
    assert extracted.ocr_uncertainty

    audit_res = audit_extracted_documents([extracted])
    assert audit_res.status == "issues_found"
    codes = [f.code for f in audit_res.findings]
    assert "IMAGE_EXCESSIVE_BLUR" in codes


def test_missing_page_multipage_pdf_detection():
    """Verify multi-page PDF with missing sequential page produces MISSING_PAGE_IN_SEQUENCE finding."""
    pdf_bytes = (SPECIMENS_DIR / "missing_page_multipage.pdf").read_bytes()
    extractor = LocalFallbackDocumentExtractor()
    extracted = extractor.extract(pdf_bytes, filename="missing_page_multipage.pdf")

    assert any("missing page" in n.lower() for n in extracted.extraction_notes)

    audit_res = audit_extracted_documents([extracted])
    assert audit_res.status == "issues_found"
    codes = [f.code for f in audit_res.findings]
    assert "MISSING_PAGE_IN_SEQUENCE" in codes


def test_financial_year_validity_distinction():
    """Verify valid financial year passes while invalid financial year raises warning."""
    valid_bytes = (SPECIMENS_DIR / "valid_financial_year_certificate.pdf").read_bytes()
    invalid_bytes = (SPECIMENS_DIR / "invalid_financial_year_certificate.pdf").read_bytes()

    extractor = LocalFallbackDocumentExtractor()
    doc_valid = extractor.extract(valid_bytes, filename="valid_fy.pdf")
    doc_invalid = extractor.extract(invalid_bytes, filename="invalid_fy.pdf")

    audit_valid = audit_extracted_documents([doc_valid], target_financial_year="2026-27")
    fy_findings_valid = [f for f in audit_valid.findings if f.code == "FINANCIAL_YEAR_MISMATCH"]
    assert len(fy_findings_valid) == 0

    audit_invalid = audit_extracted_documents([doc_invalid], target_financial_year="2026-27")
    fy_findings_invalid = [f for f in audit_invalid.findings if f.code == "FINANCIAL_YEAR_MISMATCH"]
    assert len(fy_findings_invalid) == 1
    assert "2020-21" in fy_findings_invalid[0].message


def test_ocr_uncertainty_distinguished_from_rule_failure():
    """Verify OCR uncertainty produces warning recommendation rather than hard invalidation."""
    uncertain_doc = ExtractedDocument(
        document_id="uncertain_doc_01",
        document_type="income_certificate",
        person_name="Sunita Ramesh Patil",
        annual_family_income=120000,
        income_currency="INR",
        valid_financial_year="2026-27",
        confidence=0.85,
        source_file_sha256="a" * 64,
        ocr_uncertainty=True,
    )
    audit_res = audit_extracted_documents([uncertain_doc])
    assert audit_res.status == "review_required"
    codes = [f.code for f in audit_res.findings]
    assert "OCR_UNCERTAINTY" in codes
    ocr_finding = next(f for f in audit_res.findings if f.code == "OCR_UNCERTAINTY")
    assert ocr_finding.severity == "warning"
    assert "caseworker" in ocr_finding.recommended_action.lower()
