import re

with open("static/index.html", encoding="utf-8") as f:
    html = f.read()

scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
script = scripts[-1] if scripts else ""

# State definition
m_state = re.search(r'const state\s*=\s*\{.*?\};', script, re.DOTALL)
if m_state:
    print("=== STATE ===")
    print(m_state.group(0))

# Search for results rendering
for term in ["renderResults", "renderEvaluationResults", "evaluations", "evaluateEligibility"]:
    idx = script.find(term)
    if idx != -1:
        print(f"\n=== Found '{term}' at {idx} ===")
        print(script[idx:idx+600])
