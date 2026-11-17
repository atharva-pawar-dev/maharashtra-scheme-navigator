from pathlib import Path
import json

candidates_dir = Path("data/candidates")
if candidates_dir.is_dir():
    print("Candidates files:", [p.name for p in candidates_dir.glob("*.json")])
    for p in candidates_dir.glob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                print(f"  {p.name}: scheme_id={d.get('scheme_id')}, rule_status={d.get('rule_status')}, pub_auth={d.get('publication_authorized')}")
            elif isinstance(d, list):
                print(f"  {p.name}: list of {len(d)} items")
        except Exception as e:
            print(f"  {p.name}: error {e}")

demo_schemes = json.loads(Path("data/demo/schemes.json").read_text(encoding="utf-8"))
print("Demo schemes count:", len(demo_schemes))
for s in demo_schemes:
    print(f"  demo scheme_id={s.get('scheme_id')}, name={s.get('name')}, rule_status={s.get('rule_status')}, pub_auth={s.get('publication_authorized')}")
