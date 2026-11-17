import json
from pathlib import Path

path = Path("data/source_registry/canonical_schemes.json")
data = json.loads(path.read_text(encoding="utf-8"))
print(f"Total canonical schemes in JSON: {len(data)}")

statuses = {}
categories = {}
has_rule = 0
has_evidence = 0
publication_statuses = {}

for s in data:
    st = s.get("publication_status") or s.get("status")
    publication_statuses[st] = publication_statuses.get(st, 0) + 1
    cat = s.get("category_code") or s.get("state_central_joint_classification")
    categories[cat] = categories.get(cat, 0) + 1
    if s.get("eligibility_rule") or s.get("eligibility_criteria"):
        has_rule += 1
    if s.get("sources") or s.get("source_documents"):
        has_evidence += 1

print("Publication statuses:", publication_statuses)
print("Categories sample:", list(categories.items())[:5])
print(f"Has rule: {has_rule}, Has evidence: {has_evidence}")

# Check first scheme structure
s0 = data[0]
print("Keys in scheme 0:", list(s0.keys()))
print("Scheme 0 ID:", s0.get("scheme_id"))
print("Scheme 0 name:", s0.get("official_scheme_name"))
print("Scheme 0 publication_status:", s0.get("publication_status"))
print("Scheme 0 eligibility_criteria:", s0.get("eligibility_criteria"))
print("Scheme 0 eligibility_rule AST present?", "eligibility_rule" in s0)
