from pathlib import Path

html_path = Path("static/index.html")
content = html_path.read_text(encoding="utf-8")

old_code = """      let badgeClass = 'badge-active';
      let badgeLabel = isMr ? 'सत्यापित योजना' : (isHi ? 'सत्यापित योजना' : 'Verified Scheme');
      if (s.isDemo || s.name.includes('(demo fixture)') || s.name.includes('(Demo Fixture)')) {
        badgeClass = 'badge-demo';
        badgeLabel = isMr ? 'डेमो नमुना' : (isHi ? 'डेमो नमूना' : 'Demo Fixture');
      } else if (!s.publication_authorized) {
        badgeClass = 'badge-draft';
        badgeLabel = isMr ? 'पुनरावलोकन आवश्यक' : (isHi ? 'समीक्षा आवश्यक' : 'Review Required');
      }"""

new_code = """      let badgeClass = 'badge-active';
      let badgeLabel = isMr ? 'सत्यापित योजना' : (isHi ? 'सत्यापित योजना' : 'Verified Scheme');
      if (s.isDemo || s.name.includes('(demo fixture)') || s.name.includes('(Demo Fixture)')) {
        badgeClass = 'badge-demo';
        badgeLabel = isMr ? 'डेमो नमुना' : (isHi ? 'डेमो नमूना' : 'Demo Fixture');
      } else if (s.isDecisionReady) {
        badgeClass = 'badge-decision-ready';
        badgeLabel = isMr ? '🟢 निर्णय-सज्ज' : (isHi ? '🟢 निर्णय-सज्ज' : '🟢 Decision Ready');
      } else if (s.isLimitedInfo) {
        badgeClass = 'badge-limited-info';
        badgeLabel = isMr ? 'ℹ️ मर्यादित माहिती' : (isHi ? 'ℹ️ सीमित जानकारी' : 'ℹ️ Limited Info');
      } else if (!s.publication_authorized) {
        badgeClass = 'badge-draft';
        badgeLabel = isMr ? 'पुनरावलोकन आवश्यक' : (isHi ? 'समीक्षा आवश्यक' : 'Review Required');
      }"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    html_path.write_text(content, encoding="utf-8")
    print("SUCCESS: Patched renderSchemes (LF mode)")
else:
    old_crlf = old_code.replace("\n", "\r\n")
    new_crlf = new_code.replace("\n", "\r\n")
    if old_crlf in content:
        content = content.replace(old_crlf, new_crlf, 1)
        html_path.write_text(content, encoding="utf-8")
        print("SUCCESS: Patched renderSchemes (CRLF mode)")
    else:
        print("FAILED: old_code not found in content!")
