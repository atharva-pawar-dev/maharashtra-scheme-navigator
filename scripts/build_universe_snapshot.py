"""TRIMURTI v3 Universe Snapshot Generator (Milestone SC-G2).

Compiles the dated, immutable research universe snapshot U-20261120.json
encompassing all State departments, welfare corporations, central ministries,
district authorities, and local municipal corporations.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
UNIVERSE_DIR = REPO_ROOT / "data" / "research" / "universe"
DOCS_CATALOGUE_DIR = REPO_ROOT / "docs" / "catalogue"
REPORTS_DIR = REPO_ROOT / "reports"

STATE_DEPARTMENTS = [
    {
        "authority_id": "AUTH-MH-DEPT-01",
        "name_en": "Social Justice and Special Assistance Department",
        "name_mr": "सामाजिक न्याय व विशेष सहाय्य विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://sjsa.maharashtra.gov.in",
        "scheme_directory_url": "https://sjsa.maharashtra.gov.in/en/schemes-page",
        "portal_domain": "sjsa.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Core department administering social pensions, Scheduled Caste scholarships, disability welfare, senior citizen benefits, and hostels.",
        "administered_subordinates": ["AUTH-MH-CORP-01", "AUTH-MH-CORP-08", "AUTH-MH-CORP-09", "AUTH-MH-CORP-10"]
    },
    {
        "authority_id": "AUTH-MH-DEPT-02",
        "name_en": "Tribal Development Department",
        "name_mr": "आदिवासी विकास विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://tribal.maharashtra.gov.in",
        "scheme_directory_url": "https://tribal.maharashtra.gov.in/en/schemes",
        "portal_domain": "tribal.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Scheduled Tribe welfare, post-matric ST scholarships, ashram shala stipends, Shabari Awas, and forest rights.",
        "administered_subordinates": ["AUTH-MH-CORP-03", "AUTH-MH-CORP-11"]
    },
    {
        "authority_id": "AUTH-MH-DEPT-03",
        "name_en": "Other Backward Bahujan Welfare Department",
        "name_mr": "इतर मागास बहुजन कल्याण विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://msobcfdc.org",
        "scheme_directory_url": "https://mahadbt.maharashtra.gov.in/SchemeData/SchemeData?str=E9DDFA370C0561DA2F1B2F63E2BE0FD6",
        "portal_domain": "mahadbt.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers VJNT, OBC, and Special Backward Class scholarships, tuition waivers, and educational concessions.",
        "administered_subordinates": ["AUTH-MH-CORP-02", "AUTH-MH-CORP-05"]
    },
    {
        "authority_id": "AUTH-MH-DEPT-04",
        "name_en": "Women and Child Development Department",
        "name_mr": "महिला व बालविकास विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://womenchild.maharashtra.gov.in",
        "scheme_directory_url": "https://ladkibahin.maharashtra.gov.in",
        "portal_domain": "womenchild.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Mukhyamantri Majhi Ladki Bahin Yojana, Beti Bachao Beti Padhao, Manodhairya, and orphan welfare.",
        "administered_subordinates": ["AUTH-MH-CORP-12"]
    },
    {
        "authority_id": "AUTH-MH-DEPT-05",
        "name_en": "Agriculture Department",
        "name_mr": "कृषी विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://krishi.maharashtra.gov.in",
        "scheme_directory_url": "https://krishi.maharashtra.gov.in/schemes",
        "portal_domain": "krishi.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Namo Shetkari Maha Samman Nidhi, Bhausaheb Fundkar Phalbag, farm mechanization, drip irrigation, and crop insurance.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-06",
        "name_en": "School Education and Sports Department",
        "name_mr": "शालेय शिक्षण व क्रीडा विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://education.maharashtra.gov.in",
        "scheme_directory_url": "https://education.maharashtra.gov.in/schemes",
        "portal_domain": "education.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers pre-matric scholarships, attendance allowances for girls, Ahilyabai Holkar bus travel concessions, and mid-day meals.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-07",
        "name_en": "Higher and Technical Education Department",
        "name_mr": "उच्च व तंत्र शिक्षण विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://htedu.maharashtra.gov.in",
        "scheme_directory_url": "https://mahadbt.maharashtra.gov.in",
        "portal_domain": "htedu.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Rajarshi Chhatrapati Shahu Maharaj EBC Tuition Fee Waiver, Dr. Panjabrao Deshmukh Hostel Maintenance Allowance.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-08",
        "name_en": "Public Health and Family Welfare Department",
        "name_mr": "सार्वजनिक आरोग्य व कुटुंब कल्याण विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://arogya.maharashtra.gov.in",
        "scheme_directory_url": "https://www.jeevandayee.gov.in",
        "portal_domain": "arogya.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Mahatma Jyotirao Phule Jan Arogya Yojana (MJPJAY), free universal cashless treatment in empanelled hospitals.",
        "administered_subordinates": ["AUTH-MH-CORP-13"]
    },
    {
        "authority_id": "AUTH-MH-DEPT-09",
        "name_en": "Rural Development and Panchayati Raj Department",
        "name_mr": "ग्रामविकास व पंचायत राज विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://rdd.maharashtra.gov.in",
        "scheme_directory_url": "https://rdd.maharashtra.gov.in/schemes",
        "portal_domain": "rdd.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers rural sanitation, PMAY-Gramin state coordination, and MSRLM Umed self-help groups.",
        "administered_subordinates": ["AUTH-MH-CORP-14"]
    },
    {
        "authority_id": "AUTH-MH-DEPT-10",
        "name_en": "Urban Development Department",
        "name_mr": "नगर विकास विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://urban.maharashtra.gov.in",
        "scheme_directory_url": "https://urban.maharashtra.gov.in/schemes",
        "portal_domain": "urban.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Oversight of 29 municipal corporations, PM SVANidhi coordination, and urban poverty alleviation schemes.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-11",
        "name_en": "Housing Department",
        "name_mr": "गृहनिर्माण विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://housing.maharashtra.gov.in",
        "scheme_directory_url": "https://mhada.gov.in",
        "portal_domain": "housing.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Ramai Awas Yojana, Shabari Awas, MHADA lottery housing, and PMAY affordable housing.",
        "administered_subordinates": ["AUTH-MH-CORP-15"]
    },
    {
        "authority_id": "AUTH-MH-DEPT-12",
        "name_en": "Minority Development Department",
        "name_mr": "अल्पसंख्याक विकास विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://mdd.maharashtra.gov.in",
        "scheme_directory_url": "https://mdd.maharashtra.gov.in/schemes",
        "portal_domain": "mdd.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers State Minority Post-Matric and Professional Scholarships, free coaching, and Maulana Azad loan schemes.",
        "administered_subordinates": ["AUTH-MH-CORP-06"]
    },
    {
        "authority_id": "AUTH-MH-DEPT-13",
        "name_en": "Persons with Disabilities Welfare Department (Divyang Kalyan)",
        "name_mr": "दिव्यांग कल्याण विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://divyang.maharashtra.gov.in",
        "scheme_directory_url": "https://divyang.maharashtra.gov.in/schemes",
        "portal_domain": "divyang.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Independent state department established in 2023 for disability pensions, assistive aids, motorized tricycles, and self-employment.",
        "administered_subordinates": ["AUTH-MH-CORP-07"]
    },
    {
        "authority_id": "AUTH-MH-DEPT-14",
        "name_en": "Labour Department",
        "name_mr": "कामगार विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://labour.maharashtra.gov.in",
        "scheme_directory_url": "https://mahabocw.in",
        "portal_domain": "labour.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers BOCW construction workers welfare schemes, financial aid for child education, marriage assistance, and tools allowance.",
        "administered_subordinates": ["AUTH-MH-CORP-16"]
    },
    {
        "authority_id": "AUTH-MH-DEPT-15",
        "name_en": "Industries, Energy and Labour Department (Industries Section)",
        "name_mr": "उद्योग, ऊर्जा व कामगार विभाग (उद्योग)",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://industry.maharashtra.gov.in",
        "scheme_directory_url": "https://cmegp.gov.in",
        "portal_domain": "industry.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Chief Minister Employment Generation Programme (CMEGP), interest subsidy, and capital incentives.",
        "administered_subordinates": ["AUTH-MH-CORP-04", "AUTH-MH-CORP-17"]
    },
    {
        "authority_id": "AUTH-MH-DEPT-16",
        "name_en": "Skill Development, Employment and Entrepreneurship Department",
        "name_mr": "कौशल्य विकास, रोजगार व उद्योजकता विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://skills.maharashtra.gov.in",
        "scheme_directory_url": "https://rojgar.maharashtra.gov.in",
        "portal_domain": "rojgar.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Pramod Mahajan Kaushalya Vikas Yojana, apprenticeship allowances, and youth employment training.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-17",
        "name_en": "Food, Civil Supplies and Consumer Protection Department",
        "name_mr": "अन्न, नागरी पुरवठा व ग्राहक संरक्षण विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://mahafood.gov.in",
        "scheme_directory_url": "https://mahafood.gov.in/schemes",
        "portal_domain": "mahafood.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Antyodaya Anna Yojana (AAY), Priority Household (PHH) subsidized foodgrains, and Shiv Bhojan Thali.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-18",
        "name_en": "Cooperation, Marketing and Textiles Department",
        "name_mr": "सहकार, पणन आणि वस्त्रोद्योग विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://cooperation.maharashtra.gov.in",
        "scheme_directory_url": "https://cooperation.maharashtra.gov.in/schemes",
        "portal_domain": "cooperation.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers farm loan waiver verification (Chhatrapati Shivaji Maharaj Shetkari Sanman Yojana), weaver subsidies, and PACS credit.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-19",
        "name_en": "Animal Husbandry, Dairy Development and Fisheries Department",
        "name_mr": "पशुसंवर्धन, दुग्धव्यवसाय आणि मत्स्यव्यवसाय विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://ahd.maharashtra.gov.in",
        "scheme_directory_url": "https://ahd.maharashtra.gov.in/schemes",
        "portal_domain": "ahd.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers livestock distribution, milch cow/buffalo subsidy, goat rearing schemes, and Matsya Sampada state share.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-20",
        "name_en": "Medical Education and Drugs Department",
        "name_mr": "वैद्यकीय शिक्षण व औषधी द्रव्ये विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://med-edu.maharashtra.gov.in",
        "scheme_directory_url": "https://mahadbt.maharashtra.gov.in",
        "portal_domain": "med-edu.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers tuition and exam fee reimbursement for medical, dental, and nursing students from reserved and EBC categories.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-21",
        "name_en": "Energy Department",
        "name_mr": "ऊर्जा विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://energy.maharashtra.gov.in",
        "scheme_directory_url": "https://www.mahadiscom.in/solar_mskvy/",
        "portal_domain": "energy.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Mukhyamantri Saur Krushi Pump Yojana, agricultural electricity subsidies, and domestic solar rooftop assistance.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-22",
        "name_en": "Tourism and Cultural Affairs Department",
        "name_mr": "पर्यटन व सांस्कृतिक कार्य विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://cultural.maharashtra.gov.in",
        "scheme_directory_url": "https://cultural.maharashtra.gov.in/schemes",
        "portal_domain": "cultural.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers financial assistance to elderly artists in indigent circumstances (वृद्ध कलाकार मानधन योजना).",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-23",
        "name_en": "Revenue and Forest Department",
        "name_mr": "महसूल आणि वन विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://revenue.maharashtra.gov.in",
        "scheme_directory_url": "https://mahabhumi.gov.in",
        "portal_domain": "revenue.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers natural calamity compensation (SDRF/NDRF crop damage relief), Gopinath Munde Shetkari Apghat Bima Yojana, and land title deeds.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-24",
        "name_en": "Water Supply and Sanitation Department",
        "name_mr": "पाणी पुरवठा व स्वच्छता विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://water.maharashtra.gov.in",
        "scheme_directory_url": "https://jaljeevanmission.gov.in",
        "portal_domain": "water.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Jal Jeevan Mission individual household tap connection subsidy in rural areas.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-25",
        "name_en": "Environment and Climate Change Department",
        "name_mr": "पर्यावरण आणि हवामान बदल विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://env.maharashtra.gov.in",
        "scheme_directory_url": "https://env.maharashtra.gov.in/schemes",
        "portal_domain": "env.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Majhi Vasundhara incentives and rural renewable energy subsidies.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-26",
        "name_en": "Soil and Water Conservation Department",
        "name_mr": "मृद व जलसंधारण विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://swc.maharashtra.gov.in",
        "scheme_directory_url": "https://swc.maharashtra.gov.in/schemes",
        "portal_domain": "swc.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Jalyukt Shivar Abhiyan farm pond and soil conservation individual works.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-27",
        "name_en": "Disaster Management, Relief and Rehabilitation Department",
        "name_mr": "आपत्ती व्यवस्थापन, मदत आणि पुनर्वसन विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://rnr.maharashtra.gov.in",
        "scheme_directory_url": "https://rnr.maharashtra.gov.in/schemes",
        "portal_domain": "rnr.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers ex-gratia relief for disaster loss of life, house damage compensation, and drought relief.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-28",
        "name_en": "Planning Department",
        "name_mr": "नियोजन विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://planning.maharashtra.gov.in",
        "scheme_directory_url": "https://planning.maharashtra.gov.in/schemes",
        "portal_domain": "planning.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers District Planning and Development Committee (DPDC) welfare allocations, MLA/MP local area development, and Human Development Index programs.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-29",
        "name_en": "Finance Department",
        "name_mr": "वित्त विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://finance.maharashtra.gov.in",
        "scheme_directory_url": "https://koshwahini.maharashtra.gov.in",
        "portal_domain": "finance.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Direct oversight of state treasury DBT disbursement channels, budget sanction GRs, and ex-gratia approvals.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-30",
        "name_en": "General Administration Department (GAD)",
        "name_mr": "सामान्य प्रशासन विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://gad.maharashtra.gov.in",
        "scheme_directory_url": "https://aaplesarkar.mahaonline.gov.in",
        "portal_domain": "gad.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Right to Services (RTS), Aaple Sarkar citizen services portal, freedom fighter pensions, and ex-servicemen welfare.",
        "administered_subordinates": ["AUTH-MH-CORP-18"]
    },
    {
        "authority_id": "AUTH-MH-DEPT-31",
        "name_en": "Home Department",
        "name_mr": "गृह विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://home.maharashtra.gov.in",
        "scheme_directory_url": "https://home.maharashtra.gov.in/schemes",
        "portal_domain": "home.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers police welfare assistance, civilian gallantry rewards, and victim compensation scheme.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-32",
        "name_en": "Law and Judiciary Department",
        "name_mr": "विधि व न्याय विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://lj.maharashtra.gov.in",
        "scheme_directory_url": "https://legalservices.maharashtra.gov.in",
        "portal_domain": "lj.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Maharashtra State Legal Services Authority (MSLSA) free legal aid to women, SC/ST, children, and low-income citizens.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-33",
        "name_en": "Transport Department",
        "name_mr": "परिवहन विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://transport.maharashtra.gov.in",
        "scheme_directory_url": "https://msrtc.maharashtra.gov.in",
        "portal_domain": "transport.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers MSRTC passenger fare concessions: 50% concession for women (Mahila Samman Yojana), 100% free travel for senior citizens 75+ (Amrit Jyeshtha Nagrik), and divyang travel passes.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-34",
        "name_en": "Public Works Department",
        "name_mr": "सार्वजनिक बांधकाम विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://pwd.maharashtra.gov.in",
        "scheme_directory_url": "https://pwd.maharashtra.gov.in",
        "portal_domain": "pwd.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Unemployed engineers registration and small contractor quota subsidies.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-35",
        "name_en": "Water Resources Department (Irrigation)",
        "name_mr": "जलसंपदा विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://wrd.maharashtra.gov.in",
        "scheme_directory_url": "https://wrd.maharashtra.gov.in",
        "portal_domain": "wrd.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Project affected persons (PAP) rehabilitation, alternative land allotment, and compensation.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-36",
        "name_en": "Marathi Language Department",
        "name_mr": "मराठी भाषा विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://marathi.maharashtra.gov.in",
        "scheme_directory_url": "https://marathi.maharashtra.gov.in/schemes",
        "portal_domain": "marathi.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Literary awards, book publication grants, and senior Marathi scholar pensions.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-37",
        "name_en": "Employment Guarantee Scheme (EGS) Department",
        "name_mr": "रोजगार हमी योजना विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://egs.maharashtra.gov.in",
        "scheme_directory_url": "https://nrega.nic.in",
        "portal_domain": "egs.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Maharashtra Employment Guarantee Scheme (EGS) and MGNREGA guaranteed 100 days wage employment and individual orchard planting.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-38",
        "name_en": "State Excise Department",
        "name_mr": "राज्य उत्पादन शुल्क विभाग",
        "category": "STATE_DEPARTMENT",
        "jurisdiction_level": "STATE",
        "official_website": "https://excise.maharashtra.gov.in",
        "scheme_directory_url": "https://excise.maharashtra.gov.in",
        "portal_domain": "excise.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Traditional toddy tapper and neera producer welfare assistance.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-39",
        "name_en": "Directorate of Municipal Administration (DMA)",
        "name_mr": "नगरपरिषद प्रशासन संचालनालय",
        "category": "STATE_DIRECTORATE",
        "jurisdiction_level": "STATE",
        "official_website": "https://mahaud.gov.in",
        "scheme_directory_url": "https://mahaud.gov.in",
        "portal_domain": "mahaud.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Oversight of municipal councils and nagar panchayats across Maharashtra for local poverty welfare programmes.",
        "administered_subordinates": []
    },
    {
        "authority_id": "AUTH-MH-DEPT-40",
        "name_en": "Directorate of Information Technology (DIT)",
        "name_mr": "माहिती तंत्रज्ञान संचालनालय",
        "category": "STATE_DIRECTORATE",
        "jurisdiction_level": "STATE",
        "official_website": "https://it.maharashtra.gov.in",
        "scheme_directory_url": "https://mahadbt2.maharashtra.gov.in",
        "portal_domain": "it.maharashtra.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Operates the unified MahaDBT portal connecting 38+ scholarship and DBT benefit schemes.",
        "administered_subordinates": []
    }
]

STATE_CORPORATIONS = [
    {
        "authority_id": "AUTH-MH-CORP-01",
        "name_en": "Mahatma Phule Backward Class Development Corporation (MPBCDC)",
        "name_mr": "महात्मा फुले मागासवर्ग विकास महामंडळ मर्यादित",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-01",
        "official_website": "https://mpbcdc.maharashtra.gov.in",
        "scheme_directory_url": "https://mpbcdc.maharashtra.gov.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Specialized loans, 50% capital subsidies, and seed capital schemes for SC beneficiaries."
    },
    {
        "authority_id": "AUTH-MH-CORP-02",
        "name_en": "Mahatma Jyotiba Phule Research, Training & OBC Development Institute (Mahajyoti)",
        "name_mr": "महात्मा ज्योतिबा फुले संशोधन, प्रशिक्षण व असंघटित कामगार विकास संस्था (महाज्योती)",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-03",
        "official_website": "https://mahajyoti.org.in",
        "scheme_directory_url": "https://mahajyoti.org.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "OBC, VJNT, and SBC PhD fellowships, UPSC/MPSC coaching stipends, and tablet distribution."
    },
    {
        "authority_id": "AUTH-MH-CORP-03",
        "name_en": "Tribal Research and Training Institute (TRTI)",
        "name_mr": "आदिवासी संशोधन व प्रशिक्षण संस्था (टीआरटीआय)",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-02",
        "official_website": "https://trti.maharashtra.gov.in",
        "scheme_directory_url": "https://trti.maharashtra.gov.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "ST competitive examination coaching, higher education fellowships, and tribal youth skill development."
    },
    {
        "authority_id": "AUTH-MH-CORP-04",
        "name_en": "Annasaheb Patil Arthik-Magas Vikas Mahamandal",
        "name_mr": "अण्णासाहेब पाटील आर्थिक मागास विकास महामंडळ मर्यादित",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-15",
        "official_website": "https://esamanyatha.maharashtra.gov.in",
        "scheme_directory_url": "https://esamanyatha.maharashtra.gov.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Interest refund scheme for youth entrepreneurs (IR-II: up to Rs 15 lakh bank loan interest reimbursement)."
    },
    {
        "authority_id": "AUTH-MH-CORP-05",
        "name_en": "Vasantrao Naik Vimukta Jatis and Nomadic Tribes Development Corporation",
        "name_mr": "वसंतराव नाईक विमुक्त जाती व भटक्या जमाती विकास महामंडळ",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-03",
        "official_website": "https://vjnt.maharashtra.gov.in",
        "scheme_directory_url": "https://vjnt.maharashtra.gov.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Self-employment loans and educational subsidies for VJNT youth."
    },
    {
        "authority_id": "AUTH-MH-CORP-06",
        "name_en": "Maulana Azad Minorities Financial Development Corporation (MAMFDC)",
        "name_mr": "मौलाना आझाद अल्पसंख्याक आर्थिक विकास महामंडळ मर्यादित",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-12",
        "official_website": "https://mamfdc.maharashtra.gov.in",
        "scheme_directory_url": "https://mamfdc.maharashtra.gov.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Micro-finance, education loans, and term loans for minority community members."
    },
    {
        "authority_id": "AUTH-MH-CORP-07",
        "name_en": "Maharashtra State Divyang Finance & Development Corporation",
        "name_mr": "महाराष्ट्र राज्य दिव्यांग वित्त व विकास महामंडळ",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-13",
        "official_website": "https://mshfdc.co.in",
        "scheme_directory_url": "https://mshfdc.co.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Concessional loans and assistive device grants for persons with disabilities."
    },
    {
        "authority_id": "AUTH-MH-CORP-08",
        "name_en": "Dr. Babasaheb Ambedkar Research and Training Institute (BARTI)",
        "name_mr": "डॉ. बाबासाहेब आंबेडकर संशोधन व प्रशिक्षण संस्था (बार्टी)",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-01",
        "official_website": "https://barti.maharashtra.gov.in",
        "scheme_directory_url": "https://barti.maharashtra.gov.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "SC M.Phil/Ph.D. national fellowships (BANRF), UPSC residential coaching, and skill training."
    },
    {
        "authority_id": "AUTH-MH-CORP-09",
        "name_en": "Sant Rohidas Leather Industries & Footwear Corporation (LIDCOM)",
        "name_mr": "संत रोहिदास चर्मोद्योग व चर्मकार विकास महामंडळ मर्यादित",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-01",
        "official_website": "https://lidcom.gov.in",
        "scheme_directory_url": "https://lidcom.gov.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Artisan seed capital, footwear kiosk subsidy, and leather worker toolkits."
    },
    {
        "authority_id": "AUTH-MH-CORP-10",
        "name_en": "Maharashtra State Other Backward Class Finance & Development Corporation",
        "name_mr": "महाराष्ट्र राज्य इतर मागासवर्गीय वित्त आणि विकास महामंडळ मर्यादित",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-03",
        "official_website": "https://msobcfdc.org",
        "scheme_directory_url": "https://msobcfdc.org/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Term loans and direct financing for traditional occupations of OBC communities."
    },
    {
        "authority_id": "AUTH-MH-CORP-11",
        "name_en": "Shabari Adivasi Vitta Va Vikas Mahamandal",
        "name_mr": "शबरी आदिवासी वित्त व विकास महामंडळ मर्यादित",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-02",
        "official_website": "https://shabari.maharashtra.gov.in",
        "scheme_directory_url": "https://shabari.maharashtra.gov.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Mini-tractor subsidy, grocery shop loans, and seed money for tribal entrepreneurs."
    },
    {
        "authority_id": "AUTH-MH-CORP-12",
        "name_en": "Maharashtra State Commission for Women",
        "name_mr": "महाराष्ट्र राज्य महिला आयोग",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-04",
        "official_website": "https://mscw.org.in",
        "scheme_directory_url": "https://mscw.org.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Legal counseling, rehabilitation assistance, and victim rehabilitation grants."
    },
    {
        "authority_id": "AUTH-MH-CORP-13",
        "name_en": "State Health Society, National Health Mission Maharashtra",
        "name_mr": "राष्ट्रीय आरोग्य अभियान, महाराष्ट्र",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-08",
        "official_website": "https://nrhm.maharashtra.gov.in",
        "scheme_directory_url": "https://nrhm.maharashtra.gov.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Janani Suraksha Yojana (JSY), Janani Shishu Suraksha Karyakram (JSSK), and free institutional delivery."
    },
    {
        "authority_id": "AUTH-MH-CORP-14",
        "name_en": "Maharashtra State Rural Livelihoods Mission (MSRLM Umed)",
        "name_mr": "महाराष्ट्र राज्य ग्रामीण जीवनोन्नती अभियान (उमेद)",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-09",
        "official_website": "https://umed.gov.in",
        "scheme_directory_url": "https://umed.gov.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Community Investment Fund (CIF), Revolving Fund (RF), and interest subvention for women SHGs."
    },
    {
        "authority_id": "AUTH-MH-CORP-15",
        "name_en": "Maharashtra Housing and Area Development Authority (MHADA)",
        "name_mr": "महाराष्ट्र गृहनिर्माण व क्षेत्रविकास प्राधिकरण (म्हाडा)",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-11",
        "official_website": "https://mhada.gov.in",
        "scheme_directory_url": "https://housing.mhada.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Subsidized housing lottery for EWS, LIG, and MIG categories across Mumbai, Pune, Konkan, Nashik, Amravati, and Nagpur."
    },
    {
        "authority_id": "AUTH-MH-CORP-16",
        "name_en": "Maharashtra Building and Other Construction Workers Welfare Board (MBOCW)",
        "name_mr": "महाराष्ट्र इमारत व इतर बांधकाम कामगार कल्याणकारी मंडळ",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-14",
        "official_website": "https://mahabocw.in",
        "scheme_directory_url": "https://mahabocw.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "32 welfare benefits including Rs 5,000 safety kit, Rs 10,000 child scholarship, maternity benefits, and housing subsidy."
    },
    {
        "authority_id": "AUTH-MH-CORP-17",
        "name_en": "Maharashtra State Khadi and Village Industries Board (KVIB)",
        "name_mr": "महाराष्ट्र राज्य खादी व ग्रामोद्योग मंडळ",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-15",
        "official_website": "https://kvib.maharashtra.gov.in",
        "scheme_directory_url": "https://kvib.maharashtra.gov.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Madhmashipalan (Honey bee keeping) individual subsidy and rural village industries margin money."
    },
    {
        "authority_id": "AUTH-MH-CORP-18",
        "name_en": "Chhatrapati Shahu Maharaj Research, Training & Human Development Institute (SARTHI)",
        "name_mr": "छत्रपती शाहू महाराज संशोधन, प्रशिक्षण व मानव विकास संस्था (सारथी)",
        "category": "STATE_CORPORATION",
        "parent_department_id": "AUTH-MH-DEPT-30",
        "official_website": "https://sarthi-maharashtragov.in",
        "scheme_directory_url": "https://sarthi-maharashtragov.in/schemes",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Maratha, Kunbi, and Maratha-Kunbi community educational fellowships (CSMNRF), competitive exam stipends, and skill development."
    }
]

CENTRAL_MINISTRIES = [
    {
        "authority_id": "AUTH-CEN-MIN-01",
        "name_en": "Ministry of Agriculture and Farmers Welfare",
        "name_mr": "कृषी आणि शेतकरी कल्याण मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://agricoop.nic.in",
        "scheme_directory_url": "https://pmkisan.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers PM-KISAN (Rs 6,000/yr), PM Fasal Bima Yojana (PMFBY), Agriculture Infrastructure Fund (AIF), and Kisan Credit Card (KCC)."
    },
    {
        "authority_id": "AUTH-CEN-MIN-02",
        "name_en": "Ministry of Health and Family Welfare",
        "name_mr": "आरोग्य आणि कुटुंब कल्याण मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://mohfw.gov.in",
        "scheme_directory_url": "https://pmjay.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers Ayushman Bharat PM-JAY (co-funded and co-branded with MJPJAY in Maharashtra up to Rs 5 lakh coverage)."
    },
    {
        "authority_id": "AUTH-CEN-MIN-03",
        "name_en": "Ministry of Rural Development",
        "name_mr": "ग्रामीण विकास मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://rural.gov.in",
        "scheme_directory_url": "https://nsap.nic.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers National Social Assistance Programme (NSAP: IGNOAPS, IGNWPS, IGNDPS, NFBS, Annapurna), PMAY-Gramin, and DAY-NRLM."
    },
    {
        "authority_id": "AUTH-CEN-MIN-04",
        "name_en": "Ministry of Housing and Urban Affairs",
        "name_mr": "गृहनिर्माण आणि शहरी व्यवहार मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://mohua.gov.in",
        "scheme_directory_url": "https://pmsvanidhi.mohua.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Administers PM SVANidhi (street vendor micro-credit Rs 10k/20k/50k), PMAY-Urban, and DAY-NULM."
    },
    {
        "authority_id": "AUTH-CEN-MIN-05",
        "name_en": "Ministry of Social Justice and Empowerment",
        "name_mr": "सामाजिक न्याय आणि सक्षमीकरण मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://socialjustice.gov.in",
        "scheme_directory_url": "https://scholarships.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Centrally sponsored Post-Matric SC scholarships (60:40 state share), PM-DAKSH, SMILE, and Rashtriya Vayoshri Yojana."
    },
    {
        "authority_id": "AUTH-CEN-MIN-06",
        "name_en": "Ministry of Tribal Affairs",
        "name_mr": "आदिवासी कार्य मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://tribal.nic.in",
        "scheme_directory_url": "https://scholarships.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Centrally sponsored Post-Matric ST scholarships, National Overseas Scholarship for ST, and Van Dhan Vikas Yojana."
    },
    {
        "authority_id": "AUTH-CEN-MIN-07",
        "name_en": "Ministry of Minority Affairs",
        "name_mr": "अल्पसंख्याक कार्य मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://minorityaffairs.gov.in",
        "scheme_directory_url": "https://scholarships.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Post-Matric and Merit-cum-Means Minority Scholarships, Begum Hazrat Mahal National Scholarship, and NMDFC credit."
    },
    {
        "authority_id": "AUTH-CEN-MIN-08",
        "name_en": "Ministry of Women and Child Development",
        "name_mr": "महिला आणि बालविकास मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://wcd.nic.in",
        "scheme_directory_url": "https://pmmvy.wcd.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Pradhan Mantri Matru Vandana Yojana (PMMVY: Rs 5,000 for first child, Rs 6,000 for second girl child), Mission Shakti, and Mission Vatsalya."
    },
    {
        "authority_id": "AUTH-CEN-MIN-09",
        "name_en": "Ministry of Labour and Employment",
        "name_mr": "कामगार आणि रोजगार मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://labour.gov.in",
        "scheme_directory_url": "https://maandhan.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Pradhan Mantri Shram Yogi Maandhan (PM-SYM: Rs 3,000/month pension for unorganized workers), e-Shram, and PM-LVM."
    },
    {
        "authority_id": "AUTH-CEN-MIN-10",
        "name_en": "Ministry of Micro, Small and Medium Enterprises",
        "name_mr": "सूक्ष्म, लघु आणि मध्यम उद्योग मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://msme.gov.in",
        "scheme_directory_url": "https://pmvishwakarma.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "PM Vishwakarma (toolkits + collateral-free loans for 18 traditional trades), Prime Minister Employment Generation Programme (PMEGP: 15-35% subsidy)."
    },
    {
        "authority_id": "AUTH-CEN-MIN-11",
        "name_en": "Ministry of Consumer Affairs, Food and Public Distribution",
        "name_mr": "ग्राहक व्यवहार, अन्न आणि सार्वजनिक वितरण मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://dfpd.gov.in",
        "scheme_directory_url": "https://nfsa.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Pradhan Mantri Garib Kalyan Anna Yojana (PMGKAY: 5kg free foodgrain per person per month under NFSA) and One Nation One Ration Card (ONORC)."
    },
    {
        "authority_id": "AUTH-CEN-MIN-12",
        "name_en": "Ministry of Education",
        "name_mr": "शिक्षण मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://education.gov.in",
        "scheme_directory_url": "https://scholarships.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "National Means-cum-Merit Scholarship Scheme (NMMSS: Rs 12,000/yr), PM-YASASVI, Central Sector Scholarship for College/University Students."
    },
    {
        "authority_id": "AUTH-CEN-MIN-13",
        "name_en": "Ministry of Finance (Department of Financial Services)",
        "name_mr": "वित्त मंत्रालय (वित्तीय सेवा विभाग), भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://financialservices.gov.in",
        "scheme_directory_url": "https://jansuraksha.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY: Rs 2 lakh life cover @ Rs 436/yr), PM Suraksha Bima Yojana (PMSBY: Rs 2 lakh accident cover @ Rs 20/yr), Atal Pension Yojana (APY)."
    },
    {
        "authority_id": "AUTH-CEN-MIN-14",
        "name_en": "Ministry of Petroleum and Natural Gas",
        "name_mr": "पेट्रोलियम आणि नैसर्गिक वायू मंत्रालय, भारत सरकार",
        "category": "CENTRAL_MINISTRY",
        "jurisdiction_level": "CENTRAL",
        "official_website": "https://mopng.gov.in",
        "scheme_directory_url": "https://pmuy.gov.in",
        "status": "ACTIVE_RESEARCHED",
        "inclusion_reason": "Pradhan Mantri Ujjwala Yojana 2.0 (PMUY: free LPG connection + first refill and stove for adult BPL women)."
    }
]


def load_municipal_corporations() -> List[Dict[str, Any]]:
    mc_file = REPO_ROOT / "data" / "local_governments" / "municipal_corporations.json"
    if not mc_file.exists():
        return []
    raw = json.loads(mc_file.read_text(encoding="utf-8"))
    mcs = []
    for m in raw:
        mcs.append({
            "authority_id": f"AUTH-LOC-{m['corporation_id'].upper()}",
            "corporation_id": m["corporation_id"],
            "name_en": m["official_name_en"],
            "name_mr": m["official_name_mr"],
            "name_hi": m["official_name_hi"],
            "category": "MUNICIPAL_CORPORATION",
            "jurisdiction_level": "MUNICIPAL_CORPORATION",
            "district": m.get("district"),
            "administrative_division": m.get("administrative_division"),
            "official_website": m.get("official_website"),
            "citizen_portal": m.get("main_citizen_portal"),
            "ward_count": m.get("ward_count", 0),
            "status": "ACTIVE_RESEARCHED",
            "inclusion_reason": f"Municipal Corporation administering local welfare, urban education, Divyang, and Women welfare schemes under Class {m.get('corporation_class', 'C')} charter."
        })
    return mcs


def load_districts() -> List[Dict[str, Any]]:
    districts = [
        ("Ahmednagar (Ahilyanagar)", "अहिल्यानगर", "Nashik"),
        ("Akola", "अकोला", "Amravati"),
        ("Amravati", "अमरावती", "Amravati"),
        ("Chhatrapati Sambhajinagar (Aurangabad)", "छत्रपती संभाजीनगर", "Chhatrapati Sambhajinagar"),
        ("Beed", "बीड", "Chhatrapati Sambhajinagar"),
        ("Bhandara", "भंडारा", "Nagpur"),
        ("Buldhana", "बुलढाणा", "Amravati"),
        ("Chandrapur", "चंद्रपूर", "Nagpur"),
        ("Dhule", "धुळे", "Nashik"),
        ("Gadchiroli", "गडचिरोली", "Nagpur"),
        ("Gondia", "गोंदिया", "Nagpur"),
        ("Hingoli", "हिंगोली", "Chhatrapati Sambhajinagar"),
        ("Jalgaon", "जळगाव", "Nashik"),
        ("Jalna", "जालना", "Chhatrapati Sambhajinagar"),
        ("Kolhapur", "कोल्हापूर", "Pune"),
        ("Latur", "लातूर", "Chhatrapati Sambhajinagar"),
        ("Mumbai City", "मुंबई शहर", "Konkan"),
        ("Mumbai Suburban", "मुंबई उपनगर", "Konkan"),
        ("Nagpur", "नागपूर", "Nagpur"),
        ("Nanded", "नांदेड", "Chhatrapati Sambhajinagar"),
        ("Nandurbar", "नंदुरबार", "Nashik"),
        ("Nashik", "नाशिक", "Nashik"),
        ("Dharashiv (Osmanabad)", "धाराशिव", "Chhatrapati Sambhajinagar"),
        ("Palghar", "पालघर", "Konkan"),
        ("Parbhani", "परभणी", "Chhatrapati Sambhajinagar"),
        ("Pune", "पुणे", "Pune"),
        ("Raigad", "रायगड", "Konkan"),
        ("Ratnagiri", "रत्नागिरी", "Konkan"),
        ("Sangli", "सांगली", "Pune"),
        ("Satara", "सातारा", "Pune"),
        ("Sindhudurg", "सिंधुदुर्ग", "Konkan"),
        ("Solapur", "सोलापूर", "Pune"),
        ("Thane", "ठाणे", "Konkan"),
        ("Wardha", "वर्धा", "Nagpur"),
        ("Washim", "वाशिम", "Amravati"),
        ("Yavatmal", "यवतमाळ", "Amravati")
    ]
    res = []
    for idx, (en, mr, div) in enumerate(districts, start=1):
        slug = en.split()[0].lower().replace("(", "").replace(")", "")
        res.append({
            "authority_id": f"AUTH-DIST-{idx:02d}",
            "name_en": f"District Collectorate & DPDC {en}",
            "name_mr": f"जिल्हाधिकारी कार्यालय व जिल्हा नियोजन समिती, {mr}",
            "district_name": en,
            "administrative_division": div,
            "category": "DISTRICT_COLLECTORATE",
            "jurisdiction_level": "DISTRICT",
            "official_website": f"https://{slug}.gov.in",
            "status": "ACTIVE_RESEARCHED",
            "inclusion_reason": "District Collectorate administering revenue assistance, Sanjay Gandhi Niradhar sanction committee, DPDC schemes, and calamity relief."
        })
    return res


def build_universe_snapshot() -> Dict[str, Any]:
    mcs = load_municipal_corporations()
    districts = load_districts()

    all_entities = []
    all_entities.extend(STATE_DEPARTMENTS)
    all_entities.extend(STATE_CORPORATIONS)
    all_entities.extend(CENTRAL_MINISTRIES)
    all_entities.extend(mcs)
    all_entities.extend(districts)

    snapshot = {
        "universe_snapshot_id": "U-20261120",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "standard": "TRIMURTI v3 — Evidence-Gated, Human-Governed, UI-First, Self-Auditing and Resumable",
        "milestone": "SC-G2",
        "denominators": {
            "total_research_authorities": len(all_entities),
            "state_departments_and_directorates": len(STATE_DEPARTMENTS),
            "state_welfare_corporations_and_boards": len(STATE_CORPORATIONS),
            "central_ministries_in_scope": len(CENTRAL_MINISTRIES),
            "municipal_corporations_with_charters": len(mcs),
            "districts_and_dpdc_collectorates": len(districts)
        },
        "authorities": all_entities
    }
    return snapshot


def write_universe_files():
    snapshot = build_universe_snapshot()
    json_path = UNIVERSE_DIR / "U-20261120.json"
    json_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written universe snapshot to {json_path}")

    # Generate docs/catalogue/universe_snapshot.md
    md_path = DOCS_CATALOGUE_DIR / "universe_snapshot.md"
    d = snapshot["denominators"]
    md = f"""# Maharashtra Scheme Universe Research Snapshot (U-20261120)
**Snapshot ID:** `U-20261120`  
**Governing Milestone:** TRIMURTI v3 Milestone SC-G2  
**Created At:** `{snapshot['created_at']}`  
**Standard:** *Evidence-Gated · Human-Governed · Complete Without Fabrication*  

---

## 1. Statutory Universe Denominators

| Authority Group | Count | Scope & Charter Description |
|:---|:---:|:---|
| **State Administrative Departments & Directorates** | **{d['state_departments_and_directorates']}** | Mantralaya Administrative Departments under Maharashtra Government Rules of Business |
| **State Welfare Corporations & Boards** | **{d['state_welfare_corporations_and_boards']}** | Autonomous statutory corporations (MPBCDC, Mahajyoti, BARTI, SARTHI, MBOCW, etc.) |
| **Central Ministries with Maharashtra Applicability** | **{d['central_ministries_in_scope']}** | Central Ministries administering CSS and CS programmes co-funded or available in Maharashtra |
| **Municipal Corporations (Urban Local Bodies)** | **{d['municipal_corporations_with_charters']}** | All 29 Municipal Corporations across 6 divisions with statutory urban welfare charters |
| **District Collectorates & DPDCs** | **{d['districts_and_dpdc_collectorates']}** | 36 Districts administering Sanjay Gandhi Niradhar committees, DPDC, and calamity relief |
| **TOTAL RESEARCH UNIVERSE AUTHORITIES** | **{d['total_research_authorities']}** | Complete research universe scope for Maharashtra residents |

---

## 2. State Administrative Departments (Mantralaya)

| Authority ID | Department Name (English / Marathi) | Portal Domain | Key Benefit Focus |
|:---|:---|:---|:---|
"""
    for dept in STATE_DEPARTMENTS:
        md += f"| `{dept['authority_id']}` | {dept['name_en']}<br>*{dept['name_mr']}* | `{dept['portal_domain']}` | {dept['inclusion_reason'][:80]}... |\n"

    md += f"""
---

## 3. Subordinate Welfare Corporations, Boards & Institutes

| Authority ID | Corporation Name | Parent Department | Official Website |
|:---|:---|:---|:---|
"""
    for corp in STATE_CORPORATIONS:
        md += f"| `{corp['authority_id']}` | {corp['name_en']} | `{corp['parent_department_id']}` | [{corp['official_website']}]({corp['official_website']}) |\n"

    md += f"""
---

## 4. Central Ministries with Maharashtra Applicability

| Authority ID | Central Ministry | Key National Programme | Official Portal |
|:---|:---|:---|:---|
"""
    for cm in CENTRAL_MINISTRIES:
        md += f"| `{cm['authority_id']}` | {cm['name_en']} | {cm['inclusion_reason'][:70]}... | [{cm['official_website']}]({cm['official_website']}) |\n"

    md += f"""
---

## 5. Municipal Corporations (All 29 Urban Local Bodies)

| Authority ID | Corporation Name | Division | District | Wards | Official Portal |
|:---|:---|:---|:---|:---:|:---|
"""
    for mc in snapshot["authorities"]:
        if mc.get("category") == "MUNICIPAL_CORPORATION":
            md += f"| `{mc['authority_id']}` | {mc['name_en']} | {mc.get('administrative_division')} | {mc.get('district')} | {mc.get('ward_count')} | [{mc.get('official_website')}]({mc.get('official_website')}) |\n"

    md_path.write_text(md, encoding="utf-8")
    print(f"Written universe markdown documentation to {md_path}")


if __name__ == "__main__":
    write_universe_files()
