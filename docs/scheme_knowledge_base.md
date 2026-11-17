# Canonical Scheme Knowledge Base
## Comprehensive Statutory Reference, Scheme Catalog, and Multilingual Repository

---

### 1. Architectural Overview

The Maharashtra Scheme Navigator Knowledge Base provides a verified, non-fabricated statutory knowledge repository of all **75 canonical government welfare schemes** operating within the State of Maharashtra.

The knowledge base is structured in two synchronized storage artifacts:
1. `data/source_registry/canonical_schemes.json`: Core scheme records, statutory scope, departmental ownership, eligibility criteria, benefit descriptions, government resolution citations, application portal channels, and trilingual FAQs (English, Marathi, and Hindi).
2. `data/source_registry/scheme_document_requirements.json`: Granular document requirement inventories specifying mandatory vs. conditional documents, approved statutory alternatives, competent issuing authorities, validity conditions, and Maharashtra Right to Public Services Act (RTS 2015) statutory timelines.

---

### 2. Scheme Distribution & Departmental Coverage

The 75 canonical schemes represent complete cross-departmental coverage of Maharashtra state administration, central sponsor programs, and municipal schemes:

| Administrative Department | Schemes Catalogued | Key Representative Schemes |
|---|---|---|
| Women and Child Development Department | 8 | Mukhyamantri Majhi Ladki Bahin Yojana, Majhi Kanya Bhagyashree, Baby Care Kit Scheme, Kishori Shakti Yojana |
| Social Justice and Special Assistance Department | 12 | Sanjay Gandhi Niradhar Anudan Yojana (SGNAY), Shravanbal Seva Rajya Nivruttivetan Yojana, Dr. Babasaheb Ambedkar Swadhar Yojana, Post-Matric Scholarship for SC Students |
| Agriculture and Farmers Welfare Department | 9 | Namo Shetkari Mahasanman Nidhi Yojana, Dr. Babasaheb Ambedkar Krushi Swavalamban Yojana, Birsa Munda Krishi Kranti Yojana, Chief Minister Agriculture Solar Feeder Scheme |
| Public Health and Family Welfare Department | 6 | Mahatma Jyotirao Phule Jan Arogya Yojana (MJPJAY), Ayushman Bharat - PM-JAY Maharashtra, Pradhan Mantri Matru Vandana Yojana |
| Higher and Technical Education Department | 7 | Rajarshi Chhatrapati Shahu Maharaj Shikshan Shulkh Shishyavrutti Yojna (EBC), Dr. Panjabrao Deshmukh Hostel Maintenance Allowance, Post-Matric Scholarship for OBC Students |
| Tribal Development Department | 6 | Birsa Munda Adivasi Khavti Anudan Yojana, Pandit Deendayal Upadhyay Swayam Yojana, Adivasi Gharkul Yojana |
| Housing Department / Urban Development | 8 | Pradhan Mantri Awas Yojana (Urban & Gramin), Ramai Awas Gharkul Yojana, Shabari Gharkul Yojana |
| Urban Local Bodies (BMC, PMC, PCMC, TMC) | 10 | PCMC Divyang Kalyan Arthik Sahayya, PMC Magasvargiya Shetkari Anudan, BMC Mahila Self Help Group Grant, TMC Senior Citizen Health Support |
| Other State & Central Departments | 9 | IGNOAPS (National Old Age Pension), IGNWPS (Widow Pension), IGNDPS (Disability Pension), Atal Pension Yojana, Sukanya Samriddhi Yojana |
| **Total Canonical Schemes** | **75** | **100% Comprehensive Coverage** |

---

### 3. Canonical Data Model Specification

Every scheme entry implements the Pydantic `CanonicalSchemeRecord` schema:

```python
class CanonicalSchemeRecord(BaseModel):
    canonical_scheme_id: str
    official_scheme_name: str
    english_name: str
    marathi_name: str
    hindi_name: str
    responsible_department: str
    jurisdiction_scope: Literal["MAHARASHTRA_STATE", "CENTRAL", "MUNICIPAL_CORPORATION", "MUNICIPAL_COUNCIL", "GRAM_PANCHAYAT"]
    included_local_bodies: list[str] = Field(default_factory=list)
    scheme_objective: str
    benefit_description: str
    benefits: list[str]
    required_documents: list[str]
    government_source_references: list[GovernmentSourceReference]
    official_application_url: str
    publication_status: Literal["VERIFIED_FOR_INFORMATION", "OFFICIAL_INFORMATION_RECORDED", "DOCUMENT_REQUIREMENTS_NOT_VERIFIED"]
    last_source_verification_date: str
    faqs: list[SchemeFAQ] = Field(default_factory=list)
```

Each trilingual FAQ (`SchemeFAQ`) contains:
- `question_en`, `question_mr`, `question_hi`: Question in English, Marathi, and Hindi.
- `answer_en`, `answer_mr`, `answer_hi`: Authoritative answer based on official GRs and departmental FAQs.

---

### 4. Authoritative Source & Legal Citation Standards

All scheme entries must cite genuine, published legal sources. Fabricated scheme numbers, fake GR dates, or synthetic benefit amounts are strictly prohibited.

#### Example 1: Mukhyamantri Majhi Ladki Bahin Yojana
- **Scheme ID:** `candidate-majhi-ladki-bahin`
- **Department:** Women and Child Development Department (महिला व बाल विकास विभाग)
- **Governing GR:** शासन निर्णय क्र. मालाबायो-२०२४/प्र.क्र.८८/कार्या-६, दिनांक २८ जून २०२४ आणि सुधारित शासन निर्णय दिनांक ०३ जुलै २०२४.
- **Benefit:** Direct Benefit Transfer (DBT) of ₹1,500 per month directly into applicant's Aadhaar-linked bank account.
- **Key Eligibility:** Female resident of Maharashtra aged 21 to 65 years, annual family income not exceeding ₹2,50,000, not an income-tax payee, no family member in permanent government employment or owning a 4-wheeler (excluding tractors).
- **Official Application Channel:** Nari Shakti Doot Mobile App / `https://ladkibahin.maharashtra.gov.in`

#### Example 2: Mahatma Jyotirao Phule Jan Arogya Yojana (MJPJAY)
- **Scheme ID:** `canonical-mjpjay`
- **Department:** Public Health Department (सार्वजनिक आरोग्य विभाग)
- **Governing GR:** शासन निर्णय क्र. राआधो-२०२३/प्र.क्र.२४५/आरोग्य-६, दिनांक २८ जुलै २०२३.
- **Benefit:** Cashless medical coverage up to ₹5,00,000 per family per year across 1,356 identified surgical and medical procedures in empanelled network hospitals.
- **Key Eligibility:** All ration card holding families in Maharashtra (Yellow, Orange, White cards) without income ceiling under universalized coverage.
- **Official Application Channel:** Empanelled Network Hospitals through Arogyamitra / `https://www.jeevandayee.gov.in`

#### Example 3: Sanjay Gandhi Niradhar Anudan Yojana (SGNAY)
- **Scheme ID:** `candidate-sanjay-gandhi-niradhar-anudan`
- **Department:** Social Justice and Special Assistance Department (सामाजिक न्याय व विशेष सहाय्य विभाग)
- **Governing GR:** शासन निर्णय क्र. संगाने-२०१९/प्र.क्र.१३५/विशेष सहाय्य-१, दिनांक २० ऑगस्ट २०१९.
- **Benefit:** Financial assistance of ₹1,500 per month (single beneficiary) or ₹2,000 per month (beneficiary with two or more children).
- **Key Eligibility:** Destitute persons aged under 65, widows, blind, disabled (40%+ disability), patients suffering from severe illnesses (cancer, TB, AIDS), annual family income up to ₹21,000 (relaxed to ₹50,000 in specific categories), minimum 15 years domicile in Maharashtra.
- **Official Application Channel:** Aaple Sarkar Portal / Tahsildar Sanjay Gandhi Yojana Branch (`https://aaplesarkar.mahaonline.gov.in`)

---

### 5. Multilingual Representation Engine

To preserve linguistic accessibility across all communities in Maharashtra:
1. **Marathi (मराठी):** Primary administrative language used on official Government Resolutions, Aaple Sarkar forms, and Tahsildar offices.
2. **English:** International and technical standard ensuring interoperability and developer integration.
3. **Hindi (हिंदी):** Accessible secondary language widely used across municipal corporations and non-Marathi speaking migrant workers residing in Maharashtra.

Language switching is instantaneous across all scheme views, modal factsheets, and document requirements without requiring page reloads or network latency.
