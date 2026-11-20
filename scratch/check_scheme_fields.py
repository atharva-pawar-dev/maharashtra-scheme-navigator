import json

with open("data/catalogue/schemes.json", "r", encoding="utf-8") as f:
    schemes = json.load(f)

s = schemes[0]
print("Keys in scheme 0:", list(s.keys()))
for k, v in s.items():
    if k in ["scheme_id", "tier", "verification_tier", "status", "publication_authorized", "verification_status"]:
        print(f"{k}: {v}")
print("\nUnique values of tier/status across schemes:")
for field in ["tier", "verification_tier", "status", "verification_status"]:
    vals = {s.get(field) for s in schemes if field in s}
    print(f"{field}: {vals}")
