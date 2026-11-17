# Maharashtra Scheme Navigator: Application Progress & Document Lifecycle Model

## Executive Summary
This document outlines the state machine, business logic invariants, and document lifecycle architecture governing citizen application preparation in the **Maharashtra Scheme Navigator**. Preparing an official government scheme application involves substantial citizen effort (gathering revenue records, caste certificates, income affidavits, bank passbooks). The system enforces strict architectural constraints to prevent cognitive overload while ensuring that work done on any scheme is never lost.

---

## 1. The Single Active Scheme Invariant
Citizens cannot simultaneously apply for multiple complex government schemes without confusion and conflicting document queues. Therefore, the system enforces a strict business rule:

> **Invariant**: A citizen can have at most **ONE** active scheme in the "My Progress" (`माझा अर्ज`) workspace at any point in time.

### State Transitions:
1. **Activation (`POST /progress/activate`)**:
   - Selecting a scheme (via `selectSchemeForApplication(schemeId)`) designates it as the sole `active` scheme.
   - If another scheme was already active, the store atomically moves the prior scheme into the `paused_schemes` table, preserving all its uploaded documents, verified checks, and roadmap milestones.
2. **Resumption**:
   - A citizen can switch back to a paused scheme at any time. The previous active scheme is safely parked in `paused_schemes`, and the selected scheme is restored with 100% of its existing progress.
3. **Permanent Dismissal (`POST /progress/dismiss`)**:
   - If a citizen explicitly chooses to abandon a scheme, clicking **"Dismiss Scheme from Progress"** (`प्रगतीमधून ही योजना हटवा`) triggers a confirmation modal.
   - Upon citizen confirmation, the scheme is removed from `active_progress` and recorded in `dismissed_schemes`.
   - The scheme is permanently excluded from future recommendations for that citizen session unless explicitly reset.

---

## 2. Empty Progress State Standards
When no scheme is currently active (e.g., initial visit or post-dismissal), the Progress view (`/progress`) renders a clean, welcoming state complying with exact design standards:
- **Heading**: "No schemes selected." / "कोणतीही योजना निवडलेली नाही"
- **Description**: Explains that selecting an eligible scheme starts document preparation.
- **Action Buttons**:
  - `[पात्र योजना पहा / Explore eligible schemes]` -> redirects to `/results` or `/explore`.
  - `[योजना शोधा / Find schemes for me]` -> redirects to `/interview`.

---

## 3. Document Workspace Lifecycle
The document workspace (`/workspace/:id/documents`) guides citizens through collecting and verifying mandatory prerequisite documents:
- **Accepted Formats**: Single PDF (up to 10 pages, 15 MiB) or image files (PNG, JPG, WEBP, up to 12 MiB).
- **Client-Side Validation**: File type and file size checks occur before network transfer.
- **Verification Status**:
  - Documents are marked as `UPLOADED`, `VERIFIED_MOCK`, or `REJECTED_BLURRY`.
  - Checkmarks dynamically update the progress roadmap.

---

## 4. Document Preparation Completion Card
When all required documents for an active scheme are uploaded and confirmed, the system presents the dedicated completion card:
- **Container**: `#preparation-completion-card`
- **Confirmation Message**: Highlights readiness for the official government portal (Aaple Sarkar or MahaDBT).
- **Restricted Navigation**: Exactly two clean, uncluttered navigation options are provided:
  1. **"Return to Home"** (`मुख्यपृष्ठावर परत जा`) -> routes to `/`.
  2. **"Back to my eligible schemes"** (`माझ्या पात्र योजनांकडे परत`) -> routes to `/results`.

---

## 5. Official Application Redirection
Scheme Navigator is a preparation and guidance platform; final application submission occurs exclusively on the designated Government of Maharashtra portals in compliance with RTS Act 2015:
- **MahaDBT**: For scholarship, DBT, and social justice welfare benefits.
- **Aaple Sarkar**: For revenue, certificate, and tahsildar public services.
- **PM-KISAN / Krishi Portal**: For agricultural subsidies.

Every scheme roadmap provides a direct, verified link (`#roadmap-portal-link`) with `target="_blank" rel="noopener noreferrer"` directing citizens to the authentic government portal.
