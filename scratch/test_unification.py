import json
from pathlib import Path
from scheme_navigator.source_registry.registry import SourceRegistry
from scheme_navigator.source_registry.models import CanonicalSchemeRecord
from scheme_navigator.domain.models import Scheme, RuleNode, SourceReference
from datetime import datetime, timezone

reg = SourceRegistry()
canonical_records = reg.list_canonical_schemes()
print(f"Total canonical records from registry: {len(canonical_records)}")

# Let's inspect candidate schemes and demo schemes
demo_schemes = json.loads(Path("data/demo/schemes.json").read_text(encoding="utf-8"))
demo_map = {s["scheme_id"]: s for s in demo_schemes}

candidate_schemes = json.loads(Path("data/candidates/candidate_schemes.json").read_text(encoding="utf-8"))
cand_map = {s["scheme_id"]: s for s in candidate_schemes}
print("Demo map keys:", list(demo_map.keys()))
print("Cand map keys:", list(cand_map.keys()))
