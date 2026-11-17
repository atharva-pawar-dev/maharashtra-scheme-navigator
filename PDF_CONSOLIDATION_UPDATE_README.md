# Scheme Navigator — PDF page consolidation update

This patch introduces conservative grouping of consecutive PDF pages that appear to belong to one certificate.

## Files in this patch

- `src/scheme_navigator/api/main.py` — keeps the original page-level extraction results, groups compatible pages into logical documents, and audits logical documents.
- `src/scheme_navigator/documents/grouping.py` — page grouping and evidence-preserving merge logic.
- `tests/test_document_upload.py` — updated upload tests, including a two-page same-certificate case.
- `tests/test_pdf_grouping.py` — focused tests for grouping and non-grouping cases.

No API key or real citizen document is included.

## Apply the patch

Extract this ZIP into the project root so the `src` and `tests` folders merge with the existing folders. Allow `main.py` and `test_document_upload.py` to be replaced. The new `grouping.py` and `test_pdf_grouping.py` will be added.

Back up your current `src/scheme_navigator/api/main.py` before replacing it.

## Run tests

With the project virtual environment activated from the project root:

```powershell
python -m pytest tests/test_document_audit.py tests/test_gemini_extractor.py tests/test_document_upload.py tests/test_pdf_preprocess.py tests/test_pdf_grouping.py -q
python -m pytest -q
```

The patch was validated against the supplied project snapshot: 44 tests passed.

## Response behavior change

For PDF uploads:

- `page_extractions` contains the original per-page Gemini extraction results.
- `extracted_documents` contains logical documents used by the audit. Consecutive pages are grouped only when document type matches, at least one shared identity anchor (name or DOB) matches exactly, and all overlapping key fields are consistent.
- `document_groups` lists each logical document ID and its source page numbers.
- Ambiguous or conflicting pages remain separate; the grouping heuristic does not prove that pages are part of the same genuine certificate.

For image uploads, `extracted_documents` still contains the one extracted document; `page_extractions` and `document_groups` are empty lists.
