import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://www.pcmcindia.gov.in/schemes.php'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    content = resp.read().decode('utf-8', errors='ignore')

table_match = re.search(r'<table[^>]*>(.*?)</table>', content, re.DOTALL | re.IGNORECASE)
if table_match:
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_match.group(1), re.DOTALL | re.IGNORECASE)
    print(f"Total rows in PCMC schemes table: {len(rows)}")
    for r in rows:
        cols = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', r, re.DOTALL | re.IGNORECASE)
        clean_cols = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', c)).strip() for c in cols]
        print("ROW:", clean_cols)
else:
    print("Table not found!")
