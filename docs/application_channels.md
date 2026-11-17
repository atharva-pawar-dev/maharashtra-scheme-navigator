# Official Application Channels & Honest Citizen Tracking Architecture

## 1. Statutory Handoff & Channel Transparency
Scheme Navigator guides citizens through application preparation and routes them to the **competent, officially gazetted authority** for actual application submission.

### Non-Negotiable Operational Boundaries:
1. **No Password or OTP Collection**: Scheme Navigator never requests, stores, or processes citizen login credentials, passwords, or SMS OTPs for government portals (such as MahaDBT, Aaple Sarkar, DigiLocker, or Sarathi).
2. **No Unauthorized Form Automation**: The platform does not use undocumented backend endpoints or headless automation to inject unauthorized form submissions into government portals.
3. **No False Confirmation Claims**: A submission is never marked as government-approved unless an authorized, cryptographically verified government integration exists.

---

## 2. Channel Registry Inventory (`data/source_registry/application_channels.json`)
The registry provides validated application channel records for **100% of all 75 canonical schemes**:

### 2.1 Classification of Official Application Channels
| Channel Type | Count | Description & Examples |
|---|---|---|
| `DIRECT_OFFICIAL_PORTAL` | 42 | Dedicated, secure online portals maintained by GoM or Central Ministries (e.g., `ladkibahin.maharashtra.gov.in`, `mahadbt2.maharashtra.gov.in`, `pmsvanidhi.mohua.gov.in`, `pmkisan.gov.in`, `pmsuryaghar.gov.in`). |
| `OFFLINE_OFFICE_APPLICATION` | 27 | Schemes administered physically through designated civic offices: Municipal Ward Offices (Prabhag Karyalayas), Setu Suvidha Kendras, Citizen Facilitation Centers (CFC), Anganwadi Desks, Tahsildar Sanjay Gandhi Branches, or District Social Welfare Offices. |
| `PUBLIC_SERVICE_PORTAL` | 6 | Standard prerequisite certification portals (e.g., Aaple Sarkar `aaplesarkar.mahaonline.gov.in` for Domicile, Income, and Caste certificates). |
| **Total** | **75** | **100% Verified against Active Government Portals & GR Procedures** |

---

## 3. Application Channel Schema (`ApplicationChannelRecord`)
Each channel record contains operational fields to assist the citizen:
- `scheme_id`: Stable canonical scheme identifier.
- `portal_name`: Official name of the portal or administering office.
- `portal_url`: Validated HTTPS link to the citizen gateway.
- `department`: Competent government department.
- `login_requirement`: Authentication requirements (e.g., *Citizen Mobile OTP + Aadhaar Verification*, *DigiLocker*, or *Physical Form Submission*).
- `application_window`: Published application dates (e.g., *Round the year*, *July to October annually*).
- `fresh_vs_renewal`: Guidance on whether fresh applications and renewal cycles use separate portals.
- `offline_procedure`: Detailed physical submission instructions (office address, desk officer title, required document copies).
- `preparation_checklist`: Final checklist of documents required before opening the portal or visiting the office.
- `tracking_url`: Official government application tracking portal.
- `grievance_url`: Official grievance redressal gateway (e.g., `grievances.maharashtra.gov.in`, `sarathi.pcmcindia.gov.in`).
- `statutory_hand_off_notice`: Mandatory disclaimer emphasizing independent guidance.

---

## 4. Honest Citizen Tracking Architecture
Citizen application progress is tracked through `CitizenApplicationTrackRecord` (`POST /application/track` and `GET /application/track/{thread_id}`):

### 4.1 Strict Tracking Invariant: `is_citizen_reported = True`
Because Scheme Navigator operates as an independent platform without direct backend write access to government databases, **every application status updated by a citizen is explicitly flagged with `is_citizen_reported = True`**.

### 4.2 Tracking Status Hierarchy
| Tracking Status | Source of Truth | Display Label (EN / MR / HI) |
|---|---|---|
| `PREPARATION_IN_PROGRESS` | Scheme Navigator | Preparation in Progress / कागदपत्रे तयार करणे सुरू / दस्तावेज़ तैयारी जारी |
| `READY_TO_APPLY` | Scheme Navigator | Ready to Apply / अर्ज करण्यास सज्ज / आवेदन के लिए तैयार |
| `OFFICIAL_PORTAL_OPENED` | Scheme Navigator (Browser Event) | Official Portal Opened / अधिकृत पोर्टल उघडले / आधिकारिक पोर्टल खोला गया |
| `CITIZEN_REPORTED_SUBMITTED` | Citizen Self-Report | Submitted (Citizen Reported) / सादर केले (नागरिकाने नोंदवलेले) / जमा किया (नागरिक द्वारा दर्ज) |
| `OFFICIALLY_SUBMITTED` | Reserved for Official API Integration | Officially Submitted / अधिकृतरीत्या सादर / आधिकारिक तौर पर जमा |
| `OFFICIALLY_APPROVED` | Reserved for Official API Integration | Officially Approved / अधिकृतरीत्या मंजूर / आधिकारिक तौर पर स्वीकृत |
| `OFFICIALLY_REJECTED` | Reserved for Official API Integration | Officially Rejected / अधिकृतरीत्या नामंजूर / आधिकारिक तौर पर अस्वीकृत |

The UI clearly indicates to citizens that updating their status in Scheme Navigator records their personal preparation journey and does not alter their statutory standing in the government portal.
