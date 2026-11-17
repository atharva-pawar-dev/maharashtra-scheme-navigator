# Document Audit, Extraction & Application Readiness Lifecycle

## 1. Architectural Mission
The Scheme Navigator document processing pipeline (`scheme_navigator.documents`) provides citizen-facing document auditing and preparation guidance to ensure applicants possess all mandatory certificates before approaching official government portals or Setu Suvidha Kendras.

### Non-Negotiable Integrity Invariant:
**Scheme Navigator is an independent guidance platform. Document extraction, OCR analysis, and readiness audits conducted on this platform do not constitute official statutory validation, government verification, or formal document submission.**

---

## 2. Secure Document Ingestion
To protect citizen privacy and host infrastructure, all file uploads undergo rigorous multi-stage security validation:
1. **File Type & MIME Validation**:
   - Only validated PDF (`application/pdf`) and high-resolution image formats (`image/jpeg`, `image/png`) are accepted.
   - Raw magic bytes are verified to prevent executable disguising or polyglot file attacks.
2. **File Size Limits**: Capped strictly at **10 MB** per upload to prevent denial-of-service (DoS) memory exhaustion.
3. **Isolated Private Storage**:
   - Uploaded files are stored in private local directories (`data/uploads`) strictly outside public web roots.
   - Files are never accessible via static web URLs.
4. **Cryptographic Identity**: Every file is tagged with its SHA-256 digest, a unique `document_id`, and parent `review_id` (UUIDv4).

---

## 3. Extraction & Multi-Page Conflict Resolution
Documents (such as Tahsildar Income Certificates, Domicile Certificates, or Caste Certificates) are processed through an intelligent extraction engine:
1. **OCR Pre-Processing**: High-contrast adaptive binarization, skew correction, and page grouping.
2. **Field-Level Extraction with Confidence**:
   - Key attributes (Beneficiary Name, Certificate Number, Issue Date, Annual Income, Caste/Category) are extracted alongside confidence scores ($0.00$ to $1.00$).
   - Marathi Devanagari text is parsed using specialized Marathi tokenizers and bilingual dictionary mappings.
3. **Multi-Page & Cross-Document Conflict Detection**:
   - When multiple pages or multiple documents are uploaded (e.g., Income Certificate vs. Ration Card), the engine compares extracted values.
   - Discrepancies (e.g., income listed as ₹80,000 on certificate but ₹1,20,000 on application affidavit) trigger a `FIELD_CONFLICT` state requiring user or reviewer resolution.

---

## 4. Human Reviewer Workflow (`reviewer.html`)
The platform includes an authorized reviewer dashboard (`/reviewer.html` and `/documents/reviews/*` APIs):
- **Role-Based Reviewer Access**: Requires authentication with `reviewer` or `catalogue_admin` role.
- **Side-by-Side Visual Audit**: Reviewers inspect the original scan alongside extracted fields.
- **Correction Audit Trail**: Any manual correction (e.g., fixing an OCR digit error in an income figure) logs an immutable event (`ReviewEvent`) containing timestamp, reviewer ID, previous value, corrected value, and audit justification in `data/document_reviews.sqlite3`.
- **Reviewer Sign-off**: Once all required documents for a target scheme are validated, the review transitions to `COMPLETED_READY`.

---

## 5. Application Readiness States
Citizen progress is tracked through transparent lifecycle phases:
| Readiness Phase | Description |
|---|---|
| `NOT_PROVIDED` | Mandatory document identified from scheme rules but not yet uploaded by citizen. |
| `UPLOADED` | File received securely; queued for pre-processing. |
| `EXTRACTION_PENDING` | OCR / extraction worker processing scan. |
| `EXTRACTION_COMPLETE` | Extracted fields available for citizen review. |
| `USER_CORRECTION_REQUIRED` | Low confidence score or field conflict detected; citizen review needed. |
| `REVIEWED` | Verified by citizen or reviewer; consistent with statutory scheme criteria. |
| `NEEDS_REPLACEMENT` | Document expired, illegible, or issued by an incompetent authority. |
| `READY_FOR_OFFICIAL_HANDOFF` | Complete dossier ready; citizen guided to the official government portal. |

---

## 6. Data Retention & DPDP Privacy Compliance
In compliance with the Digital Personal Data Protection (DPDP) principles:
- **Default 24-Hour Retention (`DATA_RETENTION_HOURS = 24`)**: Citizen uploaded files, OCR temporary bitmaps, and intermediate review sessions expire automatically after 24 hours.
- **Automated Purge Service (`POST /admin/retention/purge`)**: Securely deletes expired file blobs and scrubs associated SQLite records.
- **Explicit Citizen Reset (`POST /profile/reset`)**: Citizens can immediately wipe all profile data, uploaded files, and review sessions with a single action.
