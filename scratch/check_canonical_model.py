from scheme_navigator.source_registry.models import CanonicalSchemeRecord
import json

data = json.loads(open("data/source_registry/canonical_schemes.json", encoding="utf-8").read())
print("Total records:", len(data))
first = CanonicalSchemeRecord.model_validate(data[0])
print("Record 0 validated successfully!")
print("ID:", first.canonical_scheme_id)
print("Fields on CanonicalSchemeRecord:")
for f in sorted(list(first.model_fields.keys())):
    val = getattr(first, f)
    print(f"  {f}: {type(val).__name__} = {repr(val)[:60]}")
