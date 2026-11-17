# Local Government Jurisdiction & Multi-Tier Geographic Isolation Architecture

## 1. Architectural Mission & Statutory Local Body Hierarchy
The Scheme Navigator Jurisdiction Engine enforces **strict statutory geographic isolation** across all official tiers of governance in Maharashtra:

```
Tier 1: Central Government Schemes (GoI)
   ↓
Tier 2: Maharashtra State Government Schemes (GoM)
   ↓
Tier 3: Administrative Divisions (6 Divisions: Konkan, Pune, Nashik, Chhatrapati Sambhajinagar, Amravati, Nagpur)
   ↓
Tier 4: Revenue Districts (36 Districts)
   ↓
Tier 5: Urban Local Bodies (424 ULBs)
   ├── 29 Municipal Corporations (Classes A+, A, B, C, D)
   ├── 245 Municipal Councils (Classes A, B, C)
   └── 150 Nagar Panchayats (Transitional urban areas)
   ↓
Tier 6: Rural Local Governments (Panchayati Raj Institutions)
   ├── 34 Zilla Parishads (District rural apex)
   ├── 351 Panchayat Samitis (Taluka level)
   └── ~27,800 Gram Panchayats (Village level)
   ↓
Special Jurisdictions:
   ├── 7 Central Cantonment Boards (Ministry of Defence: Pune, Kirkee, Dehu Rd, Deolali, Kamptee, Ahmednagar, Aurangabad)
   ├── Administrative Wards & Electoral Prabhags
   └── Special Areas (PESA Schedule V Tribal Areas, Matheran Eco-Sensitive Zone, Mahabaleshwar)
```

No resident of one urban local body or rural tier may ever receive eligibility results for schemes enacted, funded, or administered exclusively by another local body.

---

## 2. Statutory Geographic Token System & 11 Scopes

The runtime resolves citizen profile location attributes into authoritative hierarchical jurisdiction tokens:

| Tier | Jurisdiction Scope | Canonical Token Format | Example | Statutory Mapping |
|---|---|---|---|---|
| Tier 1 | `CENTRAL` | `jurisdiction:central` | PM SVANidhi, PM-KISAN, PM Surya Ghar | Applicable pan-India / all Maharashtra residents |
| Tier 2 | `MAHARASHTRA_STATE` | `jurisdiction:state:maharashtra` | Majhi Ladki Bahin, Sanjay Gandhi Niradhar | Applicable to all validated residents of Maharashtra |
| Tier 3 | `DIVISION` | `jurisdiction:division:{slug}` | `jurisdiction:division:pune` | Resolves citizen district to one of 6 divisions |
| Tier 4 | `DISTRICT` | `jurisdiction:district:{slug}` | `jurisdiction:district:gadchiroli` | Matches specific beneficiary districts |
| Tier 5 Corp | `MUNICIPAL_CORPORATION` | `jurisdiction:mc:{corp_id}` | `jurisdiction:mc:mc-pune`, `jurisdiction:mc:mc-pimpri-chinchwad` | Matches verified municipal corporation + residency years |
| Tier 5 Ward | `WARD` | `jurisdiction:mc:{corp_id}:ward:{slug}` | `jurisdiction:mc:mc-pune:ward:kothrud` | Matches ward within designated corporation |
| Tier 5 Council | `MUNICIPAL_COUNCIL` | `jurisdiction:tier:municipal_council` | `jurisdiction:council:baramati` | Applicable to 245 Class A/B/C Municipal Councils |
| Tier 5 NP | `NAGAR_PANCHAYAT` | `jurisdiction:tier:nagar_panchayat` | `jurisdiction:tier:nagar_panchayat` | Applicable to 150 transitional Nagar Panchayats |
| Tier 6 Rural | `GRAM_PANCHAYAT` | `jurisdiction:tier:rural` | `jurisdiction:tier:gram_panchayat` | Applicable to rural village residents |
| Tier 6 ZP | `ZILLA_PARISHAD` | `jurisdiction:zp:{district}` | `jurisdiction:zp:pune` | Applicable to rural residents within 34 Zilla Parishads |
| Special Cantonment | `CANTONMENT_BOARD` | `jurisdiction:tier:cantonment` | `jurisdiction:cantonment:cb-pune` | Applicable to 7 Central MoD Cantonment Boards |
| Special | `SPECIAL_AREA` | `jurisdiction:special:{area_id}` | `jurisdiction:special:pesa_tribal` | Matches designated eco-sensitive or tribal PESA zones |

---

## 3. Strict Boundary Isolation Rules

### Rule 1: Municipal Corporation Mutual Exclusion
A citizen residing within one municipal corporation boundary (e.g., Pune Municipal Corporation, `mc-pune`) is strictly prohibited from receiving schemes enacted by any adjoining or distant municipal corporation (e.g., Pimpri Chinchwad Municipal Corporation, `mc-pimpri-chinchwad`).
- If `profile.municipal_corporation == "mc-pune"`, all PCMC-specific schemes evaluate to `status="INELIGIBLE"` with failure condition:
  `"Geographically inapplicable: Programme belongs to ['mc-pimpri-chinchwad'] and does not apply to residents of 'mc-pune'."`

### Rule 2: Urban Local Body vs. Rural Local Body Isolation
- A resident of a **Municipal Corporation** or **Municipal Council** cannot qualify for rural-exclusive schemes (e.g., Zilla Parishad Shetkari Sheti Shala).
- A resident of a **Gram Panchayat** cannot qualify for Municipal Corporation urban welfare schemes (e.g., PMC Shahari Garib Arogya Yojana).

### Rule 3: Single Canonical Record for Centrally Sponsored Programmes
Centrally sponsored schemes implemented through Urban Local Bodies (e.g., **PM SVANidhi**, **PMAY Urban**) are defined as a single canonical scheme with `jurisdiction_scope="CENTRAL"` and `implementing_authority="Urban Development Department"`. They are open to all qualifying municipal residents without requiring 29 redundant duplicates.

---

## 4. Boundary PIN Ambiguity & Explicit Confirmation Protocol

Certain Indian Postal PIN codes cross administrative boundary lines between adjoining municipal corporations. The engine maintains an authoritative `PIN_AMBIGUITY_REGISTRY`:

| Ambiguous PIN Code | Traversing Administrative Boundaries | Representative Localities |
|---|---|---|
| `411027` | PMC vs. PCMC | Aundh (PMC) vs. Pimple Saudagar / Sangvi (PCMC) |
| `411061` | PMC vs. PCMC | Bopodi (PMC) vs. Dapodi (PCMC) |
| `411057` | PMC vs. PCMC | Baner Extension (PMC) vs. Wakad (PCMC) |
| `400607` | TMC vs. MBMC | Ghodbunder (TMC) vs. Kashimira Border (MBMC) |
| `410206` | NMMC vs. PMC-Panvel | Belapur Outskirts (NMMC) vs. New Panvel (Panvel MC) |

### Fail-Closed Ambiguity Invariant:
When an ambiguous PIN code is submitted without confirmed local body:
1. Engine **MUST NOT** guess or pick a default corporation.
2. Engine returns `status = "LOCATION_REQUIRES_CONFIRMATION"`.
3. Engine returns `candidate_local_bodies = ["mc-pimpri-chinchwad", "mc-pune"]`.
4. Engine returns a transparent localized explanation requiring citizen confirmation before issuing local scheme decisions.

---

## 5. Dynamic Invalidation on Relocation

When a citizen changes their local government in their profile (e.g., from `mc-pune` to `mc-pimpri-chinchwad`):
- All previous municipal scheme eligibility decisions are immediately invalidated.
- Rule evaluation re-executes deterministically against the new jurisdiction scope.
- Old municipal schemes flip from Eligible to Ineligible; new municipal schemes become actively evaluated.
