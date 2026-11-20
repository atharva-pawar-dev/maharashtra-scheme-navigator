with open("static/index.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('id="view-explore"')
if idx != -1:
    print(text[idx:idx+2000])
else:
    print("view-explore not found")
