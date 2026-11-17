with open("static/index.html", encoding="utf-8") as f:
    s = f.read()

idx = s.find('id="view-documents"')
if idx != -1:
    print("=== VIEW-DOCUMENTS HTML ===")
    print(s[idx:idx+2500])

idx2 = s.find('id="view-roadmap"')
if idx2 != -1:
    print("\n=== VIEW-ROADMAP HTML ===")
    print(s[idx2:idx2+2500])
