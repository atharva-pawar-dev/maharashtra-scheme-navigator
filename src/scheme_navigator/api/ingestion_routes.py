from __future__ import annotations

import difflib
import hashlib
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Annotated

from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from pypdf import PdfReader

from scheme_navigator.ingestion.dedup import detect_scheme_duplicates
from scheme_navigator.ingestion.lineage import get_scheme_lineage, list_registered_lineages
from scheme_navigator.ingestion.models import (
    DocumentChangeEvent,
    DuplicateDetectionReport,
    IngestedSnapshot,
    IngestionReviewItem,
    IngestionReviewStatus,
    IngestionSourceKind,
    SchemeLineageReport,
)
from scheme_navigator.ingestion.store import IngestionStore
from scheme_navigator.security.audit_logger import audit_logger
from scheme_navigator.security.auth import require_role
from scheme_navigator.security.models import AuditEventType, UserRole, UserSession
from scheme_navigator.security.rate_limiter import rate_limit
from scheme_navigator.security.upload import validate_uploaded_document_security

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


def _store() -> IngestionStore:
    return IngestionStore()


class DuplicateCheckRequest(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    department: str | None = None
    candidate_id: str | None = None


class ReviewItemUpdateRequest(BaseModel):
    status: IngestionReviewStatus
    reviewer_id: str = Field(min_length=2, max_length=120)
    review_notes: str | None = Field(default=None, max_length=2000)


@router.get("/sources", response_model=list[IngestedSnapshot])
def list_ingested_sources(source_kind: str | None = None) -> list[IngestedSnapshot]:
    """List ingested source snapshots and version integrity records."""
    return _store().list_snapshots(source_kind=source_kind)


@router.get("/changes", response_model=list[DocumentChangeEvent])
def list_document_changes(source_url: str | None = None) -> list[DocumentChangeEvent]:
    """List detected modifications to official government source documents."""
    return _store().list_changes(source_url=source_url)


@router.get("/queue", response_model=list[IngestionReviewItem])
def list_review_queue(
    status: Annotated[IngestionReviewStatus | None, Query()] = None
) -> list[IngestionReviewItem]:
    """List items in the human-review queue for newly ingested scheme documents."""
    return _store().list_review_queue(status=status)


@router.get("/queue/{item_id}", response_model=IngestionReviewItem)
def get_review_item(item_id: str) -> IngestionReviewItem:
    """Retrieve an individual ingestion review queue item."""
    item = _store().get_review_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found.")
    return item


@router.post("/queue/{item_id}/review", response_model=dict)
def update_review_item(item_id: str, payload: ReviewItemUpdateRequest) -> dict:
    """Submit an analyst or legal review for an ingested scheme record."""
    store = _store()
    item = store.get_review_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found.")

    updated = store.update_review_status(
        item_id=item_id,
        status=payload.status,
        reviewer_id=payload.reviewer_id,
        notes=payload.review_notes,
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update review item status.")

    return {
        "item_id": item_id,
        "status": payload.status.value,
        "reviewer_id": payload.reviewer_id,
        "message": f"Review status updated to {payload.status.value}. Candidate remains in draft quarantine.",
    }


@router.post("/detect-duplicates", response_model=DuplicateDetectionReport)
def check_scheme_duplicates(payload: DuplicateCheckRequest) -> DuplicateDetectionReport:
    """Check a candidate scheme title against the registered alias index and distinct branches."""
    return detect_scheme_duplicates(
        candidate_title=payload.title,
        department=payload.department,
        candidate_id=payload.candidate_id,
    )


@router.get("/lineage/{scheme_id}", response_model=SchemeLineageReport)
def view_scheme_lineage(scheme_id: str) -> SchemeLineageReport:
    """Inspect the chronological Government Resolution lineage and superseded rules for a scheme."""
    lineage = get_scheme_lineage(scheme_id)
    if not lineage:
        raise HTTPException(
            status_code=404,
            detail=f"Lineage for scheme '{scheme_id}' was not found in the registered repository.",
        )
    return lineage


@router.get("/lineages", response_model=list[SchemeLineageReport])
def list_all_lineages() -> list[SchemeLineageReport]:
    """List all registered legislative and executive Government Resolution lineages."""
    return list_registered_lineages()


@router.post(
    "/upload-source",
    tags=["ingestion"],
    dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))],
)
async def upload_source_document(
    file: UploadFile = File(...),
    source_url: str = Form(...),
    official_reference: str | None = Form(default=None),
    publication_date: str | None = Form(default=None),
    source_kind: IngestionSourceKind = Form(default=IngestionSourceKind.GOVERNMENT_RESOLUTION),
    session: UserSession = Depends(require_role(UserRole.ANALYST)),
) -> dict:
    """Manually ingest an official Government Resolution or notification document for air-gapped review."""
    raw = await file.read(15 * 1024 * 1024 + 1)
    if len(raw) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Uploaded source exceeds 15 MiB limit.")
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    filename = file.filename or "uploaded_source"
    try:
        safe_fname, detected_mime = validate_uploaded_document_security(raw, filename, file.content_type)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

    sha256 = hashlib.sha256(raw).hexdigest()
    snapshot_id = f"snap_{uuid.uuid4().hex[:16]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    title = safe_fname
    extracted_text = ""
    is_pdf = detected_mime in {"application/pdf", "application/x-pdf"} or safe_fname.lower().endswith(".pdf")
    if is_pdf:
        try:
            reader = PdfReader(BytesIO(raw))
            extracted_text = "\n".join((p.extract_text() or "") for p in reader.pages)
            if reader.metadata and reader.metadata.title:
                title = str(reader.metadata.title).strip() or safe_fname
        except Exception:
            extracted_text = f"Binary PDF source document ({len(raw)} bytes)."
    elif "html" in detected_mime or detected_mime.startswith("text/"):
        soup = BeautifulSoup(raw, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else safe_fname
        for tag in soup(["script", "style", "noscript", "nav", "footer"]):
            tag.decompose()
        extracted_text = soup.get_text(" ", strip=True)

    out_dir = Path("data/ingested")
    out_dir.mkdir(parents=True, exist_ok=True)
    stored_path = out_dir / f"{snapshot_id}_{safe_fname}"
    stored_path.write_bytes(raw)

    snapshot = IngestedSnapshot(
        snapshot_id=snapshot_id,
        source_url=source_url,
        final_url=source_url,
        source_kind=source_kind,
        sha256=sha256,
        byte_size=len(raw),
        retrieved_at=now_iso,
        publication_date=publication_date,
        official_reference=official_reference,
        title=title,
        extracted_text=extracted_text,
    )

    store = _store()
    saved_snapshot, change_event = store.save_snapshot(snapshot)

    review_item_id = f"rev_{uuid.uuid4().hex[:12]}"
    review_item = IngestionReviewItem(
        item_id=review_item_id,
        source_url=source_url,
        source_title=title,
        source_kind=source_kind,
        sha256=sha256,
        retrieved_at=now_iso,
        review_status=IngestionReviewStatus.PENDING_REVIEW,
        extracted_scheme_data={"title": title, "reference": official_reference, "source_kind": source_kind.value},
        created_at=now_iso,
        updated_at=now_iso,
    )
    store.enqueue_for_review(review_item)

    audit_logger.log_event(
        event_type=AuditEventType.DOC_UPLOADED,
        actor_id=session.user_id,
        actor_role=session.role.value,
        action="manual_source_ingestion",
        resource=snapshot_id,
        details={"sha256": sha256, "url": source_url, "size": len(raw)},
    )

    return {
        "snapshot_id": snapshot_id,
        "sha256": sha256,
        "title": title,
        "review_item_id": review_item_id,
        "change_event": change_event.summary if change_event else None,
        "review_status": "pending_review",
    }


@router.get(
    "/compare",
    tags=["ingestion"],
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
def compare_source_snapshots(
    snapshot_id_a: str,
    snapshot_id_b: str,
    session: UserSession = Depends(require_role(UserRole.ANALYST)),
) -> dict:
    """Compare two ingested snapshots to inspect legal changes and text differences."""
    store = _store()
    snap_a = store.get_snapshot_by_id(snapshot_id_a)
    snap_b = store.get_snapshot_by_id(snapshot_id_b)
    if not snap_a or not snap_b:
        raise HTTPException(status_code=404, detail="One or both snapshots could not be found.")

    lines_a = snap_a.extracted_text.splitlines(keepends=True)
    lines_b = snap_b.extracted_text.splitlines(keepends=True)
    diff = list(difflib.unified_diff(lines_a, lines_b, fromfile=snap_a.snapshot_id, tofile=snap_b.snapshot_id, n=3))

    return {
        "snapshot_a": {
            "id": snap_a.snapshot_id,
            "sha256": snap_a.sha256,
            "title": snap_a.title,
            "retrieved_at": snap_a.retrieved_at,
            "byte_size": snap_a.byte_size,
        },
        "snapshot_b": {
            "id": snap_b.snapshot_id,
            "sha256": snap_b.sha256,
            "title": snap_b.title,
            "retrieved_at": snap_b.retrieved_at,
            "byte_size": snap_b.byte_size,
        },
        "is_content_identical": snap_a.sha256 == snap_b.sha256,
        "diff_line_count": len(diff),
        "unified_diff": "".join(diff[:100]),
    }
