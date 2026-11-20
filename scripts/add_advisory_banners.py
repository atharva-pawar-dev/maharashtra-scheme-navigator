import json
from pathlib import Path

p = Path("data/catalogue/schemes.json")
schemes = json.loads(p.read_text(encoding="utf-8"))
banner = {
    "en": "Informational Listing: This scheme has been identified from official Government of Maharashtra records but has not yet undergone full eligibility attestation. Eligibility cannot be definitively confirmed online. Please verify with the administering department before applying.",
    "mr": "माहितीपर नोंद: ही योजना महाराष्ट्र शासनाच्या अधिकृत नोंदींमधून समाविष्ट केली आहे, परंतु अंतिम पात्रता पडताळणी प्रलंबित आहे. अर्ज करण्यापूर्वी संबंधित विभागाकडे खातरजमा करावी.",
    "hi": "सूचनात्मक प्रविष्टि: यह योजना महाराष्ट्र सरकार के आधिकारिक रिकॉर्ड से पहचानी गई है, लेकिन इसकी अंतिम पात्रता सत्यापन लंबित है। कृपया आवेदन करने से पहले संबंधित विभाग से पुष्टि करें。"
}

new_ids = {
    "candidate-mahila-samman-msrtc",
    "candidate-amrit-jyeshtha-nagrik-msrtc",
    "candidate-pm-svanidhi",
    "candidate-pm-vishwakarma",
    "candidate-pmmvy",
    "candidate-pmay-gramin",
    "candidate-pmay-urban",
    "candidate-pm-fasal-bima",
    "candidate-saur-krushi-pump",
    "candidate-shabari-awas",
    "candidate-mbocw-toolkit",
    "candidate-mahajyoti-fellowship",
    "candidate-sarthi-csmnrf",
    "candidate-mslsa-free-legal-aid",
}

for s in schemes:
    sid = s.get("scheme_id") or s.get("id")
    if sid in new_ids or s.get("public_status_category") == "LIMITED_INFORMATION":
        s["advisory_banner"] = banner

p.write_text(json.dumps(schemes, indent=2, ensure_ascii=False), encoding="utf-8")
print("Updated schemes.json with advisory banners.")
