"""Canonical Profile Vocabulary Registry for Maharashtra Scheme Navigator.

Single source of truth defining the standard attributes of a citizen profile,
their allowed values, units, Devanagari labels, and validation constraints.
Derived strictly from statutory Maharashtra welfare schemes and Government Resolutions.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class FieldDataType(StrEnum):
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    ENUM = "enum"
    DATE = "date"
    LIST = "list"


class CasteCategory(StrEnum):
    SC = "SC"
    ST = "ST"
    VJ = "VJ"
    NT_B = "NT-B"
    NT_C = "NT-C"
    NT_D = "NT-D"
    SBC = "SBC"
    OBC = "OBC"
    SEBC = "SEBC"
    EWS = "EWS"
    OPEN = "Open"


class MaritalStatus(StrEnum):
    SINGLE = "single"
    MARRIED = "married"
    WIDOWED = "widowed"
    DIVORCED = "divorced"
    ABANDONED = "abandoned"
    DESERTED = "deserted"


class RationCardType(StrEnum):
    AAY = "aay"              # Antyodaya Anna Yojana (Yellow)
    BPL_YELLOW = "bpl_yellow" # Below Poverty Line (Yellow)
    APL_ORANGE = "apl_orange" # Above Poverty Line (Orange)
    WHITE = "white"           # Above ₹1,00,000 income (White)
    NONE = "none"


class AreaType(StrEnum):
    RURAL = "rural"
    URBAN = "urban"
    SEMI_URBAN = "semi_urban"


class VocabularyField(BaseModel):
    name: str = Field(..., description="Unique slug of the profile field")
    data_type: FieldDataType
    label_en: str
    label_mr: str
    description: str
    allowed_values: List[str] | None = None
    min_value: float | None = None
    max_value: float | None = None
    unit: str | None = None
    is_substantive: bool = True  # If False (e.g. resident_state, nationality), does not count toward substantive criteria threshold


# The Canonical Profile Vocabulary Registry
CANONICAL_PROFILE_VOCABULARY: Dict[str, VocabularyField] = {
    # Non-Substantive Jurisdiction / Geographic Anchors
    "resident_state": VocabularyField(
        name="resident_state",
        data_type=FieldDataType.STRING,
        label_en="Resident State",
        label_mr="रहिवासी राज्य",
        description="State of permanent residence",
        allowed_values=["maharashtra", "other"],
        is_substantive=False,
    ),
    "nationality": VocabularyField(
        name="nationality",
        data_type=FieldDataType.STRING,
        label_en="Nationality",
        label_mr="राष्ट्रीयत्व",
        description="Country of citizenship",
        allowed_values=["indian", "other"],
        is_substantive=False,
    ),

    # Demographics & Identity
    "age": VocabularyField(
        name="age",
        data_type=FieldDataType.INTEGER,
        label_en="Age (Years)",
        label_mr="वय (वर्षे)",
        description="Age of citizen in completed years as of evaluation date",
        min_value=0,
        max_value=120,
        unit="years",
        is_substantive=True,
    ),
    "date_of_birth": VocabularyField(
        name="date_of_birth",
        data_type=FieldDataType.DATE,
        label_en="Date of Birth",
        label_mr="जन्मतारीख",
        description="Exact date of birth for cut-off date calculations",
        is_substantive=True,
    ),
    "gender": VocabularyField(
        name="gender",
        data_type=FieldDataType.ENUM,
        label_en="Gender",
        label_mr="लिंग",
        description="Gender of the citizen",
        allowed_values=["female", "male", "transgender", "other"],
        is_substantive=True,
    ),
    "marital_status": VocabularyField(
        name="marital_status",
        data_type=FieldDataType.ENUM,
        label_en="Marital Status",
        label_mr="वैवाहिक स्थिती",
        description="Legal and marital status",
        allowed_values=[m.value for m in MaritalStatus],
        is_substantive=True,
    ),
    "domicile_years_in_maharashtra": VocabularyField(
        name="domicile_years_in_maharashtra",
        data_type=FieldDataType.INTEGER,
        label_en="Years of Domicile in Maharashtra",
        label_mr="महाराष्ट्रातील वास्तव्याची वर्षे",
        description="Continuous years of residence in Maharashtra (commonly 15 years required)",
        min_value=0,
        max_value=120,
        unit="years",
        is_substantive=True,
    ),
    "district": VocabularyField(
        name="district",
        data_type=FieldDataType.STRING,
        label_en="District",
        label_mr="जिल्हा",
        description="Administrative district in Maharashtra (36 districts)",
        is_substantive=True,
    ),
    "area_type": VocabularyField(
        name="area_type",
        data_type=FieldDataType.ENUM,
        label_en="Area Type",
        label_mr="परिसर प्रकार",
        description="Rural or urban classification",
        allowed_values=[a.value for a in AreaType],
        is_substantive=True,
    ),
    "municipal_corporation": VocabularyField(
        name="municipal_corporation",
        data_type=FieldDataType.STRING,
        label_en="Municipal Corporation",
        label_mr="महानगरपालिका",
        description="Urban Local Body ID/Name for municipal-specific welfare",
        is_substantive=True,
    ),

    # Financial & Economic Criteria
    "annual_family_income": VocabularyField(
        name="annual_family_income",
        data_type=FieldDataType.INTEGER,
        label_en="Annual Family Income",
        label_mr="वार्षिक कौटुंबिक उत्पन्न",
        description="Total annual family income from all sources as certified by revenue authority",
        min_value=0,
        max_value=100_000_000,
        unit="INR",
        is_substantive=True,
    ),
    "ration_card_type": VocabularyField(
        name="ration_card_type",
        data_type=FieldDataType.ENUM,
        label_en="Ration Card Category",
        label_mr="रेशन कार्ड प्रकार",
        description="Targeted public distribution food security card",
        allowed_values=[r.value for r in RationCardType],
        is_substantive=True,
    ),
    "bpl": VocabularyField(
        name="bpl",
        data_type=FieldDataType.BOOLEAN,
        label_en="Below Poverty Line (BPL)",
        label_mr="दारिद्र्यरेषेखालील (BPL)",
        description="Whether listed in official state BPL census / SECC survey",
        is_substantive=True,
    ),
    "income_tax_payer": VocabularyField(
        name="income_tax_payer",
        data_type=FieldDataType.BOOLEAN,
        label_en="Income Tax Payer in Family",
        label_mr="कुटुंबात आयकर भरणारी व्यक्ती आहे का",
        description="Statutory exclusion criterion for major DBT schemes (e.g. Ladki Bahin)",
        is_substantive=True,
    ),
    "govt_employee_in_family": VocabularyField(
        name="govt_employee_in_family",
        data_type=FieldDataType.BOOLEAN,
        label_en="Regular Government Employee in Family",
        label_mr="कुटुंबात नियमित सरकारी कर्मचारी/पेन्शनधारक आहे का",
        description="Statutory exclusion for welfare income transfers",
        is_substantive=True,
    ),
    "owns_four_wheeler": VocabularyField(
        name="owns_four_wheeler",
        data_type=FieldDataType.BOOLEAN,
        label_en="Family Owns Four-Wheeler (Excluding Tractor)",
        label_mr="कुटुंबाच्या नावावर चारचाकी वाहन आहे का (ट्रॅक्टर वगळून)",
        description="Asset exclusion criterion under Ladki Bahin and social pensions",
        is_substantive=True,
    ),
    "bank_account_aadhaar_seeded": VocabularyField(
        name="bank_account_aadhaar_seeded",
        data_type=FieldDataType.BOOLEAN,
        label_en="Aadhaar-Seeded Bank Account (DBT Enabled)",
        label_mr="आधार जोडलेले बँक खाते (DBT सक्षम)",
        description="Whether applicant possesses active bank account linked to NPCI Aadhaar mapper",
        is_substantive=True,
    ),
    "aadhaar_linked_bank_account": VocabularyField(
        name="aadhaar_linked_bank_account",
        data_type=FieldDataType.BOOLEAN,
        label_en="Aadhaar-Seeded Bank Account (DBT Enabled)",
        label_mr="आधार जोडलेले बँक खाते (DBT सक्षम)",
        description="Whether applicant possesses active bank account linked to NPCI Aadhaar mapper",
        is_substantive=True,
    ),
    "residence_years": VocabularyField(
        name="residence_years",
        data_type=FieldDataType.INTEGER,
        label_en="Years of Domicile / Residence in Maharashtra",
        label_mr="महाराष्ट्रातील वास्तव्याची वर्षे",
        description="Continuous years of residence in Maharashtra",
        min_value=0,
        max_value=120,
        unit="years",
        is_substantive=True,
    ),
    "has_land": VocabularyField(
        name="has_land",
        data_type=FieldDataType.BOOLEAN,
        label_en="Owns Agricultural Land",
        label_mr="स्वतःच्या नावावर शेतीजमीन आहे",
        description="Whether applicant possesses agricultural landholding",
        is_substantive=True,
    ),
    "landholding_hectares": VocabularyField(
        name="landholding_hectares",
        data_type=FieldDataType.FLOAT,
        label_en="Landholding (Hectares)",
        label_mr="शेतीजमीन धारणा (हेक्टर)",
        description="Area of cultivable landholding in hectares",
        min_value=0.0,
        max_value=10_000.0,
        unit="hectares",
        is_substantive=True,
    ),
    "receives_other_scheme_benefit": VocabularyField(
        name="receives_other_scheme_benefit",
        data_type=FieldDataType.BOOLEAN,
        label_en="Receives Similar Financial Benefit (>₹1500/month)",
        label_mr="इतर योजनेतून ₹१५०० पेक्षा जास्त लाभ मिळतो का",
        description="Exclusion criterion to prevent double-dipping across parallel cash transfers",
        is_substantive=True,
    ),

    # Social Category & Vulnerability
    "caste_category": VocabularyField(
        name="caste_category",
        data_type=FieldDataType.ENUM,
        label_en="Social Category / Caste",
        label_mr="सामाजिक प्रवर्ग / जात",
        description="Recognized social category in Maharashtra",
        allowed_values=[c.value for c in CasteCategory],
        is_substantive=True,
    ),
    "minority_status": VocabularyField(
        name="minority_status",
        data_type=FieldDataType.STRING,
        label_en="Religious Minority Community",
        label_mr="अल्पसंख्याक समुदाय",
        description="Muslim, Christian, Buddhist, Sikh, Parsi, Jain, or Jewish community membership",
        allowed_values=["muslim", "christian", "buddhist", "sikh", "parsi", "jain", "jewish", "none"],
        is_substantive=True,
    ),
    "is_widow": VocabularyField(
        name="is_widow",
        data_type=FieldDataType.BOOLEAN,
        label_en="Widowed Woman",
        label_mr="विधवा महिला",
        description="Special targeted category under SGNAY and Indira Gandhi schemes",
        is_substantive=True,
    ),
    "is_destitute": VocabularyField(
        name="is_destitute",
        data_type=FieldDataType.BOOLEAN,
        label_en="Destitute / Niradhar",
        label_mr="निराधार व्यक्ती",
        description="Person with no source of livelihood or supporting family",
        is_substantive=True,
    ),
    "has_disability": VocabularyField(
        name="has_disability",
        data_type=FieldDataType.BOOLEAN,
        label_en="Person with Disability (Divyang)",
        label_mr="दिव्यांग व्यक्ती",
        description="Whether citizen has recognized benchmark disability",
        is_substantive=True,
    ),
    "disability_percentage": VocabularyField(
        name="disability_percentage",
        data_type=FieldDataType.INTEGER,
        label_en="Disability Percentage",
        label_mr="दिव्यांगत्वाची टक्केवारी",
        description="Certified benchmark disability percentage (usually >= 40% or >= 80%)",
        min_value=0,
        max_value=100,
        unit="percentage",
        is_substantive=True,
    ),
    "disability_type": VocabularyField(
        name="disability_type",
        data_type=FieldDataType.STRING,
        label_en="Disability Category",
        label_mr="दिव्यांगत्वाचा प्रकार",
        description="Locomotor, visual, hearing, intellectual, mental illness, or multiple disability",
        is_substantive=True,
    ),

    # Occupation & Agriculture
    "occupation": VocabularyField(
        name="occupation",
        data_type=FieldDataType.STRING,
        label_en="Occupation",
        label_mr="व्यवसाय",
        description="Primary occupation (farmer, agricultural laborer, artisan, student, unemployed)",
        is_substantive=True,
    ),
    "is_farmer": VocabularyField(
        name="is_farmer",
        data_type=FieldDataType.BOOLEAN,
        label_en="Farmer (Landholding)",
        label_mr="शेतकरी (जमीनधारक)",
        description="Whether citizen or family holds agricultural land registered in 7/12 extract",
        is_substantive=True,
    ),
    "land_holding_hectares": VocabularyField(
        name="land_holding_hectares",
        data_type=FieldDataType.FLOAT,
        label_en="Agricultural Landholding (Hectares)",
        label_mr="शेतीजमीन धारणा (हेक्टर)",
        description="Area of cultivable landholding (small/marginal farmer threshold <= 2.0 ha)",
        min_value=0.0,
        max_value=10_000.0,
        unit="hectares",
        is_substantive=True,
    ),

    # Education
    "is_student": VocabularyField(
        name="is_student",
        data_type=FieldDataType.BOOLEAN,
        label_en="Currently Enrolled Student",
        label_mr="सध्या शिक्षण घेत असलेला विद्यार्थी",
        description="Enrolled in recognized school, college, or university",
        is_substantive=True,
    ),
    "education_level": VocabularyField(
        name="education_level",
        data_type=FieldDataType.STRING,
        label_en="Education Level / Course",
        label_mr="शिक्षणाची पातळी / अभ्यासक्रम",
        description="Class 10, Class 12, Diploma, Undergraduate, Postgraduate, Professional Course",
        is_substantive=True,
    ),
    "institution_type": VocabularyField(
        name="institution_type",
        data_type=FieldDataType.STRING,
        label_en="Institution Type",
        label_mr="संस्थेचा प्रकार",
        description="Government, Government-Aided, Private Unaided, Autonomous",
        allowed_values=["government", "government_aided", "private_unaided", "autonomous"],
        is_substantive=True,
    ),
}


def is_field_substantive(field_name: str) -> bool:
    """Return whether a profile field is a substantive eligibility condition.
    
    Residency and nationality alone are NOT substantive criteria under Prime Directive 2.
    """
    vocab = CANONICAL_PROFILE_VOCABULARY.get(field_name)
    if vocab is not None:
        return vocab.is_substantive
    # Unknown fields default to substantive only if not state/nationality
    return field_name not in ("resident_state", "nationality", "country")
