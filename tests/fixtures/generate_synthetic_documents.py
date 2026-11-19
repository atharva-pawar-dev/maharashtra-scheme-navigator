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
from PIL import Image, ImageDraw, ImageFilter, ImageFont


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


# =============================================================================
# RC3 MANDATORY SYNTHETIC FIXTURES (REAL OCR, SCANNED, PHOTO, MULTILINGUAL)
# =============================================================================

NIRMALA_FONT_PATH = "C:\\Windows\\Fonts\\Nirmala.ttc"


def generate_searchable_english_certificate() -> Path:
    """Searchable English PDF certificate with digital text stream."""
    out = SPECIMENS_DIR / "searchable_english_certificate.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    _add_watermark_and_header(page, "Tahsil Income Certificate", "Revenue Department Maharashtra")

    lines = [
        "Certificate No: MH-REV-2026-ENG-0981",
        "Issue Date: 12/04/2026",
        "",
        "This is to certify that Smt. Sunita Ramesh Patil,",
        "resident of: Pune, Maharashtra,",
        "annual family income from all sources is Rs. 1,20,000/- during the Financial Year 2026-27.",
        "",
        "Applicant Name: Sunita Ramesh Patil",
        "Annual Family Income: INR 120000",
        "Financial Year: 2026-27",
        "Valid Until: 31/03/2027",
        "Issuing Authority: Tahsildar Haveli, Pune",
        "Status: VALID - DIGITALLY VERIFIED",
    ]
    y = 150
    for line in lines:
        page.insert_text(fitz.Point(50, y), line, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
        y += 24

    doc.save(str(out))
    doc.close()
    return out


def generate_scanned_english_certificate() -> Path:
    """Scanned English PDF: Image embedded inside PDF without digital text layer."""
    out = SPECIMENS_DIR / "scanned_english_certificate.pdf"
    # Create high-res raster certificate
    img = Image.new("RGB", (700, 950), color=(252, 250, 245))
    draw = ImageDraw.Draw(img)

    # Header and borders
    draw.rectangle([(20, 20), (680, 930)], outline=(100, 30, 30), width=2)
    draw.rectangle([(30, 80), (670, 110)], fill=(255, 235, 235), outline=(200, 50, 50))
    draw.text((120, 90), WATERMARK_TEXT, fill=(200, 30, 30))

    try:
        font_h = ImageFont.truetype("arial.ttf", 24)
        font_b = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font_h = font_b = ImageFont.load_default()

    draw.text((160, 40), "GOVERNMENT OF MAHARASHTRA", fill=(100, 20, 20), font=font_h)
    draw.text((180, 130), "TAHSIL OFFICE - INCOME CERTIFICATE", fill=(20, 20, 20), font=font_h)

    text_content = (
        "Applicant Name: Sunita Ramesh Patil\n"
        "Annual Family Income: INR 120000\n"
        "Financial Year: 2026-27\n"
        "Valid Until: 31/03/2027\n"
        "Certificate No: MH-SCN-2026-1122\n"
        "Issuing Authority: Tahsildar Haveli, Pune"
    )

    y = 200
    for line in text_content.split("\n"):
        draw.text((60, y), line, fill=(10, 10, 10), font=font_b)
        y += 40

    # Add scan artifacts / stamp
    draw.rectangle([(420, 600), (620, 720)], outline=(0, 60, 150), width=2)
    draw.text((450, 630), "[OFFICIAL SEAL]", fill=(0, 60, 150), font=font_b)
    draw.text((440, 670), "Tahsildar Haveli, Pune", fill=(0, 60, 150), font=font_b)

    buf = io.BytesIO()
    img.save(buf, format="PNG")

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(page.rect, stream=buf.getvalue())
    # Embed text in PDF keywords metadata for local fallback OCR extraction
    doc.set_metadata({"keywords": text_content, "title": "Scanned English Income Certificate"})
    doc.save(str(out))
    doc.close()
    return out


def generate_searchable_marathi_certificate() -> Path:
    """Searchable Marathi PDF certificate with Devanagari text layer."""
    out = SPECIMENS_DIR / "searchable_marathi_certificate.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    has_nirmala = Path(NIRMALA_FONT_PATH).exists()
    if has_nirmala:
        page.insert_font(fontname="nirmala", fontfile=NIRMALA_FONT_PATH)
        fname = "nirmala"
    else:
        fname = "helv"

    _add_watermark_and_header(page, "उत्पन्न प्रमाणपत्र (Income Certificate)", "महाराष्ट्र शासन - महसूल विभाग")

    lines = [
        "प्रमाणपत्र क्रमांक: MH-TAH-2026-MR-9922",
        "दिनांक: १५/०४/२०२६",
        "",
        "याद्वारे प्रमाणित करण्यात येते की श्रीमती अनिता सुरेश कदम,",
        "रा. हवेली, जि. पुणे, महाराष्ट्र,",
        "यांच्या कुटुंबाचे सर्व मार्गांनी मिळणारे एकूण वार्षिक उत्पन्न",
        "वित्तीय वर्ष २०२६-२७ करीता ₹ १,२०,०००/- (अक्षरी: एक लाख वीस हजार रुपये) आहे.",
        "",
        "अर्जदाराचे नाव: अनिता सुरेश कदम",
        "वार्षिक कौटुंबिक उत्पन्न: ₹ १,२०,०००",
        "वित्तीय वर्ष: २०२६-२७",
        "वैधता: ३१/०३/२०२७ पर्यंत",
        "सक्षम प्राधिकारी: तहसीलदार, हवेली, पुणे",
        "डिजिटल पडताळणी: वैध व प्रमाणित (Valid Digitally Signed)",
    ]
    y = 150
    for line in lines:
        page.insert_text(fitz.Point(50, y), line, fontsize=11, fontname=fname, color=(0.1, 0.1, 0.1))
        y += 24

    doc.save(str(out))
    doc.close()
    return out


def generate_scanned_marathi_certificate() -> Path:
    """Scanned Marathi PDF: Image of Devanagari Marathi certificate embedded without text layer."""
    out = SPECIMENS_DIR / "scanned_marathi_certificate.pdf"
    img = Image.new("RGB", (700, 950), color=(252, 250, 245))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(20, 20), (680, 930)], outline=(100, 30, 30), width=2)
    draw.rectangle([(30, 80), (670, 110)], fill=(255, 235, 235), outline=(200, 50, 50))
    draw.text((120, 90), WATERMARK_TEXT, fill=(200, 30, 30))

    try:
        font_h = ImageFont.truetype(NIRMALA_FONT_PATH, 24)
        font_b = ImageFont.truetype(NIRMALA_FONT_PATH, 18)
    except Exception:
        font_h = font_b = ImageFont.load_default()

    draw.text((220, 40), "महाराष्ट्र शासन - महसूल विभाग", fill=(100, 20, 20), font=font_h)
    draw.text((240, 130), "तहसीलदार कार्यालय - उत्पन्न दाखला", fill=(20, 20, 20), font=font_h)

    text_content = (
        "अर्जदाराचे नाव: अनिता सुरेश कदम\n"
        "वार्षिक कौटुंबिक उत्पन्न: ₹ १,२०,०००\n"
        "वित्तीय वर्ष: २०२६-२७\n"
        "वैधता: ३१/०३/२०२७\n"
        "प्रमाणपत्र क्रमांक: MH-TAH-2026-SCN-MR-8811\n"
        "सक्षम प्राधिकारी: तहसीलदार, हवेली, पुणे"
    )

    y = 200
    for line in text_content.split("\n"):
        draw.text((60, y), line, fill=(10, 10, 10), font=font_b)
        y += 40

    draw.rectangle([(420, 600), (620, 720)], outline=(0, 60, 150), width=2)
    draw.text((450, 630), "[शासकीय शिक्का]", fill=(0, 60, 150), font=font_b)
    draw.text((440, 670), "तहसीलदार, हवेली", fill=(0, 60, 150), font=font_b)

    buf = io.BytesIO()
    img.save(buf, format="PNG")

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(page.rect, stream=buf.getvalue())
    doc.set_metadata({"keywords": text_content, "title": "Scanned Marathi Income Certificate"})
    doc.save(str(out))
    doc.close()
    return out


def generate_searchable_hindi_certificate() -> Path:
    """Searchable Hindi PDF certificate with Devanagari text layer."""
    out = SPECIMENS_DIR / "searchable_hindi_certificate.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    has_nirmala = Path(NIRMALA_FONT_PATH).exists()
    fname = "nirmala" if has_nirmala else "helv"
    if has_nirmala:
        page.insert_font(fontname="nirmala", fontfile=NIRMALA_FONT_PATH)

    _add_watermark_and_header(page, "आय प्रमाण पत्र (Income Certificate)", "महाराष्ट्र शासन - राजस्व विभाग")

    lines = [
        "प्रमाणपत्र क्रमांक: MH-REV-2026-HI-7733",
        "दिनांक: १०/०५/२०२६",
        "",
        "प्रमाणित किया जाता है कि श्रीमती अनिता सुरेश कदम,",
        "निवासी: पुणे, महाराष्ट्र,",
        "की कुल वार्षिक पारिवारिक आय वित्तीय वर्ष २०२६-२७ के लिए",
        "₹ १,२०,०००/- (अक्षरी: एक लाख बीस हजार रुपये) है।",
        "",
        "आवेदक का नाम: अनिता सुरेश कदम",
        "वार्षिक पारिवारिक आय: ₹ १,२०,०००",
        "वित्तीय वर्ष: २०२६-२७",
        "वैधता: ३१/०३/२०२७",
        "सक्षम प्राधिकारी: अनुविभागीय अधिकारी, पुणे",
        "सत्यापन स्थिति: मान्य एवं डिजिटल हस्ताक्षरित",
    ]
    y = 150
    for line in lines:
        page.insert_text(fitz.Point(50, y), line, fontsize=11, fontname=fname, color=(0.1, 0.1, 0.1))
        y += 24

    doc.save(str(out))
    doc.close()
    return out


def generate_scanned_hindi_certificate() -> Path:
    """Scanned Hindi PDF: Image of Devanagari Hindi certificate embedded without text layer."""
    out = SPECIMENS_DIR / "scanned_hindi_certificate.pdf"
    img = Image.new("RGB", (700, 950), color=(252, 250, 245))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(20, 20), (680, 930)], outline=(100, 30, 30), width=2)
    draw.rectangle([(30, 80), (670, 110)], fill=(255, 235, 235), outline=(200, 50, 50))
    draw.text((120, 90), WATERMARK_TEXT, fill=(200, 30, 30))

    try:
        font_h = ImageFont.truetype(NIRMALA_FONT_PATH, 24)
        font_b = ImageFont.truetype(NIRMALA_FONT_PATH, 18)
    except Exception:
        font_h = font_b = ImageFont.load_default()

    draw.text((220, 40), "महाराष्ट्र शासन - राजस्व विभाग", fill=(100, 20, 20), font=font_h)
    draw.text((250, 130), "आय प्रमाण पत्र", fill=(20, 20, 20), font=font_h)

    text_content = (
        "आवेदक का नाम: अनिता सुरेश कदम\n"
        "वार्षिक पारिवारिक आय: ₹ १,२०,०००\n"
        "वित्तीय वर्ष: २०२६-२७\n"
        "वैधता: ३१/०३/२०२७\n"
        "प्रमाणपत्र क्रमांक: MH-REV-2026-SCN-HI-6622\n"
        "सक्षम प्राधिकारी: अनुविभागीय अधिकारी, पुणे"
    )

    y = 200
    for line in text_content.split("\n"):
        draw.text((60, y), line, fill=(10, 10, 10), font=font_b)
        y += 40

    draw.rectangle([(420, 600), (620, 720)], outline=(0, 60, 150), width=2)
    draw.text((450, 630), "[शासकीय मुहर]", fill=(0, 60, 150), font=font_b)
    draw.text((440, 670), "अनुविभागीय अधिकारी", fill=(0, 60, 150), font=font_b)

    buf = io.BytesIO()
    img.save(buf, format="PNG")

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(page.rect, stream=buf.getvalue())
    doc.set_metadata({"keywords": text_content, "title": "Scanned Hindi Income Certificate"})
    doc.save(str(out))
    doc.close()
    return out


def generate_marathi_photograph() -> Path:
    """Realistic JPG photograph of Marathi certificate with perspective border & text comment."""
    out = SPECIMENS_DIR / "marathi_photograph.jpg"
    img = Image.new("RGB", (800, 1050), color=(245, 240, 230))
    draw = ImageDraw.Draw(img)

    # Document sheet on top of table surface
    draw.rectangle([(40, 40), (760, 1010)], fill=(255, 254, 250), outline=(180, 170, 160), width=2)
    draw.rectangle([(50, 100), (750, 130)], fill=(255, 235, 235), outline=(200, 50, 50))
    draw.text((150, 110), WATERMARK_TEXT, fill=(200, 30, 30))

    try:
        font_h = ImageFont.truetype(NIRMALA_FONT_PATH, 26)
        font_b = ImageFont.truetype(NIRMALA_FONT_PATH, 20)
    except Exception:
        font_h = font_b = ImageFont.load_default()

    draw.text((250, 60), "महाराष्ट्र शासन - महसूल विभाग", fill=(100, 20, 20), font=font_h)
    draw.text((270, 150), "उत्पन्न प्रमाणपत्र (Photo)", fill=(20, 20, 20), font=font_h)

    text_content = (
        "अर्जदाराचे नाव: अनिता सुरेश कदम\n"
        "वार्षिक कौटुंबिक उत्पन्न: ₹ १,२०,०००\n"
        "वित्तीय वर्ष: २०२६-२७\n"
        "वैधता: ३१/०३/२०२७\n"
        "प्रमाणपत्र क्रमांक: MH-PHOTO-MR-2026-5544\n"
        "सक्षम प्राधिकारी: तहसीलदार, हवेली, पुणे"
    )

    y = 230
    for line in text_content.split("\n"):
        draw.text((80, y), line, fill=(15, 15, 15), font=font_b)
        y += 45

    # Stamp
    draw.rectangle([(480, 700), (700, 840)], outline=(20, 70, 160), width=2)
    draw.text((510, 730), "[शासकीय शिक्का]", fill=(20, 70, 160), font=font_b)
    draw.text((500, 780), "तहसीलदार, हवेली", fill=(20, 70, 160), font=font_b)

    img.save(str(out), format="JPEG", quality=90, comment=text_content.encode("utf-8"))
    return out


def generate_hindi_photograph() -> Path:
    """Realistic JPG photograph of Hindi certificate with perspective border & text comment."""
    out = SPECIMENS_DIR / "hindi_photograph.jpg"
    img = Image.new("RGB", (800, 1050), color=(245, 240, 230))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(40, 40), (760, 1010)], fill=(255, 254, 250), outline=(180, 170, 160), width=2)
    draw.rectangle([(50, 100), (750, 130)], fill=(255, 235, 235), outline=(200, 50, 50))
    draw.text((150, 110), WATERMARK_TEXT, fill=(200, 30, 30))

    try:
        font_h = ImageFont.truetype(NIRMALA_FONT_PATH, 26)
        font_b = ImageFont.truetype(NIRMALA_FONT_PATH, 20)
    except Exception:
        font_h = font_b = ImageFont.load_default()

    draw.text((250, 60), "महाराष्ट्र शासन - राजस्व विभाग", fill=(100, 20, 20), font=font_h)
    draw.text((280, 150), "आय प्रमाण पत्र (Photo)", fill=(20, 20, 20), font=font_h)

    text_content = (
        "आवेदक का नाम: अनिता सुरेश कदम\n"
        "वार्षिक पारिवारिक आय: ₹ १,२०,०००\n"
        "वित्तीय वर्ष: २०२६-२७\n"
        "वैधता: ३१/०३/२०२७\n"
        "प्रमाणपत्र क्रमांक: MH-PHOTO-HI-2026-4433\n"
        "सक्षम प्राधिकारी: अनुविभागीय अधिकारी, पुणे"
    )

    y = 230
    for line in text_content.split("\n"):
        draw.text((80, y), line, fill=(15, 15, 15), font=font_b)
        y += 45

    draw.rectangle([(480, 700), (700, 840)], outline=(20, 70, 160), width=2)
    draw.text((510, 730), "[शासकीय मुहर]", fill=(20, 70, 160), font=font_b)
    draw.text((500, 780), "अनुविभागीय अधिकारी", fill=(20, 70, 160), font=font_b)

    img.save(str(out), format="JPEG", quality=90, comment=text_content.encode("utf-8"))
    return out


def generate_low_resolution_document() -> Path:
    """Low resolution PNG document (< 300px) that triggers LOW_RESOLUTION_IMAGE finding."""
    out = SPECIMENS_DIR / "low_resolution_document.png"
    img = Image.new("RGB", (180, 120), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "LOW RES SCAN", fill=(100, 10, 10))
    draw.text((10, 30), WATERMARK_TEXT[:25], fill=(200, 50, 50))
    draw.text((10, 50), "Income: 120000", fill=(50, 50, 50))
    draw.text((10, 70), "FY: 2026-27", fill=(50, 50, 50))
    img.save(str(out), format="PNG")
    return out


def generate_blurred_document() -> Path:
    """Excessively blurred document with Laplacian variance < 45, triggering IMAGE_EXCESSIVE_BLUR."""
    out = SPECIMENS_DIR / "blurred_document.png"
    img = Image.new("RGB", (600, 800), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), WATERMARK_TEXT, fill=(200, 50, 50))
    draw.text((50, 120), "TAHSIL OFFICE INCOME CERTIFICATE", fill=(20, 20, 20))
    draw.text((50, 180), "Applicant Name: Sunita Ramesh Patil", fill=(0, 0, 0))
    draw.text((50, 240), "Annual Family Income: INR 120000", fill=(0, 0, 0))
    for y in range(300, 700, 40):
        draw.line([(50, y), (550, y)], fill=(150, 150, 150), width=3)
    blurred = img.filter(ImageFilter.GaussianBlur(radius=10))
    blurred.save(str(out), format="PNG")
    return out


def generate_missing_page_multipage() -> Path:
    """Multi-page document where Page 2 of 3 is missing, triggering sequence violation."""
    out = SPECIMENS_DIR / "missing_page_multipage.pdf"
    doc = fitz.open()

    # Page 1 of 3
    p1 = doc.new_page(width=595, height=842)
    _add_watermark_and_header(p1, "Application Submission - Page 1 of 3", "Revenue Department Maharashtra")
    p1.insert_text(fitz.Point(50, 160), "Applicant Name: Sunita Ramesh Patil", fontsize=12, fontname="helv")
    p1.insert_text(fitz.Point(50, 190), "Scheme: Sanjay Gandhi Niradhar Anudan Yojana", fontsize=11, fontname="helv")
    p1.insert_text(fitz.Point(50, 230), "Page Sequence Declared: Page 1 of 3", fontsize=11, fontname="helv", color=(0.8, 0.2, 0.2))

    # Page 3 of 3 (Page 2 missing!)
    p3 = doc.new_page(width=595, height=842)
    _add_watermark_and_header(p3, "Application Submission - Page 3 of 3", "Revenue Department Maharashtra")
    p3.insert_text(fitz.Point(50, 160), "Statutory Declaration & Signature Page", fontsize=12, fontname="helv")
    p3.insert_text(fitz.Point(50, 190), "Page Sequence Declared: Page 3 of 3 (Notice: Page 2 of 3 is MISSING)", fontsize=11, fontname="helv", color=(0.8, 0.2, 0.2))
    p3.insert_text(fitz.Point(50, 230), "Warning: Incomplete multi-page submission cannot be processed.", fontsize=11, fontname="helv")

    doc.save(str(out))
    doc.close()
    return out


def generate_valid_financial_year_certificate() -> Path:
    """Income certificate with valid active financial year 2026-27."""
    out = SPECIMENS_DIR / "valid_financial_year_certificate.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    _add_watermark_and_header(page, "Tahsil Income Certificate (Active FY 2026-27)", "Revenue Department Maharashtra")

    lines = [
        "Certificate No: MH-REV-2026-FY-VALID-01",
        "Issue Date: 05/04/2026",
        "",
        "Applicant Name: Sunita Ramesh Patil",
        "Total Annual Family Income: INR 120000",
        "Financial Year: 2026-27",
        "Valid Until: 31/03/2027",
        "Status: ACTIVE AND VALID FOR SCHEME YEAR 2026-27",
    ]
    y = 150
    for line in lines:
        page.insert_text(fitz.Point(50, y), line, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
        y += 24

    doc.save(str(out))
    doc.close()
    return out


def generate_invalid_financial_year_certificate() -> Path:
    """Income certificate with invalid/past financial year 2020-21."""
    out = SPECIMENS_DIR / "invalid_financial_year_certificate.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    _add_watermark_and_header(page, "Tahsil Income Certificate (Stale FY 2020-21)", "Revenue Department Maharashtra")

    lines = [
        "Certificate No: MH-REV-2020-FY-STALE-99",
        "Issue Date: 12/06/2020",
        "",
        "Applicant Name: Sunita Ramesh Patil",
        "Total Annual Family Income: INR 120000",
        "Financial Year: 2020-21",
        "Valid Until: 31/03/2021",
        "Status: STALE / PAST FINANCIAL YEAR (REPLACEMENT REQUIRED)",
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
        # Baseline fixtures
        "valid_income": generate_valid_income_certificate(),
        "expired_income": generate_expired_income_certificate(),
        "name_mismatch": generate_name_mismatch_aadhaar(),
        "income_exceeded": generate_income_exceeded_certificate(),
        "unreadable_blur": generate_unreadable_blur(),
        "incomplete_multipage": generate_incomplete_multipage(),
        "wrong_type": generate_wrong_document_type(),
        "alternative_domicile": generate_alternative_domicile_ration_card(),
        "transliterated_name": generate_transliterated_name_certificate(),
        # RC3 mandatory fixtures
        "searchable_english": generate_searchable_english_certificate(),
        "scanned_english": generate_scanned_english_certificate(),
        "searchable_marathi": generate_searchable_marathi_certificate(),
        "scanned_marathi": generate_scanned_marathi_certificate(),
        "searchable_hindi": generate_searchable_hindi_certificate(),
        "scanned_hindi": generate_scanned_hindi_certificate(),
        "marathi_photo": generate_marathi_photograph(),
        "hindi_photo": generate_hindi_photograph(),
        "low_resolution": generate_low_resolution_document(),
        "blurred_doc": generate_blurred_document(),
        "missing_page": generate_missing_page_multipage(),
        "valid_fy": generate_valid_financial_year_certificate(),
        "invalid_fy": generate_invalid_financial_year_certificate(),
    }


if __name__ == "__main__":
    generated = generate_all_specimens()
    print(f"Successfully generated {len(generated)} synthetic document specimens in {SPECIMENS_DIR}")
    for k, p in generated.items():
        print(f"  - {k}: {p.name} ({p.stat().st_size} bytes)")
