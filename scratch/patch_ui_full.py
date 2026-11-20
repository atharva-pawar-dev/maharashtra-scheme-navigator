from pathlib import Path

html_path = Path("static/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. CSS
old_css = ".badge-draft { background: #F3F4F6; color: #4B5563; border: 1px solid #E5E7EB; }"
new_css = """.badge-draft { background: #F3F4F6; color: #4B5563; border: 1px solid #E5E7EB; }
    .badge-decision-ready { background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; }
    .badge-limited-info { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }"""

if old_css in content and ".badge-decision-ready" not in content:
    content = content.replace(old_css, new_css)
    print("Patched CSS")
else:
    print("CSS already patched or old_css not found")

# 2. filterSchemes
old_filter = """    if (q) {
      filtered = filtered.filter(s => 
        s.name.toLowerCase().includes(q) || 
        (s.department && s.department.toLowerCase().includes(q)) ||
        (s.summary && s.summary.toLowerCase().includes(q))
      );
    }"""

new_filter = """    if (q) {
      filtered = filtered.filter(s => {
        const nameMatches = (s.name && s.name.toLowerCase().includes(q)) ||
                            (s.english_name && s.english_name.toLowerCase().includes(q)) ||
                            (s.marathi_name && s.marathi_name.toLowerCase().includes(q)) ||
                            (s.hindi_name && s.hindi_name.toLowerCase().includes(q)) ||
                            (s.official_scheme_name && s.official_scheme_name.toLowerCase().includes(q)) ||
                            (s.scheme_id && s.scheme_id.toLowerCase().includes(q)) ||
                            (Array.isArray(s.aliases) && s.aliases.some(a => String(a).toLowerCase().includes(q)));
        const deptMatches = s.department && s.department.toLowerCase().includes(q);
        const sumMatches = s.summary && s.summary.toLowerCase().includes(q);
        const benefitMatches = s.benefit_description && s.benefit_description.toLowerCase().includes(q);
        return nameMatches || deptMatches || sumMatches || benefitMatches;
      });
    }"""

if old_filter in content:
    content = content.replace(old_filter, new_filter)
    print("Patched filterSchemes")
else:
    print("filterSchemes already patched or not found")

# 3. openSchemeDetail badges and banners
old_detail_badge = """    let badgeLabel = isMr ? 'सत्यापित योजना' : (isHi ? 'सत्यापित योजना' : 'Officially Verified Scheme');
    let badgeClass = 'badge-active';
    if (scheme.isDemo || scheme.name.includes('(demo fixture)') || scheme.name.includes('(Demo Fixture)')) {
      badgeClass = 'badge-demo';
      badgeLabel = isMr ? 'डेमो नमुना' : (isHi ? 'डेमो नमूना' : 'Demo Fixture');
    } else if (!scheme.publication_authorized) {
      badgeClass = 'badge-draft';
      badgeLabel = isMr ? 'पुनरावलोकन आवश्यक' : (isHi ? 'समीक्षा आवश्यक' : 'Review Required');
    }"""

new_detail_badge = """    let badgeLabel = isMr ? 'सत्यापित योजना' : (isHi ? 'सत्यापित योजना' : 'Officially Verified Scheme');
    let badgeClass = 'badge-active';
    if (scheme.isDemo || scheme.name.includes('(demo fixture)') || scheme.name.includes('(Demo Fixture)')) {
      badgeClass = 'badge-demo';
      badgeLabel = isMr ? 'डेमो नमुना' : (isHi ? 'डेमो नमूना' : 'Demo Fixture');
    } else if (scheme.isDecisionReady) {
      badgeClass = 'badge-decision-ready';
      badgeLabel = isMr ? '🟢 निर्णय-सज्ज' : (isHi ? '🟢 निर्णय-सज्ज' : '🟢 Decision Ready');
    } else if (scheme.isLimitedInfo) {
      badgeClass = 'badge-limited-info';
      badgeLabel = isMr ? 'ℹ️ मर्यादित माहिती' : (isHi ? 'ℹ️ सीमित जानकारी' : 'ℹ️ Limited Info');
    } else if (!scheme.publication_authorized) {
      badgeClass = 'badge-draft';
      badgeLabel = isMr ? 'पुनरावलोकन आवश्यक' : (isHi ? 'समीक्षा आवश्यक' : 'Review Required');
    }

    let advisoryBanner = '';
    if (scheme.isDecisionReady) {
      const bannerTitle = isMr ? '🟢 निर्णय-सज्ज योजना (Decision Ready)' : (isHi ? '🟢 निर्णय-सज्ज योजना (Decision Ready)' : '🟢 Decision Ready Scheme');
      const bannerText = isMr
        ? 'या योजनेचे सर्व पात्रता निकष, अपवर्जने (exclusions) आणि आवश्यक कागदपत्रे शासन निर्णयानुसार संपूर्णपणे पडताळलेली आहेत.'
        : (isHi
          ? 'इस योजना के सभी पात्रता मानदंड, बहिष्करण और आवश्यक दस्तावेज़ शासन निर्णय के अनुसार पूर्णतः सत्यापित हैं।'
          : 'All eligibility criteria, formal exclusions, and required documents have been fully verified against official Government Resolutions.');
      advisoryBanner = `
        <div style="background:#ECFDF5; border:1px solid #A7F3D0; padding:12px; border-radius:var(--radius-sm); margin-bottom:14px; font-size:0.86rem; color:#065F46;">
          <strong>${bannerTitle}:</strong> ${bannerText}
        </div>
      `;
    } else if (scheme.isLimitedInfo) {
      const bannerTitle = isMr ? 'ℹ️ मर्यादित माहिती (Limited Information)' : (isHi ? 'ℹ️ सीमित जानकारी (Limited Information)' : 'ℹ️ Limited Information');
      const bannerText = isMr
        ? 'या योजनेची मूलभूत माहिती उपलब्ध आहे, परंतु अंतिम पात्रता निश्चितीसाठी अधिकृत शासन निर्णय व संकेतस्थळाचा संदर्भ घ्यावा. आवश्यक कागदपत्रे व दाखले सादर करावे लागतील.'
        : (isHi
          ? 'इस योजना की बुनियादी जानकारी उपलब्ध है, लेकिन अंतिम पात्रता पुष्टि के लिए आधिकारिक शासन निर्णय देखें। आवश्यक कागदपत्रे व दाखले सादर करावे लागतील।'
          : 'Basic information is available. For full decision-ready eligibility and exclusion confirmation, consult official portal/GR. Documents and certificates will be required.');
      advisoryBanner = `
        <div style="background:#EFF6FF; border:1px solid #BFDBFE; padding:12px; border-radius:var(--radius-sm); margin-bottom:14px; font-size:0.86rem; color:#1E40AF;">
          <strong>${bannerTitle}:</strong> ${bannerText}
        </div>
      `;
    }"""

if old_detail_badge in content:
    content = content.replace(old_detail_badge, new_detail_badge)
    print("Patched openSchemeDetail badges")
else:
    print("openSchemeDetail badges not found or already patched")

# 4. openSchemeDetail content.innerHTML
old_content_html = """    content.innerHTML = `
      <span class="scheme-badge ${badgeClass}" style="margin-bottom:8px; display:inline-block;">${badgeLabel}</span>
      <h3 style="font-size:1.4rem; color:var(--deep-heritage-maroon); margin-bottom:8px;">${escapeHtml(scheme.name)}</h3>"""

new_content_html = """    content.innerHTML = `
      <span class="scheme-badge ${badgeClass}" style="margin-bottom:8px; display:inline-block;">${badgeLabel}</span>
      ${advisoryBanner}
      <h3 style="font-size:1.4rem; color:var(--deep-heritage-maroon); margin-bottom:8px;">${escapeHtml(scheme.name)}</h3>
      ${portalUrl ? `<div style="font-size:0.82rem; color:var(--slate-muted); margin-bottom:6px;">🌐 <strong>Portal:</strong> <a href="${escapeHtml(portalUrl)}" target="_blank" rel="noopener noreferrer" style="color:var(--paithani-teal); text-decoration:underline;">${escapeHtml(portalUrl)}</a></div>` : ''}
      ${scheme.original_gr_and_amendments && scheme.original_gr_and_amendments.length > 0 ? `<div style="font-size:0.82rem; color:var(--slate-muted); margin-bottom:10px;">📜 <strong>GR:</strong> ${scheme.original_gr_and_amendments.map(g => escapeHtml(g)).join(', ')}</div>` : ''}"""

if old_content_html in content:
    content = content.replace(old_content_html, new_content_html)
    print("Patched content.innerHTML")
else:
    print("content.innerHTML not found or already patched")

html_path.write_text(content, encoding="utf-8")
print("Finished updating static/index.html")
