# Root-Cause Analysis & Fix Report: Guided Interview Context, Focused Eligibility & Stale Results Elimination

## Executive Summary
This root-cause audit investigates and resolves the four major defects observed in the **Maharashtra Scheme Navigator** interview and eligibility lifecycle:
1. **Defect 1**: Entering via *Explore Schemes → Check Eligibility* entered a generic interview flow whose subsequent *View Results* action displayed stale scheme results from an earlier interview or the full 60-scheme catalogue scoreboard.
2. **Defect 2**: Clicking *New Interview* presented a static welcome message but failed to display any subsequent question, hanging on a blank screen.
3. **Defect 3**: The interview state was agnostic to how the citizen entered the journey (*Find Schemes for Me* `DISCOVERY` vs. a selected scheme `FOCUSED_SCHEME`).
4. **Defect 4**: Navigating, refreshing, or restarting the interview caused cross-contamination of evaluation results and loss of the target scheme.

---

## Detailed Investigation of the 9 Core Audit Areas

### 1. Why focused assessments entered the generic flow and reused previous results
- **Client Completion Misdirection**: In `static/index.html`, upon interview completion, `handleInterviewTurn()` generated a completion action button calling `triggerEvaluationFromProfile()`.
- **Global Evaluation Override**: `triggerEvaluationFromProfile()` ignored `state.selectedSchemeId` and unconditionally invoked `POST /eligibility/evaluate?scope=canonical`. This evaluated all 60 canonical schemes and rendered the full 5-outcome scoreboard (`.scoreboard`), completely obliterating the single-scheme context.
- **Client Cache Stagnation**: `state.results` in JavaScript was never cleared upon starting a focused assessment. If a citizen previously ran a catalogue evaluation, `state.results` retained all 60 scheme evaluation results. When navigating to `/results`, those stale results were displayed immediately.

### 2. Why "New Interview" returned a welcome message without a question
- **Profile Persistence Conflict**: When a citizen answers interview questions, their demographic and financial attributes (e.g. `gender`, `age_years`, `resident_state`, `annual_family_income`, `bpl`, `aadhaar_linked_bank_account`) are saved to the persistent `CitizenProfile` in SQLite (`data/citizen_profiles.sqlite3`).
- **Question Selection Short-Circuit**: In `src/scheme_navigator/agents/interviewer.py` (`_choose_question`):
  ```python
  for slot in slots:
      rule_field = _slot_rule_field(slot)
      if profile.value_for_rule(rule_field) is not None:
          continue
  ```
  When `resetInterview()` was clicked, it created an ephemeral session thread ID but passed the existing populated `state.profile` to `/interview/start`. Because every required field for viable schemes already had a value in `profile`, `candidates` evaluated to an empty list `[]`.
- **Backend Returned `is_complete=True, next_question=None`**: With 0 missing candidate slots, `_choose_question()` returned `{"next_question": None, "is_complete": True}`.
- **Frontend Hang**: In `static/index.html`, `startGuidedInterview()` printed the welcome message. Then `handleInterviewTurn()` received `res.question == null`. Because the frontend had no handling for instant completion on turn 1, the chat stream stopped dead after the greeting, leaving the citizen with a blank chat area and no next action.

### 3. Where interview context was stored
- Previously, interview context was stored inconsistently across three disjoint systems:
  - **Client memory**: `state.interviewStarted`, `state.selectedSchemeId`, `state.threadId`, `state.results` (ephemeral, lost on refresh).
  - **LangGraph checkpointer**: In `data/interviews.sqlite3`, keyed strictly by `thread_id` using raw serialized binary checkpoints.
  - **Citizen store**: In `data/citizen_profiles.sqlite3`, a loose `interview_runs` table containing only `(thread_id, session_id, scheme_id, status, state_json)`. It had no mode tracking, no versioning, and no evaluation results persistence.

### 4. How selectedSchemeId was lost across navigation
- `state.selectedSchemeId` existed solely as a top-level JavaScript variable.
- Navigating to `/interview` directly or clicking the navbar button bypassed Explore, leaving `state.selectedSchemeId` as `null` or pointing to a stale scheme from a previous session.
- The server-side `/interview/start` API accepted `scheme_id` as an optional parameter, but never enforced mode boundaries, stored mode metadata, or validated `scheme_id` against the published catalogue.

### 5. How the LangGraph interview agent decides which question to ask next
- The agent builds an `InterviewState` containing `profile`, `candidate_schemes`, and `asked_fields`.
- In `_choose_question`:
  - It iterates over viable schemes and evaluates their eligibility AST using `evaluate_node`.
  - It collects `unresolved_fields`.
  - For each unresolved field with a defined `QUESTION_SPEC`, it calculates information gain using Shannon entropy:
    $$IG(S, \text{slot}) = H(S) - \sum_{v \in \text{values}} \frac{|S_v|}{|S|} H(S_v)$$
  - It sorts candidates by score descending and selects the slot with the highest information gain.

### 6. Why the interview agent asked questions irrelevant to the target scheme
- In focused assessment, the candidate schemes list in LangGraph remained populated with all active catalogue schemes.
- The agent calculated entropy across *all* catalogue schemes, frequently deciding that `is_student`, `caste_category`, or `has_land` had high information gain across the broader catalogue, even when the citizen was attempting to evaluate *Mukhyamantri Majhi Ladki Bahin Yojana* (which only depends on gender, residence, age, income, and Aadhaar bank account).

### 7. Where transcripts, state, questions and answers are persisted
- LangGraph checkpoints are written to `data/interviews.sqlite3` under `checkpoints` and `checkpoint_blobs`.
- Citizen demographic profiles are stored in `data/citizen_profiles.sqlite3` (`citizen_profiles` table).
- Interview runs are stored in `data/citizen_profiles.sqlite3` (`interview_runs` table).

### 8. How eligibility evaluation consumes interview state
- Upon interview completion, `profile` in `InterviewState` contains all answers normalized to citizen attributes.
- Previously, the client triggered `POST /eligibility/evaluate` with `state.profile`. The rule engine evaluated all 60 catalogue schemes against the profile, returning a massive array of evaluations.

### 9. Why View Results displayed stale results from another interview
- The results view was backed by a single global variable `state.results`.
- When switching between Discovery and Focused assessments, `state.results` was never cleared or isolated by `run_id`.
- Furthermore, because `/interview/start` did not return evaluations on completion, the client relied on whatever results were already in memory or called the full-catalogue evaluate endpoint.

---

## Architectural Remedies Applied

1. **Domain Models (`src/scheme_navigator/domain/models.py`)**:
   - Added `InterviewMode` enum: `DISCOVERY`, `FOCUSED_SCHEME`.
   - Added `InterviewRunContext` model with `interview_run_id`, `mode`, `target_scheme_id`, `citizen_profile_id`, `catalogue_version`, `rule_version`, `language`, `status`, `created_at`, `completed_at`.
   - Updated `InterviewStart` schema to accept `mode`, `target_scheme_id`, `scope`.

2. **Database Migrations (`src/scheme_navigator/core/migrations.py`)**:
   - Added Migration version 2 to `CITIZEN_PROFILE_MIGRATIONS`, altering `interview_runs` to add `mode`, `target_scheme_id`, `catalogue_version`, `rule_version`, `language`, `completed_at`, `results_json`.

3. **Persistent Citizen Store (`src/scheme_navigator/core/citizen_store.py`)**:
   - Updated `create_interview_run` to persist run mode, target scheme, versions, and language.
   - Added `complete_interview_run(thread_id, results, final_state)` to atomically persist evaluation results with the run.
   - Added `get_interview_run_results(thread_id)` to retrieve run-isolated results.

4. **Interviewer Agent Optimization (`src/scheme_navigator/agents/interviewer.py`)**:
   - In `_choose_question`: If `mode == "FOCUSED_SCHEME"` or `target_scheme_id` is set, restricts candidate schemes strictly to `[target_scheme_id]`.
   - Assigns direct priority to target scheme missing fields, skipping all irrelevant catalogue slots.
   - If missing statutory fields cannot be collected via questions, returns structured diagnostic `QUESTION_SELECTION_UNRESOLVED`.
   - Enriched question payload with `question_id`, `required`, `reason`, `language`.

5. **API Backend Hardening (`src/scheme_navigator/api/main.py`)**:
   - In `start_interview`: Validates `target_scheme_id` against canonical catalog; returns 404 for invalid/hallucinated schemes.
   - Records `InterviewRunContext` in persistent store.
   - In `_interview_response`: Upon `is_complete`, computes evaluation results (strictly target scheme in `FOCUSED_SCHEME`, or all candidate schemes in `DISCOVERY`), and atomically completes the run via `complete_interview_run`.
   - Added endpoint `GET /interview/{thread_id}/results` with RBAC and tenant authorization.

6. **Frontend State Isolation (`static/index.html`)**:
   - Added `targetSchemeId`, `interviewMode`, `runResults` to `state`.
   - Updated `startFindSchemesJourney()`: sets `interviewMode = 'DISCOVERY'`, clears results, generates `run_disc_...`.
   - Updated `startFocusedAssessment(schemeId)`: sets `interviewMode = 'FOCUSED_SCHEME'`, `targetSchemeId = schemeId`, clears results, generates `run_foc_...`.
   - Updated `resetInterview()`: respects active journey context, generating fresh `run_foc_...` or `run_disc_...`.
   - Added `renderInterviewJourneyChoice()`: handles direct visits to `/interview` with explicit options.
   - Updated `handleInterviewTurn()`: handles turn 1 instant completions gracefully with clear messaging and `✨ View Results` CTA.
   - Updated `renderResultsCards()`: in `FOCUSED_SCHEME` mode, hides `.scoreboard` and `#not-eligible-accordion`, rendering a dedicated focused result card with verified statutory remarks, satisfied/unmet/missing criteria pills, and official Government Resolution citations.
