# MSN-I18N-001: Localization Architecture & Defect Root Cause Audit

**Audit Date:** 2026-11-23  
**Auditor:** Principal Software & Localization Engineer  
**Scope:** Application-Wide Language Consistency, Runtime State Repair, & Zero Mixed-Language Experience  
**Governing Standard:** Zero unexplained language mixing across every citizen journey.

---

## 1. Executive Summary & Defect Reproduction

A forensic audit of Maharashtra Scheme Navigator identified the root causes of the reported multilingual defects (Screenshot 1 and Screenshot 2):

1. **Screenshot 1 Root Cause (English selected, bottom navigation in Marathi):**
   In `static/index.html` (View 6: `view-documents`), the bottom action bar `#doc-bottom-actions` contains:
   - `<button class="btn btn-secondary" onclick="showView('results')">← मागे जा</button>`: Has hardcoded Marathi text with no element `id` or localization binding.
   - `<button id="btn-portal-official">अधिकृत पोर्टलवर जा ↗</button>`: Has hardcoded Marathi text in the HTML markup, and `applyLanguage()` never updates this element.
   - `<button id="btn-proceed-roadmap">पूर्वतयारी मार्गदर्शक पहा →</button>`: Has hardcoded Marathi text in the HTML markup, and `applyLanguage()` never updates this element.
   When English or Hindi is selected, the rest of the document view switches, but these bottom action buttons remain frozen in Marathi.

2. **Screenshot 2 Root Cause (Marathi selected, document requirement cards in English):**
   In `src/scheme_navigator/services/document_prep.py`:
   - `prepare_intelligent_document_audit()` builds `DocumentRequirementStatus` objects.
   - `document_name` is populated directly from `r_spec["document_name"]` in `data/source_registry/scheme_document_requirements.json`, which stores all names exclusively in English (`"Income Certificate"`, `"Domicile Certificate"`, `"Aadhaar Card"`, etc.).
   - `issuing_authority` is copied verbatim from English strings (`"Tehsildar / SDO via Aaple Sarkar"`, `"UIDAI"`, etc.).
   - `alt_info` string templates concatenate English prefixes (`" Permitted alternatives: ..."`) even when `language == "mr"`.
   - `action_needed` concatenates the English authority name with Marathi verbs (`"Tehsildar / SDO via Aaple Sarkar मार्फत अर्ज करा."`).
   When `renderDocumentAuditorView()` in `static/index.html` receives this response, it renders the raw English `rq.document_name` and English explanations into the Marathi UI.

3. **Runtime State Fragmentation Root Cause:**
   - `static/index.html` maintains language in memory `state.language` and in `sessionStorage` under `scheme_nav_session`. However, `setLanguage(lang)` never calls `saveSession()` and never writes to `localStorage`.
   - `static/dv_design_kit.js` maintains language in `localStorage` under `dv_lang`.
   - Because `index.html` and `dv_design_kit.js` use separate, unsynchronized storage mechanisms, page refreshes, direct navigation, or moving between the main app and document modules reset or desynchronize the citizen's chosen language.

---

## 2. Component-by-Component Defect Inventory

### A. Static HTML Markup Defect Points (`static/index.html`)

| Line(s) | Element / Component | Current Hardcoded State | Defect Mechanism |
| :--- | :--- | :--- | :--- |
| **1207** | Document View Back Button | `← मागे जा` | Hardcoded Marathi; no ID; untouched by `applyLanguage()` |
| **1209** | Document View Portal Button | `अधिकृत पोर्टलवर जा ↗` | Hardcoded Marathi; ID `btn-portal-official` not in `applyLanguage()` |
| **1210** | Document View Roadmap Button | `पूर्वतयारी मार्गदर्शक पहा →` | Hardcoded Marathi; ID `btn-proceed-roadmap` not in `applyLanguage()` |
| **1200** | Document View Completed Return | `<span id="lbl-comp-results">माझ्या पात्र योजनांकडे परत जा</span>` | Hardcoded Marathi; not in `applyLanguage()` |
| **1219** | Roadmap View Header | `<h3 id="roadmap-ws-title">पूर्वतयारी मार्गदर्शक व अवलंबित्व आलेख</h3>` | Hardcoded Marathi; not in `applyLanguage()` |
| **1233** | Roadmap View Portal Button | `अधिकृत पोर्टलवर जा ↗` | Hardcoded Marathi; not in `applyLanguage()` |
| **1245-1246**| Confirmation Modal Buttons | `रद्द करा` / `पुष्टी करा` | Hardcoded Marathi in `#confirm-modal`; not in `applyLanguage()` |
| **1266-1267**| Factsheet Modal Actions | `🖨️ मुद्रित करा (Print)` / `🔗 दुवा कॉपी करा` | Mixed English/Marathi; not in `applyLanguage()` |
| **1279-1309**| Issue Report Modal & Options | `त्रुटीचा प्रकार (Issue Type)` / `नोंदणी करा` | Mixed English/Marathi options; not in `applyLanguage()` |
| **1090, 1126**| Scheme View Roadmap Shortcuts | `पूर्वतयारी मार्गदर्शक पहा` | Hardcoded Marathi button text |

---

### B. Backend API Defect Points (`src/scheme_navigator/services/document_prep.py`)

1. **Untranslated Document Names:**
   The canonical document requirements dataset defines documents in English:
   - `"Income Certificate"`
   - `"Domicile Certificate"`
   - `"Aadhaar Card"`
   - `"7/12 Extract"`
   - `"Bank Account Details"`
   - `"Ration Card"`
   `document_prep.py` fails to map these canonical strings to Marathi (`उत्पन्नाचा दाखला`, `अधिवास दाखला`, `आधार कार्ड`, `७/१२ उतारा`, `बँक पासबुक`, `शिधापत्रिका`) and Hindi (`आय प्रमाण-पत्र`, `अधिवास प्रमाण-पत्र`, `आधार कार्ड`, `7/12 खतौनी`, `बैंक पासबुक`, `राशन कार्ड`).

2. **Untranslated Issuing Authorities:**
   Authorities are passed as raw English strings:
   - `"Tehsildar / SDO via Aaple Sarkar"`
   - `"Talathi / Revenue Department (Mahabhulekh)"`
   - `"Unique Identification Authority of India (UIDAI)"`
   - `"Scheduled Commercial Bank / Post Office"`
   These must be mapped to natural citizen-facing Marathi and Hindi terms.

3. **Hardcoded Explanation Snippets:**
   - Line 610: `alt_info = f" Permitted alternatives: {', '.join(alt_list)}."` (English prefix leak).
   - Line 611: `rts_info = f" Statutory RTS timeline: {rts_limit} days."` (English prefix leak).
   - Line 622: `action_text = f"Apply through {authority}."` vs `f"{authority} मार्फत अर्ज करा."` (leaves English authority inside Marathi sentence).

---

### C. State Synchronization & Persistence Defect Points

1. **Storage Disconnect:**
   - Standard app storage key: `sessionStorage.getItem('scheme_nav_session')`
   - Design kit storage key: `localStorage.getItem('dv_lang')`
   - Neither system listened to storage events or updated the other on language change.
2. **Missing Save on Switch:**
   - In `static/index.html`, `setLanguage(lang)` updated the in-memory variable `state.language` and set `document.documentElement.lang = lang`, but never persisted the selection to `localStorage` or `sessionStorage`.
   - On browser refresh or returning to the site, the language reverted to Marathi (`'mr'`) regardless of prior user action.
3. **Async Request Race Conditions:**
   - If an asynchronous API call (e.g. `/canonical-schemes/{id}/documents/audit`) was in flight when the citizen toggled language from English to Marathi, the returned report payload was rendered in the old language captured at request start time.

---

## 3. Consolidation Architecture (One Single Source of Truth)

To enforce the non-negotiable rule of **Zero Mixed-Language Experience**, we establish:

1. **Authoritative Client Language State:**
   - Primary persistent key: `localStorage.setItem('sn_language', lang)`.
   - Also mirror in `sessionStorage` and `document.documentElement.lang`.
   - Synchronize both `static/index.html` and `static/dv_design_kit.js` to read from and write to `'sn_language'`.
   - Listen to `window.addEventListener('storage', ...)` so cross-tab or cross-frame language switches instantly reflect everywhere.

2. **Complete DOM Localization Binding in `applyLanguage()`:**
   - Every static text element in `static/index.html` receives a dedicated ID and translation in `I18N_PAGE` (English, Marathi, Hindi).
   - `applyLanguage()` iterates through all registered keys, updating:
     - Navigation headers and brand titles.
     - Section headers, badges, and CTAs.
     - Bottom action buttons (`#lbl-doc-bottom-back`, `#btn-portal-official`, `#btn-proceed-roadmap`).
     - Modals (Confirm modal, Report modal, Factsheet modal).
     - Placeholders, titles, and ARIA labels.

3. **Backend Document Localization Engine:**
   - In `document_prep.py`, implement trilingual lookup tables for:
     - Document names (`DOC_NAMES_TRILINGUAL`)
     - Issuing authorities (`AUTHORITIES_TRILINGUAL`)
     - Alternative document names (`ALTERNATIVES_TRILINGUAL`)
   - Honor `language` parameter (`en`, `mr`, `hi`) across all generated requirement statuses, findings, conflict messages, and action guidance.

4. **Dynamic Frontend Re-rendering on Language Change:**
   - When `setLanguage(lang)` is invoked:
     - Update DOM static strings via `applyLanguage()`.
     - Re-render active view (`renderDocumentAuditorView`, `renderPrepareView`, `renderSchemes`, `renderResultsCards`).
     - Re-trigger audit with new `language` parameter to refresh dynamic backend text immediately.

---

## 4. Verification & Testing Strategy

A dedicated 10-point test battery (`tests/i18n/test_language_consistency.py`) and gate runner (`scripts/i18n_gate.py`) will be executed against the live application:
- **L1:** Shell consistency across EN, MR, HI.
- **L2:** Document upload & auditor screen consistency (Screenshots 1 & 2 verification).
- **L3:** Full navigation consistency across all routes.
- **L4:** Runtime language switching without state or progress loss.
- **L5:** Language persistence across refresh, navigation, and backend restart.
- **L6:** Dynamic async response localization.
- **L7:** All 13 document requirement and upload states localized.
- **L8:** Missing-key detection (fail closed, no silent fallback).
- **L9:** Controlled official-name and source-quotation exceptions.
- **L10:** Visual ergonomics and Devanagari line-height ($\ge 1.7$) across 4 viewports.
