from __future__ import annotations

from scheme_navigator.ingestion.models import (
    AmendmentRecord,
    AmendmentType,
    SchemeLineageReport,
    SupersededRuleNotice,
)

# Registered legislative and executive lineage for Maharashtra schemes
MAHARASHTRA_SCHEME_LINEAGES: dict[str, SchemeLineageReport] = {
    "candidate-majhi-ladki-bahin": SchemeLineageReport(
        scheme_id="candidate-majhi-ladki-bahin",
        canonical_name="Mukhyamantri Majhi Ladki Bahin Yojana",
        administering_department="Women and Child Development Department, Government of Maharashtra",
        base_resolution=AmendmentRecord(
            order_index=1,
            gr_date="2024-06-28",
            gr_number="202406281814018230",
            title="Maharashtra GR No. Sankirna-2024/CR137/Karya-02 (Base Scheme Promulgation)",
            amendment_type=AmendmentType.BASE_RESOLUTION,
            source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/202406281814018230.pdf",
            source_sha256="4c82a8b88a21b06042f46382b23d1327c8fa37a1eacefadbc9ca66778f0093fd",
            operative_clauses=["Gender: Female", "Resident: Maharashtra", "Age: 21-60", "Income: <= 2.5L", "Benefit: Rs. 1,500/mo"],
            superseded_clauses=["Age upper limit: 60 years (superseded by Shuddhipatra 03-07-2024)"],
            verbatim_mr="२१ ते ६० वयोगटातील पात्र महिलांना दरमहा रु. १५००/- थेट बँक खात्यात जमा करण्यात येतील.",
            translation_en="Eligible women in the age group 21 to 60 will receive Rs. 1,500 per month deposited into their bank account.",
        ),
        amendments=[
            AmendmentRecord(
                order_index=2,
                gr_date="2024-07-03",
                gr_number="202407031335114330",
                title="Maharashtra GR No. Sankirna-2024/CR137/Karya-02 (Shuddhipatra Amendment)",
                amendment_type=AmendmentType.SHUDDHIPATRA,
                source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/202407031335114330.pdf",
                source_sha256="69f6b4dc283f7721c2e4adc1d62262df21213e7413fb739406d1470ccc08df40",
                operative_clauses=["Age: 21-65 years", "15-year Ration card or Voter ID acceptable in lieu of Domicile Certificate"],
                superseded_clauses=[],
                verbatim_mr="वयोमर्यादा २१ ते ६० वर्षे ऐवजी २१ ते ६५ वर्षे अशी सुधारित करण्यात येत आहे.",
                translation_en="Age limit is amended from 21-60 years to 21-65 years.",
            ),
            AmendmentRecord(
                order_index=3,
                gr_date="2024-07-12",
                gr_number="202407121401594230",
                title="Maharashtra GR No. Sankirna-2024/CR137/Karya-02 (Clarification Order)",
                amendment_type=AmendmentType.CLARIFICATION,
                source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/202407121401594230.pdf",
                source_sha256="f39fcfbbe8ff299d4cb7752860fe22e8564a235c939b4c21111880744df134cd",
                operative_clauses=["Yellow and Orange ration cards satisfy income verification without separate income certificate"],
                superseded_clauses=[],
                verbatim_mr="पिवळे अथवा केशरी रेशनकार्डधारक कुटुंबांना उत्पन्नाच्या दाखल्याची आवश्यकता नाही.",
                translation_en="Families holding yellow or orange ration cards do not require a separate income certificate.",
            ),
        ],
        superseded_rules=[
            SupersededRuleNotice(
                condition_id="c_mmlby_age_lte_60",
                original_gr_reference="202406281814018230",
                superseding_gr_reference="202407031335114330",
                effective_date="2024-07-01",
                original_value=60,
                revised_value=65,
                description="Age ceiling of 60 years superseded by Shuddhipatra extending coverage to 65 years.",
            )
        ],
        unresolved_conflicts=[
            "Political proposal to enhance monthly benefit to Rs. 2,100 has no gazetted Government Resolution as of November 2026. Rate remains Rs. 1,500/month.",
            "Historical e-KYC deadlines (30 Sept / 15 Oct 2024) expired and are omitted from prospective logic.",
        ],
        current_operative_gr_references=["202406281814018230", "202407031335114330", "202407121401594230"],
    ),

    "candidate-sanjay-gandhi-niradhar": SchemeLineageReport(
        scheme_id="candidate-sanjay-gandhi-niradhar",
        canonical_name="Sanjay Gandhi Niradhar Anudan Yojana",
        administering_department="Social Justice and Special Assistance Department, Government of Maharashtra",
        base_resolution=AmendmentRecord(
            order_index=1,
            gr_date="2019-08-20",
            gr_number="201908201550269614",
            title="Maharashtra GR No. SGNAY-2019/CR105/Karya-03 (Consolidated Scheme Rules)",
            amendment_type=AmendmentType.BASE_RESOLUTION,
            source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/201908201550269614.pdf",
            source_sha256="2a1f27f6d66b5b32c46bb57e29e44b8311e13ef60c064fcc12d9ab5d1abc016a",
            operative_clauses=["Destitute categories", "Income <= Rs. 21,000 for destitute", "Income <= Rs. 50,000 for disabled", "Age < 65"],
            superseded_clauses=["Initial benefit of Rs. 1,000/month superseded by GR 05-07-2023"],
            verbatim_mr="निराधार व्यक्तींना दरमहा रु. १०००/- अर्थसहाय्य देण्यात येईल.",
            translation_en="Destitute persons will be provided financial assistance of Rs. 1,000 per month.",
        ),
        amendments=[
            AmendmentRecord(
                order_index=2,
                gr_date="2023-07-05",
                gr_number="202307051752538914",
                title="Maharashtra GR No. SGNAY-2023/CR78/Karya-03 (Benefit Enhancement)",
                amendment_type=AmendmentType.BENEFIT_REVISION,
                source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/202307051752538914.pdf",
                source_sha256="85f619e9d67dc219bb0247b23bd7a7abf1020153fa1d854dbb5528ceac67491c",
                operative_clauses=["Benefit increased from Rs. 1,000 to Rs. 1,500/month"],
                superseded_clauses=["Assistance rate of Rs. 1,000/month superseded"],
                verbatim_mr="संजय गांधी निराधार अनुदान योजनेअंतर्गत अनुदानाचा दर दरमहा रु. १,०००/- वरून रु. १,५००/- इतका सुधारित करण्यात येत आहे.",
                translation_en="The rate of grant under SGNAY is enhanced from Rs. 1,000 to Rs. 1,500 per month.",
            ),
            AmendmentRecord(
                order_index=3,
                gr_date="2025-09-15",
                gr_number="202509151620000000",
                title="Maharashtra GR No. SGNAY-2025/CR112/Karya-03 (Divyang Benefit Enhancement)",
                amendment_type=AmendmentType.DISABILITY_REVISION,
                source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/202509151620000000.pdf",
                source_sha256="b86f64465a7439806d7ecb3d41170a0e8026adb77a713db591f2df7bfef7a065",
                operative_clauses=["Disability assistance enhanced to Rs. 2,500/month for >= 40% certified disability"],
                superseded_clauses=["Disability benefit rate of Rs. 1,500/month superseded for disabled category"],
                verbatim_mr="विशेष दिव्यांग लाभार्थ्यांसाठी दरमहा रु. २,५००/- अर्थसहाय्य लागू राहील.",
                translation_en="For special disabled beneficiaries, assistance of Rs. 2,500 per month will apply.",
            ),
        ],
        superseded_rules=[
            SupersededRuleNotice(
                condition_id="c_sgnay_benefit_1000",
                original_gr_reference="201908201550269614",
                superseding_gr_reference="202307051752538914",
                effective_date="2023-07-01",
                original_value=1000,
                revised_value=1500,
                description="Assistance rate of Rs. 1,000 superseded by Rs. 1,500 per month.",
            ),
            SupersededRuleNotice(
                condition_id="c_sgnay_divyang_benefit_1500",
                original_gr_reference="202307051752538914",
                superseding_gr_reference="202509151620000000",
                effective_date="2025-10-01",
                original_value=1500,
                revised_value=2500,
                description="Disability assistance rate of Rs. 1,500 superseded by Rs. 2,500 per month.",
            ),
        ],
        unresolved_conflicts=[
            "Blanket age >= 18 restriction was erroneous: Category 3 covers destitute minor orphans (< 18), and disabled minors are eligible. Upper limit is strictly age < 65.",
            "Bal Sangopan Yojana operates under Women & Child Development as the primary child foster welfare scheme.",
        ],
        current_operative_gr_references=["201908201550269614", "202307051752538914", "202509151620000000"],
    ),

    "candidate-shravanbal-nivruttivetan": SchemeLineageReport(
        scheme_id="candidate-shravanbal-nivruttivetan",
        canonical_name="Shravanbal Seva Rajya Nivruttivetan Yojana",
        administering_department="Social Justice and Special Assistance Department, Government of Maharashtra",
        base_resolution=AmendmentRecord(
            order_index=1,
            gr_date="2019-08-20",
            gr_number="201908201550269614",
            title="Maharashtra GR No. SGNAY-2019/CR105/Karya-03 (Part II Shravanbal Guidelines)",
            amendment_type=AmendmentType.BASE_RESOLUTION,
            source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/201908201550269614.pdf",
            source_sha256="85ebc9241b4a3f3962ee5261898adb183854873aa719b33a349fb05626704153",
            operative_clauses=["Age >= 65", "Group A: Central BPL list (IGNOAPS top-up)", "Group B: State non-BPL income <= Rs. 21,000"],
            superseded_clauses=["Initial pension rate of Rs. 1,000/month superseded"],
            verbatim_mr="६५ वर्षे व त्यावरील निराधार व्यक्तींना दरमहा रु. १०००/- निवृत्तीवेतन देण्यात येईल.",
            translation_en="Destitute senior citizens aged 65 and above will be given a monthly pension of Rs. 1,000.",
        ),
        amendments=[
            AmendmentRecord(
                order_index=2,
                gr_date="2023-07-05",
                gr_number="202307051752538914",
                title="Maharashtra GR No. SGNAY-2023/CR78/Karya-03 (Pension Enhancement)",
                amendment_type=AmendmentType.BENEFIT_REVISION,
                source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/202307051752538914.pdf",
                source_sha256="e442859d35c7936cd2d201fba6faa5f3eebacadafcdaa0fb20c05d3e96d005fa",
                operative_clauses=["Total pension enhanced to Rs. 1,500/month for Group A and Group B"],
                superseded_clauses=["Pension rate of Rs. 1,000/month superseded"],
                verbatim_mr="श्रावणबाळ योजनेअंतर्गत निवृत्तीवेतन दरमहा रु. १,५००/- इतके सुधारित करण्यात येत आहे.",
                translation_en="Under Shravanbal Yojana, pension is enhanced to Rs. 1,500 per month.",
            ),
            AmendmentRecord(
                order_index=3,
                gr_date="2025-09-15",
                gr_number="202509151620000000",
                title="Maharashtra GR No. SGNAY-2025/CR112/Karya-03 (Divyang Pension Enhancement)",
                amendment_type=AmendmentType.DISABILITY_REVISION,
                source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/202509151620000000.pdf",
                source_sha256="64916b3c03e13c96b309159db76d41c0b72c757a603c4f765c6d0f0595892a31",
                operative_clauses=["Disability pension enhanced to Rs. 2,500/month for >= 40% certified disability"],
                superseded_clauses=[],
                verbatim_mr="दिव्यांग ज्येष्ठ नागरिकांसाठी सुधारित दर दरमहा रु. २,५००/- राहील.",
                translation_en="The revised rate for disabled senior citizens will be Rs. 2,500 per month.",
            ),
        ],
        superseded_rules=[
            SupersededRuleNotice(
                condition_id="c_shravanbal_pension_1000",
                original_gr_reference="201908201550269614",
                superseding_gr_reference="202307051752538914",
                effective_date="2023-07-01",
                original_value=1000,
                revised_value=1500,
                description="Pension rate of Rs. 1,000 superseded by Rs. 1,500 per month.",
            ),
        ],
        unresolved_conflicts=[
            "Group A involves dual funding: IGNOAPS Central share + Maharashtra State top-up.",
            "Group B is 100% state funded for non-BPL residents with annual income <= Rs. 21,000.",
        ],
        current_operative_gr_references=["201908201550269614", "202307051752538914", "202509151620000000"],
    ),

    "candidate-payment-tuition-exam-fees-obc-girls": SchemeLineageReport(
        scheme_id="candidate-payment-tuition-exam-fees-obc-girls",
        canonical_name="Payment of Tuition Fees and Examination Fees to OBC Girls Pursuing Professional Courses",
        administering_department="Higher and Technical Education Department, Government of Maharashtra",
        base_resolution=AmendmentRecord(
            order_index=1,
            gr_date="2024-07-08",
            gr_number="शिष्यवृ-२०२४/प्र.क्र.१०५/तांशि-४",
            title="Maharashtra GR dated 8 July 2024 (100% Fee Reimbursement for Girls in Professional Courses)",
            amendment_type=AmendmentType.BASE_RESOLUTION,
            source_url="https://gr.maharashtra.gov.in/Site/Upload/GR/202407081745100000.pdf",
            source_sha256="da5b6f552073347fe6912a8f82b444c100b9bfce5e6fa21e970605e02a21cc2d",
            operative_clauses=[
                "Female students belonging to OBC, EBC, SEBC",
                "Family annual income <= Rs. 8,00,000",
                "Admission via Centralized Admission Process (CAP) in approved professional degree/diploma courses",
                "100% tuition and examination fee reimbursement; ZERO maintenance allowance",
            ],
            superseded_clauses=[],
            verbatim_mr="व्यावसायिक अभ्यासक्रमास केंद्रीभूत प्रवेश प्रक्रियेद्वारे (CAP) प्रवेश घेणाऱ्या इतर मागास प्रवर्गातील मुलींना १००% शिक्षण शुल्क व परीक्षा शुल्क प्रतिपूर्ती करण्यात येईल.",
            translation_en="100% tuition fee and examination fee reimbursement will be provided to OBC girls admitted to professional courses through CAP.",
        ),
        amendments=[],
        superseded_rules=[],
        unresolved_conflicts=[
            "Does not cover non-CAP management quota seats or non-professional general degree courses (B.A., B.Com., B.Sc.).",
            "Distinct from OBC Bahujan Welfare Department's Post-Matric Scholarship which covers maintenance allowances.",
        ],
        current_operative_gr_references=["शिष्यवृ-२०२४/प्र.क्र.१०५/तांशि-४"],
    ),
}


def get_scheme_lineage(scheme_id: str) -> SchemeLineageReport | None:
    """Retrieve the authoritative legislative and executive lineage report for a scheme."""
    return MAHARASHTRA_SCHEME_LINEAGES.get(scheme_id)


def list_registered_lineages() -> list[SchemeLineageReport]:
    """List all registered scheme lineages."""
    return list(MAHARASHTRA_SCHEME_LINEAGES.values())
