import json

with open("data/catalogue/schemes.json", "r", encoding="utf-8") as f:
    schemes = json.load(f)

s = schemes[0]
print("Scheme:", s["scheme_id"])
print("Name:", s["name_en"], "/", s["name_mr"])
print("Eligibility criteria count:", len(s.get("eligibility", [])))
for c in s.get("eligibility", []):
    print(" - Condition:", c.get("condition_id"), "| Field:", c.get("field"), "| Op:", c.get("operator"), "| Val:", c.get("value"), "| Verbatim quote:", c.get("verbatim_quote"))
print("Exclusions count:", len(s.get("exclusions", [])))
for ex in s.get("exclusions", []):
    print(" - Exclusion:", ex.get("exclusion_id"), "| Desc:", ex.get("description"), "| Rule:", ex.get("rule_condition"))
print("Sources count:", len(s.get("sources", [])))
for src in s.get("sources", []):
    print(" - Source:", src.get("source_id"), "| URL:", src.get("url"), "| SHA256:", src.get("evidence_sha256")[:16])
