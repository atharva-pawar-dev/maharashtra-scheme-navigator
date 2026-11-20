import json

with open("data/catalogue/schemes.json", "r", encoding="utf-8") as f:
    schemes = json.load(f)

for s in schemes:
    ex_count = len(s.get("exclusions", []))
    crit_count = len(s.get("eligibility", []))
    v_stat = s.get("verification", {}).get("status")
    if v_stat == "verified_primary" or ex_count > 0:
        print(f"{s['scheme_id']}: status={v_stat}, crit={crit_count}, exclusions={ex_count}")
