from pathlib import Path
import re

html_path = Path("static/index.html")
content = html_path.read_text(encoding="utf-8")

matches = re.findall(r"(?:renderSchemeCard|renderFocusedResultCard|openSchemeDetail)[^{]*\{", content)
print("Found functions:", matches)

# Find badge logic
for match in re.finditer(r"(?:badge|Decision Ready|Limited Information|Tier A|Tier B|Tier C)", content, re.IGNORECASE):
    snippet = content[max(0, match.start()-100):min(len(content), match.end()+150)]
    print("-" * 50)
    print(snippet)
    if match.start() > 100000:
        break
