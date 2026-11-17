import re

with open("static/index.html", encoding="utf-8") as f:
    html = f.read()

# Header nav
m_nav = re.search(r'<header[^>]*>.*?</header>', html, re.DOTALL)
if m_nav:
    print("--- HEADER SNIPPET ---")
    print(m_nav.group(0)[:1500])

# Review portal mentions
review_mentions = re.findall(r'.{0,50}(?:reviewer|Review Portal|पुनरावलोकन).{0,50}', html, re.IGNORECASE)
print(f"\nReview portal mentions count: {len(review_mentions)}")
for rm in review_mentions[:5]:
    print("  ", rm.strip().replace("\n", " "))

# Views in HTML
views = re.findall(r'<div[^>]+id="(view-[^"]+)"[^>]*>', html)
print("\nHTML Views:", views)
