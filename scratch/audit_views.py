import re

with open("static/index.html", encoding="utf-8") as f:
    content = f.read()

print("HTML Length:", len(content))

# Look for view IDs
views = re.findall(r'id=["\'](view-[^"\']+)["\']', content)
print("Views found:", views)

# Look for functions related to view navigation
nav_funcs = re.findall(r'function\s+([a-zA-Z0-9_]*(?:view|navigate|page|show|tab)[a-zA-Z0-9_]*)\s*\(', content, re.IGNORECASE)
print("Nav functions:", set(nav_funcs))

# Look for header links
header_match = re.search(r'<nav[^>]*>.*?</nav>', content, re.DOTALL)
if header_match:
    print("Header nav snippet:", header_match.group(0)[:500])

# Look for canonical-schemes fetch
fetches = re.findall(r'fetch\([^\)]+\)', content)
print("Fetches count:", len(fetches))
for fetch in fetches[:10]:
    print("Fetch:", fetch.strip()[:80])
