import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Check pagination links
url = 'https://mahadma.maharashtra.gov.in/en/list-of-corporation-2/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    content = resp.read().decode('utf-8', errors='ignore')
    # Look for pagination links or data-table URLs
    pager = re.findall(r'href=[\"\']([^\"\']*(?:page|paged|list-of-corporation)[^\"\']*)[\"\']', content, re.IGNORECASE)
    print("Pagination links:", set(pager))
    # Look for table scripts or data attributes
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    for s in scripts:
        if 'list-of-corporation' in s or 'dataTable' in s or 'ajax' in s or 'json' in s:
            print("Relevant script snippet:", s[:300])
