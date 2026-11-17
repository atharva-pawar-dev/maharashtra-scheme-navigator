import re

with open("static/index.html", encoding="utf-8") as f:
    html = f.read()

scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
script = scripts[-1] if scripts else ""

for func_name in ["showView", "loadSchemes", "startGuidedInterview", "renderPrepareView", "renderDiscoveredSchemes", "prepareScheme", "dismissScheme"]:
    idx = script.find(f"function {func_name}")
    if idx != -1:
        print(f"=== {func_name} ===")
        print(script[idx:idx+800])
        print()
