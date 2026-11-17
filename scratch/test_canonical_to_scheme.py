from scheme_navigator.source_registry.models import CanonicalSchemeRecord
from scheme_navigator.domain.models import Scheme, RuleNode, SourceReference
from datetime import datetime, timezone
import json

raw_list = json.loads(open("data/source_registry/canonical_schemes.json", encoding="utf-8").read())

schemes = []
for item in raw_list:
    rec = CanonicalSchemeRecord.model_validate(item)
    # Check if we can construct a Scheme or view
    cid = rec.canonical_scheme_id
    print(f"Validated {cid}")

print(f"Successfully validated all {len(raw_list)} records!")
