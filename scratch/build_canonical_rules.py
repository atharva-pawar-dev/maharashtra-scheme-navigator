import json
import re
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone

data = json.loads(Path("data/source_registry/canonical_schemes.json").read_text(encoding="utf-8"))
cand_schemes = {s["scheme_id"]: s for s in json.loads(Path("data/candidates/candidate_schemes.json").read_text(encoding="utf-8"))}
demo_schemes = {s["scheme_id"]: s for s in json.loads(Path("data/demo/schemes.json").read_text(encoding="utf-8"))}

def parse_income(text):
    if not text:
        return None
    m = re.search(r"(\d[\d,]+)", text.replace("₹", "").replace(",", ""))
    if m:
        try:
            val = int(m.group(1))
            if "lakh" in text.lower():
                val = val * 100_000
            return val
        except Exception:
            pass
    if "2.5 lakh" in text.lower() or "2,50,000" in text:
        return 250000
    if "8 lakh" in text.lower() or "8,00,000" in text:
        return 800000
    if "1.5 lakh" in text.lower() or "1,50,000" in text:
        return 150000
    if "2 lakh" in text.lower() or "2,00,000" in text:
        return 200000
    if "24,000" in text:
        return 24000
    return None

def parse_age(text):
    if not text:
        return None, None
    m_range = re.search(r"(\d+)\s*-\s*(\d+)", text)
    if m_range:
        return int(m_range.group(1)), int(m_range.group(2))
    m_above = re.search(r"(\d+)\s*(?:years?\s*(?:and|&)\s*above|\+)", text, re.IGNORECASE)
    if m_above:
        return int(m_above.group(1)), None
    return None, None

built_rules = 0
for s in data:
    cid = s["canonical_scheme_id"]
    if cid in demo_schemes:
        rule = demo_schemes[cid]["eligibility_rule"]
        built_rules += 1
    elif cid in cand_schemes:
        rule = cand_schemes[cid]["eligibility_rule"]
        built_rules += 1
    else:
        # Build rule from criteria fields
        children = []
        # State
        children.append({
            "op": "eq", "field": "resident_state", "value": "maharashtra",
            "condition_id": f"c_{cid.replace('-', '_')}_state", "is_hard_statutory": True
        })
        # Gender
        gender = s.get("gender_conditions")
        if gender == "FEMALE_ONLY":
            children.append({
                "op": "eq", "field": "gender", "value": "female",
                "condition_id": f"c_{cid.replace('-', '_')}_gender", "is_hard_statutory": True
            })
        elif gender == "MALE_ONLY":
            children.append({
                "op": "eq", "field": "gender", "value": "male",
                "condition_id": f"c_{cid.replace('-', '_')}_gender", "is_hard_statutory": True
            })
        # Income
        inc = parse_income(s.get("family_income_requirements"))
        if inc:
            children.append({
                "op": "lte", "field": "annual_family_income", "value": inc,
                "condition_id": f"c_{cid.replace('-', '_')}_income", "is_hard_statutory": False
            })
        # Age
        min_age, max_age = parse_age(s.get("age_requirements"))
        if min_age is not None:
            children.append({
                "op": "gte", "field": "age", "value": min_age,
                "condition_id": f"c_{cid.replace('-', '_')}_min_age", "is_hard_statutory": True
            })
        if max_age is not None:
            children.append({
                "op": "lte", "field": "age", "value": max_age,
                "condition_id": f"c_{cid.replace('-', '_')}_max_age", "is_hard_statutory": True
            })
        # Social
        soc = s.get("social_category_requirements")
        if soc and soc not in {"ALL", "OPEN"}:
            if soc == "SC":
                children.append({"op": "eq", "field": "caste_category", "value": "SC", "condition_id": f"c_{cid.replace('-', '_')}_caste", "is_hard_statutory": True})
            elif soc == "ST":
                children.append({"op": "eq", "field": "caste_category", "value": "ST", "condition_id": f"c_{cid.replace('-', '_')}_caste", "is_hard_statutory": True})
            elif soc in {"OBC", "VJNT", "SBC"}:
                children.append({"op": "eq", "field": "caste_category", "value": soc, "condition_id": f"c_{cid.replace('-', '_')}_caste", "is_hard_statutory": True})
        # Land
        if "farmer" in str(s.get("beneficiary_category", "")).lower() or "agriculture" in str(s.get("responsible_department", "")).lower():
            if "land" in str(s.get("required_documents", [])).lower() or "7/12" in str(s.get("required_documents", [])).lower():
                children.append({"op": "eq", "field": "has_land", "value": True, "condition_id": f"c_{cid.replace('-', '_')}_land", "is_hard_statutory": False})
        # Disability
        if "disability" in cid or "divyang" in cid:
            children.append({"op": "eq", "field": "has_disability", "value": True, "condition_id": f"c_{cid.replace('-', '_')}_disability", "is_hard_statutory": True})
            children.append({"op": "gte", "field": "disability_percentage", "value": 40, "condition_id": f"c_{cid.replace('-', '_')}_dispct", "is_hard_statutory": True})
        # Student
        if "scholarship" in cid or "tuition" in cid or "student" in str(s.get("beneficiary_category", "")).lower():
            children.append({"op": "eq", "field": "is_student", "value": True, "condition_id": f"c_{cid.replace('-', '_')}_student", "is_hard_statutory": True})

        rule = {"op": "all", "children": children}
        built_rules += 1

print(f"Total schemes with rules: {built_rules}")
