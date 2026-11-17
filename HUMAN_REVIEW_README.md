# Scheme Navigator — Human-in-the-Loop Document Review (local prototype)

## What this update adds

A local SQLite-backed review workflow for document pre-audit results:

- `POST /documents/audit-upload` creates a `pending_review` case in non-production environments and returns `review.review_id`.
- `GET /documents/reviews/{review_id}` returns immutable original Gemini extractions, current corrected values, page mappings, original/current audit results and the event history.
- `PATCH /documents/reviews/{review_id}/documents/{document_id}` lets a reviewer confirm or correct explicitly allow-listed extracted fields.
- `POST /documents/reviews/{review_id}/complete` records that a human review has been completed and locks further corrections.
- `DELETE /documents/reviews/{review_id}` deletes the case and its event history.

Original Gemini/page extraction snapshots are not overwritten. Each field action records the reviewer-supplied ID, action (`field_confirmed` or `field_corrected`), original page value(s), previous value, new value, note and page numbers. After a PDF correction, current page overlays are re-grouped and the audit is recalculated. This can consolidate pages when the conflicting value is resolved.

## Apply the files

Copy these files into the matching locations in the project:

- `src/scheme_navigator/api/main.py` (replace)
- `src/scheme_navigator/domain/models.py` (replace)
- `src/scheme_navigator/documents/review_store.py` (new)
- `tests/test_document_review.py` (new)

No Gemini configuration change is required. The existing `GEMINI_API_KEY` and `GEMINI_MODEL` remain as configured.

## Local API flow

1. Upload a synthetic test certificate using `POST /documents/audit-upload`.
2. Copy the returned `review.review_id`.
3. Read the case using `GET /documents/reviews/{review_id}`.
4. Copy the current `document_id` for the field to edit.
5. Submit a correction or confirmation:

```json
{
  "reviewer_id": "local-reviewer-01",
  "note": "Compared page 2 against the original synthetic certificate.",
  "corrections": {
    "annual_family_income": 180000
  }
}
```

Use `null` to clear an extracted field. Only the fields declared in `DocumentFieldCorrections` are editable; document IDs, source hashes, evidence and model confidence cannot be changed through this endpoint.

6. Inspect the response. The original extraction remains unchanged; the current extraction and audit are recalculated. For PDFs, current page values are updated for the selected logical group and the pages are regrouped.
7. When review is complete, call:

```json
{
  "reviewer_id": "local-reviewer-01",
  "confirm_review_complete": true,
  "note": "I inspected the source pages and completed this pre-audit review."
}
```

A completed review becomes read-only. Completion does not mean that the certificate is genuine, officially verified or that the citizen is eligible for a scheme. Outstanding warnings may remain and should be disclosed.

## Local storage and privacy

- SQLite path defaults to `data/document_reviews.sqlite3`.
- Override it with `DOCUMENT_REVIEW_DB_PATH`.
- Cases expire after `data_retention_hours` from the existing app settings (default: 24 hours); expired rows are purged on review-store access.
- The raw uploaded PDF/image is **not** persisted. Extracted fields, evidence snippets, hashes and review events are persisted temporarily.
- `.sqlite3` files are ignored by Git in the starter `.gitignore`.
- Deleting a review deletes its event history as well.

## Important security limitation

This is a local developer prototype, not a production reviewer portal. `reviewer_id` is caller-supplied and is **not authenticated**. Review endpoints return 503 when `APP_ENV` is `production`/`prod` until proper authentication, authorization, CSRF protections for browser sessions, role checks and secure deployment controls are implemented. Do not expose a local development server or this SQLite database to a public network.

The original source document is not retained by the API. A reviewer must keep the synthetic/local source file available separately while inspecting it. A future browser UI can use a client-side document preview, or a properly secured document store with controlled retention.

## Test

With the project `.venv` active, run:

```powershell
python -m pytest tests/test_document_review.py -q
python -m pytest -q
```

The packaged project snapshot passed 65 tests in the development container. Your local count may differ if your repository contains additional tests.
