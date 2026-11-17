import json
from pathlib import Path

path = Path("data/candidates/candidate_schemes.json")
data = json.loads(path.read_text(encoding="utf-8"))
print("Candidates count:", len(data))
for s in data:
    print("Scheme ID:", s.get("scheme_id"))
    print("Name:", s.get("name"))
    print("Rule status:", s.get("rule_status"))
    print("Publication authorized:", s.get("publication_authorized"))
    print("Rule:", json.dumps(s.get("eligibility_rule"), indent=2)[:300])
    print("Evidence count:", len(s.get("evidence", [])))
    print("---")
