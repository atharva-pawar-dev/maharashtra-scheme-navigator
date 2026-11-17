# Scheme Navigator — Agent Instructions

## Product goal

Build a reliable, citizen-facing Maharashtra government scheme navigator. A citizen should be able to describe their circumstances, discover potentially relevant schemes, answer only useful follow-up questions, understand why a scheme may or may not apply, see what information is missing, and receive a practical document/application checklist with official links.

Product-first means shipping complete, testable citizen journeys. It does **not** mean relaxing accuracy, privacy, security, or engineering standards.

## Non-negotiable quality rules

1. Never invent scheme benefits, eligibility conditions, required documents, departments, application routes, deadlines, or official URLs.
2. Treat government scheme data as evidence-backed policy data. Record the official source, the relevant section, retrieval/verification time, and the evidence excerpt/hash where the existing model supports it.
3. Clearly distinguish `draft`, `reviewed`, `active`, and `retired` scheme rules. Do not mark a rule `active` or approved merely to make a demo work. Demo-only approval metadata is never production approval.
4. Preserve fail-closed, three-valued eligibility evaluation. Missing information is unknown, not false and not true. Never silently infer an answer.
5. Explain the conditions behind each eligibility result. Distinguish eligible, ineligible, needs-more-information, and unverified/not-approved states. Do not imply a government approval or guarantee of benefits.
6. AI may help with language understanding, extraction, and explanation; deterministic, reviewed rules remain authoritative for eligibility.
7. Do not let raw OCR or an unverified document overwrite an applicant-declared field. A completed review workflow is not proof of document authenticity or automatic confirmation of every extracted field.
8. Keep personal data out of logs, fixtures, commits, and external services unless required and explicitly authorized. Never expose full Aadhaar numbers, OTPs, or other secrets.
9. Prefer small, backward-compatible changes. Inspect before editing. Do not rewrite working subsystems without a demonstrated need.
10. Add or update tests for each behaviour change. Run targeted tests and the complete suite before declaring work complete. Report actual command output; never claim tests passed without running them.

## Known project context

- Local Windows project root: `C:\Users\Admin\Downloads\scheme-navigator\scheme-navigator`
- Python 3.11 virtual environment; run commands from the project root.
- Test commands:
  - `python -m compileall -q src tests`
  - `python -m pytest -q`
- Last previously reported full-suite baseline: 96 tests passed (2026-11-05).
- After the catalog-runtime change, the user reported 3 targeted catalog tests passed. The full suite still needs to be rerun after that change.
- Main package: `src/scheme_navigator/`
- Main API: `src/scheme_navigator/api/main.py`
- Settings: `src/scheme_navigator/core/config.py`
- Catalog loader: `src/scheme_navigator/services/catalog.py`
- Scheme/profile models and rule AST: `src/scheme_navigator/domain/models.py`
- Eligibility logic: `src/scheme_navigator/services/rule_engine.py`
- Interview graph: `src/scheme_navigator/agents/interviewer.py`
- Applicant assessment: `src/scheme_navigator/services/assessment.py`
- Document extraction/audit: `src/scheme_navigator/documents/audit.py`
- Document review persistence: `src/scheme_navigator/documents/review_store.py`

## Current architecture and observed behaviour

- `SchemeCatalog` loads a JSON array into validated `Scheme` models and rejects duplicate scheme IDs.
- Demo records live in `data/demo/schemes.json`. At last inspection there were only two, both named as demo fixtures: Mukhyamantri Majhi Ladki Bahin Yojana and Indira Gandhi National Old Age Pension Scheme (Maharashtra).
- Those demo records include illustrative benefits, eligibility rules, sources, evidence hashes, and explicit demo-only approval metadata. Do not present them as verified production guidance.
- `Scheme` has `sources`, `rule_version`, `rule_status`, `approved_by`, `approval_reference`, `last_verified_at`, and `languages` fields.
- `SourceReference` validates HTTPS URLs and verifies that `evidence_sha256` matches the UTF-8 evidence excerpt. A matching hash proves integrity of the stored excerpt, not authenticity or correctness of the source itself.
- `RuleNode` is a constrained JSON-logic-like AST with logical operators (`all`, `any`, `not`) and comparison operators. It limits supported citizen-profile fields and validates tree shape/depth.
- `evaluate_node` uses three-valued logic. Missing profile fields remain unknown.
- `has_non_demo_approval_metadata` gates confirmed eligibility decisions; keep demo markers from being treated as approval.
- Interview endpoints are `/interview/start` and `/interview/answer`. The LangGraph interview recalculates scheme evaluations and selects follow-up questions based on missing fields/information gain.
- Existing interview tests intentionally assert that an unapproved/demo scheme is retained provisionally even when a known criterion fails. Do not remove that safety behaviour without redesigning the distinction between provisional candidates and question-worthy schemes, with tests.
- `/schemes` returns the catalog and `/eligibility/evaluate` evaluates a submitted citizen profile against it.
- Production currently uses an empty catalog unless a configured catalog is provided.
- Recent catalog-runtime change adds `scheme_catalog_path` to settings and `SchemeCatalog.for_runtime(configured_path=..., demo_fixtures_enabled=...)`. Intended precedence: configured catalog, demo fixture when enabled, otherwise empty catalog. Preserve this behaviour unless tests and deployment requirements justify a change.
- The local `data/` folder contains SQLite stores (`document_reviews.sqlite3`, `interviews.sqlite3`, and possible WAL/SHM files). Treat them as local runtime data, not source-controlled fixtures.

## Product development priorities

Work in vertical slices, in this order unless repository evidence suggests a dependency:

1. **Reliable catalog loading and governance:** separate demo fixtures from a real curated catalog; establish validation and review gates; never manufacture production approval metadata.
2. **First complete discovery journey:** citizen starts an interview, answers profile questions, receives useful per-scheme results with explanations and missing fields, and gets a next-step/document/application plan.
3. **Official scheme coverage:** add schemes in small batches only after checking current official government sources and documenting eligibility, benefit, documents, application route, source section, and verification date.
4. **User experience:** make the journey clear and accessible; support Marathi/Hindi/English as data and UI coverage allows.
5. **Documents:** later connect extracted/corrected values to the citizen profile with explicit field-level provenance/confirmation. Do not expand document architecture before the core discovery journey works.

Avoid spending time on new infrastructure unless it directly unlocks a citizen-visible milestone.

## Safe repository and Git practices

Before editing, inspect `git status --short` and `git diff`. Do not overwrite or discard the user's uncommitted work.

Never commit:
- `.env` files or API keys/secrets;
- `.venv/`, Python caches, or generated build artifacts;
- local SQLite databases and their `-wal` / `-shm` files;
- uploaded citizen documents, extracted personal data, or local review/interview records.

If `.gitignore` is missing or incomplete, propose a minimal safe update and explain it before committing. Use a private repository for any remote collaboration. Do not push code or create public repositories without explicit user approval.

## Working protocol for coding agents

1. Start with a read-only reconnaissance: inspect `git status`, project tree, relevant modules, and tests.
2. State the specific citizen-facing outcome and acceptance criteria before editing.
3. Make the smallest cohesive change; avoid speculative refactors.
4. Add regression tests, including negative/unknown/unapproved cases where relevant.
5. Run compile checks, targeted tests, and the full test suite.
6. Review the final diff for accidental data, secrets, generated files, unrelated changes, and weakened safety checks.
7. Summarize files changed, behaviour gained, tests actually run/results, and any remaining risks. Do not commit/push/deploy unless expressly asked.

## Current immediate next step

Inspect the repository's current Git status and diff, then run:

```powershell
python -m compileall -q src tests
python -m pytest -q
```

Do not start another interview-engine redesign yet. First verify the catalog-runtime change against the full suite. Then plan the first end-to-end citizen discovery slice using the existing interview, rule engine, catalog, and assessment components.
