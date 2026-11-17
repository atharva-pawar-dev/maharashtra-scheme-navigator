import json

data = json.loads(open("data/source_registry/canonical_schemes.json", encoding="utf-8").read())
print(f"Total: {len(data)}")
for i, s in enumerate(data):
    cid = s.get("canonical_scheme_id")
    status = s.get("publication_status")
    name = s.get("official_scheme_name")
    dep = s.get("responsible_department")
    print(f"{i+1:2d}. {cid:40s} | {status:22s} | {name[:45]}")
