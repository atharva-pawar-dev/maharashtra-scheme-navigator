# Root-Cause Analysis and File-Level Implementation Plan
## Definitive Production-Grade Catalogue, Eligibility & Citizen Journey Integration

### 1. Baseline Summary
- **Baseline Test Suite**: 303 passed, 0 failed in 122s.
- **Safety Backup**: `backup-before-definitive-integration-20261113-173409`
- **Git State**: Clean working tree on master branch.

---

### 2. Root-Cause Analysis of Current Architectural Inconsistencies

1. **Dual Catalogue Disconnect (Split-Brain Catalogue)**:
   - *Discovery/Explore*: Fetches `/canonical-schemes` from `SourceRegistry` (loading `data/source_registry/canonical_schemes.json` containing 60 canonical schemes).
   - *Interview & Eligibility Evaluation*: Calls `SchemeCatalog` (`catalog.all()`, `catalog.get(scheme_id)`), which loads `data/demo/schemes.json` (containing only 2 demo fixtures: `demo-majhi-ladki-bahin`, `demo-indira-gandhi-old-age-pension`).
   - *Consequence*:
     - When a citizen selects "Check my eligibility" on any canonical scheme in Explore, `/interview/start` returns 404 (`Scheme not found in active catalogue`).
     - The guided interview only evaluates the 2 demo schemes, ignoring the 60 canonical schemes.
     - Evaluation endpoints evaluate only the 2 demo schemes.
     - Explore and interview display conflicting realities.

2. **Silent Demo Fallback in Frontend**:
   - `static/index.html` has fallback logic where a failed or empty `/canonical-schemes` silently calls `/schemes` (demo fixtures).
   - This violates production separation invariants: failures must display explicit error states, not silently masquerade demo fixtures as real schemes.

3. **Citizen Profile & Interview Run Coupling**:
   - The citizen's profile is tightly coupled to interview chat memory.
   - Selecting a scheme in Explore starts an interview that can replay older chat turns, uses stale question state, or evaluates the entire catalogue instead of scoping to the selected scheme.
   - There is no persistent SQLite-backed citizen profile storage that retains citizen attributes independently of interview thread IDs.
   - Data privacy: A proper "Reset my data" endpoint clearing profile, runs, progress, and dismissals is required.

4. **Eligibility Engine Outcome States & Matching Logic**:
   - Currently, `EligibilityStatus` only has `eligible`, `ineligible`, `needs_information`, `needs_review`.
   - The user specification mandates 5 distinct outcome states:
     - `ELIGIBLE`: All statutory & mandatory requirements met with verified evidence.
     - `PARTIAL`: Configurable threshold (>= 70% passing, <= 2 non-hard criteria failed, 0 hard statutory criteria failed). Exploratory matching only, clearly separated from statutory approval.
     - `NEEDS_INFO`: Unknown conditions remain that could resolve the outcome.
     - `NOT_ELIGIBLE`: Hard statutory criterion failed (hidden by default with toggle).
     - `NEEDS_REVIEW`: Unresolved policy or unverified evidence.
   - Machine-readable rules for canonical schemes must be available to the engine so the interview and evaluation evaluate the real catalogue.

5. **My Progress: Exactly One Active Scheme**:
   - There is no server-backed single-active-scheme constraint.
   - The system must ensure exactly 1 active scheme per citizen session, with paused progress preserved, and a formal dismissal action ("Remove from progress") requiring confirmation that excludes the dismissed scheme from recommendations until profile reset.

6. **Navigation & SPA URL Routing**:
   - Visiting `/explore`, `/interview`, `/results`, `/progress`, or `/workspace/{scheme_id}` directly returns 404 because FastAPI only routes `/`.
   - The browser Back button must be supported via History API / `popstate` and a visible Back button.
   - Review Portal is currently in the top header rather than a fixed bottom-right floating button with dark blue styling and role restrictions.

---

### 3. File-Level Implementation Plan

#### Phase 1: Unified Canonical Catalogue Architecture
- **Files**:
  - `src/scheme_navigator/services/catalog.py`: Upgrade `SchemeCatalog` to be the single source of truth. Load canonical schemes from `data/source_registry/canonical_schemes.json` with machine-readable rules and publication statuses. Provide strict environment-aware separation (production = canonical published catalogue only; development/test = isolated fixtures or canonical).
  - `src/scheme_navigator/source_registry/canonical_schemes.json`: Ensure canonical schemes have machine-readable rule ASTs, statutory vs non-hard condition flags, and evidence references.
  - `src/scheme_navigator/domain/models.py`: Update `EligibilityStatus` to include `PARTIAL` (`partial`), and add condition-level metadata (`is_hard_statutory`, `condition_id`).

#### Phase 2: Server-Side Persistent Citizen Profile & Progress Store
- **Files**:
  - `src/scheme_navigator/core/citizen_store.py`: Implement SQLite-backed persistent store `CitizenProfileStore` (tables: `citizen_profiles`, `interview_runs`, `citizen_progress`, `dismissed_schemes`).
  - `src/scheme_navigator/core/migrations.py`: Add migration for `citizen_profiles.sqlite3`.
  - `src/scheme_navigator/api/main.py`: Wire citizen profile persistence, session ownership, `/profile` CRUD, `/profile/reset` ("Reset my data"), `/progress` (single active scheme, pause/resume, dismiss with confirmation).

#### Phase 3: Adaptive Catalogue-Driven Interviewer
- **Files**:
  - `src/scheme_navigator/agents/interviewer.py`: Drive questions dynamically from machine-readable rules across all viable schemes in the active catalogue. Support scoped runs for focused scheme assessment (seeded from persistent profile, asking only missing fields for that scheme). Expand `QUESTION_SPECS` for all required profile fields with multilingual labels (en, mr, hi).

#### Phase 4: Deterministic 5-State Rule Engine
- **Files**:
  - `src/scheme_navigator/services/rule_engine.py`: Implement tri-state evaluation with `PARTIAL` outcome calculation (configurable `partial_min_pass_ratio=0.70`, `partial_max_failed_non_hard=2`, 0 hard statutory failures). Retain `NEEDS_REVIEW` for unverified/policy-unresolved schemes.
  - `src/scheme_navigator/core/config.py`: Add configurable thresholds.

#### Phase 5: Navigation, URL Routing & UI Upgrades
- **Files**:
  - `src/scheme_navigator/api/main.py`: Register FastAPI routes for `/`, `/explore`, `/interview`, `/results`, `/progress`, `/workspace/{scheme_id}` returning `index.html`.
  - `static/index.html`:
    - Remove demo fallback from `loadSchemes`.
    - Implement browser History API (`pushState`, `popstate`, real URLs).
    - Implement reusable Back button.
    - Move Review Portal from header to fixed bottom-right button with dark blue styling (`#1E3A8A`), visible focus, role restrictions.
    - Implement My Progress with exactly 1 active scheme, confirmation on switch, dustbin icon + exact dismissal confirmation text, empty state "No schemes selected".
    - Implement 5 status groups on Results page (Eligible, Partial, Needs Info, Needs Review, Not Eligible hidden by default).
    - Post-verification completion view: exactly two next-step buttons ("Return to Home", "Back to my eligible schemes").

#### Phase 6: Comprehensive Testing Suite
- **Files**:
  - `tests/test_golden_citizen_profiles.py`: 10 synthetic golden profiles with independent assertions.
  - `tests/test_focused_assessment_and_progress.py`: Regression tests for focused assessment (no stale chat, scoped run) and 1-active-scheme progress/dismissal.
  - `tests/test_browser_citizen_experience.py`: Playwright browser test suite covering all 25 mandated scenarios against live Uvicorn instance.

#### Phase 7: Acceptance Documentation
- **Files**:
  - `docs/catalogue_integration_audit.md`
  - `docs/interview_and_eligibility_architecture.md`
  - `docs/citizen_profile_persistence.md`
  - `docs/application_progress_model.md`
  - `docs/final_release_readiness_report.md`
  - `docs/remaining_risks.md`
