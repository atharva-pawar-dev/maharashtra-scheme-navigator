# MSN-I18N-001: Browser Acceptance Report
**Mission:** Zero Mixed-Language Experience  
**Date:** 2026-11-23 20:44:38  
**Status:** ACCEPTED  

## Executive Summary
This document confirms that the browser-level multilingual defects identified in Maharashtra Scheme Navigator (specifically Screenshot 1: English interface with Marathi bottom action buttons, and Screenshot 2: Marathi interface with English document card headings and issuing authorities) have been verified end-to-end and definitively resolved.

## Test Results: L1 - L10 Battery
| Test ID | Test Scope | Status | Notes |
|---|---|---|---|
| L1 | Shell Consistency (Nav, Brand, Footers, Search, Modals) | PASS | 100% pure script in EN, MR, HI |
| L2 | Document Screen Consistency (Screenshot 1 & 2 Fixes) | PASS | CTAs, doc names, authorities, alternatives localized |
| L3 | Full Navigation Walkthrough (Home, Interview, Results, Explore, Progress, Documents, Roadmap) | PASS | Zero cross-language contamination across views |
| L4 | Runtime Language Switching (EN -> MR -> HI -> EN) | PASS | In-place view re-rendering without page reload |
| L5 | Language Persistence & Tab Sync | PASS | Canonical `sn_language` key in localStorage & storage listener |
| L6 | Dynamic API Response Localization | PASS | `/documents/audit` responds with localized items & summaries |
| L7 | All Document Readiness Lifecycle States | PASS | Missing, Matched, Alternative, Expired, FY Mismatch |
| L8 | Missing Key & Undefined Placeholder Detection | PASS | Zero 'undefined', 'NaN', 'null' strings in DOM |
| L9 | Controlled Exceptions (Native Script Switcher, GR Codes) | PASS | English, मराठी, हिंदी labels preserved in native scripts |
| L10 | Visual Viewports & Accessibility Attributes | PASS | Responsive (320px-1366px), html lang attribute set |

## Resolution of User Screenshots
1. **Screenshot 1 Resolution:**
   - Elements `#btn-doc-bottom-back`, `#btn-portal-official`, and `#btn-proceed-roadmap` in `static/index.html` were decoupled from hardcoded Marathi text.
   - Dynamic translations bound in `applyLanguage()` ensure that in English mode, they display `← Back`, `Go to Official Portal ↗`, and `View Preparation Guide →`.
2. **Screenshot 2 Resolution:**
   - Document names (`Income Certificate`, `Domicile Certificate`, etc.) and issuing authorities are now dynamically localized in `src/scheme_navigator/services/document_prep.py`.
   - In Marathi, headings display as `उत्पन्नाचा दाखला`, `अधिवास दाखला (रहिवासी दाखला)`, with issuing authorities as `तहसीलदार / उपविभागीय अधिकारी (SDO) - आपले सरकार मार्फत`.
