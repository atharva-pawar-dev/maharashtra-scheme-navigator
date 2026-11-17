# Maharashtra Scheme Navigator: Citizen Profile Persistence & Privacy Architecture

## Executive Summary
This document specifies the persistent data model, storage architecture, provenance tracking, and privacy safeguards of the **Maharashtra Scheme Navigator**. Citizen trust depends on two fundamental guarantees:
1. **Durability**: Citizens should never lose their interview responses, uploaded documents, or roadmap milestones upon browser reload or accidental tab closure.
2. **Citizen Data Sovereignty**: In compliance with the Digital Personal Data Protection (DPDP) Act 2023 and the Maharashtra Digital Services Framework, citizens retain unconditional control over their profile data, including instantaneous, irreversible data erasure upon request.

---

## 1. Persistent SQLite Architecture
The platform utilizes an embedded, zero-maintenance, thread-safe SQLite database:
- **Default Database Path**: `data/citizen_profiles.sqlite3`
- **Configuration Parameter**: `citizen_profile_db_path` in `src/scheme_navigator/core/config.py`
- **Store Service**: `CitizenProfileStore` in `src/scheme_navigator/core/citizen_store.py`

### Database Schema Definition
The database initializes with strict constraints and WAL (Write-Ahead Logging) journaling:

```sql
CREATE TABLE IF NOT EXISTS citizen_profiles (
    session_id TEXT PRIMARY KEY,
    profile_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profile_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    scheme_id TEXT NOT NULL,
    status TEXT NOT NULL,
    pass_ratio REAL DEFAULT 0.0,
    matched_conditions JSON,
    failed_conditions JSON,
    unknown_conditions JSON,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES citizen_profiles(session_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS active_progress (
    session_id TEXT PRIMARY KEY,
    active_scheme_id TEXT,
    progress_data JSON NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES citizen_profiles(session_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS paused_schemes (
    session_id TEXT NOT NULL,
    scheme_id TEXT NOT NULL,
    progress_data JSON NOT NULL,
    paused_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(session_id, scheme_id),
    FOREIGN KEY(session_id) REFERENCES citizen_profiles(session_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dismissed_schemes (
    session_id TEXT NOT NULL,
    scheme_id TEXT NOT NULL,
    dismissed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(session_id, scheme_id),
    FOREIGN KEY(session_id) REFERENCES citizen_profiles(session_id) ON DELETE CASCADE
);
```

---

## 2. Provenance Tracking & Session Association
Each citizen session is governed by an immutable `session_id` generated client-side and synchronized with server storage:
1. **Local Session Cache**: Stored in `localStorage.getItem('scheme_navigator_thread_id')`.
2. **Session Header Synchronization**: Every API request delivers the session context via JSON payload or `X-Session-ID` header.
3. **Cross-Tab Durability**: Opening the application in multiple tabs or navigating between SPA routes (`/`, `/explore`, `/interview`, `/results`, `/progress`, `/workspace/:id`) seamlessly reloads profile progress from the SQLite store.

---

## 3. Privacy-Preserving Data Erasure
To satisfy DPDP Act 2023 requirements, the platform provides an explicit **"Reset My Data"** (`माझा डेटा हटवा`) facility:
1. **Confirmation Safeguard**: Clicking `#btn-reset-citizen-profile` opens a high-contrast modal (`#modal-confirm`) warning the citizen:
   - Marathi: *"आपण आपली सर्व माहिती, निवडलेल्या योजना व कागदपत्रे कायमस्वरूपी हटवू इच्छिता का? ही क्रिया पूर्ववत केली जाऊ शकत नाही."*
   - English: *"Are you sure you want to permanently delete all your profile information, selected schemes, and uploaded documents? This action cannot be undone."*
2. **Transactional Database Deletion**:
   - Calling `POST /profile/reset` executes an atomic cascade deletion across all tables (`citizen_profiles`, `profile_evaluations`, `active_progress`, `paused_schemes`, `dismissed_schemes`).
3. **Client-Side Storage Purge**:
   - Clears `localStorage` session keys.
   - Resets state objects (`state.profile`, `state.activeProgress`, `state.results`).
   - Reinitializes the UI to pristine initial state without requiring page reload.
4. **Verification**:
   - `test_focused_assessment_and_progress.py::test_profile_persistence_and_reset` asserts that profile records are permanently erased from SQLite (`get_profile() is None`).
   - `test_browser_citizen_experience.py::test_18_citizen_profile_reset_modal_and_data_clearance` asserts UI clearance.
