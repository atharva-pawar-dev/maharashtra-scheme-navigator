from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime

from scheme_navigator.domain.models import DocumentFinding, ExtractedDocument


@dataclass(frozen=True)
class PdfDocumentGroup:
    """One logical document inferred from one or more consecutive PDF pages."""

    document: ExtractedDocument
    page_numbers: tuple[int, ...]


@dataclass(frozen=True)
class PdfPageFieldConflict:
    """A field whose non-empty extracted values disagree across PDF pages."""

    field_name: str
    finding: DocumentFinding


def _normalized_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _same_logical_certificate(
    left: ExtractedDocument,
    right: ExtractedDocument,
) -> bool:
    """Conservative page-linking rule; this is not document authenticity checking."""
    if left.document_type != right.document_type:
        return False
    if left.document_type in {"other", "unknown"}:
        return False

    # Require at least one exact identity anchor shared by both pages.
    matching_identity_anchor = False

    if left.person_name and right.person_name:
        if _normalized_name(left.person_name) != _normalized_name(right.person_name):
            return False
        matching_identity_anchor = True

    if left.date_of_birth and right.date_of_birth:
        if left.date_of_birth != right.date_of_birth:
            return False
        matching_identity_anchor = True

    if not matching_identity_anchor:
        return False

    # If both pages expose a value for one of these fields, it must agree.
    # Missing on one page is allowed because a multi-page certificate can split fields.
    consistency_fields = (
        "valid_financial_year",
        "annual_family_income",
        "income_currency",
        "issue_date",
        "valid_until",
        "certificate_number_masked",
    )
    for field_name in consistency_fields:
        left_value = getattr(left, field_name)
        right_value = getattr(right, field_name)
        if left_value is not None and right_value is not None and left_value != right_value:
            return False

    return True


def _merge_page_group(
    pages: list[tuple[int, ExtractedDocument]],
    source_file_sha256: str,
    group_index: int,
) -> PdfDocumentGroup:
    first_page_number, first_document = pages[0]
    merged_data = first_document.model_dump(mode="python")

    # Carry forward fields that were absent from the first page but found on later pages.
    optional_fields = (
        "person_name",
        "date_of_birth",
        "issue_date",
        "valid_until",
        "valid_financial_year",
        "annual_family_income",
        "income_currency",
        "certificate_number_masked",
    )
    for _, page_document in pages[1:]:
        for field_name in optional_fields:
            if merged_data.get(field_name) is None:
                merged_data[field_name] = getattr(page_document, field_name)

    # Preserve evidence with its page number; do not silently overwrite one page with another.
    evidence_by_field: dict[str, list[str]] = {}
    notes: list[str] = []
    for page_number, page_document in pages:
        for field_name, evidence_text in page_document.field_evidence.items():
            item = f"Page {page_number}: {evidence_text}"
            if item not in evidence_by_field.setdefault(field_name, []):
                evidence_by_field[field_name].append(item)
        for note in page_document.extraction_notes:
            item = f"Page {page_number}: {note}"
            if item not in notes:
                notes.append(item)

    merged_data["field_evidence"] = {
        field_name: " | ".join(page_evidence)
        for field_name, page_evidence in evidence_by_field.items()
    }
    merged_data["confidence"] = min(page.confidence for _, page in pages)
    merged_data["extraction_notes"] = notes[:20]
    merged_data["source_file_sha256"] = source_file_sha256
    merged_data["document_id"] = hashlib.sha256(
        f"{source_file_sha256}:logical-document:{group_index}".encode("utf-8")
    ).hexdigest()[:16]

    page_numbers = tuple(page_number for page_number, _ in pages)
    if len(pages) > 1:
        merged_data["extraction_notes"] = (
            merged_data["extraction_notes"]
            + [
                "Consecutive PDF pages were grouped using matching document type, "
                "identity evidence and consistent overlapping fields. Review the "
                "page-level extractions to confirm they belong to one certificate."
            ]
        )[:20]

    return PdfDocumentGroup(
        document=ExtractedDocument.model_validate(merged_data),
        page_numbers=page_numbers,
    )


def group_pdf_page_extractions(
    page_documents: list[tuple[int, ExtractedDocument]],
    source_file_sha256: str,
) -> list[PdfDocumentGroup]:
    """Group adjacent PDF pages that strongly appear to be one certificate.

    Pages are merged only if their document types match, at least one shared
    identity field matches exactly, and every other overlapping certificate field
    is consistent. Ambiguous or conflicting pages remain separate so that
    ``find_pdf_page_field_conflicts`` can report disagreements with page evidence.
    """
    if not page_documents:
        raise ValueError("At least one extracted PDF page is required.")

    page_groups: list[list[tuple[int, ExtractedDocument]]] = []
    for page_number, document in page_documents:
        if page_number < 1:
            raise ValueError("PDF page numbers must start at 1.")

        if page_groups and page_groups[-1][-1][0] == page_number - 1:
            previous_documents = [page_doc for _, page_doc in page_groups[-1]]
            if all(_same_logical_certificate(previous, document) for previous in previous_documents):
                page_groups[-1].append((page_number, document))
                continue

        page_groups.append([(page_number, document)])

    return [
        _merge_page_group(group, source_file_sha256, index)
        for index, group in enumerate(page_groups, start=1)
    ]


# Fields compared across page-level Gemini results. Identity fields can be
# compared across document types; certificate-specific fields are compared only
# between pages with the same detected document type.
_PDF_CONFLICT_FIELDS: tuple[tuple[str, str, bool], ...] = (
    ("person_name", "applicant name", False),
    ("date_of_birth", "date of birth", False),
    ("valid_financial_year", "financial year", True),
    ("annual_family_income", "annual family income", True),
    ("income_currency", "income currency", True),
    ("issue_date", "issue date", True),
    ("valid_until", "valid-until date", True),
    ("certificate_number_masked", "masked certificate number", True),
)

_FULL_ID_PATTERN = re.compile(r"(?<!\d)\d{4}[- ]?\d{4}[- ]?\d{4}(?!\d)")
_PAGE_NUMBER_PATTERN = re.compile(r"\bPage\s+(\d+)\s*:", re.IGNORECASE)

_CONFLICT_ACTIONS = {
    "person_name": (
        "Compare the original pages and confirm whether they refer to the same applicant. "
        "Correct an extraction error or obtain an authoritative correction if the source differs."
    ),
    "date_of_birth": (
        "Compare the original pages and confirm the applicant's date of birth against the "
        "authoritative identity document before proceeding."
    ),
    "valid_financial_year": (
        "Inspect both original pages and confirm the financial year printed on the certificate. "
        "Do not assume either extracted year is correct."
    ),
    "annual_family_income": (
        "Inspect both original pages and confirm the annual family income from the issuing "
        "certificate. Do not select either amount automatically."
    ),
    "income_currency": (
        "Inspect the original pages and confirm the currency associated with the income amount."
    ),
    "issue_date": (
        "Compare the original pages and confirm the certificate's printed issue date."
    ),
    "valid_until": (
        "Compare the original pages and confirm the printed validity or expiry date."
    ),
    "certificate_number_masked": (
        "Compare the masked certificate references on the original pages. Do not disclose or "
        "enter a full government identifier in the report."
    ),
}


def _normalized_conflict_value(field_name: str, value: object) -> object:
    if isinstance(value, (date, datetime)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    if field_name == "person_name" and isinstance(value, str):
        return _normalized_name(value)
    if isinstance(value, str):
        normalized = " ".join(unicodedata.normalize("NFKC", value).casefold().split())
        if field_name == "certificate_number_masked":
            return normalized.replace(" ", "")
        return normalized
    return value


def _safe_page_evidence(
    page_number: int,
    document: ExtractedDocument,
    field_name: str,
) -> str:
    """Return a short, page-labelled excerpt without exposing a full 12-digit ID."""
    evidence = document.field_evidence.get(field_name)
    if field_name == "certificate_number_masked":
        if evidence or document.certificate_number_masked:
            return f"Page {page_number}: [masked certificate-number evidence withheld]"
    if isinstance(evidence, str) and evidence.strip():
        excerpt = " ".join(evidence.split())
        excerpt = _FULL_ID_PATTERN.sub("[REDACTED 12-DIGIT ID]", excerpt)
        excerpt = excerpt[:180]
        return f"Page {page_number}: \"{excerpt}\""

    # Do not echo names, dates of birth, or certificate numbers when the model did
    # not provide supporting text. Values remain available in page_extractions.
    if field_name in {"person_name", "date_of_birth", "certificate_number_masked"}:
        fallback = "extracted value differs; supporting excerpt unavailable"
    else:
        fallback = str(getattr(document, field_name))
    return f"Page {page_number}: {fallback}"


def find_pdf_page_field_conflicts(
    page_documents: list[tuple[int, ExtractedDocument]],
) -> list[PdfPageFieldConflict]:
    """Find conflicting non-null fields across original PDF page extractions.

    This must be called with page-level results, before grouping. A conflict keeps
    pages separate during grouping and is surfaced as a review finding here.
    Missing values are not treated as disagreements. For certificate-specific
    fields, different document types are not compared against one another.
    """
    conflicts: list[PdfPageFieldConflict] = []

    if not page_documents:
        return conflicts

    for field_name, field_label, same_document_type_only in _PDF_CONFLICT_FIELDS:
        candidate_sets: dict[str, list[tuple[int, ExtractedDocument, object]]] = {}
        for page_number, document in page_documents:
            value = getattr(document, field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            type_key = document.document_type if same_document_type_only else "all"
            candidate_sets.setdefault(type_key, []).append((page_number, document, value))

        for type_key, candidates in candidate_sets.items():
            value_groups: dict[object, list[tuple[int, ExtractedDocument, object]]] = {}
            for item in candidates:
                page_number, document, value = item
                normalized = _normalized_conflict_value(field_name, value)
                value_groups.setdefault(normalized, []).append(item)

            if len(value_groups) < 2:
                continue

            evidence_items: list[str] = []
            conflict_page_ids: list[str] = []
            for page_number, document, _ in candidates:
                evidence_items.append(_safe_page_evidence(page_number, document, field_name))
                if document.document_id not in conflict_page_ids:
                    conflict_page_ids.append(document.document_id)

            # Different scripts cannot reliably establish that names refer to
            # different people; keep this a review warning rather than an error.
            severity = "warning"
            if field_name == "date_of_birth":
                severity = "error"
            elif field_name == "person_name":
                script_families = {
                    _script_family(str(value))
                    for _, _, value in candidates
                    if value is not None
                }
                severity = "warning" if len(script_families) > 1 else "error"

            type_suffix = (
                f" ({type_key.replace('_', ' ')})"
                if same_document_type_only
                else ""
            )
            message = (
                f"{field_label}{type_suffix} has conflicting extracted values across PDF pages: "
                + "; ".join(evidence_items[:10])
                + ". Do not select a value automatically; inspect the original pages."
            )

            conflicts.append(
                PdfPageFieldConflict(
                    field_name=field_name,
                    finding=DocumentFinding(
                        code="DOCUMENT_FIELD_CONFLICT",
                        severity=severity,
                        category=(
                            "document_validity"
                            if field_name in {
                                "valid_financial_year",
                                "issue_date",
                                "valid_until",
                            }
                            else "document_consistency"
                        ),
                        message=message,
                        recommended_action=_CONFLICT_ACTIONS.get(
                            field_name,
                            "Inspect the original pages and confirm the conflicting value manually.",
                        ),
                        document_ids=conflict_page_ids,
                        evidence=evidence_items[:10],
                        page_numbers=sorted({
                            int(match.group(1))
                            for excerpt in evidence_items
                            for match in _PAGE_NUMBER_PATTERN.finditer(excerpt)
                        })[:20],
                    ),
                )
            )

    return conflicts


def _script_family(value: str) -> str:
    has_latin = any("A" <= char.upper() <= "Z" for char in value)
    has_devanagari = any("\u0900" <= char <= "\u097f" for char in value)
    if has_latin and has_devanagari:
        return "mixed"
    if has_latin:
        return "latin"
    if has_devanagari:
        return "devanagari"
    return "other"
