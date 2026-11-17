from pathlib import Path

def fix():
    p = Path(r"c:\Users\Admin\Downloads\scheme-navigator\scheme-navigator\scratch\build_full_database.py")
    c = p.read_text(encoding="utf-8")
    c = c.replace("'field': 'social_category'", "'field': 'caste_category'")
    c = c.replace("'field': 'is_bpl'", "'field': 'bpl'")
    c = c.replace("'field': 'is_farmer'", "'field': 'has_land'")
    c = c.replace('"field": "social_category"', '"field": "caste_category"')
    c = c.replace('"field": "is_bpl"', '"field": "bpl"')
    c = c.replace('"field": "is_farmer"', '"field": "has_land"')
    p.write_text(c, encoding="utf-8")
    print("Fixed field names in build_full_database.py")

if __name__ == "__main__":
    fix()
