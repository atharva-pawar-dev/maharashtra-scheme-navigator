import urllib.request
import ssl
import re
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

corporations = []

for page in [1, 2, 3]:
    url = f"https://mahadma.maharashtra.gov.in/en/list-of-corporation-2/?paged={page}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            table_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.DOTALL | re.IGNORECASE)
            for row in table_matches:
                cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
                clean_cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                if clean_cells and clean_cells[0].isdigit():
                    corporations.append({
                        "sr_no": int(clean_cells[0]),
                        "division": clean_cells[1],
                        "district": clean_cells[2],
                        "name": clean_cells[3],
                        "class": clean_cells[4] if len(clean_cells) > 4 else "",
                        "foundation_year": clean_cells[5] if len(clean_cells) > 5 else "",
                        "population_2011": clean_cells[6] if len(clean_cells) > 6 else "",
                        "area_sq_km": clean_cells[7] if len(clean_cells) > 7 else "",
                    })
    except Exception as e:
        print(f"Error on page {page}:", e)

print(f"Total corporations scraped from live DMA: {len(corporations)}")
for c in corporations:
    print(f"  {c['sr_no']}. {c['name']} (District: {c['district']}, Div: {c['division']}, Class: {c['class']})")

with open("scratch/dma_corporations_scraped.json", "w", encoding="utf-8") as f:
    json.dump(corporations, f, indent=2, ensure_ascii=False)
