# Adaptive Interview & Citizen Discovery Architecture

## 1. Overview & Dual-Mode Citizen Journeys
The Scheme Navigator interview engine (`scheme_navigator.agents.interview_graph`) powers two distinct citizen discovery pathways:
1. **Discovery Mode (`mode="DISCOVERY"`)**:
   - Catalogue-wide triage across all 75 canonical schemes.
   - Designed for citizens who do not know what schemes exist and want to discover everything they may qualify for.
   - Dynamically selects questions based on information gain and beneficiary profile attributes.
2. **Focused Scheme Assessment (`mode="FOCUSED_SCHEME"`)**:
   - Targeted evaluation anchored to an explicit `target_scheme_id` (e.g., launched from **Explore Schemes**).
   - Constrains probing strictly to the prerequisites, age brackets, income rules, and documents required by that designated scheme.
   - Never leaks results from or to other scheme evaluations.

---

## 2. Adaptive Question Selection & Information Gain
To respect citizen time, the interview agent evaluates profile state before asking any question:
- **Direct Evaluation on Sufficient Profile**: If the saved citizen profile already contains the attributes required to resolve eligibility, the engine evaluates immediately without displaying redundant questions.
- **Triage Priority Order**:
  1. *Location & Jurisdiction*: State domicile, district, and local government body (enables early elimination of geographically restricted municipal schemes).
  2. *Demographics*: Age, gender, marital status.
  3. *Socio-Economic*: Annual family income bracket, BPL ration card status, caste category.
  4. *Target Characteristics*: Occupation (farmer, student, artisan), disability status (UDID percentage).
- **No Infinite Loops**: Once an attribute is provided, it is committed to the session profile; the interviewer will never prompt for it again within the same session.

---

## 3. Strict Thread Isolation & Anti-Stale Guarantees
Cross-session data leakage and stale results from previous runs are eliminated by design:
1. **Cryptographic Thread Ownership**:
   - Every interview execution is bound to a unique `thread_id` (UUIDv4) and tied to the active citizen session (`session_id`).
   - Any attempt to access or answer an interview thread belonging to another session is rejected with HTTP 403 Forbidden.
2. **Run-Specific Transcript & Results Storage**:
   - Interview transcripts and interim evaluations are stored keyed to `(thread_id, run_index)` in `data/interviews.sqlite3`.
   - Results from previous threads are never cached or returned for a new thread.
3. **Dynamic Recalculation on Profile Relocation**:
   - If a citizen updates their location (e.g., from Pune Municipal Corporation to Pimpri Chinchwad Municipal Corporation), all location-dependent evaluations are immediately marked stale and recalculated. Unrelated personal attributes (income, age, gender) are preserved intact.

---

## 4. Multilingual Interview Execution (EN, MR, HI)
The interview engine operates natively in three languages without mixed-language artifacts:
- **Language Preservation**: The language selected by the citizen (`en`, `mr`, `hi`) is persisted on the thread state.
- **Natural Devanagari Prompts**: Questions, choices, explanation notes, and button labels are rendered using culturally natural Marathi and Hindi phrasing (not machine-translated English jargon).
- **Flexible Answer Parsing**: The NLU parser accepts:
  - Yes / No responses in all languages (*होय / नाही*, *हाँ / नहीं*).
  - Numeric entries for income (₹1.5 लाख, 1,50,000, 80k).
  - Conversational age inputs (28 वर्षे, 45 years).

---

## 5. Persistence, Pause & Resume Lifecycle
Citizen interviews can be paused, resumed, or recovered across browser sessions:
- **Live Persistence**: Every answer submission commits state to SQLite within an ACID transaction.
- **Browser Refresh Safety**: Reloading `/interview` reads the existing `thread_id` from secure local storage and queries `GET /interview/{thread_id}`, restoring the exact step, conversation history, and profile sidebar.
- **Thread Lifecycle States**:
  - `ACTIVE`: Interview in progress; awaiting citizen answer.
  - `EVALUATION_READY`: All required information collected; ready for scoreboard generation.
  - `COMPLETED`: Results generated and archived.
