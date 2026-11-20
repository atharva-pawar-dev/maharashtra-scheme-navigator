import json

with open("data/catalogue/schemes.json", "r", encoding="utf-8") as f:
    schemes = json.load(f)

print(f"Total schemes in catalogue: {len(schemes)}")
tier_a = [s for s in schemes if s.get("verification_status") == "verified_primary"]
print(f"Tier A schemes: {len(tier_a)}")
for i, s in enumerate(tier_a):
    dept = s.get("department", {}).get("en") if isinstance(s.get("department"), dict) else s.get("department")
    title = s.get("title", {}).get("en") if isinstance(s.get("title"), dict) else s.get("title")
    criteria = len(s.get("eligibility_criteria", []))
    sources = len(s.get("sources", []))
    print(f"{i+1:2d}. {s['scheme_id']}: {title} | Dept: {dept} | Crit: {criteria} | Sources: {sources}")
