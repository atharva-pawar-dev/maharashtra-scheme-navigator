import urllib.request
import ssl
import re
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://pmc.gov.in/mr/educational-schemes', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    data = resp.read().decode('utf-8', errors='ignore')

m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', data)
if m:
    nd = json.loads(m.group(1))
    print("Found NEXT_DATA keys:", list(nd.keys()))
    props = nd.get('props', {})
    page_props = props.get('pageProps', {})
    print("pageProps keys:", list(page_props.keys()))
    # dump pageProps structure or text
    print(json.dumps(page_props, indent=2, ensure_ascii=False)[:2000])
else:
    print("No NEXT_DATA found")
