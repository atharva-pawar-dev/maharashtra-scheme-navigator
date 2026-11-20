import json

with open("data/catalogue/schemes.json", "r", encoding="utf-8") as f:
    schemes = json.load(f)

for s in schemes[:5]:
    print(s["scheme_id"], "-> verification:", s.get("verification"), "substantive_criteria_count:", s.get("substantive_criteria_count"), "eligibility_incomplete:", s.get("eligibility_incomplete"))

v_types = {s.get("verification", {}).get("tier") for s in schemes if isinstance(s.get("verification"), dict)}
print("\nVerification tiers:", v_types)
for s in schemes:
    if isinstance(s.get("verification"), dict):
        tier = s["verification"].get("tier")
        print(f"Tier: {tier} -> {s['scheme_id']}")
