from pathlib import Path

html_path = Path("static/index.html")
content = html_path.read_text(encoding="utf-8")

old_block = """    const isDemo = schemeId.startsWith('demo-') || s.publication_status === 'DEMO_ONLY' || s.publication_status === 'ACTIVE_DEMO_FIXTURE';
    const isVerified = s.publication_status === 'VERIFIED_FOR_INFORMATION' || s.publication_status === 'VERIFIED_FOR_ELIGIBILITY' || s.publication_status === 'PUBLISHED';

    return {
      ...s,
      scheme_id: schemeId,
      name: name,
      department: dept,
      summary: summary,
      benefits: benefits,
      last_verified_date: s.last_verified_date || '2026-10-15',
      isDemo: isDemo,
      isVerified: isVerified,
      publication_authorized: isVerified || s.publication_authorized || false
    };"""

new_block = """    const isDemo = schemeId.startsWith('demo-') || s.public_status_category === 'DEMO_FIXTURE' || s.publication_status === 'DEMO_ONLY' || s.publication_status === 'ACTIVE_DEMO_FIXTURE';
    const isDecisionReady = Boolean(s.is_decision_ready || s.public_status_category === 'DECISION_READY');
    const isLimitedInfo = !isDemo && !isDecisionReady;
    const isVerified = isDecisionReady || s.publication_status === 'VERIFIED_FOR_INFORMATION' || s.publication_status === 'VERIFIED_FOR_ELIGIBILITY' || s.publication_status === 'PUBLISHED';

    return {
      ...s,
      scheme_id: schemeId,
      name: name,
      department: dept,
      summary: summary,
      benefits: benefits,
      last_verified_date: s.last_verified_date || '2026-10-15',
      isDemo: isDemo,
      isDecisionReady: isDecisionReady,
      isLimitedInfo: isLimitedInfo,
      public_status_category: s.public_status_category || (isDecisionReady ? 'DECISION_READY' : (isDemo ? 'DEMO_FIXTURE' : 'LIMITED_INFORMATION')),
      isVerified: isVerified,
      publication_authorized: isVerified || s.publication_authorized || false
    };"""

# Normalize CRLF / LF for clean replace
if old_block in content:
    content = content.replace(old_block, new_block, 1)
    html_path.write_text(content, encoding="utf-8")
    print("SUCCESS: Replaced normalizeSchemeForUI (LF mode)")
else:
    # Try CRLF
    old_crlf = old_block.replace("\n", "\r\n")
    new_crlf = new_block.replace("\n", "\r\n")
    if old_crlf in content:
        content = content.replace(old_crlf, new_crlf, 1)
        html_path.write_text(content, encoding="utf-8")
        print("SUCCESS: Replaced normalizeSchemeForUI (CRLF mode)")
    else:
        print("FAILED: old_block not found in content!")
