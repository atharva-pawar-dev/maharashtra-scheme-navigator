import json
from pathlib import Path

data = json.loads(Path("data/source_registry/canonical_schemes.json").read_text(encoding="utf-8"))

for s in data[9:20]:
    print("ID:", s.get("canonical_scheme_id"))
    print("  age:", s.get("age_requirements"))
    print("  gender:", s.get("gender_conditions"))
    print("  income:", s.get("family_income_requirements"))
    print("  social:", s.get("social_category_requirements"))
    print("  geo:", s.get("geographic_applicability"))
    print("  other:", s.get("other_eligibility_conditions"))
    print("  docs:", s.get("required_documents"))
    print()
