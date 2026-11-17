import json
from pathlib import Path
from scheme_navigator.source_registry.models import CanonicalSchemeRecord
from scheme_navigator.domain.models import Scheme, RuleNode, SourceReference
from datetime import datetime, timezone

data = json.loads(Path("data/source_registry/canonical_schemes.json").read_text(encoding="utf-8"))
print(f"Loaded {len(data)} canonical schemes.")

# Let's inspect the candidate schemes in data/candidates/candidate_schemes.json
cand_data = json.loads(Path("data/candidates/candidate_schemes.json").read_text(encoding="utf-8"))
print(f"Loaded {len(cand_data)} candidate schemes with rules.")
for c in cand_data:
    print(f"  {c['scheme_id']}: rule={c['eligibility_rule']['op']} with {len(c['eligibility_rule']['children'])} children, evidence={len(c.get('evidence', []))}")
