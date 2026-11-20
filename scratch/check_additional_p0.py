import json

with open("data/catalogue/schemes.json", "r", encoding="utf-8") as f:
    schemes = json.load(f)

sids = [
    "candidate-post-matric-obc-girls-professional",
    "candidate-tuition-fees-obc-girls",
    "scheme-majhi-kanya-bhagyashree",
    "scheme-mukhyamantri-bal-seva",
    "scheme-pm-svanidhi",
    "scheme-pmay-gramin",
    "scheme-pm-kusum-saur-pump",
    "scheme-swadhar-hostel-dbt"
]

for s in schemes:
    if s["scheme_id"] in sids:
        print("="*50)
        print("ID:", s["scheme_id"])
        print("Name:", s.get("name_en"))
        print("Verification status:", s.get("verification", {}).get("status"))
        print("Substantive criteria count:", s.get("substantive_criteria_count"))
        print("Eligibility criteria:", len(s.get("eligibility", [])))
