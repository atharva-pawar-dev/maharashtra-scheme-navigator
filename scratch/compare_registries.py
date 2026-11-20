import json

with open("data/source_registry/canonical_schemes.json", "r", encoding="utf-8") as f:
    sr_schemes = json.load(f)

with open("data/catalogue/schemes.json", "r", encoding="utf-8") as f:
    cat_schemes = json.load(f)

print(f"Source registry schemes: {len(sr_schemes)}")
print(f"Catalogue schemes: {len(cat_schemes)}")

sr_ids = {s["canonical_scheme_id"] for s in sr_schemes}
cat_ids = {s["scheme_id"] for s in cat_schemes}

print(f"Overlap: {len(sr_ids.intersection(cat_ids))}")
print(f"Only in SR: {sr_ids - cat_ids}")
print(f"Only in Cat: {cat_ids - sr_ids}")
