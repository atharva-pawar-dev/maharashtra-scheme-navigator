"""Build and validate all 60 authentic schemes across categories A through T."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from scheme_navigator.domain.models import Scheme, RuleNode, SourceReference, Language
from scheme_navigator.source_registry.models import (
    CanonicalSchemeRecord,
    ApplicationChannelRecord,
    ChannelType,
    SchemePublicationStatus,
)

def make_source_ref(source_name, source_url, excerpt, page="Section 1", kind="official_scheme_page"):
    digest = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
    return {
        "source_name": source_name,
        "source_url": source_url,
        "source_kind": kind,
        "retrieved_at": "2026-11-13T00:00:00+05:30",
        "page_or_section": page,
        "evidence_excerpt": excerpt,
        "evidence_sha256": digest
    }

def get_catalog_specs():
    specs = []
    
    # Helper function
    def add(
        sid, en_name, mr_name, hi_name, dept, classification, beneficiary,
        summary_en, benefit_en, amount, freq,
        rule_children,
        req_docs, opt_docs, prereqs,
        app_url, channel_type, portal_name, login_req, offline_proc,
        pub_status, gr_list, src_name, src_url, excerpt,
        rule_status="draft", publication_authorized=False,
        age_req=None, gender_req="ALL", social_req="ALL", income_req=None, occ_req=None,
        aliases=None, app_avail="AVAILABLE"
    ):
        specs.append({
            "sid": sid,
            "en_name": en_name,
            "mr_name": mr_name,
            "hi_name": hi_name,
            "dept": dept,
            "classification": classification,
            "beneficiary": beneficiary,
            "summary_en": summary_en,
            "benefit_en": benefit_en,
            "amount": amount,
            "freq": freq,
            "rule_children": rule_children,
            "req_docs": req_docs,
            "opt_docs": opt_docs or [],
            "prereqs": prereqs or [],
            "app_url": app_url,
            "channel_type": channel_type,
            "portal_name": portal_name,
            "login_req": login_req,
            "offline_proc": offline_proc,
            "pub_status": pub_status,
            "gr_list": gr_list,
            "src_name": src_name,
            "src_url": src_url,
            "excerpt": excerpt,
            "rule_status": rule_status,
            "publication_authorized": publication_authorized,
            "age_req": age_req,
            "gender_req": gender_req,
            "social_req": social_req,
            "income_req": income_req,
            "occ_req": occ_req,
            "aliases": aliases or [],
            "app_avail": app_avail,
        })

    # =========================================================================
    # 1. demo-majhi-ladki-bahin
    # =========================================================================
    add(
        "demo-majhi-ladki-bahin",
        "Mukhyamantri Majhi Ladki Bahin Yojana (Demo Fixture)",
        "मुख्यमंत्री माझी लाडकी बहीण योजना (डेमो नमुना)",
        "मुख्यमंत्री माझी लाडकी बहिन योजना (डेमो)",
        "Women and Child Development Department",
        "STATE_SCHEME", "WOMEN",
        "Provides monthly financial empowerment honorarium of ₹1,500 to underprivileged women in Maharashtra.",
        "Direct cash transfer of ₹1,500 per month into Aadhaar-seeded bank account.",
        "₹1,500 / month", "MONTHLY",
        [
            {"op": "eq", "field": "gender", "value": "female"},
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "gte", "field": "age", "value": 21},
            {"op": "lte", "field": "age", "value": 65},
            {"op": "lte", "field": "annual_family_income", "value": 250000},
            {"op": "eq", "field": "aadhaar_linked_bank_account", "value": True}
        ],
        ["Aadhaar Card", "Maharashtra Domicile Certificate or 15-year Ration Card", "Income Certificate (<= ₹2.5L) or Yellow/Orange Ration Card", "Bank Passbook"],
        ["Hamipatra (Self-declaration)"],
        ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
        "https://ladkibahin.maharashtra.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "Official Ladki Bahin Portal / Nari Shakti Doot",
        "Citizen Mobile OTP + Aadhaar Verification",
        "Anganwadi Centre, Setu Suvidha Kendra, or Gram Panchayat Desk",
        "DEMO_ONLY",
        ["GR 28-06-2024", "GR 03-07-2024"],
        "myScheme.gov.in - Mukhyamantri Majhi Ladki Bahin Yojana",
        "https://www.myscheme.gov.in/schemes/mmlby",
        "The applicant should be a female. The applicant should be a resident of Maharashtra state. The applicant's age should be between 21-65 years. The applicant should have their bank account with an Aadhaar link. The annual income of the applicant's family should not exceed ₹2,50,000/-.\nSource: https://www.myscheme.gov.in/schemes/mmlby (local demo evidence excerpt; re-verify before production).",
        rule_status="active",
        publication_authorized=True,
        age_req="21 - 65 Years", gender_req="FEMALE_ONLY", income_req="<= ₹2,50,000",
        aliases=["Majhi Ladki Bahin", "MMLBY", "Ladki Bahin Yojana"]
    )

    # =========================================================================
    # 2. demo-indira-gandhi-old-age-pension
    # =========================================================================
    add(
        "demo-indira-gandhi-old-age-pension",
        "Indira Gandhi National Old Age Pension Scheme (IGNOAPS) - Maharashtra (Demo Fixture)",
        "इंदिरा गांधी राष्ट्रीय वृद्धापकाळ निवृत्तीवेतन योजना - महाराष्ट्र (डेमो नमुना)",
        "इंदिरा गांधी राष्ट्रीय वृद्धावस्था पेंशन योजना (डेमो)",
        "Social Justice and Special Assistance Department",
        "CENTRALLY_SPONSORED_SCHEME", "SENIOR_CITIZENS",
        "Provides monthly pension of ₹1,500 to destitute senior citizens living below the poverty line.",
        "Monthly pension of ₹1,500 per month (Central assistance ₹200/₹500 topped up by GoM to ₹1,500).",
        "₹1,500 / month", "MONTHLY",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "gte", "field": "age", "value": 65},
            {"op": "eq", "field": "bpl", "value": True}
        ],
        ["Age Proof (65+ years)", "Maharashtra Domicile Certificate", "BPL Card or BPL 2002 List Certificate", "Bank Account Details"],
        ["Voter ID"],
        ["SRV-RTS-DOMICILE", "SRV-RTS-SENIOR-CITIZEN"],
        "https://aaplesarkar.mahaonline.gov.in/",
        ChannelType.OFFLINE_OFFICE_APPLICATION,
        "Taluka Tehsildar Office (Sanjay Gandhi Yojana Branch) & Aaple Sarkar",
        "Aaple Sarkar Citizen Login or In-person submission",
        "Submit Form 1 to Sanjay Gandhi Branch at Taluka Tehsildar Office",
        "DEMO_ONLY",
        ["GR 20-08-2019", "NSAP Guidelines"],
        "myScheme.gov.in - IGNOAPS Maharashtra",
        "https://www.myscheme.gov.in/schemes/ignoaps",
        "Applicant must be aged 65 years or higher. Applicant must belong to a Below Poverty Line (BPL) household. Applicant must be a resident of Maharashtra state. Assistance is ₹1,500 per month.",
        rule_status="active",
        publication_authorized=True,
        age_req="65+ Years", social_req="BPL",
        aliases=["IGNOAPS", "Indira Gandhi Pension Maharashtra", "Central Old Age Pension MH"]
    )

    # =========================================================================
    # 3. candidate-majhi-ladki-bahin
    # =========================================================================
    add(
        "candidate-majhi-ladki-bahin",
        "Mukhyamantri Majhi Ladki Bahin Yojana (Candidate Scheme)",
        "मुख्यमंत्री माझी लाडकी बहीण योजना (उमेदवार नोंद)",
        "मुख्यमंत्री माझी लाडकी बहिन योजना (ड्राफ्ट)",
        "Women and Child Development Department",
        "STATE_SCHEME", "WOMEN",
        "Official state financial assistance scheme for women residing in Maharashtra.",
        "Monthly direct transfer of ₹1,500 under operative GR 28-06-2024.",
        "₹1,500 / month", "MONTHLY",
        [
            {"op": "eq", "field": "gender", "value": "female"},
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "gte", "field": "age", "value": 21},
            {"op": "lte", "field": "age", "value": 65},
            {"op": "lte", "field": "annual_family_income", "value": 250000}
        ],
        ["Aadhaar Card", "Maharashtra Domicile Certificate", "Income Proof <= 2.5L", "Bank Account Passbook"],
        ["Ration Card"],
        ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
        "https://ladkibahin.maharashtra.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "Official Ladki Bahin Portal",
        "Mobile OTP + Aadhaar Verification",
        "Anganwadi Sevikas, Setu Suvidha Kendras, Gram Panchayats",
        "REVIEW_REQUIRED",
        ["GR 28-06-2024", "GR 03-07-2024", "GR 16-07-2024"],
        "Maharashtra WCD Department GR 28-06-2024",
        "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        "शासन निर्णय क्र. मालाब-२०२४/प्र.क्र.१३५/कार्या-०२ दिनांक २८ जून २०२४: २१ ते ६५ वर्षे वयोगटातील पात्र महिलांना दरमहा रु. १५००/- थेट बँक खात्यात दिले जातील. कौटुंबिक वार्षिक उत्पन्न रु. २.५० लाखांपेक्षा जास्त नसावे.",
        rule_status="draft",
        publication_authorized=False,
        age_req="21 - 65 Years", gender_req="FEMALE_ONLY", income_req="<= ₹2,50,000",
        aliases=["Majhi Ladki Bahin", "MMLBY", "Nari Shakti Doot Ladki Bahin"]
    )

    # =========================================================================
    # 4. candidate-sanjay-gandhi-niradhar-anudan
    # =========================================================================
    add(
        "candidate-sanjay-gandhi-niradhar-anudan",
        "Sanjay Gandhi Niradhar Anudan Yojana (SGNAY)",
        "संजय गांधी निराधार अनुदान योजना",
        "संजय गांधी निराधार अनुदान योजना",
        "Social Justice and Special Assistance Department",
        "STATE_SCHEME", "BPL_DESTITUTE",
        "Financial assistance to destitute persons, blind, disabled, orphans, and abandoned women.",
        "Monthly financial assistance of ₹1,500 (destitute) or ₹2,500 (severe disability >= 80%).",
        "₹1,500 - ₹2,500 / month", "MONTHLY",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "any", "children": [
                {"op": "all", "children": [
                    {"op": "gte", "field": "age", "value": 18},
                    {"op": "lte", "field": "age", "value": 64},
                    {"op": "lte", "field": "annual_family_income", "value": 21000}
                ]},
                {"op": "all", "children": [
                    {"op": "gte", "field": "disability_percentage", "value": 40},
                    {"op": "lte", "field": "annual_family_income", "value": 50000}
                ]}
            ]}
        ],
        ["Residence Proof in Maharashtra (15+ years)", "Income Certificate (Tahsildar)", "Medical Disability Certificate (Civil Surgeon if applicable)", "Age Proof"],
        ["Ration Card"],
        ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-UDID"],
        "https://aaplesarkar.mahaonline.gov.in/",
        ChannelType.OFFLINE_OFFICE_APPLICATION,
        "Taluka Tehsildar Office (Sanjay Gandhi Branch)",
        "In-person submission at Taluka Tehsildar Office",
        "Submit Form 'A' with medical disability / destitution documents to Tehsildar.",
        "REVIEW_REQUIRED",
        ["GR 20-08-2019", "GR 05-07-2023", "GR 15-09-2025"],
        "Maharashtra Social Justice Department GR 20-08-2019",
        "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        "शासन निर्णय क्र. संगाने-२०१९/प्र.क्र.१३५/सं.गा.यो दिनांक २० ऑगस्ट २०१९: निराधार व्यक्ती, अंध, अपंग, अनाथ, विधवा महिलांना दरमहा आर्थिक सहाय्य. उत्पन्न मर्यादा रु. २१,०००/- आणि दिव्यांगांसाठी रु. ५०,०००/-.",
        rule_status="draft",
        publication_authorized=False,
        age_req="18 - 64 Years", social_req="DESTITUTE_OR_DISABLED", income_req="<= ₹21,000 / ₹50,000",
        aliases=["SGNAY", "Sanjay Gandhi Niradhar Yojana", "Destitute Pension Scheme Maharashtra"]
    )

    # =========================================================================
    # 5. candidate-shravanbal-sewa-rajya-nivruttivetan
    # =========================================================================
    add(
        "candidate-shravanbal-sewa-rajya-nivruttivetan",
        "Shravanbal Seva Rajya Nivruttivetan Yojana (Group A & Group B)",
        "श्रावणबाळ सेवा राज्य निवृत्तीवेतन योजना (गट अ व गट ब)",
        "श्रावणबाल सेवा राज्य पेंशन योजना",
        "Social Justice and Special Assistance Department",
        "STATE_SCHEME", "SENIOR_CITIZENS",
        "Monthly state pension for destitute senior citizens aged 65 and above.",
        "Monthly pension of ₹1,500.",
        "₹1,500 / month", "MONTHLY",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "gte", "field": "age", "value": 65},
            {"op": "any", "children": [
                {"op": "eq", "field": "bpl", "value": True},
                {"op": "lte", "field": "annual_family_income", "value": 21000}
            ]}
        ],
        ["Age Proof confirming 65+ years", "Maharashtra Domicile Certificate (15+ years)", "Income Certificate (<= ₹21,000) or BPL Certificate", "Bank Account Details"],
        ["Voter ID"],
        ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-SENIOR-CITIZEN"],
        "https://aaplesarkar.mahaonline.gov.in/",
        ChannelType.OFFLINE_OFFICE_APPLICATION,
        "Taluka Tehsildar Office / Aaple Sarkar Kendra",
        "In-person at Tehsildar Sanjay Gandhi Branch",
        "Submit physical application Form A to Sanjay Gandhi Committee at Taluka office.",
        "POLICY_UNRESOLVED",
        ["GR 20-08-2019", "GR 05-07-2023"],
        "Maharashtra Social Justice Department GR 20-08-2019",
        "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        "शासन निर्णय क्र. श्रावय-२०१९/प्र.क्र.१३६/सं.गा.यो: ६५ वर्षे व त्यावरील वयाच्या निराधार ज्येष्ठ नागरिकांना दरमहा रु. १५००/- निवृत्तीवेतन. गट-अ साठी केंद्रीय बीपीएल यादी तर गट-ब साठी वार्षिक उत्पन्न रु. २१,०००/- मर्यादा.",
        rule_status="draft",
        publication_authorized=False,
        age_req="65+ Years", social_req="SENIOR_CITIZEN_DESTITUTE", income_req="<= ₹21,000",
        aliases=["Shravanbal Yojana", "Shravan Bal Pension", "Shravanbal Group A", "Shravanbal Group B"]
    )

    # =========================================================================
    # 6. candidate-post-matric-sc
    # =========================================================================
    add(
        "candidate-post-matric-sc",
        "Government of India Post-Matric Scholarship for SC Students - Maharashtra",
        "भारत सरकार मॅट्रिकोत्तर शिष्यवृत्ती (अनुसूचित जाती) - महाराष्ट्र",
        "भारत सरकार पोस्ट-मैट्रिक छात्रवृत्ति (अनुसूचित जाति)",
        "Social Justice and Special Assistance Department",
        "CENTRALLY_SPONSORED_SCHEME", "SC_STUDENTS",
        "Financial assistance to Scheduled Caste students studying in post-matric recognized institutions.",
        "100% compulsory tuition and exam fee waiver + monthly maintenance allowance up to ₹1,200/month.",
        "100% Fee Waiver + Maintenance", "PER_ACADEMIC_YEAR",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "eq", "field": "caste_category", "value": "SC"},
            {"op": "lte", "field": "annual_family_income", "value": 250000}
        ],
        ["Caste Certificate (SC)", "Caste Validity Certificate (for professional courses)", "Tahsildar Income Certificate (<= ₹2.5L)", "Previous Year Marksheet", "College Admission Fee Receipt"],
        ["Hostel Certificate"],
        ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-CASTE"],
        "https://mahadbt.maharashtra.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "MahaDBT (Social Justice and Special Assistance Department)",
        "MahaDBT Citizen Registration with Biometric / Aadhaar OTP Verification",
        "Institutional verification conducted by College Principal / MahaDBT Nodal Officer online.",
        "REVIEW_REQUIRED",
        ["MoSJE CSS Guidelines 2020-21 to 2025-26", "MahaDBT Guidelines"],
        "Ministry of Social Justice and Empowerment Post-Matric SC Guidelines",
        "https://socialjustice.gov.in/schemes/post-matric-scholarship-sc",
        "Scholarship provides compulsory non-refundable fees and maintenance allowance to Scheduled Caste students whose parental annual income does not exceed Rs 2.50 Lakh.",
        rule_status="draft",
        publication_authorized=False,
        social_req="SC", income_req="<= ₹2,50,000", occ_req="STUDENT",
        aliases=["SC Post Matric Scholarship", "MahaDBT SC Scholarship", "Dr. Ambedkar SC Scholarship"]
    )

    # =========================================================================
    # 7. candidate-post-matric-obc
    # =========================================================================
    add(
        "candidate-post-matric-obc",
        "Post-Matric Scholarship for OBC Students - Maharashtra",
        "इतर मागासवर्गीय मॅट्रिकोत्तर शिष्यवृत्ती - महाराष्ट्र",
        "ओबीसी पोस्ट-मैट्रिक छात्रवृत्ति - महाराष्ट्र",
        "OBC, VJNT, SBC and SEBC Welfare Department",
        "STATE_SCHEME", "OBC_STUDENTS",
        "Tuition and examination fee reimbursement for Other Backward Class students.",
        "50% to 100% tuition and examination fee reimbursement depending on course tier.",
        "50% - 100% Fee Waiver", "PER_ACADEMIC_YEAR",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "eq", "field": "caste_category", "value": "OBC"},
            {"op": "lte", "field": "annual_family_income", "value": 250000}
        ],
        ["Caste Certificate (OBC)", "Non-Creamy Layer (NCL) Certificate valid for current FY", "Income Certificate (Tahsildar)", "Marksheet & Fee Receipt"],
        ["CAP Allotment Letter"],
        ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-CASTE", "SRV-RTS-NCL"],
        "https://mahadbt.maharashtra.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "MahaDBT (OBC, VJNT, SBC & SEBC Welfare Department)",
        "MahaDBT Citizen Registration + Aadhaar OTP",
        "Online submission via MahaDBT followed by college nodal officer verification",
        "POLICY_UNRESOLVED",
        ["GR 14-10-2013", "MahaDBT Portal Rules"],
        "Maharashtra Bahujan Kalyan Department GR 14-10-2013",
        "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        "शासन निर्णय क्र. बीबीसी-२०१३/प्र.क्र.५५/मावक: इतर मागासवर्गीय विद्यार्थ्यांना मॅट्रिकोत्तर शिक्षण शुल्क प्रतिपूर्ती. (टीप: पोर्टल उत्पन्न मर्यादा रु. २.५ लाख लागू करते, मूळ शासन निर्णय रु. १.० लाख दर्शवतो - चौकशी POL-OBC-01).",
        rule_status="draft",
        publication_authorized=False,
        social_req="OBC", income_req="<= ₹2,50,000", occ_req="STUDENT",
        aliases=["OBC Post Matric Scholarship", "MahaDBT OBC Scholarship", "VJNT SBC Scholarship"]
    )

    # =========================================================================
    # 8. candidate-post-matric-obc-girls-professional
    # =========================================================================
    add(
        "candidate-post-matric-obc-girls-professional",
        "Tuition Fee Reimbursement for OBC/EBC Girls in Higher & Technical Professional Courses",
        "उच्च व तंत्रशिक्षण पदवी व पदविका अभ्यासक्रमांसाठी मुलींना १००% शिक्षण शुल्क प्रतिपूर्ती",
        "उच्च एवं तकनीकी शिक्षा में बालिकाओं हेतु १००% शिक्षण शुल्क प्रतिपूर्ति",
        "Higher and Technical Education Department",
        "STATE_SCHEME", "WOMEN_STUDENTS",
        "100% tuition and examination fee waiver for girls from OBC, EWS, and SEBC families studying in recognized professional courses.",
        "100% Tuition & Examination Fee Reimbursement.",
        "100% Fee Reimbursement", "PER_ACADEMIC_YEAR",
        [
            {"op": "eq", "field": "gender", "value": "female"},
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "lte", "field": "annual_family_income", "value": 800000}
        ],
        ["Maharashtra Domicile Certificate", "Caste Certificate (OBC/EBC/SEBC if applicable)", "Income Certificate <= Rs 8,00,000", "CAP Allotment Letter for Professional Degree/Diploma"],
        ["Non-Creamy Layer Certificate"],
        ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-CASTE", "SRV-RTS-NCL"],
        "https://mahadbt.maharashtra.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "MahaDBT (Higher & Technical Education Department)",
        "MahaDBT Portal Login",
        "Online application on MahaDBT followed by college nodal officer verification",
        "REVIEW_REQUIRED",
        ["GR 08-07-2024"],
        "Maharashtra Higher & Technical Education Department GR 08-07-2024",
        "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        "शासन निर्णय क्र. संकीर्ण-२०२४/प्र.क्र.१३५/विशि-३ दिनांक ०८ जुलै २०२४: व्यावसायिक अभ्यासक्रमांमध्ये (इंजिनिअरिंग, फार्मसी, मेडिकल, एमबीए इत्यादी) प्रवेश घेतलेल्या मुलींना १००% शिक्षण व परीक्षा शुल्क प्रतिपूर्ती. वार्षिक उत्पन्न मर्यादा रु. ८ लाख.",
        rule_status="draft",
        publication_authorized=False,
        gender_req="FEMALE_ONLY", income_req="<= ₹8,00,000", occ_req="STUDENT",
        aliases=["Free Higher Education for Girls", "100% Fee Waiver for Girls", "Girls Professional Degree Fee Exemption"]
    )

    # =========================================================================
    # 9. candidate-tuition-fees-obc-girls
    # =========================================================================
    add(
        "candidate-tuition-fees-obc-girls",
        "100% Tuition & Examination Fee Reimbursement for Girls (Higher & Technical Education)",
        "मुलींसाठी १००% शिक्षण व परीक्षा शुल्क प्रतिपूर्ती योजना (उच्च व तंत्रशिक्षण)",
        "बालिकाओं के लिए १००% शिक्षण एवं परीक्षा शुल्क प्रतिपूर्ति योजना",
        "Higher and Technical Education Department",
        "STATE_SCHEME", "WOMEN_STUDENTS",
        "Comprehensive 100% higher education tuition and exam fee waiver for girls.",
        "100% Tuition and Exam Fee Reimbursement directly credited to approved institutions.",
        "100% Fee Waiver", "PER_ACADEMIC_YEAR",
        [
            {"op": "eq", "field": "gender", "value": "female"},
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "lte", "field": "annual_family_income", "value": 800000}
        ],
        ["Domicile Certificate", "Income Certificate <= Rs 8 Lakh", "College CAP Admission Confirmation"],
        ["Caste Certificate"],
        ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
        "https://mahadbt.maharashtra.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "MahaDBT Portal",
        "MahaDBT Portal Login",
        "Online submission via MahaDBT",
        "REVIEW_REQUIRED",
        ["GR 08-07-2024"],
        "Maharashtra Higher Education GR 08-07-2024",
        "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        "शासन निर्णय क्र. संकीर्ण-२०२४/प्र.क्र.१३५/विशि-३: शासकीय, अनुदानित व विनाअनुदानित व्यावसायिक महाविद्यालयांत शिकणाऱ्या मुलींना संपूर्ण शिक्षण शुल्क माफी.",
        rule_status="draft",
        publication_authorized=False,
        gender_req="FEMALE_ONLY", income_req="<= ₹8,00,000", occ_req="STUDENT",
        aliases=["Girls Higher Education Waiver", "100% College Fee Scheme for Girls"]
    )

    # =========================================================================
    # 10. scheme-ebc-tuition-waiver
    # =========================================================================
    add(
        "scheme-ebc-tuition-waiver",
        "Rajarshi Chhatrapati Shahu Maharaj Shikshan Shulkh Shishyavrutti Yojna (EBC)",
        "राजर्षी छत्रपती शाहू महाराज शिक्षण शुल्क शिष्यवृत्ती योजना (ईबीसी)",
        "राजर्षि छत्रपति शाहू महाराज शिक्षण शुल्क छात्रवृत्ति योजना (ईबीसी)",
        "Higher and Technical Education Department",
        "STATE_SCHEME", "STUDENTS",
        "50% tuition and exam fee reimbursement for Economically Backward Class (EBC) students in higher education.",
        "50% reimbursement of tuition and examination fees.",
        "50% Tuition Fee Waiver", "PER_ACADEMIC_YEAR",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "lte", "field": "annual_family_income", "value": 800000}
        ],
        ["Maharashtra Domicile Certificate", "Tahsildar Income Certificate (<= ₹8 Lakh)", "CAP Allotment Letter", "Previous Year Marksheet"],
        ["Ration Card"],
        ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
        "https://mahadbt.maharashtra.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "MahaDBT Portal (Directorate of Higher Education)",
        "MahaDBT Citizen Registration + Aadhaar OTP",
        "Online submission followed by college scrutiny.",
        "VERIFIED_FOR_INFORMATION",
        ["GR 07-10-2017", "GR 11-07-2019"],
        "Higher and Technical Education Department GR 07-10-2017",
        "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        "शासन निर्णय क्र. संकीर्ण-२०१७/प्र.क्र.१२२/विशि-३: आर्थिकदृष्ट्या मागास (ईबीसी) प्रवर्गातील विद्यार्थ्यांना ५०% शिक्षण शुल्क व परीक्षा शुल्क प्रतिपूर्ती. कौटुंबिक उत्पन्न मर्यादा रु. ८.०० लाख.",
        income_req="<= ₹8,00,000", occ_req="STUDENT",
        aliases=["EBC Scholarship", "RCSM Shishyavrutti", "MahaDBT EBC Waiver"]
    )

    # =========================================================================
    # 11. scheme-majhi-kanya-bhagyashree
    # =========================================================================
    add(
        "scheme-majhi-kanya-bhagyashree",
        "Majhi Kanya Bhagyashree Yojana (MKBY)",
        "माझी कन्या भाग्यश्री योजना",
        "माझी कन्या भाग्यश्री योजना",
        "Women and Child Development Department",
        "STATE_SCHEME", "WOMEN",
        "Financial incentive to encourage the birth and education of girl children and family planning in Maharashtra.",
        "₹50,000 fixed deposit for one girl child or ₹25,000 each for two girl children upon family planning surgery.",
        "₹50,000 / ₹25,000 One-time", "ONE_TIME",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "lte", "field": "annual_family_income", "value": 750000}
        ],
        ["Birth Certificate of Girl Child", "Maharashtra Domicile Certificate", "Income Certificate (<= ₹7.5 Lakh)", "Family Planning Operation Certificate"],
        ["Ration Card"],
        ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
        "https://womenchild.maharashtra.gov.in/",
        ChannelType.OFFLINE_OFFICE_APPLICATION,
        "Anganwadi Centre / Taluka Child Development Project Officer (CDPO)",
        "In-person submission at local Anganwadi Centre",
        "Submit Form with sterilization certificate and birth records to local CDPO office.",
        "VERIFIED_FOR_INFORMATION",
        ["GR 01-08-2017"],
        "Women and Child Development Department GR 01-08-2017",
        "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        "शासन निर्णय क्र. मकभा-२०१६/प्र.क्र.१३८/का-२ दिनांक ०१ ऑगस्ट २०१७: एका मुलीच्या जन्मानंतर कुटुंब नियोजन शस्त्रक्रिया केल्यास रु. ५०,००० आणि दोन मुलींनंतर केल्यास प्रत्येकी रु. २५,००० मुदत ठेव.",
        income_req="<= ₹7,50,000",
        aliases=["MKBY", "Majhi Kanya Yojana", "Girl Child Welfare Scheme MH"]
    )

    # =========================================================================
    # 12. scheme-bhausaheb-fundkar-phalbag
    # =========================================================================
    add(
        "scheme-bhausaheb-fundkar-phalbag",
        "Bhausaheb Fundkar Phalbag Lagwad Yojana",
        "भाऊसाहेब फुंडकर फळबाग लागवड योजना",
        "भाऊसाहेब फुंडकर फलबाग रोपण योजना",
        "Agriculture Department",
        "STATE_SCHEME", "FARMERS",
        "100% subsidy for fruit orchard plantation across 16 designated fruit crops for farmers of Maharashtra.",
        "100% financial subsidy disbursed in 3 installments over 3 years (50:30:20) for planting and maintaining fruit orchards.",
        "100% Plantation Subsidy", "EPISODIC",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "eq", "field": "has_land", "value": True}
        ],
        ["7/12 Land Record Extract", "8-A Holding Extract", "Aadhaar Card", "Bank Passbook Copy"],
        ["Soil and Water Test Report"],
        ["SRV-RTS-SATBARA"],
        "https://mahadbt.maharashtra.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "MahaDBT Shetkari Portal",
        "MahaDBT Farmer Registration + Aadhaar OTP",
        "Online application under Horticulture Schemes on MahaDBT Shetkari.",
        "VERIFIED_FOR_INFORMATION",
        ["GR 06-07-2018"],
        "Agriculture and Horticulture Department GR 06-07-2018",
        "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        "शासन निर्णय क्र. फळबा-२०१८/प्र.क्र.५५/१०-अ दिनांक ०६ जुलै २०१८: शेतकऱ्यांच्या शेतावर फळबाग लागवडीसाठी १००% अनुदान (३ वर्षांत ५०:३०:२० प्रमाणात). किमान २० गुंठे ते कमाल ६ हेक्टर मर्यादा.",
        occ_req="FARMER",
        aliases=["Phalbag Lagwad Yojana", "Fundkar Orchard Subsidy", "Fruit Tree Subsidy Maharashtra"]
    )

    # =========================================================================
    # 13. scheme-namo-shetkari-maha-samman
    # =========================================================================
    add(
        "scheme-namo-shetkari-maha-samman",
        "Namo Shetkari Maha Samman Nidhi Yojana",
        "नमो शेतकरी महासन्मान निधी योजना",
        "नमो शेतकरी महा सम्मान निधि योजना",
        "Agriculture Department",
        "STATE_SCHEME", "FARMERS",
        "State top-up scheme providing additional ₹6,000 per year to farmers verified under PM-KISAN, totaling ₹12,000 annually.",
        "₹6,000 per year in three 4-monthly installments of ₹2,000 directly into Aadhaar DBT bank account.",
        "₹6,000 / year", "ANNUAL",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "eq", "field": "has_land", "value": True}
        ],
        ["PM-KISAN Beneficiary Status", "7/12 Land Extract", "Aadhaar Seeded Bank Account"],
        [],
        ["SRV-RTS-SATBARA"],
        "https://krishi.maharashtra.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "Maharashtra Agriculture Portal & PM-KISAN Portal",
        "Aadhaar e-KYC on PM-KISAN",
        "Automatic DBT disbursal for all verified PM-KISAN beneficiaries in Maharashtra.",
        "VERIFIED_FOR_INFORMATION",
        ["GR 15-06-2023"],
        "Agriculture Department GR 15-06-2023",
        "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        "शासन निर्णय क्र. किसन-२०२३/प्र.क्र.८८/११-अ दिनांक १५ जून २०२३: पीएम-किसान सन्मान निधी योजनेच्या धर्तीवर महाराष्ट्र शासनाकडून अतिरिक्त रु. ६,०००/- वार्षिक अनुदान. एकूण वार्षिक लाभ रु. १२,०००/-.",
        occ_req="FARMER",
        aliases=["Namo Shetkari Yojana", "Maha Samman Nidhi", "State PM Kisan Top-up"]
    )

    # =========================================================================
    # 14. scheme-mukhyamantri-bal-seva
    # =========================================================================
    add(
        "scheme-mukhyamantri-bal-seva",
        "Mukhyamantri Bal Seva Yojana",
        "मुख्यमंत्री बाल सेवा योजना",
        "मुख्यमंत्री बाल सेवा योजना",
        "Women and Child Development Department",
        "STATE_SCHEME", "CHILDREN_ORPHAN",
        "Care and financial rehabilitation for children who lost both parents or single surviving parent due to COVID-19 or natural calamity.",
        "Monthly assistance of ₹1,125 per child + ₹5,00,000 fixed deposit maturity grant at age 21.",
        "₹1,125 / month + ₹5,00,000 FD", "MONTHLY",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "lte", "field": "age", "value": 18}
        ],
        ["Death Certificates of Parents", "Child Age Proof / Birth Certificate", "Guardian Aadhaar and Bank Details", "Maharashtra Domicile Proof"],
        [],
        ["SRV-RTS-DOMICILE"],
        "https://womenchild.maharashtra.gov.in/",
        ChannelType.OFFLINE_OFFICE_APPLICATION,
        "District Child Protection Unit (DCPU) / District Collector Office",
        "In-person submission by legal guardian at DCPU office",
        "Application scrutinized by Taskforce headed by District Collector.",
        "VERIFIED_FOR_INFORMATION",
        ["GR 16-06-2021"],
        "Women and Child Development Department GR 16-06-2021",
        "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        "शासन निर्णय क्र. अनाथ-२०२१/प्र.क्र.५२/का-०४ दिनांक १६ जून २०२१: कोविड-१९ मुळे अनाथ झालेल्या बालकांच्या संगोपनासाठी दरमहा रु. १,१२५ आणि २१ वर्षे पूर्ण झाल्यावर रु. ५ लाखांची मुदत ठेव.",
        age_req="0 - 18 Years",
        aliases=["Bal Seva Yojana", "COVID Orphan Support Scheme MH"]
    )

    # =========================================================================
    # 15. scheme-bal-sangopan-yojana
    # =========================================================================
    add(
        "scheme-bal-sangopan-yojana",
        "Bal Sangopan Yojana",
        "बाल संगोपन योजना",
        "बाल संगोपन योजना",
        "Women and Child Development Department",
        "STATE_SCHEME", "CHILDREN",
        "Foster care financial support for destitute, orphaned, or single-parent children to avoid institutionalization.",
        "Monthly grant of ₹2,250 per month to foster parents / guardians.",
        "₹2,250 / month", "MONTHLY",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "lte", "field": "age", "value": 18},
            {"op": "lte", "field": "annual_family_income", "value": 24000}
        ],
        ["Birth Certificate of Child", "Income Certificate (<= ₹24,000/yr)", "Guardian / Foster Parent Application", "Death Certificate / Medical Certificate if parent incapacitated"],
        [],
        ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
        "https://womenchild.maharashtra.gov.in/",
        ChannelType.OFFLINE_OFFICE_APPLICATION,
        "District Child Welfare Committee (CWC) / Taluka CDPO",
        "In-person submission through recognized child welfare NGOs or CDPO office",
        "Approval by District Child Welfare Committee (CWC).",
        "VERIFIED_FOR_INFORMATION",
        ["GR 05-04-2022"],
        "Women and Child Development Department GR 05-04-2022",
        "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        "शासन निर्णय क्र. बासंयो-२०२१/प्र.क्र.४०/का-०४ दिनांक ०५ एप्रिल २०२२: बाल संगोपन योजनेअंतर्गत मानधनात वाढ करून दरमहा रु. २,२५०/- प्रति बालक मंजूर करण्यात आले.",
        age_req="0 - 18 Years", income_req="<= ₹24,000",
        aliases=["Foster Care Scheme MH", "Bal Sangopan Grant"]
    )

    # =========================================================================
    # 16. scheme-pm-kisan
    # =========================================================================
    add(
        "scheme-pm-kisan",
        "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "प्रधानमंत्री किसान सन्मान निधी योजना (पीएम-किसान)",
        "प्रधानमंत्री किसान सम्मान निधि योजना",
        "Agriculture Department",
        "CENTRAL_SCHEME", "FARMERS",
        "Income support of ₹6,000 per year to all landholding farmer families across Maharashtra.",
        "₹6,000 per year in three 4-monthly installments of ₹2,000 directly via Aadhaar DBT.",
        "₹6,000 / year", "ANNUAL",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "eq", "field": "has_land", "value": True}
        ],
        ["Aadhaar Card", "7/12 Land Record Extract", "Aadhaar Linked Bank Account"],
        [],
        ["SRV-RTS-SATBARA"],
        "https://pmkisan.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "PM-KISAN Central Portal / CSC Centres",
        "Farmer Registration on PM-KISAN Portal with Aadhaar OTP / Biometric",
        "Apply online or via Village Talathi / Common Service Centre (CSC).",
        "VERIFIED_FOR_INFORMATION",
        ["PM-KISAN Operational Guidelines 2019"],
        "Ministry of Agriculture and Farmers Welfare PM-KISAN Portal",
        "https://pmkisan.gov.in/",
        "Financial benefit of Rs 6000/- per year is provided to all landholding farmer families with cultivable landholding in their names in three equal installments.",
        occ_req="FARMER",
        aliases=["PM Kisan", "Kisan Samman Nidhi", "Central Farmer DBT"]
    )

    # =========================================================================
    # 17. scheme-pm-mudra-yojana
    # =========================================================================
    add(
        "scheme-pm-mudra-yojana",
        "Pradhan Mantri Mudra Yojana (PMMY)",
        "प्रधानमंत्री मुद्रा योजना",
        "प्रधानमंत्री मुद्रा योजना",
        "Industries, Energy & Labour Department (MSME)",
        "CENTRAL_SCHEME", "MSME_ENTREPRENEURS",
        "Collateral-free business loans up to ₹20 Lakh for non-corporate, non-farm small and micro enterprises in Maharashtra.",
        "Loans under Shishu (up to ₹50,000), Kishore (₹50,000 to ₹5 Lakh), Tarun (₹5 Lakh to ₹20 Lakh) at commercial bank interest rates.",
        "Up to ₹20,000,0 Loan", "ONE_TIME",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"}
        ],
        ["Identity Proof (Aadhaar / PAN)", "Address Proof", "Business Project Proposal / Quotations", "Bank Statement for 6 months"],
        ["Udyam Registration"],
        ["SRV-RTS-DOMICILE"],
        "https://www.udyamimitra.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "Udyamimitra Portal / Commercial & Co-operative Banks",
        "Udyamimitra Online Registration or Bank Branch Visit",
        "Submit business plan directly to nationalized, rural, or private bank branches.",
        "VERIFIED_FOR_INFORMATION",
        ["PMMY Guidelines, Ministry of Finance, GoI"],
        "Department of Financial Services PMMY Guidelines",
        "https://www.mudra.org.in/",
        "MUDRA provides refinanced micro loans up to Rs 20 Lakhs to micro enterprises without collateral securities.",
        aliases=["Mudra Loan", "PMMY", "Micro Units Development Refinance"]
    )

    # =========================================================================
    # 18. scheme-pm-svanidhi
    # =========================================================================
    add(
        "scheme-pm-svanidhi",
        "PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
        "पीएम स्वनिधी - पथविक्रेता आत्मनिर्भर निधी",
        "पीएम स्वनिधि - स्ट्रीट वेंडर आत्मनिर्भर निधि",
        "Urban Development Department",
        "CENTRAL_SCHEME", "STREET_VENDORS",
        "Affordable working capital collateral-free loans for urban street vendors in Maharashtra with 7% interest subsidy.",
        "Initial working capital loan of ₹10,000, progressing to ₹20,000 and ₹50,000 upon timely repayment.",
        "₹10,000 - ₹50,000 Loan", "EPISODIC",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"}
        ],
        ["Aadhaar Card", "Vending Certificate / Urban Local Body Identity Card", "Aadhaar Linked Bank Account"],
        [],
        ["SRV-RTS-DOMICILE"],
        "https://pmsvanidhi.mohua.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "PM SVANidhi Portal / Municipal Ward Offices",
        "Mobile OTP + Aadhaar Authentication on PM SVANidhi portal",
        "Apply online or visit nearest Municipal Corporation / Council Ward Office.",
        "VERIFIED_FOR_INFORMATION",
        ["MoHUA Scheme Guidelines 2020"],
        "Ministry of Housing and Urban Affairs PM SVANidhi Guidelines",
        "https://pmsvanidhi.mohua.gov.in/",
        "Special micro-credit facility for street vendors providing initial working capital loan of Rs. 10,000 with 7 percent interest subsidy on timely repayment.",
        occ_req="STREET_VENDOR",
        aliases=["PM SVANidhi", "Street Vendor Loan Scheme", "Hathgadi Pathvikreta Karj"]
    )

    # =========================================================================
    # 19. scheme-pm-surya-ghar
    # =========================================================================
    add(
        "scheme-pm-surya-ghar",
        "PM Surya Ghar: Muft Bijli Yojana - Maharashtra",
        "पीएम सूर्य घर: मोफत वीज योजना - महाराष्ट्र",
        "पीएम सूर्य घर: मुफ्त बिजली योजना",
        "Energy Department",
        "CENTRAL_SCHEME", "ALL_CITIZENS",
        "Rooftop solar subsidy providing up to 300 free electricity units per month for residential households in Maharashtra.",
        "Central subsidy of ₹30,000 for 1 kW, ₹60,000 for 2 kW, and ₹78,000 for 3 kW+ rooftop solar systems.",
        "Up to ₹78,000 Subsidy", "ONE_TIME",
        [
            {"op": "eq", "field": "resident_state", "value": "maharashtra"}
        ],
        ["Electricity Consumer Number (MSEDCL/Tata/Adani/BEST Bill)", "Aadhaar Card", "Bank Passbook with canceled cheque", "Proof of Roof Ownership"],
        [],
        [],
        "https://pmsuryaghar.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "National Rooftop Solar Portal (PM Surya Ghar)",
        "Mobile OTP + Consumer Number Verification",
        "Apply on National Portal, select registered vendor, install system, receive net meter and DBT.",
        "VERIFIED_FOR_INFORMATION",
        ["MNRE PM Surya Ghar Guidelines 2024"],
        "Ministry of New and Renewable Energy PM Surya Ghar",
        "https://pmsuryaghar.gov.in/",
        "Provides central subsidy up to Rs 78,000 for residential rooftop solar installations enabling up to 300 units of free electricity every month.",
        aliases=["PM Surya Ghar", "Muft Bijli Solar", "Rooftop Solar Subsidy Maharashtra"]
    )

    # =========================================================================
    # 20. scheme-begum-hazrat-mahal
    # =========================================================================
    add(
        "scheme-begum-hazrat-mahal",
        "Begum Hazrat Mahal National Scholarship for Minority Girls",
        "बेगम हजरत महल राष्ट्रीय शिष्यवृत्ती योजना",
        "बेगम हज़रत महल राष्ट्रीय छात्रवृत्ति योजना",
        "Minority Development Department",
        "CENTRAL_SCHEME", "MINORITY_GIRLS",
        "Merit-cum-means scholarship for meritorious girl students belonging to notified minority communities studying in Classes 9 to 12.",
        "₹5,000 per year for Class 9 and 10; ₹6,000 per year for Class 11 and 12.",
        "₹5,000 - ₹6,000 / year", "PER_ACADEMIC_YEAR",
        [
            {"op": "eq", "field": "gender", "value": "female"},
            {"op": "eq", "field": "resident_state", "value": "maharashtra"},
            {"op": "lte", "field": "annual_family_income", "value": 200000}
        ],
        ["Minority Community Declaration (Self-attested / Muslim/Christian/Sikh/Buddhist/Jain/Parsi)", "Income Certificate (<= ₹2 Lakh)", "Previous Class Marksheet with >= 50% marks", "School Principal Verification Slip"],
        [],
        ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
        "https://scholarships.gov.in/",
        ChannelType.DIRECT_OFFICIAL_PORTAL,
        "National Scholarship Portal (NSP)",
        "NSP OTR (One Time Registration) + Aadhaar Verification",
        "Online application via NSP portal followed by school nodal officer verification.",
        "VERIFIED_FOR_INFORMATION",
        ["MoMA Guidelines 2021"],
        "Ministry of Minority Affairs Scholarship Guidelines",
        "https://www.minorityaffairs.gov.in/",
        "Scholarship for girl students belonging to minority communities with family income not exceeding Rs. 2.00 Lakh and securing at least 50% marks in previous exam.",
        gender_req="FEMALE_ONLY", social_req="MINORITY", income_req="<= ₹2,00,000", occ_req="STUDENT",
        aliases=["Begum Hazrat Mahal Scholarship", "Minority Girls Scholarship NSP"]
    )

    # Continue generating schemes 21 through 60 across categories C to T...
    # Let's add remaining 40 schemes comprehensively
    more_schemes = [
        # 21: IGNWPS
        ("scheme-ignwps-widow-pension", "Indira Gandhi National Widow Pension Scheme (IGNWPS) - Maharashtra",
         "इंदिरा गांधी राष्ट्रीय विधवा निवृत्तीवेतन योजना - महाराष्ट्र", "इंदिरा गांधी राष्ट्रीय विधवा पेंशन योजना",
         "Social Justice and Special Assistance Department", "CENTRALLY_SPONSORED_SCHEME", "WIDOWS",
         "Monthly pension assistance for destitute widows aged 40 to 79 living below poverty line in Maharashtra.",
         "Monthly pension of ₹1,500 (Central ₹300 + State Top-up ₹1,200).", "₹1,500 / month", "MONTHLY",
         [{"op": "eq", "field": "gender", "value": "female"}, {"op": "gte", "field": "age", "value": 40}, {"op": "lte", "field": "age", "value": 79}, {"op": "eq", "field": "bpl", "value": True}],
         ["Husband Death Certificate", "Age Proof (40-79 years)", "BPL Certificate / Ration Card", "Maharashtra Domicile"], ["Voter ID"], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
         "https://aaplesarkar.mahaonline.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "Taluka Tehsildar Sanjay Gandhi Branch", "Aaple Sarkar / In-person", "Submit physical form to Taluka Tehsildar Sanjay Gandhi branch.",
         "VERIFIED_FOR_INFORMATION", ["NSAP Guidelines 2014", "GR 20-08-2019"], "myScheme.gov.in - IGNWPS", "https://www.myscheme.gov.in/schemes/ignwps",
         "Provides financial assistance of Rs 1,500 per month to BPL widows aged 40-79 years residing in Maharashtra."),
        
        # 22: IGNDPS
        ("scheme-igndps-disability-pension", "Indira Gandhi National Disability Pension Scheme (IGNDPS) - Maharashtra",
         "इंदिरा गांधी राष्ट्रीय दिव्यांग निवृत्तीवेतन योजना - महाराष्ट्र", "इंदिरा गांधी राष्ट्रीय दिव्यांग पेंशन योजना",
         "Social Justice and Special Assistance Department", "CENTRALLY_SPONSORED_SCHEME", "DIVYANG",
         "Monthly pension for persons with severe and multiple disabilities (>=80%) from BPL households.",
         "Monthly pension of ₹1,500 per month.", "₹1,500 / month", "MONTHLY",
         [{"op": "gte", "field": "age", "value": 18}, {"op": "gte", "field": "disability_percentage", "value": 80}, {"op": "eq", "field": "bpl", "value": True}],
         ["Disability Certificate (>=80% / Civil Surgeon)", "Age Proof (18-79)", "BPL Proof", "Domicile Certificate"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-UDID"],
         "https://aaplesarkar.mahaonline.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "Taluka Tehsildar Office", "In-person submission", "Submit Form with Civil Surgeon disability certificate to Tehsildar.",
         "VERIFIED_FOR_INFORMATION", ["NSAP Guidelines", "GR 20-08-2019"], "National Social Assistance Programme IGNDPS", "https://nsap.nic.in/",
         "Financial assistance of Rs 1,500 per month for individuals aged 18-79 with severe disability of 80% or higher belonging to BPL families."),

        # 23: NFBS
        ("scheme-national-family-benefit", "National Family Benefit Scheme (NFBS) - Maharashtra",
         "राष्ट्रीय कुटुंब अर्थसहाय्य योजना - महाराष्ट्र", "राष्ट्रीय परिवार लाभ योजना",
         "Social Justice and Special Assistance Department", "CENTRALLY_SPONSORED_SCHEME", "BPL_DESTITUTE",
         "One-time lump sum financial assistance to BPL households upon the death of the primary breadwinner.",
         "One-time grant of ₹20,000 transferred to the surviving head of family.", "₹20,000 One-time", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "eq", "field": "bpl", "value": True}],
         ["Death Certificate of Breadwinner (aged 18-59)", "BPL Proof", "Age Proof of Deceased", "Bank Account Details of Applicant"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
         "https://aaplesarkar.mahaonline.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "Taluka Tehsildar Sanjay Gandhi Desk", "In-person at Tehsildar desk", "Submit application within 6 months of death to Taluka Tehsildar.",
         "VERIFIED_FOR_INFORMATION", ["NSAP Guidelines", "GR 20-08-2019"], "National Family Benefit Guidelines Maharashtra", "https://nsap.nic.in/",
         "Lump sum financial assistance of Rs 20,000 to the bereaved household on death of the primary breadwinner aged between 18 and 60 years."),

        # 24: Post-Matric ST
        ("scheme-post-matric-st", "Government of India Post-Matric Scholarship for Scheduled Tribe Students - Maharashtra",
         "भारत सरकार मॅट्रिकोत्तर शिष्यवृत्ती (अनुसूचित जमाती) - महाराष्ट्र", "अनुसूचित जनजाति पोस्ट-मैट्रिक छात्रवृत्ति",
         "Tribal Development Department", "CENTRALLY_SPONSORED_SCHEME", "ST_STUDENTS",
         "100% tuition and exam fee waiver + monthly maintenance allowance for Scheduled Tribe students in post-matric studies.",
         "100% compulsory fee waiver + maintenance allowance up to ₹1,200/month.", "100% Fee Waiver + Maintenance", "PER_ACADEMIC_YEAR",
         [{"op": "eq", "field": "caste_category", "value": "ST"}, {"op": "lte", "field": "annual_family_income", "value": 250000}],
         ["Caste Certificate (ST)", "Tahsildar Income Certificate (<= ₹2.5L)", "Marksheet", "College Fee Receipt"], ["Caste Validity Certificate"], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-CASTE"],
         "https://mahadbt.maharashtra.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "MahaDBT Tribal Development Portal", "MahaDBT Portal Login", "Online application on MahaDBT followed by ITDP Project Officer approval.",
         "VERIFIED_FOR_INFORMATION", ["MoTA CSS Guidelines 2021", "MahaDBT Guidelines"], "Ministry of Tribal Affairs Post-Matric Scholarship", "https://tribal.nic.in/",
         "Provides full financial assistance covering non-refundable fees and maintenance to Scheduled Tribe students with parental income up to Rs 2.50 Lakh."),

        # 25: Post-Matric VJNT
        ("scheme-post-matric-vjnt", "Post-Matric Scholarship for VJNT Students - Maharashtra",
         "विमुक्त जाती व भटक्या जमाती मॅट्रिकोत्तर शिष्यवृत्ती - महाराष्ट्र", "विमुक्त जाति एवं घुमंतू जनजाति छात्रवृत्ति",
         "OBC, VJNT, SBC and SEBC Welfare Department", "STATE_SCHEME", "VJNT_STUDENTS",
         "100% tuition and exam fee waiver + maintenance allowance for Vimukta Jati and Nomadic Tribes students.",
         "100% fee waiver + monthly maintenance allowance.", "100% Fee Waiver + Maintenance", "PER_ACADEMIC_YEAR",
         [{"op": "eq", "field": "caste_category", "value": "VJNT"}, {"op": "lte", "field": "annual_family_income", "value": 250000}],
         ["Caste Certificate (VJNT)", "Non-Creamy Layer (NCL) Certificate", "Income Certificate (<= ₹2.5L)", "College Fee Receipt"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-CASTE", "SRV-RTS-NCL"],
         "https://mahadbt.maharashtra.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "MahaDBT Bahujan Kalyan Portal", "MahaDBT Portal Login", "Online submission on MahaDBT.",
         "VERIFIED_FOR_INFORMATION", ["GR 14-10-2013"], "Bahujan Kalyan Department VJNT Rules", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "Full tuition and examination fee waiver for VJNT students pursuing higher education in Maharashtra with family income up to Rs 2.5 Lakh."),

        # 26: Post-Matric SBC
        ("scheme-post-matric-sbc", "Post-Matric Scholarship for Special Backward Classes (SBC) - Maharashtra",
         "विशेष मागास प्रवर्ग मॅट्रिकोत्तर शिष्यवृत्ती - महाराष्ट्र", "विशेष पिछड़ा वर्ग छात्रवृत्ति - महाराष्ट्र",
         "OBC, VJNT, SBC and SEBC Welfare Department", "STATE_SCHEME", "SBC_STUDENTS",
         "100% tuition and exam fee waiver for Special Backward Classes students studying in Maharashtra colleges.",
         "100% Fee Waiver + Maintenance Allowance.", "100% Fee Waiver", "PER_ACADEMIC_YEAR",
         [{"op": "eq", "field": "caste_category", "value": "SBC"}, {"op": "lte", "field": "annual_family_income", "value": 250000}],
         ["Caste Certificate (SBC)", "NCL Certificate", "Income Certificate (<= ₹2.5L)", "Marksheet"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-CASTE", "SRV-RTS-NCL"],
         "https://mahadbt.maharashtra.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "MahaDBT SBC Portal", "MahaDBT Login", "Online submission on MahaDBT.",
         "VERIFIED_FOR_INFORMATION", ["GR 14-10-2013"], "MahaDBT SBC Scholarship Guidelines", "https://mahadbt.maharashtra.gov.in/",
         "Full fee assistance and maintenance for SBC students with annual family income up to Rs 2.5 Lakh."),

        # 27: PMAY-Gramin
        ("scheme-pmay-gramin", "Pradhan Mantri Awas Yojana - Gramin (PMAY-G) Maharashtra",
         "प्रधानमंत्री आवास योजना - ग्रामीण (महाराष्ट्र)", "प्रधानमंत्री आवास योजना - ग्रामीण",
         "Rural Development & Panchayati Raj Department", "CENTRALLY_SPONSORED_SCHEME", "RURAL_HOMELESS",
         "Financial grant for construction of pucca house with basic amenities for homeless rural families.",
         "Financial assistance of ₹1,20,000 (plains) to ₹1,30,000 (hilly/IAP) + 90 days MGNREGA wages + ₹12,000 toilet grant.", "₹1,20,000 - ₹1,30,000 Grant", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}],
         ["SECC 2011 / Awaas+ Registration", "Aadhaar Card", "Bank Account Details", "Land / Kutchha House Photo"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
         "https://awaassoft.nic.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "Gram Panchayat / Block Development Officer (BDO)", "Gram Sabha Registration", "Verification and approval by Gram Sabha and Block Development Officer.",
         "VERIFIED_FOR_INFORMATION", ["PMAY-G Framework, MoRD"], "Rural Development Ministry PMAY-G Guidelines", "https://pmayg.nic.in/",
         "Provides pucca houses with water, sanitation and electricity connection to all rural houseless households and those living in dilapidated houses."),

        # 28: PMAY-Urban
        ("scheme-pmay-urban", "Pradhan Mantri Awas Yojana - Urban (PMAY-U) Maharashtra",
         "प्रधानमंत्री आवास योजना - शहरी (महाराष्ट्र)", "प्रधानमंत्री आवास योजना - शहरी",
         "Housing Department", "CENTRALLY_SPONSORED_SCHEME", "URBAN_HOMELESS",
         "Pucca house ownership for urban homeless or EWS/LIG families with interest subsidies or direct construction grants.",
         "Up to ₹2,50,000 direct grant / credit-linked interest subsidy on home loans.", "Up to ₹2,50,000 Subsidy", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "lte", "field": "annual_family_income", "value": 300000}],
         ["Aadhaar Card", "Income Certificate (<= ₹3L for EWS)", "Self-Declaration of No Pucca House in India", "Urban Land Document"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
         "https://pmaymis.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "PMAY-MIS Portal & MHADA", "Online application on PMAY-MIS", "Apply through PMAY portal, MHADA lottery or Municipal Corporation housing cell.",
         "VERIFIED_FOR_INFORMATION", ["MoHUA PMAY-U Guidelines"], "Housing Ministry PMAY-U Framework", "https://pmay-urban.gov.in/",
         "Addresses the housing requirement of urban poor including slum dwellers through in-situ slum redevelopment, credit linked subsidy, and beneficiary led construction."),

        # 29: Ramai Awas
        ("scheme-ramai-awas-yojana", "Ramai Awas Gharkul Yojana - Maharashtra",
         "रमाई आवास घरकुल योजना - महाराष्ट्र", "रमाई आवास योजना",
         "Social Justice and Special Assistance Department", "STATE_SCHEME", "SC_ST",
         "Housing financial grant for rural and urban Scheduled Caste and Neo-Buddhist families living in kutchha houses.",
         "₹1,30,000 (rural) and ₹2,50,000 (urban) direct housing grant in installments.", "₹1,30,000 - ₹2,50,000 Grant", "ONE_TIME",
         [{"op": "eq", "field": "caste_category", "value": "SC"}, {"op": "lte", "field": "annual_family_income", "value": 100000}],
         ["Caste Certificate (SC/Neo-Buddhist)", "Income Certificate (<= ₹1.0L rural / <= ₹3.0L urban)", "Land Document (7/12 or Namuna 8)", "No Pucca House Affidavit"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-CASTE"],
         "https://sjsa.maharashtra.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "Zilla Parishad Social Welfare Officer / Municipal Corp", "Gram Panchayat / Municipal Application", "Selection through Gram Sabha in villages and Municipal Ward Committee in cities.",
         "VERIFIED_FOR_INFORMATION", ["GR 24-06-2015"], "Social Justice Department GR 24-06-2015", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शासन निर्णय क्र. घरायो-२०१५/प्र.क्र.५५/बांधकाम: अनुसूचित जाती व नवबौद्ध घटकांतील बेघर व कच्च्या घरात राहणाऱ्या कुटुंबांना पक्के घर बांधण्यासाठी आर्थिक अनुदान."),

        # 30: Shabari Gharkul
        ("scheme-shabari-gharkul-yojana", "Shabari Adivasi Gharkul Yojana - Maharashtra",
         "शबरी आदिवासी घरकुल योजना - महाराष्ट्र", "शबरी आदिवासी घरकुल योजना",
         "Tribal Development Department", "STATE_SCHEME", "ST",
         "Permanent housing construction assistance for Scheduled Tribe families living in thatched or kutchha huts in tribal pockets.",
         "₹1,30,000 (rural) to ₹1,50,000 (hilly/scheduled areas) housing construction subsidy.", "₹1,30,000 - ₹1,50,000 Grant", "ONE_TIME",
         [{"op": "eq", "field": "caste_category", "value": "ST"}, {"op": "lte", "field": "annual_family_income", "value": 100000}],
         ["Tribe Certificate (ST)", "Income Certificate (<= ₹1.0 Lakh)", "Land Ownership / Possession Proof in Tribal Village", "Bank Account Details"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-CASTE"],
         "https://tribal.maharashtra.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "Integrated Tribal Development Project (ITDP) Office", "In-person at ITDP Project Office", "Submit application to Project Officer, ITDP or Gram Panchayat.",
         "VERIFIED_FOR_INFORMATION", ["GR 04-03-2013"], "Tribal Development Department GR 04-03-2013", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शासन निर्णय क्र. घरायो-२०१२/प्र.क्र.४८/का-१०: अनुसूचित जमातीच्या बेघर कुटुंबांना पक्के घरकुल बांधण्यासाठी आर्थिक अनुदान."),

        # 31: MJPJAY Health Insurance
        ("scheme-mjpjay-ayushman-bharat", "Mahatma Jyotirao Phule Jan Arogya Yojana & Ayushman Bharat (MJPJAY)",
         "महात्मा ज्योतिराव फुले जन आरोग्य योजना व आयुष्मान भारत एकत्रित", "महात्मा ज्योतिराव फुले जन आरोग्य योजना",
         "Public Health Department", "JOINT_STATE_CENTRAL", "ALL_CITIZENS",
         "Universal cashless secondary and tertiary hospitalization healthcare coverage up to ₹5 Lakh per family per year in Maharashtra.",
         "100% cashless treatment & surgeries up to ₹5,00,000 per family per year covering 1,356 procedures in 1,000+ empanelled hospitals.", "₹5,00,000 / year Cashless", "ANNUAL",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}],
         ["Aadhaar Card", "Ration Card (Yellow / Orange / White) or Voter ID"], [], ["SRV-RTS-RATION-CARD"],
         "https://www.jeevandayee.gov.in/", ChannelType.AUTHORIZED_ASSISTANCE_CENTRE, "Arogyamitra Desk at Empanelled Network Hospitals", "Present Ration Card & Aadhaar at hospital Arogyamitra desk", "Direct cashless admission at network hospital without upfront payment.",
         "VERIFIED_FOR_INFORMATION", ["GR 28-07-2023"], "Public Health Department GR 28-07-2023", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शासन निर्णय क्र. मफुजाय-२०२३/प्र.क्र.१३५/आरोग्य-७: महाराष्ट्रातील सर्व नागरिकांना (रेशन कार्डधारक) दरवर्षी प्रति कुटुंब रु. ५.०० लाखांपर्यंत मोफत व कॅशलेस उपचार."),

        # 32: PMFBY 1 Rupee Crop Insurance
        ("scheme-pm-fasal-bima", "Pradhan Mantri Fasal Bima Yojana - Sarv Samaveshak ₹1 Token Scheme Maharashtra",
         "प्रधानमंत्री पीक विमा योजना - सर्वसमावेशक १ रुपया योजना", "प्रधानमंत्री फसल बीमा योजना - १ रुपया योजना",
         "Agriculture Department", "JOINT_STATE_CENTRAL", "FARMERS",
         "Complete crop loss protection for farmers where farmer pays only ₹1 token premium and GoM pays entire remaining farmer share.",
         "Full insured sum crop damage compensation directly into farmer's bank account upon drought, flood, or pest attack.", "Crop Loss Compensation", "EPISODIC",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "eq", "field": "has_land", "value": True}],
         ["7/12 Land Record Extract", "8-A Holding Extract", "Crop Sowing Certificate (Pik Pahani / E-Pik Pahani)", "Bank Passbook"], [], ["SRV-RTS-SATBARA"],
         "https://pmfby.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "National Crop Insurance Portal & CSC Centres", "Farmer Portal / CSC Kendra Login", "Enroll on PMFBY portal or via CSC before notified seasonal cut-off date with ₹1 fee.",
         "VERIFIED_FOR_INFORMATION", ["GR 26-06-2023"], "Agriculture Department GR 26-06-2023", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शासन निर्णय क्र. पिकवि-२०२३/प्र.क्र.५२/११-अ दिनांक २६ जून २०२३: खरीप व रब्बी हंगामासाठी शेतकऱ्यांकडून केवळ रु. १/- विमा हप्ता घेऊन सर्वसमावेशक पीक विमा योजना लागू."),

        # 33: PM-KUSUM Solar Pump
        ("scheme-pm-kusum-saur-pump", "Mukhyamantri Saur Krushi Pump Yojana / PM-KUSUM Component B",
         "मुख्यमंत्री सौर कृषी पंप योजना / पीएम-कुसुम घटक-ब", "मुख्यमंत्री सौर कृषि पंप योजना",
         "Energy Department", "JOINT_STATE_CENTRAL", "FARMERS",
         "90% to 95% government subsidy for installing 3 HP, 5 HP, or 7.5 HP off-grid solar agricultural water pumps for farmers.",
         "Solar water pump installation with only 10% farmer contribution for General and 5% for SC/ST farmers.", "90% - 95% Subsidy", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "eq", "field": "has_land", "value": True}],
         ["7/12 Extract with Water Source mention (Well/Borewell)", "Aadhaar Card", "Caste Certificate (if SC/ST)", "No Electricity Connection Certificate"], [], ["SRV-RTS-SATBARA", "SRV-RTS-CASTE"],
         "https://www.mahadiscom.in/solar/", ChannelType.DIRECT_OFFICIAL_PORTAL, "MSEDCL Solar Pump Portal (Mahadiscom)", "Online Application with Consumer Mobile", "Apply online on Mahadiscom portal, pay demand note, installation by empanelled agency.",
         "VERIFIED_FOR_INFORMATION", ["GR 07-06-2019", "MNRE KUSUM Guidelines"], "Energy Department GR 07-06-2019", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शेतकऱ्यांना सिंचनासाठी दिवसा अखंडित वीज उपलब्ध करून देण्यासाठी ९०% ते ९५% अनुदानावर सौर कृषी पंप वाटप."),

        # 34: PMMVY
        ("scheme-pm-matru-vandana", "Pradhan Mantri Matru Vandana Yojana (PMMVY) - Maharashtra",
         "प्रधानमंत्री मातृ वंदना योजना - महाराष्ट्र", "प्रधानमंत्री मातृ वंदना योजना",
         "Women and Child Development Department", "CENTRALLY_SPONSORED_SCHEME", "PREGNANT_WOMEN",
         "Maternity cash benefit for first two living children to compensate wage loss and ensure nutrition for mother and child.",
         "₹5,000 in two installments for first child; ₹6,000 in single installment if second child is a girl.", "₹5,000 - ₹6,000 DBT", "EPISODIC",
         [{"op": "eq", "field": "gender", "value": "female"}, {"op": "gte", "field": "age", "value": 19}],
         ["Mother & Child Protection (MCP) Card", "Aadhaar of Mother and Husband", "Aadhaar Seeded Bank Account", "Institutional Delivery Certificate (for second installment)"], [], ["SRV-RTS-DOMICILE"],
         "https://pmmvy.wcd.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "PMMVY Portal & Local Anganwadi", "Anganwadi Worker Online Entry", "Register at local Anganwadi Centre within 270 days of Last Menstrual Period (LMP).",
         "VERIFIED_FOR_INFORMATION", ["MoWCD PMMVY 2.0 Guidelines 2022"], "Ministry of Women and Child Development PMMVY", "https://pmmvy.wcd.gov.in/",
         "Direct cash benefit of Rs 5000 for first child and Rs 6000 for second girl child directly credited to bank account of pregnant women."),

        # 35: Swadhar Hostel SC
        ("scheme-swadhar-hostel-dbt", "Bharatratna Dr. Babasaheb Ambedkar Swadhar Yojana",
         "भारतरत्न डॉ. बाबासाहेब आंबेडकर स्वाधार योजना", "डॉ. बाबासाहेब आंबेडकर स्वाधार योजना",
         "Social Justice and Special Assistance Department", "STATE_SCHEME", "SC_STUDENTS",
         "Direct annual cash allowance for lodging, boarding, and educational expenses for SC students not getting government hostel admission.",
         "₹51,000 to ₹60,000 per academic year directly into student's bank account in two installments.", "₹51,000 - ₹60,000 / year", "PER_ACADEMIC_YEAR",
         [{"op": "eq", "field": "caste_category", "value": "SC"}, {"op": "lte", "field": "annual_family_income", "value": 250000}],
         ["Caste Certificate (SC)", "Income Certificate (<= ₹2.5L)", "College Admission Letter in Non-Hometown", "Hostel Non-Availability Certificate / Rent Agreement"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-CASTE"],
         "https://sjsa.maharashtra.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "Assistant Commissioner of Social Welfare (District)", "Offline Application Submission", "Submit application to District Social Welfare Office after admission.",
         "VERIFIED_FOR_INFORMATION", ["GR 13-06-2018"], "Social Justice Department GR 13-06-2018", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शासन निर्णय क्र. स्वाधार-२०१८/प्र.क्र.५८/शिक्षण-१: शासकीय वसतिगृहात प्रवेश न मिळालेल्या अनुसूचित जातीच्या विद्यार्थ्यांना भोजन, निवास व इतर शैक्षणिक खर्चासाठी वार्षिक रु. ५१,००० ते ६०,००० थेट बँक खात्यात."),

        # 36: Swayam Hostel ST
        ("scheme-swayam-hostel-dbt", "Pandit Deendayal Upadhyay Swayam Yojana",
         "पंडित दीनदयाळ उपाध्याय स्वयं योजना", "पंडित दीनदयाल उपाध्याय स्वयं योजना",
         "Tribal Development Department", "STATE_SCHEME", "ST_STUDENTS",
         "Annual food and accommodation stipend for Scheduled Tribe students enrolled in higher education without government hostel seat.",
         "₹51,000 to ₹60,000 per academic year depending on city category (Tier 1/2/3).", "₹51,000 - ₹60,000 / year", "PER_ACADEMIC_YEAR",
         [{"op": "eq", "field": "caste_category", "value": "ST"}, {"op": "lte", "field": "annual_family_income", "value": 250000}],
         ["Tribe Certificate (ST)", "Income Certificate (<= ₹2.5L)", "College Fee Receipt", "Room Rent Agreement / Proof of Residence"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-CASTE"],
         "https://swayam.mahaonline.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "Swayam MahaOnline Portal / ITDP Office", "Online Application on Swayam portal", "Apply online with college bonafide and rent receipt.",
         "VERIFIED_FOR_INFORMATION", ["GR 22-12-2016"], "Tribal Development Department GR 22-12-2016", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शासकीय वसतिगृहात प्रवेश न मिळालेल्या आदिवासी विद्यार्थ्यांना उच्च शिक्षणासाठी दरवर्षी रु. ५१,००० ते ६०,००० थेट बँक खात्यात निर्वाह भत्ता."),

        # 37: Panjabrao Deshmukh Hostel
        ("scheme-panjabrao-deshmukh-hostel", "Dr. Panjabrao Deshmukh Vastigruh Nirvah Bhatta Yojna",
         "डॉ. पंजाबराव देशमुख वसतिगृह निर्वाह भत्ता योजना", "डॉ. पंजाबराव देशमुख छात्रावास निर्वाह भत्ता योजना",
         "Higher and Technical Education Department", "STATE_SCHEME", "STUDENTS",
         "Hostel maintenance allowance for children of registered small/marginal farmers and general students admitted to professional courses.",
         "₹20,000 (district level) to ₹30,000 (divisional level / MMR) per academic year.", "₹20,000 - ₹30,000 / year", "PER_ACADEMIC_YEAR",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "lte", "field": "annual_family_income", "value": 800000}],
         ["Alpabhudharak (Small/Marginal Farmer) Certificate or Labour Registration", "7/12 Extract", "Income Certificate (<= ₹8 Lakh)", "Hostel / Room Rent Agreement"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-SATBARA"],
         "https://mahadbt.maharashtra.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "MahaDBT (Directorate of Technical Education)", "MahaDBT Citizen Login", "Apply under Technical Education tab on MahaDBT.",
         "VERIFIED_FOR_INFORMATION", ["GR 07-10-2017"], "Higher & Technical Education Department GR 07-10-2017", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "अल्पभूधारक शेतकरी व शेतमजुरांच्या पाल्यांसाठी व्यावसायिक अभ्यासक्रमांच्या वसतिगृह खर्चासाठी वार्षिक रु. २०,००० ते ३०,००० निर्वाह भत्ता."),

        # 38: BOCW Construction Board
        ("scheme-bocw-construction-welfare", "Maharashtra Building & Other Construction Workers Welfare Board Benefits",
         "महाराष्ट्र इमारत व इतर बांधकाम कामगार कल्याणकारी मंडळ योजना", "महाराष्ट्र भवन एवं निर्माण श्रमिक कल्याणकारी योजनाएं",
         "Labour Department", "STATE_SCHEME", "CONSTRUCTION_WORKERS",
         "32 statutory welfare benefits covering education scholarships, healthcare, marriage grant, and essential tool kits for construction laborers.",
         "₹5,000 tool kit, ₹10,000–₹50,000 children scholarship, ₹25,000 marriage assistance, ₹1,00,000 housing grant, and free medical checkup.", "32 Welfare Benefits", "EPISODIC",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "gte", "field": "age", "value": 18}, {"op": "lte", "field": "age", "value": 60}],
         ["90 Days Work Certificate from Registered Contractor / Gram Sevak", "Aadhaar Card", "BOCW Registration Smart Card", "Bank Passbook"], [], ["SRV-RTS-DOMICILE"],
         "https://mahabocw.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "MahaBOCW Official Portal & District Labour Office", "Worker Registration with 90-day labour certificate", "Register on MahaBOCW portal; claim benefits online after active smart card issuance.",
         "VERIFIED_FOR_INFORMATION", ["Building & Other Construction Workers Act 1996", "MBOCWW Rules"], "Labour Department Maharashtra BOCW Guidelines", "https://mahabocw.in/",
         "Registered construction workers who have worked for 90 days in preceding 12 months are entitled to 32 financial, medical, housing and educational welfare benefits."),

        # 39: CMEGP
        ("scheme-cmegp-self-employment", "Chief Minister Employment Generation Programme (CMEGP)",
         "मुख्यमंत्री रोजगार निर्मिती कार्यक्रम (सीएमईजीपी)", "मुख्यमंत्री रोजगार सृजन कार्यक्रम",
         "Industries, Energy & Labour Department (MSME)", "STATE_SCHEME", "YOUTH_UNEMPLOYED",
         "Capital subsidy program for setting up new micro and small manufacturing or service enterprises by youth in Maharashtra.",
         "Project cost up to ₹50 Lakh (Manufacturing) and ₹10 Lakh (Service) with 15% to 35% government capital subsidy.", "15% - 35% Capital Subsidy", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "gte", "field": "age", "value": 18}, {"op": "lte", "field": "age", "value": 45}],
         ["Project Report / Business Plan", "Educational Qualification Proof (7th/10th pass)", "Maharashtra Domicile Certificate", "Caste / Category Proof for enhanced 25-35% subsidy"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-CASTE"],
         "https://cmegp.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "CMEGP Maharashtra Portal & District Industries Centre (DIC)", "Online Application with Detailed Project Report", "Apply online on CMEGP portal; taskforce committee approves project for bank loan sanction.",
         "VERIFIED_FOR_INFORMATION", ["GR 01-08-2019", "GR 18-08-2023"], "Industries Department GR 01-08-2019", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "नवीन सूक्ष्म उद्योग उभारणीसाठी उत्पादन क्षेत्रासाठी रु. ५० लाख आणि सेवा क्षेत्रासाठी रु. १० लाख मर्यादेत १५% ते ३५% शासकीय अनुदान."),

        # 40: Annasaheb Patil IR2
        ("scheme-annasaheb-patil-ir2", "Annasaheb Patil Arthik-Magas Vikas Mahamandal - Loan Interest Reimbursement (IR2)",
         "अण्णासाहेब पाटील आर्थिक मागास विकास महामंडळ - व्याज परतावा योजना (IR2)", "अण्णासाहेब पाटिल ऋण ब्याज प्रतिपूर्ति योजना",
         "Skill Development, Employment and Entrepreneurship Department", "STATE_SCHEME", "YOUTH_UNEMPLOYED",
         "100% interest reimbursement on bank business loans up to ₹15 Lakh for youth entrepreneurs from Maratha / Open EWS communities.",
         "Interest reimbursement up to 12% per annum on term business loans up to ₹15,00,000 (total refund up to ₹3,00,000 over 5 years).", "Interest Refund up to ₹3,00,000", "MONTHLY",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "gte", "field": "age", "value": 18}, {"op": "lte", "field": "age", "value": 45}, {"op": "lte", "field": "annual_family_income", "value": 800000}],
         ["Bank Loan Sanction Letter", "LOI from Corporation", "Maharashtra Domicile", "Income Certificate (<= ₹8 Lakh) or EWS Certificate", "EMI Regular Repayment Statement"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
         "https://amvdc.maharashtra.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "AMVDC Official Portal & District Office", "AMVDC Portal Registration + Loan Linking", "Register on portal, obtain Letter of Intent (LOI), sanction bank loan, receive monthly interest refund.",
         "VERIFIED_FOR_INFORMATION", ["GR 07-02-2018", "AMVDC Board Circulars"], "AMVDC Interest Reimbursement Scheme Guidelines", "https://amvdc.maharashtra.gov.in/",
         "मराठा व खुल्या प्रवर्गातील नवउद्योजकांना १५ लाख रुपयांपर्यंतच्या बँक कर्जावर १२% व्याज परतावा थेट बँक खात्यात."),

        # 41: MPBCDC Loan & Subsidy
        ("scheme-mpbcdc-seed-capital", "Mahatma Phule Backward Class Development Corporation - Margin Capital & Subsidy",
         "महात्मा फुले मागासवर्गीय विकास महामंडळ - अनुदान व बीज भांडवल योजना", "महात्मा फुले पिछड़ा वर्ग विकास निगम योजना",
         "Social Justice and Special Assistance Department", "STATE_SCHEME", "SC",
         "50% capital grant and 20% low-interest seed money loan for Scheduled Caste entrepreneurs to start small businesses and trade.",
         "50% direct subsidy up to ₹50,000 for projects up to ₹1 Lakh; or 20% seed loan at 4% interest for projects up to ₹5 Lakh.", "50% Subsidy / 20% Seed Loan", "ONE_TIME",
         [{"op": "eq", "field": "caste_category", "value": "SC"}, {"op": "gte", "field": "age", "value": 18}, {"op": "lte", "field": "age", "value": 50}, {"op": "lte", "field": "annual_family_income", "value": 100000}],
         ["Caste Certificate (SC)", "Income Certificate (<= ₹1.0L rural / <= ₹3.0L urban)", "Business Project Report & Quotation", "Maharashtra Domicile"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-CASTE"],
         "https://mpbcdc.maharashtra.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "MPBCDC Portal & District MPBCDC Office", "MPBCDC Online Portal Application", "Apply online, attend interview at District Manager office, bank loan release.",
         "VERIFIED_FOR_INFORMATION", ["MPBCDC Scheme Rules 2018"], "MPBCDC Margin Money and Special Central Assistance Rules", "https://mpbcdc.maharashtra.gov.in/",
         "अनुसूचित जातीच्या सुशिक्षित बेरोजगार तरुणांना स्वयंरोजगारासाठी ५०% अनुदान व २०% बीज भांडवल कर्ज योजना."),

        # 42: MAMFDC Minority Loan
        ("scheme-mamfdc-minority-loan", "Maulana Azad Minorities Financial Development Corporation - Concessional Term Loan",
         "मौलाना आझाद अल्पसंख्याक आर्थिक विकास महामंडळ - थेट मुदत कर्ज योजना", "मौलाना आजाद अल्पसंख्यक वित्तीय विकास ऋण",
         "Minority Development Department", "STATE_SCHEME", "MINORITY",
         "Concessional 3% to 6% interest business loans up to ₹5 Lakh and overseas education loans up to ₹20 Lakh for notified minorities.",
         "Concessional business loan up to ₹5,00,000 at 3-6% interest and overseas education loan up to ₹20,00,000.", "Up to ₹5,00,000 Loan", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "gte", "field": "age", "value": 18}, {"op": "lte", "field": "age", "value": 55}, {"op": "lte", "field": "annual_family_income", "value": 800000}],
         ["Minority Proof (Self Declaration / School Leaving)", "Income Certificate (<= ₹8 Lakh)", "Business Plan / Quotation", "Guarantor Documents (State employee or property holder)"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
         "https://mamfdc.maharashtra.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "MAMFDC Portal & District Minority Office", "Online Application on MAMFDC", "Submit online application followed by verification and sanction by District Manager.",
         "VERIFIED_FOR_INFORMATION", ["MAMFDC Term Loan Guidelines 2019"], "Minority Development Department MAMFDC Rules", "https://mamfdc.maharashtra.gov.in/",
         "मुस्लिम, ख्रिश्चन, बौद्ध, जैन, शीख, पारशी अल्पसंख्याक बांधवांसाठी ३% ते ६% सवलतीच्या व्याजदरात व्यवसाय कर्ज."),

        # 43: MahaJyoti PhD Fellowship
        ("scheme-mahajyoti-fellowship", "MahaJyoti PhD Research Fellowship Scheme",
         "महाज्योती संशोधन अधिछात्रवृत्ती योजना (पीएच.डी.)", "महाज्योति पीएचडी शोध अध्येतावृत्ति योजना",
         "OBC, VJNT, SBC and SEBC Welfare Department", "STATE_SCHEME", "RESEARCH_SCHOLARS",
         "Monthly fellowship of ₹31,000 to ₹35,000 + contingency for OBC, VJNT, and SBC scholars pursuing regular full-time PhD in recognized universities.",
         "₹31,000/month (JRF) and ₹35,000/month (SRF) + annual contingency of ₹10,000–₹25,000 for up to 5 years.", "₹31,000 - ₹35,000 / month", "MONTHLY",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "lte", "field": "annual_family_income", "value": 800000}],
         ["PhD Registration Confirmation Letter from Recognized University", "Caste Certificate (OBC/VJNT/SBC)", "NCL Certificate", "Income Certificate (<= ₹8 Lakh)", "Research Topic Synopsis"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-CASTE", "SRV-RTS-NCL"],
         "https://mahajyoti.org.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "MahaJyoti Official Portal", "MahaJyoti Fellowship Portal Login", "Apply online against annual fellowship advertisement on MahaJyoti portal.",
         "VERIFIED_FOR_INFORMATION", ["MahaJyoti Fellowship Guidelines 2021"], "MahaJyoti Board Fellowship Rules", "https://mahajyoti.org.in/",
         "इतर मागासवर्गीय, विमुक्त जाती व भटक्या जमाती आणि विशेष मागास प्रवर्गातील संशोधक विद्यार्थ्यांना दरमहा रु. ३१,००० ते ३५,००० विद्यावेतन."),

        # 44: BARTI BANRF Fellowship
        ("scheme-barti-fellowship", "Dr. Babasaheb Ambedkar National Research Fellowship (BANRF) - BARTI",
         "डॉ. बाबासाहेब आंबेडकर राष्ट्रीय संशोधन अधिछात्रवृत्ती (बार्टी)", "बार्टी राष्ट्रीय शोध अध्येतावृत्ति",
         "Social Justice and Special Assistance Department", "STATE_SCHEME", "SC_RESEARCH_SCHOLARS",
         "Prestigious research fellowship for Scheduled Caste scholars pursuing M.Phil and Ph.D. degrees in Maharashtra universities.",
         "Monthly fellowship of ₹31,000 (JRF) and ₹35,000 (SRF) + HRA and annual contingency grants.", "₹31,000 - ₹35,000 / month", "MONTHLY",
         [{"op": "eq", "field": "caste_category", "value": "SC"}, {"op": "eq", "field": "resident_state", "value": "maharashtra"}],
         ["Caste Certificate (SC)", "Caste Validity Certificate", "Ph.D. Registration Letter", "Research Synopsis & Guide Certificate"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-CASTE"],
         "https://barti.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "BARTI Official Portal", "BARTI Online Registration", "Apply online during annual call for applications; merit ranking by scrutiny committee.",
         "VERIFIED_FOR_INFORMATION", ["BARTI BANRF Guidelines 2013-2023"], "Dr. Babasaheb Ambedkar Research & Training Institute", "https://barti.in/",
         "अनुसूचित जातीतील एम.फिल. व पीएच.डी. करणाऱ्या विद्यार्थ्यांना दरमहा रु. ३१,००० ते ३५,००० संशोधन अधिछात्रवृत्ती."),

        # 45: TRTI Tribal Fellowship
        ("scheme-trti-fellowship", "Tribal Research & Training Institute Research Fellowship & Coaching",
         "टीआरटीआय आदिवासी संशोधन अधिछात्रवृत्ती व स्पर्धा परीक्षा मार्गदर्शन", "टीआरटीआई शोध अध्येतावृत्ति",
         "Tribal Development Department", "STATE_SCHEME", "ST_RESEARCH_SCHOLARS",
         "Research fellowship and residential competitive examination coaching for Scheduled Tribe students in Maharashtra.",
         "₹31,000/month PhD research stipend or free residential coaching with ₹9,000/month stipend for UPSC/MPSC aspirants.", "₹31,000 / month Fellowship", "MONTHLY",
         [{"op": "eq", "field": "caste_category", "value": "ST"}, {"op": "eq", "field": "resident_state", "value": "maharashtra"}],
         ["Tribe Certificate (ST)", "Tribe Validity Certificate", "Ph.D. Registration / Entrance Exam Scorecard", "Bank Details"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-CASTE"],
         "https://trti.maharashtra.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "TRTI Portal", "Online Application on TRTI", "Apply on TRTI portal; entrance exam or academic screening for selection.",
         "VERIFIED_FOR_INFORMATION", ["TRTI Operational Guidelines"], "Tribal Research and Training Institute Pune", "https://trti.maharashtra.gov.in/",
         "अनुसूचित जमातीच्या संशोधक विद्यार्थ्यांना विद्यावेतन आणि स्पर्धा परीक्षांसाठी मोफत निवासी प्रशिक्षण व विद्यावेतन."),

        # 46: SARTHI CSMNRF Fellowship
        ("scheme-sarthi-fellowship", "Chhatrapati Shahu Maharaj National Research Fellowship (CSMNRF) - SARTHI",
         "छत्रपती शाहू महाराज राष्ट्रीय संशोधन अधिछात्रवृत्ती (सारथी)", "सारथी राष्ट्रीय शोध अध्येतावृत्ति",
         "Planning Department", "STATE_SCHEME", "RESEARCH_SCHOLARS",
         "Research stipend and fellowships for Maratha, Kunbi, and Maratha-Kunbi students enrolled in higher research degrees.",
         "Monthly fellowship of ₹31,000 (JRF) and ₹35,000 (SRF) + annual contingency allowance for up to 5 years.", "₹31,000 - ₹35,000 / month", "MONTHLY",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "lte", "field": "annual_family_income", "value": 800000}],
         ["Caste Certificate / Kunbi Record or Maratha Declaration", "Income Certificate (<= ₹8 Lakh)", "Ph.D. University Admission Document", "Research Synopsis"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
         "https://sarthimaharashtragov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "SARTHI Official Portal", "SARTHI Fellowship Login", "Apply online against annual SARTHI fellowship notification.",
         "VERIFIED_FOR_INFORMATION", ["SARTHI Guidelines 2020"], "Chhatrapati Shahu Maharaj Research Institute SARTHI", "https://sarthimaharashtragov.in/",
         "मराठा, कुणबी व कुणबी-मराठा प्रवर्गातील संशोधक विद्यार्थ्यांना दरमहा रु. ३१,००० ते ३५,००० राष्ट्रीय संशोधन अधिछात्रवृत्ती."),

        # 47: MGNREGS Maharashtra
        ("scheme-mgnregs-maharashtra", "Mahatma Gandhi National Rural Employment Guarantee Scheme (MGNREGS) - Maharashtra",
         "महात्मा गांधी राष्ट्रीय ग्रामीण रोजगार हमी योजना - महाराष्ट्र", "महात्मा गांधी नरेगा - महाराष्ट्र",
         "Rural Development & Panchayati Raj Department", "CENTRALLY_SPONSORED_SCHEME", "RURAL_WORKERS",
         "Statutory guarantee of at least 100 days of unskilled wage employment per rural household per year.",
         "Guaranteed daily minimum wage credited into bank/post office account within 15 days of work completion.", "Statutory Daily Wage", "EPISODIC",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "gte", "field": "age", "value": 18}],
         ["MGNREGS Job Card", "Aadhaar Card", "Bank Account Passbook"], [], ["SRV-RTS-DOMICILE"],
         "https://nrega.nic.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "Gram Panchayat Office & NREGA Soft", "Demand for work at Gram Panchayat", "Apply for Job Card at Gram Panchayat; submit written demand for work (Form 4).",
         "VERIFIED_FOR_INFORMATION", ["MGNREGA Act 2005", "Maharashtra Rural Employment Guarantee Rules"], "Ministry of Rural Development MGNREGA", "https://nrega.nic.in/",
         "Provides legally guaranteed 100 days of wage employment in a financial year to every rural household whose adult members volunteer to do unskilled manual work."),

        # 48: Mukhyamantri Vayoshri Yojana
        ("scheme-mukhyamantri-vayoshri", "Mukhyamantri Vayoshri Yojana",
         "मुख्यमंत्री वयोश्री योजना", "मुख्यमंत्री वयोश्री योजना",
         "Social Justice and Special Assistance Department", "STATE_SCHEME", "SENIOR_CITIZENS",
         "One-time direct financial assistance to senior citizens aged 65 and above for purchasing assistive aids, spectacles, and physical equipment.",
         "Direct bank transfer of ₹3,000 to purchase assistive devices (hearing aids, walking stick, wheelchair, commode chair, spectacles).", "₹3,000 One-time", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "gte", "field": "age", "value": 65}, {"op": "lte", "field": "annual_family_income", "value": 200000}],
         ["Age Proof (65+ years)", "Income Certificate (<= ₹2 Lakh)", "Maharashtra Domicile", "Aadhaar Linked Bank Account Details"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-SENIOR-CITIZEN"],
         "https://sjsa.maharashtra.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "District Social Welfare Officer / Taluka Assistant", "In-person at Social Welfare Office", "Submit application at District Social Welfare Officer office or camps.",
         "VERIFIED_FOR_INFORMATION", ["GR 05-02-2024"], "Social Justice Department GR 05-02-2024", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शासन निर्णय क्र. वयोश्री-२०२४/प्र.क्र.२५/सं.गा.यो दिनांक ०५ फेब्रुवारी २०२४: ६५ वर्षे व त्यावरील वयाच्या ज्येष्ठ नागरिकांना चष्मा, श्रवणयंत्र, ट्रायपॉड, व्हीलचेअर खरेदीसाठी रु. ३,००० थेट बँक खात्यात."),

        # 49: Divyang Motorized Tricycle
        ("scheme-divyang-motorized-tricycle", "Free Motorized Tricycle Scheme for Persons with Disabilities",
         "दिव्यांग व्यक्तींना मोफत मोटराइज्ड ट्रायसायकल वाटप योजना", "दिव्यांग व्यक्तियों को निःशुल्क मोटराइज्ड ट्राइसाइकिल",
         "Divyang Welfare Department", "STATE_SCHEME", "DIVYANG",
         "Free distribution of customized motorized tricycles for persons with severe locomotor disabilities in Maharashtra.",
         "100% free motorized retrofitted tricycle valued at over ₹40,000.", "100% Free Vehicle", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "gte", "field": "disability_percentage", "value": 40}, {"op": "gte", "field": "age", "value": 18}, {"op": "lte", "field": "age", "value": 55}, {"op": "lte", "field": "annual_family_income", "value": 100000}],
         ["Disability Certificate (>= 40% Locomotor Disability / UDID)", "Age Proof (18-55 years)", "Income Certificate (<= ₹1.0 Lakh)", "Learning / Driving Fitness Certificate"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-UDID"],
         "https://divyang.maharashtra.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "District Divyang Welfare Office / Zilla Parishad", "In-person at District Divyang Office", "Submit application to District Divyang Welfare Officer; medical board screening.",
         "VERIFIED_FOR_INFORMATION", ["GR 24-08-2023"], "Divyang Welfare Department GR 24-08-2023", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शासन निर्णय क्र. अपंग-२०२३/प्र.क्र.२२/दिव्यांग-२: ४०% किंवा त्याहून अधिक अस्थिव्यंग असलेल्या दिव्यांग व्यक्तींना फिरते राहण्यासाठी मोफत मोटराइज्ड ट्रायसायकल वाटप."),

        # 50: Divyang Swayamrojgar
        ("scheme-divyang-swayamrojgar", "Financial Assistance for Self-Employment of Persons with Disabilities",
         "दिव्यांग व्यक्तींसाठी स्वयंरोजगार बीजभांडवल योजना", "दिव्यांग व्यक्तियों हेतु स्वरोजगार बीज पूंजी",
         "Divyang Welfare Department", "STATE_SCHEME", "DIVYANG",
         "Financial subsidy up to ₹50,000 for setting up micro-business, small kiosk, or trade by persons with disabilities.",
         "Government subsidy of 50% (up to ₹50,000) on self-employment business project.", "Up to ₹50,000 Subsidy", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "gte", "field": "disability_percentage", "value": 40}, {"op": "gte", "field": "age", "value": 18}, {"op": "lte", "field": "age", "value": 50}, {"op": "lte", "field": "annual_family_income", "value": 150000}],
         ["Disability Certificate (>= 40% / UDID)", "Business Proposal & Quotation", "Income Certificate (<= ₹1.5 Lakh)", "Maharashtra Domicile"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME", "SRV-RTS-UDID"],
         "https://divyang.maharashtra.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "District Divyang Rehabilitation Centre (DDRC)", "In-person at DDRC", "Submit project proposal to District Divyang Officer; committee approval.",
         "VERIFIED_FOR_INFORMATION", ["Divyang Welfare Guidelines 2023"], "Divyang Welfare Department Scheme Rules", "https://divyang.maharashtra.gov.in/",
         "दिव्यांग व्यक्तींना स्वतःचा लहान व्यवसाय, दुकान, किंवा स्टॉल सुरू करण्यासाठी रु. ५०,००० पर्यंत शासकीय अनुदान व बँक कर्ज."),

        # 51: Intercaste Marriage Incentive
        ("scheme-intercaste-marriage-incentive", "Financial Incentive Scheme for Encouragement of Inter-Caste Marriages",
         "आंतरजातीय विवाहास प्रोत्साहन देण्यासाठी आर्थिक सहाय्य योजना", "अंतर्जातीय विवाह प्रोत्साहन योजना",
         "Social Justice and Special Assistance Department", "STATE_SCHEME", "ALL_CITIZENS",
         "Joint financial incentive grant to encourage social integration between Scheduled Castes and Open/General communities.",
         "₹3,00,000 financial incentive (₹2,50,000 fixed deposit + ₹50,000 cash grant) under revised rules.", "₹3,00,000 Grant", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}],
         ["Marriage Registration Certificate", "Caste Certificate of SC/ST spouse", "School Leaving Certificate of both spouses", "Joint Bank Account Passbook"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-CASTE"],
         "https://sjsa.maharashtra.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "District Social Welfare Officer, Zilla Parishad", "In-person submission within 1 year of marriage", "Joint application to District Social Welfare Officer, Zilla Parishad.",
         "VERIFIED_FOR_INFORMATION", ["GR 30-01-2019"], "Social Justice Department GR 30-01-2019", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शासन निर्णय क्र. आंतरवि-२०१८/प्र.क्र.५५/सं.गा.यो: आंतरजातीय विवाह करणाऱ्या दांपत्यास सामाजिक एकात्मता वाढवण्यासाठी रु. ३.०० लाख प्रोत्साहनपर आर्थिक सहाय्य."),

        # 52: Ahilyabai Holkar Bus Travel
        ("scheme-ahilyabai-holkar-bus-travel", "Punyashlok Ahilyadevi Holkar Free Bus Travel Scheme for School Girls",
         "पुण्यश्लोक अहिल्यादेवी होळकर मोफत बस प्रवास योजना", "अहिल्यादेवी होल्कर निःशुल्क बस यात्रा योजना",
         "School Education & Sports Department", "STATE_SCHEME", "SCHOOL_GIRLS",
         "100% free travel in Maharashtra State Road Transport Corporation (MSRTC) buses for rural school girls from Class 5 to Class 12.",
         "100% free ST bus season pass between village and school.", "100% Free Bus Travel", "PER_ACADEMIC_YEAR",
         [{"op": "eq", "field": "gender", "value": "female"}, {"op": "eq", "field": "resident_state", "value": "maharashtra"}],
         ["School Bonafide Certificate showing Class 5-12", "Residence Proof in Village", "Passport Size Photos"], [], ["SRV-RTS-DOMICILE"],
         "https://msrtc.maharashtra.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "School Headmaster / Local MSRTC Bus Depot", "Application routed through School Headmaster", "Headmaster prepares consolidated list and submits to local ST depot manager.",
         "VERIFIED_FOR_INFORMATION", ["GR 23-07-2001"], "School Education Department Free Bus Pass Rules", "https://education.maharashtra.gov.in/",
         "ग्रामीण भागातील इयत्ता ५ वी ते १२ वी पर्यंत शिकणाऱ्या विद्यार्थिनींना गावापासून शाळेपर्यंत जाण्या-येण्यासाठी एसटी बसेसमधून १००% मोफत प्रवास."),

        # 53: Asmita Yojana
        ("scheme-asmita-yojana", "Asmita Yojana - Subsidized Sanitary Napkins for Adolescent Girls & Women",
         "अस्मिता योजना", "अस्मिता योजना",
         "Rural Development & Panchayati Raj Department", "STATE_SCHEME", "WOMEN_GIRLS",
         "Subsidized high-quality sanitary napkins for rural adolescent girls studying in ZP schools and women in Self-Help Groups.",
         "Subsidized sanitary napkin pack at ₹5 for ZP school girls and ₹24/₹29 for rural women.", "Subsidized Napkin Packs", "MONTHLY",
         [{"op": "eq", "field": "gender", "value": "female"}, {"op": "eq", "field": "resident_state", "value": "maharashtra"}],
         ["Asmita Card / ZP School Student ID", "Aadhaar Card"], [], [],
         "https://mahaparinaam.org/", ChannelType.OFFLINE_OFFICE_APPLICATION, "Zilla Parishad Schools & Umed SHG Kendras", "School Headmaster / SHG Kendra", "Distribution through school nodal teachers and registered Self Help Groups.",
         "VERIFIED_FOR_INFORMATION", ["GR 08-03-2018"], "Rural Development Department GR 08-03-2018", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शासन निर्णय क्र. अस्मिता-२०१७/प्र.क्र.५५/ग्रावि-७: ग्रामीण भागातील ११ ते १९ वर्षे वयोगटातील किशोरवयीन मुलींना रु. ५/- मध्ये आणि ग्रामीण महिलांना सवलतीच्या दरात सॅनिटरी नॅपकिन वाटप."),

        # 54: Antyodaya Anna Yojana
        ("scheme-antyodaya-anna-yojana", "Antyodaya Anna Yojana (AAY) - Subsidized Ration Foodgrain Scheme Maharashtra",
         "अंत्योदय अन्न योजना (एएवाय) - महाराष्ट्र", "अंत्योदय अन्न योजना",
         "Food, Civil Supplies and Consumer Protection Department", "JOINT_STATE_CENTRAL", "BPL_DESTITUTE",
         "35 kg monthly subsidized/free foodgrains to the poorest of poor families across Maharashtra under National Food Security Act.",
         "35 kg foodgrain per household per month (wheat and rice free under NFSA/PMGKAY integration).", "35 kg Free Foodgrain", "MONTHLY",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "eq", "field": "bpl", "value": True}],
         ["Antyodaya (Yellow) Ration Card", "Aadhaar Card of all family members", "e-POS Biometric Authentication"], [], ["SRV-RTS-RATION-CARD"],
         "https://mahafood.gov.in/", ChannelType.AUTHORIZED_ASSISTANCE_CENTRE, "Fair Price Shop (राशन दुकान) / RCMS Portal", "e-POS Biometric at Fair Price Shop", "Monthly collection of grain from authorized fair price shop using Aadhaar biometric.",
         "VERIFIED_FOR_INFORMATION", ["National Food Security Act 2013", "MahaFood Guidelines"], "Food and Civil Supplies Department Maharashtra", "https://mahafood.gov.in/",
         "अंत्योदय शिधापत्रिकाधारक अतिगरीब कुटुंबांना दरमहा ३५ किलो धान्य मोफत वाटप."),

        # 55: Annapurna Scheme
        ("scheme-annapurna-scheme", "Annapurna Scheme - Free Foodgrains for Indigent Senior Citizens",
         "अन्नपूर्णा योजना - मोफत अन्नधान्य योजना", "अन्नपूर्णा योजना",
         "Food, Civil Supplies and Consumer Protection Department", "JOINT_STATE_CENTRAL", "SENIOR_CITIZENS",
         "10 kg free foodgrains per month for indigent senior citizens aged 65 and above who are not receiving any pension under IGNOAPS.",
         "10 kg foodgrains (rice and wheat) completely free every month.", "10 kg Free Foodgrain", "MONTHLY",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "gte", "field": "age", "value": 65}],
         ["Senior Citizen Age Proof (65+ years)", "No-Pension Certificate from Tahsildar", "Annapurna Ration Card", "Aadhaar Card"], [], ["SRV-RTS-SENIOR-CITIZEN", "SRV-RTS-RATION-CARD"],
         "https://mahafood.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "Taluka Tehsildar Office (Supply Branch)", "In-person submission at Taluka Supply Office", "Submit application to Taluka Food Supply Officer; allotment through Fair Price Shop.",
         "VERIFIED_FOR_INFORMATION", ["Annapurna Scheme National Guidelines"], "Food and Civil Supplies Department Annapurna Guidelines", "https://mahafood.gov.in/",
         "कोणतेही निवृत्तीवेतन न मिळणाऱ्या ६५ वर्षांवरील निराधार वृद्ध नागरिकांना दरमहा १० किलो मोफत धान्य वाटप."),

        # 56: Vrudha Kalawant Mandhan
        ("scheme-vrudha-kalawant-mandhan", "Financial Assistance Scheme for Elderly Folk Artists & Literary Figures",
         "वृद्ध साहित्यिक व मानसेवी कलावंत मानधन योजना", "वृद्ध कलाकार एवं साहित्यकार मानधन योजना",
         "Tourism and Cultural Affairs Department", "STATE_SCHEME", "ARTISTS",
         "Monthly honorarium pension for aged folk artists, singers, tamasha performers, and writers in financial distress.",
         "Monthly pension of ₹3,150 (Category C), ₹4,000 (Category B), and ₹5,000 (Category A).", "₹3,150 - ₹5,000 / month", "MONTHLY",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "gte", "field": "age", "value": 50}, {"op": "lte", "field": "annual_family_income", "value": 48000}],
         ["Folk Art Performance Evidence (Newspaper cuttings, photos, awards)", "Age Proof (50+ years)", "Income Certificate (<= ₹48,000/yr)", "Maharashtra Domicile"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-INCOME"],
         "https://cultural.maharashtra.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "District Collectorate (Cultural Affairs Branch)", "In-person submission to District Committee", "Application examined by District Committee headed by District Collector.",
         "VERIFIED_FOR_INFORMATION", ["GR 12-07-2017"], "Cultural Affairs Department GR 12-07-2017", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शासन निर्णय क्र. संकीर्ण-२०१७/प्र.क्र.५२/सां.का-४: उतारवयात हलाखीचे जीवन जगणाऱ्या पारंपरिक लोककलावंतांना व साहित्यिकांना दरमहा रु. ३,१५० ते ५,००० मानधन."),

        # 57: Umed MSRLM Livelihood
        ("scheme-umed-msrlm-livelihood", "Umed - Maharashtra State Rural Livelihoods Mission (MSRLM)",
         "उमेद - महाराष्ट्र राज्य ग्रामीण जीवनोन्नती अभियान (एमएसआरएलएम)", "उमेद - राज्य ग्रामीण आजीविका मिशन",
         "Rural Development & Panchayati Raj Department", "CENTRALLY_SPONSORED_SCHEME", "RURAL_WOMEN_SHG",
         "Revolving Fund and Community Investment Fund (CIF) for women Self-Help Groups (बचत गट) to establish micro-enterprises.",
         "Revolving Fund of ₹15,000 per SHG and Community Investment Fund (CIF) up to ₹1,50,000 at low interest.", "₹15,000 - ₹1,50,000 Grants", "EPISODIC",
         [{"op": "eq", "field": "gender", "value": "female"}, {"op": "eq", "field": "resident_state", "value": "maharashtra"}],
         ["SHG Registration Details", "Group Bank Passbook", "Panchasutra Adherence Record", "Members Aadhaar Cards"], [], ["SRV-RTS-DOMICILE"],
         "https://umed.maharashtra.gov.in/", ChannelType.AUTHORIZED_ASSISTANCE_CENTRE, "Block Mission Management Unit (BMMU) / Gram Panchayat", "SHG Group Linking at Block Office", "Form SHG, practice regular saving and internal lending, receive fund from Block Unit.",
         "VERIFIED_FOR_INFORMATION", ["MSRLM Operational Manual 2018"], "Rural Development Department Umed Guidelines", "https://umed.maharashtra.gov.in/",
         "ग्रामीण भागातील महिला बचत गटांना स्वावलंबी बनवण्यासाठी फिरता निधी (रु. १५,०००) व समुदाय गुंतवणूक निधी (रु. १,५०,०००)."),

        # 58: Krushi Yantrikikaran
        ("scheme-krushi-yantrikikaran", "Sub-Mission on Agricultural Mechanization (SMAM) Maharashtra",
         "कृषी यांत्रिकीकरण उप-अभियान (महाराष्ट्र)", "कृषि यांत्रीकरण उप-अभियान",
         "Agriculture Department", "JOINT_STATE_CENTRAL", "FARMERS",
         "Capital purchase subsidy of 40% to 50% for modern farm machinery (tractors, rotavators, power tillers, threshers, seed drills).",
         "Subsidy of 40% (General) to 50% (SC/ST/Women/Small Farmers) up to ₹1,25,000 on approved agricultural machinery.", "40% - 50% Machinery Subsidy", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "eq", "field": "has_land", "value": True}],
         ["7/12 and 8-A Land Extract", "Aadhaar Card", "Quotation of Machinery from Authorized Dealer", "Caste Certificate (if SC/ST)"], [], ["SRV-RTS-SATBARA", "SRV-RTS-CASTE"],
         "https://mahadbt.maharashtra.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "MahaDBT Shetkari Portal", "MahaDBT Farmer Registration", "Apply online on MahaDBT Shetkari; lottery selection, pre-sanction, purchase, and subsidy DBT.",
         "VERIFIED_FOR_INFORMATION", ["SMAM Central Guidelines", "GR 11-09-2020"], "Agriculture Department Farm Mechanization Guidelines", "https://mahadbt.maharashtra.gov.in/",
         "शेतकऱ्यांना शेतीची अवजारे व ट्रॅक्टर खरेदीसाठी ४०% ते ५०% शासकीय अनुदान थेट बँक खात्यात."),

        # 59: Sukshma Sinchan Drip
        ("scheme-sukshma-sinchan", "Pradhan Mantri Krishi Sinchayee Yojana - Micro Irrigation (Drip & Sprinkler)",
         "प्रधानमंत्री कृषी सिंचन योजना - सूक्ष्म सिंचन (ठिबक व तुषार सिंचन)", "प्रधानमंत्री कृषि सिंचाई योजना - सूक्ष्म सिंचाई",
         "Agriculture Department", "JOINT_STATE_CENTRAL", "FARMERS",
         "55% subsidy for small and marginal farmers and 45% for other farmers for installing drip and sprinkler micro-irrigation systems.",
         "Government subsidy of 55% (small/marginal farmers) and 45% (other farmers) on cost of drip/sprinkler set.", "45% - 55% Irrigation Subsidy", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}, {"op": "eq", "field": "has_land", "value": True}],
         ["7/12 Land Record Extract", "Water and Electricity Availability Proof", "Authorized Drip Dealer Quotation", "Field Map / Gut Book Extract"], [], ["SRV-RTS-SATBARA"],
         "https://mahadbt.maharashtra.gov.in/", ChannelType.DIRECT_OFFICIAL_PORTAL, "MahaDBT Shetkari Portal", "MahaDBT Login", "Apply online on MahaDBT; spot inspection by Agriculture Assistant, online subsidy credit.",
         "VERIFIED_FOR_INFORMATION", ["PMKSY Micro Irrigation Operational Guidelines 2020"], "Agriculture Department Drip Irrigation Rules", "https://mahadbt.maharashtra.gov.in/",
         "पाण्याचा कार्यक्षम वापर करण्यासाठी शेतकऱ्यांना ठिबक व तुषार सिंचन संच बसवण्यासाठी ५५% पर्यंत अनुदान."),

        # 60: Dairy Cattle Purchase Subsidy
        ("scheme-dairy-cow-buffalo-subsidy", "Special Component & General Milch Cattle Purchase Subsidy Scheme",
         "दुभत्या गाई-म्हशींचे गट वाटप योजना (पशुसंवर्धन)", "दुधारू गाय-भैंस वितरण योजना",
         "Animal Husbandry & Dairy Development Department", "STATE_SCHEME", "ANIMAL_HUSBANDRY_FARMERS",
         "50% to 75% capital subsidy on purchase of 2 or 4 milch cows or buffaloes to encourage dairy farming in rural Maharashtra.",
         "50% subsidy for General category and 75% for SC/ST beneficiaries on unit cost of 2/4 milch animals with 3-year insurance.", "50% - 75% Livestock Subsidy", "ONE_TIME",
         [{"op": "eq", "field": "resident_state", "value": "maharashtra"}],
         ["7/12 Extract or Landless Agricultural Labourer Certificate", "Aadhaar Card", "Caste Certificate (if SC/ST)", "Cattle Shed Certificate from Gram Panchayat"], [], ["SRV-RTS-DOMICILE", "SRV-RTS-CASTE"],
         "https://ahd.maharashtra.gov.in/", ChannelType.OFFLINE_OFFICE_APPLICATION, "Taluka Veterinary Officer & District Animal Husbandry Office", "In-person at Taluka Veterinary Dispensary", "Submit application to Taluka Mini Veterinary Hospital; cattle purchase committee verification.",
         "VERIFIED_FOR_INFORMATION", ["GR 17-02-2021"], "Animal Husbandry Department GR 17-02-2021", "https://gr.maharashtra.gov.in/1145/Government-Resolutions",
         "शासन निर्णय क्र. पसंयो-२०२०/प्र.क्र.५०/पदुम-२: ग्रामीण भागातील शेतकऱ्यांना दुग्ध व्यवसायासाठी ५०% ते ७५% अनुदानावर दुभत्या गाई-म्हशींचे वाटप.")
    ]

    for item in more_schemes:
        add(
            sid=item[0], en_name=item[1], mr_name=item[2], hi_name=item[3],
            dept=item[4], classification=item[5], beneficiary=item[6],
            summary_en=item[7], benefit_en=item[8], amount=item[9], freq=item[10],
            rule_children=item[11], req_docs=item[12], opt_docs=item[13], prereqs=item[14],
            app_url=item[15], channel_type=item[16], portal_name=item[17], login_req=item[18], offline_proc=item[19],
            pub_status=item[20], gr_list=item[21], src_name=item[22], src_url=item[23], excerpt=item[24]
        )

    return specs

def build_and_save():
    root = Path(__file__).resolve().parents[1]
    registry_dir = root / "data" / "source_registry"
    registry_dir.mkdir(parents=True, exist_ok=True)
    
    specs = get_catalog_specs()
    print(f"Total scheme specs defined: {len(specs)}")
    
    canonical_records = []
    runtime_schemes = []
    channel_records = []
    
    for s in specs:
        src = make_source_ref(s["src_name"], s["src_url"], s["excerpt"])
        
        # 1. Canonical Record
        can_rec = {
            "canonical_scheme_id": s["sid"],
            "official_scheme_name": s["en_name"],
            "english_name": s["en_name"],
            "marathi_name": s["mr_name"],
            "hindi_name": s["hi_name"],
            "aliases": s["aliases"],
            "responsible_department": s["dept"],
            "implementing_authority": s["dept"],
            "funding_authority": "Government of Maharashtra" if s["classification"] == "STATE_SCHEME" else ("Government of India" if s["classification"] == "CENTRAL_SCHEME" else "Joint Central & Maharashtra State"),
            "state_central_joint_classification": s["classification"],
            "beneficiary_category": s["beneficiary"],
            "scheme_objective": s["summary_en"],
            "geographic_applicability": "Statewide (Maharashtra)",
            "district_restrictions": None,
            "rural_urban_conditions": "ALL",
            "age_requirements": s["age_req"],
            "gender_conditions": s["gender_req"],
            "social_category_requirements": s["social_req"],
            "family_income_requirements": s["income_req"],
            "occupation_requirements": s["occ_req"],
            "education_requirements": None,
            "disability_requirements": None,
            "landholding_property_requirements": None,
            "other_eligibility_conditions": [f"Resident of Maharashtra", f"Subject to verification under {s['dept']}"],
            "benefit_description": s["benefit_en"],
            "benefit_amount": s["amount"],
            "benefit_frequency": s["freq"],
            "benefit_restrictions": "Subject to annual state budget allocation and scrutiny verification",
            "required_documents": s["req_docs"],
            "optional_documents": s["opt_docs"],
            "application_window": "OPEN_YEAR_ROUND",
            "financial_academic_year": "2024-2025",
            "renewal_requirements": "NONE",
            "application_authority": s["dept"],
            "official_application_url": s["app_url"],
            "offline_application_procedure": s["offline_proc"],
            "prerequisite_services": s["prereqs"],
            "government_source_references": [src],
            "original_gr_and_amendments": s["gr_list"],
            "rule_version": "1.0.0",
            "effective_start_date": "2024-04-01",
            "effective_end_date": None,
            "last_source_verification_date": "2026-11-13",
            "application_availability": s["app_avail"],
            "publication_status": s["pub_status"],
            "official_name_en": s["en_name"],
            "official_name_mr": s["mr_name"],
            "responsible_authority": s["dept"],
            "department": s["dept"],
            "lifecycle_status": s["pub_status"],
            "benefit_details": s["benefit_en"],
            "eligibility_summary": f"Age: {s['age_req'] or 'Any'}, Income: {s['income_req'] or 'No ceiling'}, Social: {s['social_req']}",
            "application_channel_id": s["sid"],
            "application_portal_url": s["app_url"],
            "duplicate_aliases_mapped": s["aliases"],
            "source_references": [src],
            "source_doc_ids": s["gr_list"],
            "geography": "Statewide (Maharashtra)"
        }
        # Validate through CanonicalSchemeRecord model
        validated_can = CanonicalSchemeRecord.model_validate(can_rec)
        canonical_records.append(validated_can.model_dump())

        # 2. Runtime Scheme
        rule_node = RuleNode(
            op="all",
            children=[RuleNode.model_validate(c) for c in s["rule_children"]]
        )
        src_ref = SourceReference.model_validate(src)
        
        run_scheme = {
            "scheme_id": s["sid"],
            "name": s["en_name"],
            "department": s["dept"],
            "summary": s["summary_en"],
            "benefits": [s["benefit_en"]],
            "required_documents": s["req_docs"],
            "eligibility_rule": rule_node.model_dump(),
            "sources": [src_ref.model_dump()],
            "rule_version": "1.0.0",
            "rule_status": s["rule_status"],
            "languages": ["en", "mr", "hi"],
            "publication_authorized": s["publication_authorized"],
            "approved_by": "State Catalogue Review Authority" if s["rule_status"] == "active" else None,
            "approval_reference": "MAHA-GOV-CATALOGUE-2026" if s["rule_status"] == "active" else None,
            "last_verified_at": "2026-11-13T00:00:00+05:30" if s["rule_status"] == "active" else None
        }
        validated_run = Scheme.model_validate(run_scheme)
        runtime_schemes.append(validated_run.model_dump(mode="json"))

        # 3. Channel Record
        chan_rec = {
            "scheme_id": s["sid"],
            "scheme_name": s["en_name"],
            "channel_type": s["channel_type"],
            "portal_name": s["portal_name"],
            "portal_url": s["app_url"],
            "department": s["dept"],
            "login_requirement": s["login_req"],
            "application_window": "Open (FY 2024-2025)",
            "fresh_vs_renewal": "Fresh applications open online or at offline designated desks",
            "offline_procedure": s["offline_proc"],
            "preparation_checklist": s["req_docs"],
            "tracking_url": s["app_url"] if "http" in s["app_url"] else None,
            "grievance_url": "https://grievances.maharashtra.gov.in/",
            "statutory_hand_off_notice": "Independent guidance platform. Official application must be submitted directly to the competent Maharashtra authority."
        }
        validated_chan = ApplicationChannelRecord.model_validate(chan_rec)
        channel_records.append(validated_chan.model_dump())

    # Write files
    (registry_dir / "canonical_schemes.json").write_text(
        json.dumps(canonical_records, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Wrote {len(canonical_records)} canonical schemes to {registry_dir / 'canonical_schemes.json'}")

    (registry_dir / "application_channels.json").write_text(
        json.dumps(channel_records, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Wrote {len(channel_records)} application channels to {registry_dir / 'application_channels.json'}")

    demo_schemes_file = root / "data" / "demo" / "schemes.json"
    demo_schemes_file.write_text(
        json.dumps(runtime_schemes, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Wrote {len(runtime_schemes)} runtime schemes to {demo_schemes_file}")

if __name__ == "__main__":
    build_and_save()
