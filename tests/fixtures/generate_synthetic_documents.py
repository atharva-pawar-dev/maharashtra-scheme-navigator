"""Synthetic Test Document Fixture Generator.

Generates 9 realistic, watermarked test document specimens for Maharashtra Scheme Navigator.
Every generated document explicitly contains the mandatory watermark:
'SYNTHETIC TEST SPECIMEN - NOT A REAL GOVERNMENT DOCUMENT'
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any
import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFilter


SPECIMENS_DIR = Path(__file__).resolve().parent / "specimens"
WATERMARK_TEXT = "SYNTHETIC TEST SPECIMEN - NOT A REAL GOVERNMENT DOCUMENT"


def _add_watermark_and_header(page: fitz.Page, title: str, subtitle: str = "Government of Maharashtra") -> None:
    rect = page.rect
    # Header box
    page.draw_rect(fitz.Rect(30, 20, rect.width - 30, 85), color=(0.4, 0.1, 0.1), width=1.5)
    page.insert_text(
        fitz.Point(rect.width / 2 - 140, 45),
        subtitle.upper(),
        fontsize=12,
        fontname="helv",
        color=(0.4, 0.1, 0.1),
    )
    page.insert_text(
        fitz.Point(rect.width / 2 - 160, 68),
        title.upper(),
        fontsize=14,
        fontname="helv",
        color=(0.1, 0.1, 0.1),
    )

    # Top Watermark Warning Bar
    page.draw_rect(fitz.Rect(30, 92, rect.width - 30, 112), color=(0.8, 0.2, 0.2), fill=(1.0, 0.9, 0.9))
    page.insert_text(
        fitz.Point(rect.width / 2 - 180, 106),
        WATERMARK_TEXT,
        fontsize=9,
        fontname="helv",
        color=(0.8, 0.1, 0.1),
    )

    # Diagonal Watermark across the page
    page.insert_text(
        fitz.Point(60, rect.height / 2),
        WATERMARK_TEXT,
        fontsize=14,
        fontname="helv",
        color=(0.85, 0.85, 0.85),
    )

    # Footer Warning Bar
    page.draw_rect(fitz.Rect(30, rect.height - 45, rect.width - 30, rect.height - 25), color=(0.8, 0.2, 0.2), fill=(1.0, 0.9, 0.9))
    page.insert_text(
        fitz.Point(rect.width / 2 - 180, rect.height - 32),
        WATERMARK_TEXT,
        fontsize=9,
        fontname="helv",
        color=(0.8, 0.1, 0.1),
    )


def generate_valid_income_certificate() -> Path:
    out = SPECIMENS_DIR / "valid_income_certificate.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    _add_watermark_and_header(page, "Tahsil Office Income Certificate", "Revenue Department Maharashtra")

    lines = [
        "Certificate No: MH/REV/2026/INC/00948271",
        "Date of Issue: 15/04/2026",
        "",
        "This is to certify that Smt. Sunita Ramesh Patil,",
        "resident of: House No. 42, Ward 12, Haveli, Pune, Maharashtra - 411028,",
        "belongs to the family whose total annual income from all sources during the",
        "Financial Year 2026-27 is Rs. 1,20,000/- (Rupees One Lakh Twenty Thousand Only).",
        "",
        "Beneficiary Name: Sunita Ramesh Patil",
        "Age: 32 Years | Gender: Female",
        "Annual Income: Rs. 1,20,000",
        "Financial Year: 2026-27",
        "Issuing Authority: Tahsildar, Taluka Haveli, District Pune",
        "Digital Verification: VALID - DIGITALLY SIGNED",
    ]
    y = 150
    for line in lines:
        page.insert_text(fitz.Point(50, y), line, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
        y += 24

    # Stamp box
    page.draw_rect(fitz.Rect(380, y + 20, 540, y + 80), color=(0.2, 0.4, 0.7), width=1)
    page.insert_text(fitz.Point(390, y + 45), "[OFFICIAL SEAL]", fontsize=10, fontname="helv", color=(0.2, 0.4, 0.7))
    page.insert_text(fitz.Point(390, y + 65), "Tahsildar Haveli, Pune", fontsize=9, fontname="helv", color=(0.2, 0.4, 0.7))

    doc.save(str(out))
    doc.close()
    return out


def generate_expired_income_certificate() -> Path:
    out = SPECIMENS_DIR / "expired_income_certificate.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    _add_watermark_and_header(page, "Annual Income Certificate (Past FY)", "Revenue Department Maharashtra")

    lines = [
        "Certificate No: MH/REV/2021/INC/00112233",
        "Date of Issue: 10/06/2021",
        "",
        "This is to certify that Smt. Sunita Ramesh Patil,",
        "resident of: Haveli, Pune, Maharashtra,",
        "total annual family income was Rs. 1,20,000/- for the past period.",
        "",
        "Beneficiary Name: Sunita Ramesh Patil",
        "Annual Income: Rs. 1,20,000",
        "Financial Year: 2021-22",
        "Status: EXPIRED (Past Financial Year)",
        "Issuing Authority: Tahsildar Haveli, Pune",
    ]
    y = 150
    for line in lines:
        page.insert_text(fitz.Point(50, y), line, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
        y += 24

    doc.save(str(out))
    doc.close()
    return out


def generate_name_mismatch_aadhaar() -> Path:
    out = SPECIMENS_DIR / "name_mismatch_aadhaar.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    _add_watermark_and_header(page, "Unique Identification Authority of India", "Government of India")

    lines = [
        "Identity Document Specimen (Name Mismatch Test)",
        "",
        "Name: Anita Suresh Deshmukh",
        "Father/Husband: Suresh Deshmukh",
        "DOB: 12/05/1994",
        "Gender: Female",
        "Aadhaar Number: XXXX-XXXX-4321",
        "Address: Flat 201, Kothrud, Pune - 411038",
        "",
        "Notice: Name does not match citizen profile 'Sunita Ramesh Patil'.",
    ]
    y = 150
    for line in lines:
        page.insert_text(fitz.Point(50, y), line, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
        y += 24

    doc.save(str(out))
    doc.close()
    return out


def generate_income_exceeded_certificate() -> Path:
    out = SPECIMENS_DIR / "income_exceeded_certificate.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    _add_watermark_and_header(page, "Tahsil Income Certificate (High Income)", "Revenue Department Maharashtra")

    lines = [
        "Certificate No: MH/REV/2026/INC/00998877",
        "Date of Issue: 20/05/2026",
        "",
        "Beneficiary Name: Sunita Ramesh Patil",
        "Annual Income: Rs. 4,50,000/- (Rupees Four Lakh Fifty Thousand Only)",
        "Financial Year: 2026-27",
        "Note: Annual income exceeds the ₹2,50,000 ceiling for Majhi Ladki Bahin.",
    ]
    y = 150
    for line in lines:
        page.insert_text(fitz.Point(50, y), line, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
        y += 24

    doc.save(str(out))
    doc.close()
    return out


def generate_unreadable_blur() -> Path:
    out = SPECIMENS_DIR / "unreadable_blur.pdf"
    # Create an image with severe blur and noise
    img = Image.new("RGB", (600, 800), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.text((100, 50), WATERMARK_TEXT, fill=(200, 50, 50))
    for i in range(150, 700, 30):
        draw.line([(50, i), (550, i)], fill=(180, 180, 180), width=4)
    # Apply heavy gaussian blur
    blurred = img.filter(ImageFilter.GaussianBlur(radius=8))

    # Convert to PDF
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    img_byte_arr = io.BytesIO()
    blurred.save(img_byte_arr, format="PNG")
    page.insert_image(page.rect, stream=img_byte_arr.getvalue())
    _add_watermark_and_header(page, "Unreadable Low-Confidence Document", "Synthetic Specimen")
    doc.save(str(out))
    doc.close()
    return out


def generate_incomplete_multipage() -> Path:
    out = SPECIMENS_DIR / "incomplete_multipage.pdf"
    doc = fitz.open()
    # Page 1
    p1 = doc.new_page(width=595, height=842)
    _add_watermark_and_header(p1, "Application Form Page 1 of 2", "Incomplete Submission Test")
    p1.insert_text(fitz.Point(50, 160), "Applicant: Sunita Ramesh Patil", fontsize=12, fontname="helv")
    p1.insert_text(fitz.Point(50, 190), "Scheme: Mukhyamantri Majhi Ladki Bahin", fontsize=11, fontname="helv")
    p1.insert_text(fitz.Point(50, 220), "Section A: Personal Information Completed", fontsize=11, fontname="helv")
    p1.insert_text(fitz.Point(50, 260), "Crucial Page 2 (with Bank Account and Tahsildar Seal) is MISSING.", fontsize=12, fontname="helv", color=(0.8, 0.1, 0.1))

    doc.save(str(out))
    doc.close()
    return out


def generate_wrong_document_type() -> Path:
    out = SPECIMENS_DIR / "wrong_document_type.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    _add_watermark_and_header(page, "Motor Driving License", "Motor Vehicles Department Maharashtra")

    lines = [
        "License No: MH-12-2018-0049281",
        "Name: Sunita Ramesh Patil",
        "Class of Vehicles: LMV (Light Motor Vehicle)",
        "Validity: 2018 to 2038",
        "",
        "Notice: Driving License is not an Income, Domicile, or Caste Certificate.",
    ]
    y = 150
    for line in lines:
        page.insert_text(fitz.Point(50, y), line, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
        y += 24

    doc.save(str(out))
    doc.close()
    return out


def generate_alternative_domicile_ration_card() -> Path:
    out = SPECIMENS_DIR / "alternative_domicile_ration_card.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    _add_watermark_and_header(page, "Public Distribution System Ration Card", "Food & Civil Supplies Department")

    lines = [
        "Ration Card No: RC-MH-PUN-094821",
        "Category: Yellow (BPL / Priority Household)",
        "Head of Family: Sunita Ramesh Patil",
        "Address: Haveli, Pune, Maharashtra (Resident for 15+ years)",
        "",
        "Notice: Serves as valid Alternative Document for Maharashtra Domicile / Residence Proof.",
    ]
    y = 150
    for line in lines:
        page.insert_text(fitz.Point(50, y), line, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
        y += 24

    doc.save(str(out))
    doc.close()
    return out


def generate_transliterated_name_certificate() -> Path:
    out = SPECIMENS_DIR / "transliterated_name_certificate.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    _add_watermark_and_header(page, "Domicile & Nationality Certificate", "Revenue Department Maharashtra")

    lines = [
        "Certificate No: MH/REV/DOM/2024/002941",
        "Date: 12/01/2024",
        "",
        "Name (Devanagari): सुनीता रमेश पाटील",
        "Name (English Transliteration): Sunita Ramesh Patil",
        "Resident of: Pune, Maharashtra (Continuous domicile > 15 years)",
        "",
        "Status: Verified Transliteration Match (0 Mismatch finding).",
    ]
    y = 150
    for line in lines:
        page.insert_text(fitz.Point(50, y), line, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
        y += 24

    doc.save(str(out))
    doc.close()
    return out


def generate_all_specimens() -> dict[str, Path]:
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "valid_income": generate_valid_income_certificate(),
        "expired_income": generate_expired_income_certificate(),
        "name_mismatch": generate_name_mismatch_aadhaar(),
        "income_exceeded": generate_income_exceeded_certificate(),
        "unreadable_blur": generate_unreadable_blur(),
        "incomplete_multipage": generate_incomplete_multipage(),
        "wrong_type": generate_wrong_document_type(),
        "alternative_domicile": generate_alternative_domicile_ration_card(),
        "transliterated_name": generate_transliterated_name_certificate(),
    }


if __name__ == "__main__":
    generated = generate_all_specimens()
    print(f"Successfully generated {len(generated)} synthetic document specimens in {SPECIMENS_DIR}")
    for k, p in generated.items():
        print(f"  - {k}: {p.name} ({p.stat().st_size} bytes)")
