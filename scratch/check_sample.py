import json

with open("data/catalogue/schemes.json", "r", encoding="utf-8") as f:
    schemes = json.load(f)

s = schemes[0]
print("Eligibility sample:", json.dumps(s.get("eligibility", [])[:2], indent=2, ensure_ascii=False))
print("Exclusions sample:", json.dumps(s.get("exclusions", [])[:2], indent=2, ensure_ascii=False))
print("Sources sample:", json.dumps(s.get("sources", [])[:2], indent=2, ensure_ascii=False))
