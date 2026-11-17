import re

with open("static/index.html", encoding="utf-8") as f:
    content = f.read()

# Extract script block
scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
print(f"Found {len(scripts)} script blocks.")
script = scripts[-1] if scripts else ""
print(f"Main script length: {len(script)}")

# Search for showView definition
idx = script.find("function showView")
if idx != -1:
    print("--- showView snippet ---")
    print(script[idx:idx+1200])

# Search for loadSchemes definition
idx2 = script.find("async function loadSchemes")
if idx2 != -1:
    print("--- loadSchemes snippet ---")
    print(script[idx2:idx2+1200])

# Search for startGuidedInterview
idx3 = script.find("function startGuidedInterview")
if idx3 != -1:
    print("--- startGuidedInterview snippet ---")
    print(script[idx3:idx3+1200])

# Search for focused assessment or eligibility
idx4 = script.find("checkEligibility")
if idx4 != -1:
    print("--- checkEligibility snippet ---")
    print(script[idx4:idx4+1200])
