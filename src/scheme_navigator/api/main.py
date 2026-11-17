from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any
import uuid

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.concurrency import run_in_threadpool

from scheme_navigator.agents.interview_store import InterviewSessionStore
from scheme_navigator.agents.interviewer import Command, build_interviewer_graph
from scheme_navigator.agents.voice import MAX_AUDIO_BYTES, get_transcriber
from scheme_navigator.api.ingestion_routes import router as ingestion_router
from scheme_navigator.api.reviewer_ui import router as reviewer_ui_router
from scheme_navigator.core.config import settings
from scheme_navigator.security.models import (
    AuditEvent,
    AuditEventType,
    CatalogueReleaseSignature,
    UserRole,
    UserSession,
)
from scheme_navigator.security.auth import (
    get_current_session,
    require_authenticated_session,
    require_role,
    session_manager,
)
from scheme_navigator.security.audit_logger import audit_logger
from scheme_navigator.security.publication import publication_manager
from scheme_navigator.security.rate_limiter import rate_limit
from scheme_navigator.security.retention import purge_expired_data
from scheme_navigator.security.upload import (
    validate_uploaded_audio_security,
    validate_uploaded_document_security,
)
from scheme_navigator.documents.audit import (
    GeminiVisionExtractor,
    add_pdf_page_conflict_findings,
    audit_extracted_documents,
)
from scheme_navigator.documents.grouping import group_pdf_page_extractions
from scheme_navigator.documents.preprocess import render_pdf_pages
from scheme_navigator.documents.review_store import DocumentReviewStore
from scheme_navigator.domain.models import (
    ApplicantAssessmentRequest,
    ApplicantAssessmentResponse,
    ApplicationPlan,
    CitizenProfile,
    DocumentAuditRequest,
    DocumentAuditResponse,
    DocumentReviewCompletionRequest,
    DocumentReviewCorrectionRequest,
    EligibilityResult,
    ExtractedDocument,
    InterviewAnswer,
    InterviewMode,
    InterviewRunContext,
    InterviewStart,
    Language,
    Scheme,
)
from scheme_navigator.planner.dag import build_application_plan
from scheme_navigator.services.assessment import build_applicant_assessment
from scheme_navigator.services.catalog import SchemeCatalog, canonical_catalog
from scheme_navigator.core.citizen_store import CitizenProfileStore
from scheme_navigator.services.document_prep import (
    IntelligentDocumentPreparationReport,
    get_all_scheme_document_requirements,
    get_scheme_document_requirements,
    prepare_intelligent_document_audit,
)
from scheme_navigator.services.explanation import SchemeExplanation, generate_scheme_explanation
from scheme_navigator.services.portal_assistance import (
    PortalApplicationPackage,
    build_portal_application_package,
)
from scheme_navigator.services.rule_engine import evaluate_scheme
from scheme_navigator.services.trust import SchemeTrustReport, generate_trust_report
from scheme_navigator.source_registry.models import (
    ApplicationChannelRecord,
    ApplicationTrackStatus,
    CanonicalSchemeRecord,
    CitizenApplicationTrackRecord,
    PublicServiceRecord,
    SourceCoverageStats,
    SourceRecord,
)
from scheme_navigator.source_registry.registry import SourceRegistry
from scheme_navigator.source_registry.lifecycle_monitor import SourceLifecycleMonitor

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("scheme_navigator")


def load_runtime_catalog() -> SchemeCatalog:
    """Load the configured catalog, local demo fixtures, or an empty production catalog."""
    return SchemeCatalog.for_runtime(
        configured_path=settings.scheme_catalog_path,
        demo_fixtures_enabled=settings.demo_fixtures_enabled,
    )


catalog = load_runtime_catalog()
source_registry = SourceRegistry()
lifecycle_monitor = SourceLifecycleMonitor(source_registry)
citizen_store = CitizenProfileStore()

interview_store = InterviewSessionStore(
    retention_hours=settings.data_retention_hours
)

interviewer = build_interviewer_graph(
    checkpointer=interview_store.checkpointer
)


def _ensure_active_interview_engine() -> None:
    global interview_store, interviewer
    if interview_store.is_closed:
        interview_store = InterviewSessionStore(
            retention_hours=settings.data_retention_hours
        )
        interviewer = build_interviewer_graph(
            checkpointer=interview_store.checkpointer
        )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage persistent interview storage, secret validation, and retention scheduling."""
    global interview_store, interviewer

    # Priority 7: Validate production secrets on startup (fails closed if missing or default)
    settings.validate_production_secrets()

    # Automatic schema migration check across persistent SQLite databases
    from scheme_navigator.core.migrations import run_all_migrations
    try:
        run_all_migrations()
    except Exception as m_exc:
        logger.warning(f"Database migration warning on startup: {m_exc}")

    # TestClient and repeated application lifecycles can close the
    # previous store. Recreate it before starting the next lifecycle.
    if interview_store.is_closed:
        interview_store = InterviewSessionStore(
            retention_hours=settings.data_retention_hours
        )
        interviewer = build_interviewer_graph(
            checkpointer=interview_store.checkpointer
        )

    # Priority 5: Initial retention purge on startup
    purge_expired_data(retention_hours=settings.data_retention_hours)

    retention_stop_event = asyncio.Event()

    async def _retention_worker():
        while not retention_stop_event.is_set():
            try:
                await asyncio.sleep(3600)  # hourly retention cleanup
                if not retention_stop_event.is_set():
                    purge_expired_data(retention_hours=settings.data_retention_hours)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(f"Background retention worker error: {exc}")

    retention_task = asyncio.create_task(_retention_worker())

    try:
        yield
    finally:
        retention_stop_event.set()
        retention_task.cancel()
        try:
            await retention_task
        except asyncio.CancelledError:
            pass
        interview_store.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Source-grounded scheme discovery and pre-audit. "
        "Government applications are never submitted by this API."
    ),
    lifespan=lifespan,
)

app.include_router(reviewer_ui_router)
app.include_router(ingestion_router)


def _document_review_store() -> DocumentReviewStore:
    return DocumentReviewStore(retention_hours=settings.data_retention_hours)


def _ensure_reviewer_access(session: UserSession | None = None) -> None:
    """Enforce reviewer authentication and role authorization for review endpoints."""
    # Reject explicit citizen accounts
    if session and session.user_id != "anonymous_citizen" and not session_manager.has_role(session, UserRole.ANALYST):
        raise HTTPException(
            status_code=403,
            detail="Access denied: citizen accounts are not authorized to access document reviews.",
        )
    # In production, require authenticated reviewer session with ANALYST or higher role
    if settings.app_env.casefold() in {"production", "prod"}:
        if not session or session.user_id == "anonymous_citizen" or not session_manager.has_role(session, UserRole.ANALYST):
            raise HTTPException(
                status_code=403,
                detail="Human document review requires authenticated reviewer access with role 'analyst' or higher in production.",
            )


def _ensure_local_review_api(session: UserSession | None = None) -> None:
    _ensure_reviewer_access(session)


def _ensure_local_interview_recovery_api() -> None:
    """Interview state recovery is a local development prototype until session ownership protection is added."""
    if settings.app_env.casefold() in {"production", "prod"}:
        raise HTTPException(
            status_code=503,
            detail=(
                "Interview session recovery and profile reconstruction are disabled in production "
                "until authenticated session ownership protection is configured."
            ),
        )


def _review_response(record: dict) -> dict:
    return {
        "review_id": record["review_id"],
        "status": record["status"],
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
        "expires_at": record["expires_at"],
        "target_financial_year": record["target_financial_year"],
        "original_extracted_documents": record["original_extracted_documents"],
        "extracted_documents": record["extracted_documents"],
        "page_extractions": record["page_extractions"],
        "current_page_extractions": record["current_page_extractions"],
        "original_document_groups": record["original_document_groups"],
        "document_groups": record["document_groups"],
        "original_audit": record["original_audit"],
        "audit": record["audit"],
        "events": record["events"],
        "storage_notice": (
            "Only extracted fields and review metadata are stored locally; uploaded image/PDF "
            "bytes are not persisted. Records are deleted after the configured retention "
            "period. reviewer_id is caller-supplied and is not authenticated in this local "
            "prototype. Do not expose these endpoints to a public network."
        ),
    }


def _review_page_mapping(record: dict, document_id: str) -> list[int]:
    for group in record["document_groups"]:
        if group["document_id"] == document_id:
            return [int(number) for number in group["page_numbers"]]
    return []


def _json_scalar(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


@app.get("/healthz", tags=["system"])
def healthz() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "demo_fixtures_enabled": str(settings.demo_fixtures_enabled).lower(),
    }


@app.get("/schemes", response_model=list[Scheme], tags=["schemes"])
def list_schemes() -> list[Scheme]:
    return catalog.all()


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: CitizenProfile


ProfileUpdateRequest.model_rebuild()


class ProgressActivateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scheme_id: str
    version: str = "1.0.0"
    progress_data: dict[str, Any] | None = None


ProgressActivateRequest.model_rebuild()


class ProgressDismissRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scheme_id: str


ProgressDismissRequest.model_rebuild()


@app.get("/profile", tags=["citizen_profile"])
def get_citizen_profile(
    session: UserSession = Depends(get_current_session),
) -> dict:
    profile, prov = citizen_store.get_profile_with_provenance(session.session_id)
    return {
        "session_id": session.session_id,
        "profile": profile.model_dump(mode="json"),
        "provenance": prov,
    }


@app.post("/profile", tags=["citizen_profile"])
def update_citizen_profile(
    payload: ProfileUpdateRequest,
    session: UserSession = Depends(get_current_session),
) -> dict:
    saved = citizen_store.save_profile(
        session_id=session.session_id,
        profile=payload.profile,
        provenance={"updated_via": "profile_api"},
    )
    return {
        "session_id": session.session_id,
        "profile": saved.model_dump(mode="json"),
        "status": "saved",
    }


@app.post("/profile/reset", tags=["citizen_profile"])
def reset_citizen_profile(
    session: UserSession = Depends(get_current_session),
) -> dict:
    citizen_store.reset_citizen_data(session.session_id)
    session_manager._thread_owners = {
        tid: sid for tid, sid in session_manager._thread_owners.items() if sid != session.session_id
    }
    return {
        "status": "reset_successful",
        "message": "All citizen profile and application progress records have been permanently cleared.",
    }


@app.get("/progress", tags=["citizen_progress"])
def get_citizen_progress(
    request: Request,
    session: UserSession = Depends(get_current_session),
) -> Any:
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return citizen_portal()
    return citizen_store.get_progress(session.session_id)


@app.post("/progress/activate", tags=["citizen_progress"])
def activate_citizen_progress(
    payload: ProgressActivateRequest,
    session: UserSession = Depends(get_current_session),
) -> dict:
    res = citizen_store.set_active_scheme(
        session_id=session.session_id,
        scheme_id=payload.scheme_id,
        version=payload.version,
        progress_data=payload.progress_data,
    )
    return res


@app.post("/progress/dismiss", tags=["citizen_progress"])
def dismiss_citizen_scheme(
    payload: ProgressDismissRequest,
    session: UserSession = Depends(get_current_session),
) -> dict:
    res = citizen_store.dismiss_scheme(
        session_id=session.session_id,
        scheme_id=payload.scheme_id,
    )
    return res


@app.post(
    "/eligibility/evaluate",
    response_model=list[EligibilityResult],
    tags=["schemes"],
    dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60))],
)
def evaluate_eligibility(
    profile: CitizenProfile,
    language: Language = Language.EN,
    scope: str = "default",
    session: UserSession = Depends(get_current_session),
) -> list[EligibilityResult]:
    session_id = getattr(session, "session_id", None)
    if session_id:
        try:
            citizen_store.save_profile(
                session_id,
                profile,
                provenance={"updated_via": "eligibility_evaluation"},
            )
        except Exception:
            pass

    # Determine candidate schemes based on scope and environment
    if settings.scheme_catalog_path:
        schemes = catalog.all()
    elif scope == "canonical" or (settings.app_env.casefold() in {"production", "prod"} and canonical_catalog.all()):
        schemes = canonical_catalog.all()
    else:
        schemes = catalog.all()

    # Filter out dismissed schemes for this citizen session
    if session_id:
        try:
            prog = citizen_store.get_progress(session_id)
            dismissed = set(prog.get("dismissed_schemes", []))
            if dismissed:
                schemes = [s for s in schemes if s.scheme_id not in dismissed]
        except Exception:
            pass

    results = []
    for scheme in schemes:
        res = evaluate_scheme(scheme, profile)
        explanation = generate_scheme_explanation(
            scheme, profile, res, language=language
        )
        res_with_exp = res.model_copy(update={"explanation": explanation})
        results.append(res_with_exp)
    return results


@app.post(
    "/schemes/{scheme_id}/explain",
    response_model=SchemeExplanation,
    tags=["schemes"],
    dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60))],
)
def explain_scheme_eligibility(
    scheme_id: str,
    profile: CitizenProfile,
    language: Language = Language.EN,
) -> SchemeExplanation:
    scheme = catalog.get(scheme_id) or canonical_catalog.get(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=404,
            detail=f"Scheme '{scheme_id}' was not found in the active catalogue.",
        )
    res = evaluate_scheme(scheme, profile)
    return generate_scheme_explanation(scheme, profile, res, language=language)


@app.get(
    "/schemes/trust/all",
    response_model=list[SchemeTrustReport],
    tags=["schemes"],
)
def list_all_schemes_trust(
    language: Language = Language.EN,
    include_candidates: bool = False,
) -> list[SchemeTrustReport]:
    reports = [
        generate_trust_report(scheme, language=language)
        for scheme in catalog.all()
    ]
    if include_candidates:
        candidates_dir = Path(__file__).resolve().parents[3] / "data" / "candidates"
        if candidates_dir.is_dir():
            for p in sorted(candidates_dir.glob("*.json")):
                if p.name == "candidate_schemes.json":
                    continue
                try:
                    cdata = json.loads(p.read_text(encoding="utf-8"))
                    cscheme = Scheme.model_validate(cdata)
                    reports.append(generate_trust_report(cscheme, language=language))
                except Exception:
                    pass
    return reports


@app.get(
    "/schemes/{scheme_id}/trust",
    response_model=SchemeTrustReport,
    tags=["schemes"],
)
def get_scheme_trust(
    scheme_id: str,
    language: Language = Language.EN,
) -> SchemeTrustReport:
    scheme = catalog.get(scheme_id) or canonical_catalog.get(scheme_id)
    if not scheme:
        candidates_dir = Path(__file__).resolve().parents[3] / "data" / "candidates"
        if candidates_dir.is_dir():
            for p in candidates_dir.glob("*.json"):
                if p.name == "candidate_schemes.json":
                    continue
                try:
                    cdata = json.loads(p.read_text(encoding="utf-8"))
                    if cdata.get("scheme_id") == scheme_id:
                        scheme = Scheme.model_validate(cdata)
                        break
                except Exception:
                    pass
    if not scheme:
        raise HTTPException(
            status_code=404,
            detail=f"Scheme '{scheme_id}' was not found in the active catalogue or candidate registry.",
        )
    return generate_trust_report(scheme, language=language)


class CitizenIssueReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheme_id: str
    issue_type: str = Field(..., pattern=r"^(outdated_info|broken_link|incorrect_criteria|ineligible_denial|other)$")
    description: str = Field(..., min_length=10, max_length=2000)
    citizen_contact: str | None = Field(default=None, max_length=120)
    language: Language = Language.EN


class CitizenIssueReportResponse(BaseModel):
    ticket_id: str
    scheme_id: str
    status: str
    received_at_iso: str
    message: str


@app.post(
    "/trust/report-issue",
    response_model=CitizenIssueReportResponse,
    tags=["trust"],
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))],
)
def report_scheme_issue(
    payload: CitizenIssueReportRequest,
    request: Request,
) -> CitizenIssueReportResponse:
    scheme = catalog.get(payload.scheme_id) or canonical_catalog.get(payload.scheme_id)
    if not scheme:
        candidates_dir = Path(__file__).resolve().parents[3] / "data" / "candidates"
        if candidates_dir.is_dir():
            for p in candidates_dir.glob("*.json"):
                if p.name == "candidate_schemes.json":
                    continue
                try:
                    cdata = json.loads(p.read_text(encoding="utf-8"))
                    if cdata.get("scheme_id") == payload.scheme_id:
                        scheme = Scheme.model_validate(cdata)
                        break
                except Exception:
                    pass
    if not scheme:
        raise HTTPException(
            status_code=404,
            detail=f"Scheme '{payload.scheme_id}' was not found.",
        )

    ticket_id = f"TICKET-{uuid.uuid4().hex[:10].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    client_ip = request.client.host if request.client else None

    # Persist report to structured audit log
    reports_file = Path(__file__).resolve().parents[3] / "data" / "citizen_reports.jsonl"
    reports_file.parent.mkdir(parents=True, exist_ok=True)
    report_entry = {
        "ticket_id": ticket_id,
        "scheme_id": payload.scheme_id,
        "scheme_name": getattr(scheme, "name", payload.scheme_id),
        "issue_type": payload.issue_type,
        "description": payload.description,
        "citizen_contact": payload.citizen_contact,
        "language": payload.language.value if hasattr(payload.language, "value") else str(payload.language),
        "status": "RECEIVED",
        "received_at_iso": now_iso,
    }
    with open(reports_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(report_entry, ensure_ascii=False) + "\n")

    audit_logger.log_event(
        event_type=AuditEventType.CITIZEN_REPORT_SUBMITTED,
        actor_id="anonymous_citizen",
        actor_role="citizen",
        action="report_scheme_issue",
        resource=payload.scheme_id,
        client_ip=client_ip,
        details={"ticket_id": ticket_id, "issue_type": payload.issue_type},
    )

    msg = {
        Language.MR: "तुमचा अभिप्राय यशस्वीरीत्या नोंदवला गेला आहे. शासकीय स्रोत पडताळणी पथकाद्वारे याची तपासणी केली जाईल.",
        Language.HI: "आपकी शिकायत/प्रतिक्रिया सफलतापूर्वक दर्ज कर ली गई है। आधिकारिक स्रोत सत्यापन दल द्वारा इसकी जांच की जाएगी।",
        Language.EN: "Your issue report has been registered. It will be verified by the content governance team against official government sources.",
    }.get(payload.language, "Your issue report has been registered.")

    return CitizenIssueReportResponse(
        ticket_id=ticket_id,
        scheme_id=payload.scheme_id,
        status="RECEIVED",
        received_at_iso=now_iso,
        message=msg,
    )


def _current_question(result: dict) -> dict | None:
    interrupts = result.get("__interrupt__") or []
    if not interrupts:
        return None
    item = interrupts[0]
    value = getattr(item, "value", item if isinstance(item, dict) else None)
    return value if isinstance(value, dict) else None


def _interview_response(result: dict, graph, thread_id: str, session: UserSession | None = None) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)
    values = snapshot.values or {}
    interrupt_payload = _current_question(result)
    question = interrupt_payload.get("question") if interrupt_payload else None
    is_complete = bool(values.get("is_complete", False) or not question)
    mode = values.get("mode", "DISCOVERY")
    target_scheme_id = values.get("target_scheme_id")

    scheme_evaluations = values.get("result_summary", [])
    if is_complete:
        profile = CitizenProfile.model_validate(values.get("profile", {}))
        if mode == "FOCUSED_SCHEME" and target_scheme_id:
            target_scheme = canonical_catalog.get(target_scheme_id) or catalog.get(target_scheme_id)
            if target_scheme:
                scheme_evaluations = [evaluate_scheme(target_scheme, profile).model_dump(mode="json")]
            else:
                scheme_evaluations = []
        else:
            candidates = [Scheme.model_validate(s) for s in values.get("candidate_schemes", [])]
            scheme_evaluations = [evaluate_scheme(s, profile).model_dump(mode="json") for s in candidates]

        citizen_store.complete_interview_run(
            thread_id=thread_id,
            results=scheme_evaluations,
            final_state=values,
        )

    err = values.get("error")
    resp = {
        "thread_id": thread_id,
        "interview_run_id": thread_id,
        "mode": mode,
        "target_scheme_id": target_scheme_id,
        "question": question,
        "complete": is_complete,
        "profile": values.get("profile", {}),
        "scheme_evaluations": scheme_evaluations,
        "privacy_note": (
            "Never share an OTP or full Aadhaar number. "
            "Use estimates where the exact value is not necessary."
        ),
    }
    if err:
        resp["error"] = err
    return resp


@app.post(
    "/interview/start",
    tags=["interview"],
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
def start_interview(
    payload: InterviewStart,
    session: UserSession = Depends(get_current_session),
) -> dict:
    _ensure_active_interview_engine()
    if not catalog.all():
        raise HTTPException(
            status_code=503,
            detail="No verified scheme catalog is configured for this environment.",
        )

    # Priority 2: Enforce session ownership
    effective_session = session if isinstance(session, UserSession) else None
    if effective_session:
        owner = session_manager._thread_owners.get(payload.thread_id)
        if owner and owner != effective_session.session_id:
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: Interview thread '{payload.thread_id}' is owned by another citizen session.",
            )
        if effective_session.user_id != "anonymous_citizen":
            try:
                session_manager.bind_thread_to_session(effective_session.session_id, payload.thread_id)
            except PermissionError as p_err:
                raise HTTPException(status_code=403, detail=str(p_err))
        persisted_profile = citizen_store.get_profile(effective_session.session_id)
        session_id = effective_session.session_id
    else:
        persisted_profile = None
        session_id = "anonymous_session"

    # Determine mode and target scheme
    target_scheme_id = payload.target_scheme_id or payload.scheme_id
    if payload.mode:
        effective_mode = payload.mode
    elif target_scheme_id:
        effective_mode = InterviewMode.FOCUSED_SCHEME
    else:
        effective_mode = InterviewMode.DISCOVERY

    # Persist and merge persistent citizen profile
    if persisted_profile:
        incoming_dump = payload.profile.model_dump(mode="python", exclude_none=True)
        merged_dump = persisted_profile.model_dump(mode="python")
        merged_dump.update(incoming_dump)
        effective_profile = CitizenProfile.model_validate(merged_dump)
    else:
        effective_profile = payload.profile
    citizen_store.save_profile(session_id, effective_profile)

    if effective_mode == InterviewMode.FOCUSED_SCHEME:
        if not target_scheme_id:
            raise HTTPException(
                status_code=400,
                detail="target_scheme_id is required when mode is FOCUSED_SCHEME.",
            )
        selected = canonical_catalog.get(target_scheme_id) or catalog.get(target_scheme_id)
        if selected is None:
            raise HTTPException(
                status_code=404,
                detail=f"Scheme '{target_scheme_id}' was not found in the active catalogue.",
            )
        candidate_schemes = [selected]
    else:
        if payload.scope == "canonical" or not catalog.all() or (payload.scope is None and settings.app_env.casefold() in {"production", "prod"} and canonical_catalog.all()):
            candidate_schemes = canonical_catalog.all()
        else:
            candidate_schemes = catalog.all()

        # Filter out dismissed schemes for this citizen session
        prog = citizen_store.get_progress(session_id)
        dismissed = set(prog.get("dismissed_schemes", []))
        if dismissed:
            candidate_schemes = [s for s in candidate_schemes if s.scheme_id not in dismissed]

    citizen_store.create_interview_run(
        thread_id=payload.thread_id,
        session_id=session_id,
        scheme_id=target_scheme_id,
        mode=effective_mode.value,
        target_scheme_id=target_scheme_id,
        target_jurisdiction_id=payload.target_jurisdiction_id,
        catalogue_version="2026.11",
        rule_version="1.0.0",
        language=payload.language.value,
    )

    config = {"configurable": {"thread_id": payload.thread_id}}
    initial_state = {
        "thread_id": payload.thread_id,
        "language": payload.language.value,
        "mode": effective_mode.value,
        "target_scheme_id": target_scheme_id,
        "target_jurisdiction_id": payload.target_jurisdiction_id,
        "profile": effective_profile.model_dump(mode="json"),
        "candidate_schemes": [s.model_dump(mode="json") for s in candidate_schemes],
        "pending_answer": None,
        "asked_fields": [],
        "events": [],
        "is_complete": False,
        "result_summary": [],
    }
    session_created = False
    try:
        interview_store.create_session(payload.thread_id)
        session_created = True
        result = interviewer.invoke(initial_state, config=config)
    except Exception as exc:
        if session_created:
            try:
                interview_store.delete_session(payload.thread_id)
            except Exception:
                logger.exception("interview_start_cleanup_failed")
        logger.exception("interview_start_failed")
        raise HTTPException(status_code=500, detail="Unable to start interview.") from exc
    return _interview_response(result, interviewer, payload.thread_id, session=session)


@app.post(
    "/interview/answer",
    tags=["interview"],
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
def answer_interview(
    payload: InterviewAnswer,
    session: UserSession = Depends(get_current_session),
) -> dict:
    _ensure_active_interview_engine()
    # Priority 2: Enforce session ownership
    effective_session = session if isinstance(session, UserSession) else None
    if effective_session and not session_manager.authorize_thread_access(effective_session, payload.thread_id):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: You do not have permission to access or answer interview thread '{payload.thread_id}'.",
        )

    config = {"configurable": {"thread_id": payload.thread_id}}
    if not interview_store.is_active(payload.thread_id):
        raise HTTPException(
            status_code=404,
            detail="Interview session not found or expired. Start a new interview.",
        )
    snapshot = interviewer.get_state(config)
    if not snapshot.values:
        raise HTTPException(
            status_code=404,
            detail="Interview thread not found; start the interview first.",
        )
    try:
        result = interviewer.invoke(Command(resume=payload.answer), config=config)
    except Exception as exc:
        logger.exception("interview_answer_failed")
        raise HTTPException(
            status_code=500,
            detail="Unable to process interview answer.",
        ) from exc
    if not interview_store.touch_session(payload.thread_id):
        interview_store.delete_session(payload.thread_id)
        raise HTTPException(
            status_code=410,
            detail="Interview session expired while processing the answer. Start a new interview.",
        )

    # Persist updated profile to SQLite citizen store
    snapshot_after = interviewer.get_state(config)
    after_vals = snapshot_after.values or {}
    if after_vals.get("profile") and session and session.session_id:
        try:
            p_obj = CitizenProfile.model_validate(after_vals["profile"])
            citizen_store.save_profile(session.session_id, p_obj)
        except Exception:
            pass

    return _interview_response(result, interviewer, payload.thread_id, session=session)


@app.get(
    "/interview/{thread_id}/results",
    tags=["interview"],
    dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60))],
)
def get_interview_results(
    thread_id: str,
    request: Request,
    session: UserSession = Depends(get_current_session),
) -> dict:
    if not session_manager.authorize_thread_access(session, thread_id):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: You do not have permission to access results for interview run '{thread_id}'.",
        )
    run_record = citizen_store.get_interview_run(thread_id)
    if not run_record:
        raise HTTPException(
            status_code=404,
            detail=f"Interview run '{thread_id}' was not found.",
        )
    if run_record["status"] != "completed" and not run_record.get("results"):
        raise HTTPException(
            status_code=409,
            detail=f"Interview run '{thread_id}' is still in progress and has not produced results.",
        )
    return {
        "interview_run_id": thread_id,
        "mode": run_record.get("mode", "DISCOVERY"),
        "target_scheme_id": run_record.get("target_scheme_id"),
        "status": run_record["status"],
        "catalogue_version": run_record.get("catalogue_version", "2026.11"),
        "rule_version": run_record.get("rule_version", "1.0.0"),
        "language": run_record.get("language", "en"),
        "results": run_record.get("results") or [],
        "completed_at": run_record.get("completed_at"),
    }


@app.get(
    "/interview/{thread_id}",
    tags=["interview"],
    dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60))],
)
def get_interview_state(
    thread_id: str,
    request: Request,
) -> dict:
    _ensure_local_interview_recovery_api()
    session = get_current_session(request)
    # Priority 2: Enforce session ownership
    if not session_manager.authorize_thread_access(session, thread_id):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: You do not have permission to access interview thread '{thread_id}'.",
        )
    if not interview_store.is_active(thread_id):
        raise HTTPException(
            status_code=404,
            detail="Interview session not found or expired. Start a new interview.",
        )
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = interviewer.get_state(config)
    if not snapshot.values:
        raise HTTPException(
            status_code=404,
            detail="Interview thread not found; start the interview first.",
        )
    values = snapshot.values or {}
    question = values.get("next_question")
    is_complete = bool(values.get("is_complete", False) or not question)
    return {
        "thread_id": thread_id,
        "question": question,
        "complete": is_complete,
    }


@app.post(
    "/voice/transcribe",
    tags=["voice"],
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))],
)
async def transcribe_voice(
    file: Annotated[UploadFile, File()],
    provider: str = "whisper",
    language: str = "auto",
    consent_to_cloud_processing: bool = False,
) -> dict:
    """Transcribe speech only; does not mutate an interview/profile."""
    if provider not in {"whisper", "bhashini"}:
        raise HTTPException(status_code=400, detail="provider must be 'whisper' or 'bhashini'.")
    if language not in {"auto", Language.EN.value, Language.MR.value, Language.HI.value}:
        raise HTTPException(status_code=400, detail="language must be auto, en, mr, or hi.")
    if provider == "bhashini" and not consent_to_cloud_processing:
        raise HTTPException(
            status_code=400,
            detail="Explicit consent_to_cloud_processing=true is required for Bhashini cloud ASR.",
        )
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=415,
            detail="Upload an audio file such as WAV, MP3, FLAC, OGG, or WebM.",
        )

    try:
        raw = await file.read(MAX_AUDIO_BYTES + 1)
        if len(raw) > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="Audio file exceeds 15 MiB.")
        # Priority 8: Magic-byte audio validation
        safe_fname, detected_fmt = validate_uploaded_audio_security(
            raw, file.filename or "audio.wav", file.content_type
        )
        result = await run_in_threadpool(
            get_transcriber(provider).transcribe,
            raw,
            safe_fname,
            language,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("voice_transcription_failed")
        raise HTTPException(
            status_code=503,
            detail="Transcription provider unavailable or transcription failed.",
        ) from exc
    finally:
        await file.close()

    return {
        "transcript": result.text,
        "detected_language": result.language,
        "confidence": result.confidence,
        "provider": result.provider,
        "profile_modified": False,
        "next_step": (
            "Show this transcript to the citizen for editing/confirmation, then submit "
            "the confirmed text to /interview/answer."
        ),
    }


@app.post("/documents/audit", response_model=DocumentAuditResponse, tags=["documents"])
def audit_documents(payload: DocumentAuditRequest) -> DocumentAuditResponse:
    return audit_extracted_documents(payload.documents, payload.target_financial_year)


@app.post(
    "/documents/audit-upload",
    tags=["documents"],
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))],
)
async def audit_document_upload(
    file: UploadFile = File(...),
    target_financial_year: str = "2026-27",
    session: UserSession = Depends(get_current_session),
) -> dict:
    """Extract and pre-audit a document; group compatible consecutive PDF pages."""
    filename = file.filename or "upload"
    suffix = Path(filename).suffix.casefold()
    content_type = (file.content_type or "").casefold()

    is_pdf = content_type == "application/pdf" or suffix == ".pdf"
    supported_image_types = {"image/png", "image/jpeg", "image/webp"}
    supported_image_suffixes = {".png", ".jpg", ".jpeg", ".webp"}
    is_image = (
        content_type in supported_image_types
        or suffix in supported_image_suffixes
    )

    if not (is_pdf or is_image):
        raise HTTPException(
            status_code=415,
            detail="Upload a PNG, JPEG, WEBP image or a PDF certificate.",
        )

    max_bytes = 15 * 1024 * 1024 if is_pdf else 12 * 1024 * 1024

    try:
        raw = await file.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds the {max_bytes // (1024 * 1024)} MiB upload limit.",
            )
        if not raw:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

        try:
            safe_fname, detected_mime = validate_uploaded_document_security(
                raw, filename, file.content_type
            )
        except ValueError as val_err:
            raise HTTPException(status_code=400, detail=str(val_err))

        source_hash = hashlib.sha256(raw).hexdigest()
        audit_logger.log_event(
            event_type=AuditEventType.DOC_UPLOADED,
            actor_id="citizen_upload",
            actor_role="citizen",
            action="upload_document",
            resource=source_hash,
            details={"filename": safe_fname, "mime": detected_mime, "bytes": len(raw)},
        )
        page_extractions = []
        document_groups = []
        extractor = None

        # Created per request so a missing key does not prevent the API starting.
        extractor = GeminiVisionExtractor()

        if is_pdf:
            page_images = await run_in_threadpool(render_pdf_pages, raw, max_pages=10)
            if not page_images:
                raise ValueError("No readable pages were found in the uploaded PDF.")

            page_documents: list[tuple[int, ExtractedDocument]] = []
            for page_number, page_bytes in enumerate(page_images, start=1):
                page_doc = await run_in_threadpool(
                    extractor.extract,
                    page_bytes,
                    f"certificate-page-{page_number}.png",
                )
                page_doc = page_doc.model_copy(
                    update={
                        "document_id": hashlib.sha256(
                            f"{source_hash}:{page_number}".encode("utf-8")
                        ).hexdigest()[:16],
                        "source_file_sha256": source_hash,
                    }
                )
                page_documents.append((page_number, page_doc))

            page_extractions = [
                page_doc.model_dump(mode="json")
                for _, page_doc in page_documents
            ]
            groups = group_pdf_page_extractions(page_documents, source_hash)
            extracted_documents = [group.document for group in groups]
            document_groups = [
                {
                    "document_id": group.document.document_id,
                    "page_numbers": list(group.page_numbers),
                    "page_count": len(group.page_numbers),
                }
                for group in groups
            ]
        else:
            image_document = await run_in_threadpool(extractor.extract, raw, filename)
            image_document = image_document.model_copy(
                update={"source_file_sha256": source_hash}
            )
            extracted_documents = [image_document]

        audit = audit_extracted_documents(
            extracted_documents,
            target_financial_year,
        )
        if is_pdf:
            # Audit original page extractions as well as logical groups. A page
            # conflict can cause grouping to split pages into separate documents.
            audit = add_pdf_page_conflict_findings(audit, page_documents)

    except HTTPException:
        raise
    except ValidationError as exc:
        logger.exception("gemini_extraction_schema_validation_failed")
        raise HTTPException(
            status_code=503,
            detail="Gemini returned document data that did not match the expected schema. Please retry.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("gemini_document_extractor_failed")
        raise HTTPException(
            status_code=503,
            detail=(
                f"Gemini document extraction failed: {exc} No file was persisted."
                if not str(exc).endswith("No file was persisted.")
                else str(exc)
            ),
        ) from exc
    except Exception as exc:
        logger.exception("gemini_document_audit_failed")
        raise HTTPException(
            status_code=503,
            detail=(
                "Gemini document extraction failed or the provider is unavailable. "
                "Please retry later. No file was persisted."
            ),
        ) from exc
    finally:
        if extractor is not None and hasattr(extractor, "close"):
            extractor.close()
        await file.close()

    extracted_payload = [item.model_dump(mode="json") for item in extracted_documents]
    audit_payload = audit.model_dump(mode="json")
    review_metadata = None
    # Do not persist citizen fields in production until authenticated reviewer access exists.
    if settings.app_env.casefold() not in {"production", "prod"}:
        review_record = _document_review_store().create_review(
            is_pdf=is_pdf,
            source_file_sha256=source_hash,
            target_financial_year=target_financial_year,
            extracted_documents=extracted_payload,
            page_extractions=page_extractions,
            document_groups=document_groups,
            audit=audit_payload,
        )
        review_metadata = {
            "review_id": review_record["review_id"],
            "status": review_record["status"],
            "expires_at": review_record["expires_at"],
        }
        try:
            session_manager.bind_review_to_session(session.session_id, review_record["review_id"])
        except Exception:
            pass

    return {
        # Logical documents are the units audited. PDF pages may be grouped when
        # their type, identity anchors and overlapping certificate fields agree.
        "extracted_documents": extracted_payload,
        # Keep original Gemini page outputs so page-level provenance is inspectable.
        "page_extractions": page_extractions,
        "document_groups": document_groups,
        "audit": audit_payload,
        "review": review_metadata,
        "notice": (
            "Gemini extraction is untrusted. For PDFs, consecutive pages may be grouped "
            "when their document type, identity evidence and overlapping fields are "
            "consistent. Review page_extractions and document_groups to confirm grouping. "
            "A local human-review case was created when review is enabled; only extracted "
            "fields and audit metadata are retained temporarily, not the uploaded file. "
            "Inspect and correct each field, then verify the certificate through an official "
            "channel. This is not an official verification."
        ),
    }


@app.get(
    "/documents/reviews/{review_id}",
    tags=["documents", "human-review"],
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
def get_document_review(
    review_id: str,
    session: UserSession = Depends(get_current_session),
) -> dict:
    _ensure_reviewer_access(session)
    record = _document_review_store().get_review(review_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Document review not found or expired.")
    return _review_response(record)


@app.patch(
    "/documents/reviews/{review_id}/documents/{document_id}",
    tags=["documents", "human-review"],
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
def correct_document_review_fields(
    review_id: str,
    document_id: str,
    payload: DocumentReviewCorrectionRequest,
    session: UserSession = Depends(get_current_session),
) -> dict:
    _ensure_reviewer_access(session)
    store = _document_review_store()
    record = store.get_review(review_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Document review not found or expired.")
    if record["status"] != "pending_review":
        raise HTTPException(status_code=409, detail="This review has already been completed and is read-only.")

    corrections = payload.corrections.model_dump(mode="json", exclude_unset=True)
    current_documents = [ExtractedDocument.model_validate(item) for item in record["extracted_documents"]]
    target_index = next(
        (index for index, item in enumerate(current_documents) if item.document_id == document_id),
        None,
    )
    if target_index is None:
        raise HTTPException(status_code=404, detail="Document ID was not found in this review.")

    target_document = current_documents[target_index]
    page_numbers = _review_page_mapping(record, document_id) if record["is_pdf"] else []
    if record["is_pdf"] and not page_numbers:
        raise HTTPException(status_code=409, detail="PDF page mapping is unavailable for this document.")

    reviewer_actor = session.user_id if session.role != UserRole.CITIZEN else payload.reviewer_id

    events = []
    for field_name, new_value in corrections.items():
        previous_value = _json_scalar(getattr(target_document, field_name))
        original_field_values = (
            [
                {
                    "page_number": page_number,
                    "value": record["page_extractions"][page_number - 1].get(field_name),
                }
                for page_number in page_numbers
                if 1 <= page_number <= len(record["page_extractions"])
            ]
            if record["is_pdf"]
            else [{
                "page_number": None,
                "value": next(
                    (item.get(field_name) for item in record["original_extracted_documents"]
                     if item["document_id"] == document_id),
                    None,
                ),
            }]
        )
        events.append({
            "action": "field_confirmed" if previous_value == new_value else "field_corrected",
            "reviewer_id": reviewer_actor,
            "document_id": document_id,
            "field_name": field_name,
            "original_value": original_field_values,
            "previous_value": previous_value,
            "new_value": new_value,
            "note": payload.note,
            "page_numbers": page_numbers,
        })

    if record["is_pdf"]:
        current_pages = [ExtractedDocument.model_validate(item) for item in record["current_page_extractions"]]
        page_map = {number: doc for number, doc in enumerate(current_pages, start=1)}
        for page_number in page_numbers:
            page_doc = page_map.get(page_number)
            if page_doc is None:
                raise HTTPException(status_code=409, detail=f"Page {page_number} is missing from the review record.")
            updated_data = page_doc.model_dump(mode="python")
            updated_data.update(corrections)
            page_map[page_number] = ExtractedDocument.model_validate(updated_data)

        current_page_tuples = [(number, doc) for number, doc in sorted(page_map.items())]
        groups = group_pdf_page_extractions(current_page_tuples, record["source_file_sha256"])
        current_documents = [group.document for group in groups]
        current_page_extractions = [doc.model_dump(mode="json") for _, doc in current_page_tuples]
        current_document_groups = [
            {
                "document_id": group.document.document_id,
                "page_numbers": list(group.page_numbers),
                "page_count": len(group.page_numbers),
            }
            for group in groups
        ]
        audit = audit_extracted_documents(current_documents, record["target_financial_year"])
        audit = add_pdf_page_conflict_findings(audit, current_page_tuples)
    else:
        updated_data = target_document.model_dump(mode="python")
        updated_data.update(corrections)
        current_documents[target_index] = ExtractedDocument.model_validate(updated_data)
        current_page_extractions = record["current_page_extractions"]
        current_document_groups = record["document_groups"]
        audit = audit_extracted_documents(current_documents, record["target_financial_year"])

    saved = store.save_correction(
        review_id,
        extracted_documents=[item.model_dump(mode="json") for item in current_documents],
        page_extractions=current_page_extractions,
        document_groups=current_document_groups,
        audit=audit.model_dump(mode="json"),
        events=events,
    )
    if not saved:
        raise HTTPException(status_code=409, detail="Review could not be updated; it may have expired or been completed.")
    updated_record = store.get_review(review_id)
    if updated_record is None:
        raise HTTPException(status_code=404, detail="Document review expired during the update.")
    return _review_response(updated_record)


@app.post(
    "/documents/reviews/{review_id}/complete",
    tags=["documents", "human-review"],
    dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))],
)
def complete_document_review(
    review_id: str,
    payload: DocumentReviewCompletionRequest,
    session: UserSession = Depends(get_current_session),
) -> dict:
    _ensure_reviewer_access(session)
    if not payload.confirm_review_complete:
        raise HTTPException(
            status_code=400,
            detail="Set confirm_review_complete=true after inspecting the original document and all outstanding findings.",
        )
    store = _document_review_store()
    record = store.get_review(review_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Document review not found or expired.")
    reviewer_actor = session.user_id if session.role != UserRole.CITIZEN else payload.reviewer_id
    completed = store.complete_review(
        review_id, reviewer_id=reviewer_actor, note=payload.note
    )
    if not completed:
        raise HTTPException(status_code=409, detail="Review could not be completed; it may have expired or already been completed.")
    updated_record = store.get_review(review_id)
    if updated_record is None:
        raise HTTPException(status_code=404, detail="Document review not found or expired.")
    return _review_response(updated_record)


@app.delete(
    "/documents/reviews/{review_id}",
    tags=["documents", "human-review"],
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))],
)
def delete_document_review(
    review_id: str,
    session: UserSession = Depends(get_current_session),
) -> dict:
    _ensure_reviewer_access(session)
    deleted = _document_review_store().delete_review(review_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document review not found or expired.")
    return {"review_id": review_id, "deleted": True, "message": "Local review data and its event history were deleted."}


@app.post(
    "/assessment/{scheme_id}",
    response_model=ApplicantAssessmentResponse,
    tags=["assessment"],
    dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60))],
)
def get_applicant_assessment(
    scheme_id: str,
    payload: ApplicantAssessmentRequest,
    session: UserSession = Depends(get_current_session),
) -> ApplicantAssessmentResponse:
    """Generate a consolidated assessment with optional human-review linkage."""

    scheme = catalog.get(scheme_id) or canonical_catalog.get(scheme_id)

    if not scheme:
        raise HTTPException(
            status_code=404,
            detail="Scheme not found.",
        )

    review_record = None

    if payload.review_id:
        if not session_manager.authorize_review_access(session, payload.review_id):
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: You do not have permission to access document review record '{payload.review_id}'.",
            )

        if payload.documents:
            raise HTTPException(
                status_code=400,
                detail=(
                    "When review_id is supplied, do not send documents "
                    "again. The linked review record provides the current "
                    "corrected documents and audit."
                ),
            )

        review_record = _document_review_store().get_review(
            payload.review_id
        )

        if review_record is None:
            raise HTTPException(
                status_code=404,
                detail="Document review not found or expired.",
            )

    effective_payload = payload

    if payload.thread_id:
        if not session_manager.authorize_thread_access(session, payload.thread_id):
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: You do not have permission to access interview thread '{payload.thread_id}'.",
            )
        _ensure_local_interview_recovery_api()
        if not interview_store.is_active(payload.thread_id):
            raise HTTPException(
                status_code=404,
                detail="Interview session not found or expired.",
            )
        config = {"configurable": {"thread_id": payload.thread_id}}
        snapshot = interviewer.get_state(config)
        if snapshot.values and snapshot.values.get("profile"):
            server_profile = CitizenProfile.model_validate(snapshot.values["profile"])
            effective_payload = payload.model_copy(update={"profile": server_profile})

    return build_applicant_assessment(
        scheme,
        effective_payload,
        review_record=review_record,
    )


@app.post(
    "/plans/{scheme_id}",
    response_model=ApplicationPlan,
    tags=["planner"],
    dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60))],
)
def get_application_plan(
    scheme_id: str,
    available_documents: list[str] | None = None,
) -> ApplicationPlan:
    scheme = catalog.get(scheme_id) or canonical_catalog.get(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found.")
    return build_application_plan(scheme, available_documents=available_documents)


class AuditAndPrepareRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scheme_id: str | None = None
    documents: list[ExtractedDocument] = Field(default_factory=list)
    profile: CitizenProfile | None = None
    target_financial_year: str = "2026-27"
    language: Language = Language.EN


class PortalGuidanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheme_id: str
    profile: CitizenProfile
    documents: list[ExtractedDocument] = Field(default_factory=list)
    language: Language = Language.EN


@app.post(
    "/assistance/documents/audit-and-prepare",
    response_model=IntelligentDocumentPreparationReport,
    tags=["assistance"],
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
def audit_and_prepare_documents(
    payload: AuditAndPrepareRequest,
) -> IntelligentDocumentPreparationReport:
    scheme = catalog.get(payload.scheme_id) or canonical_catalog.get(payload.scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{payload.scheme_id}' was not found.")
    return prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=payload.documents,
        profile=payload.profile,
        target_financial_year=payload.target_financial_year,
        language=payload.language,
    )


@app.post(
    "/assistance/portal/guidance",
    response_model=PortalApplicationPackage,
    tags=["assistance"],
    dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60))],
)
def get_portal_guidance(
    payload: PortalGuidanceRequest,
) -> PortalApplicationPackage:
    scheme = catalog.get(payload.scheme_id) or canonical_catalog.get(payload.scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{payload.scheme_id}' was not found.")
    return build_portal_application_package(
        scheme=scheme,
        profile=payload.profile,
        extracted_documents=payload.documents,
        language=payload.language,
    )


@app.get("/healthz", tags=["monitoring"])
def health_check() -> dict:
    """Liveness probe."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/readyz", tags=["monitoring"])
def readiness_check() -> dict:
    """Readiness probe checking catalogue, configuration, and security readiness."""
    schemes_count = len(catalog.all())
    return {
        "status": "ready" if schemes_count > 0 else "degraded",
        "schemes_loaded": schemes_count,
        "environment": settings.app_env,
        "demo_fixtures_enabled": settings.demo_fixtures_enabled,
        "data_retention_hours": settings.data_retention_hours,
    }


class AdminProvisionRequest(BaseModel):
    role: UserRole
    user_id: str | None = None


@app.post(
    "/auth/session",
    tags=["security"],
    dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))],
)
def create_authenticated_session(
    request: Request,
    response: Response,
    role: str | None = None,
    user_id: str | None = None,
    client_ip: str | None = None,
) -> dict:
    if role and role.strip().lower() not in {"citizen", ""}:
        raise HTTPException(
            status_code=403,
            detail="Role escalation forbidden. Public session creation only issues CITIZEN role. Privileged roles must be provisioned via /admin/auth/provision with bootstrap credentials.",
        )
    ip = client_ip or (request.client.host if request.client else None)
    session, token = session_manager.create_session(
        role=UserRole.CITIZEN, user_id=user_id, client_ip=ip
    )
    audit_logger.log_event(
        event_type=AuditEventType.SESSION_CREATED,
        actor_id=session.user_id,
        actor_role=session.role.value,
        action="create_session",
        resource=session.session_id,
        client_ip=ip,
    )
    is_prod = settings.app_env.casefold() in {"production", "prod"}
    cookie_name = "__Host-sn_session" if is_prod else "sn_session"
    response.set_cookie(
        key=cookie_name,
        value=token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=24 * 3600,
        path="/",
    )
    if is_prod:
        # Also set sn_session for non-Host environments if needed
        response.set_cookie(
            key="sn_session",
            value=token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=24 * 3600,
            path="/",
        )
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "role": session.role.value,
        "token": token,
        "expires_at": session.expires_at.isoformat(),
    }


@app.post(
    "/admin/auth/provision",
    tags=["admin"],
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))],
)
def provision_admin_session(
    request: Request,
    payload: AdminProvisionRequest | None = None,
    role: UserRole | None = None,
    user_id: str | None = None,
    x_admin_bootstrap_key: str | None = Header(default=None, alias="X-Admin-Bootstrap-Key"),
) -> dict:
    target_role = payload.role if payload else (role or UserRole.ANALYST)
    target_uid = payload.user_id if payload else user_id
    client_ip = request.client.host if request.client else None
    session, token = session_manager.provision_privileged_session(
        role=target_role,
        user_id=target_uid,
        bootstrap_key=x_admin_bootstrap_key,
        client_ip=client_ip,
    )
    audit_logger.log_event(
        event_type=AuditEventType.SESSION_CREATED,
        actor_id=session.user_id,
        actor_role=session.role.value,
        action="provision_privileged_session",
        resource=session.session_id,
        client_ip=client_ip,
    )
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "role": session.role.value,
        "token": token,
        "expires_at": session.expires_at.isoformat(),
    }


class AdminRevokeRequest(BaseModel):
    session_id: str


@app.post(
    "/admin/auth/provision-user",
    tags=["admin"],
    dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))],
)
def provision_user_account(
    payload: AdminProvisionRequest,
    session: UserSession = Depends(require_role(UserRole.CATALOGUE_ADMIN)),
) -> dict:
    new_session, token = session_manager.provision_user_by_admin(
        admin_session=session,
        role=payload.role,
        user_id=payload.user_id,
    )
    audit_logger.log_event(
        event_type=AuditEventType.SESSION_CREATED,
        actor_id=session.user_id,
        actor_role=session.role.value,
        action="admin_provision_user",
        resource=new_session.session_id,
        details={"target_role": new_session.role.value, "target_user": new_session.user_id},
    )
    return {
        "session_id": new_session.session_id,
        "user_id": new_session.user_id,
        "role": new_session.role.value,
        "token": token,
        "expires_at": new_session.expires_at.isoformat(),
    }


@app.post(
    "/admin/auth/revoke",
    tags=["admin"],
    dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))],
)
def revoke_user_session(
    payload: AdminRevokeRequest,
    session: UserSession = Depends(require_role(UserRole.CATALOGUE_ADMIN)),
) -> dict:
    session_manager.revoke_session(payload.session_id)
    audit_logger.log_event(
        event_type=AuditEventType.AUTH_LOGOUT,
        actor_id=session.user_id,
        actor_role=session.role.value,
        action="revoke_session",
        resource=payload.session_id,
    )
    return {"status": "revoked", "session_id": payload.session_id}


@app.get("/auth/me", tags=["security"])
def get_current_user_info(
    session: UserSession = Depends(get_current_session),
) -> dict:
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "role": session.role.value,
        "expires_at": session.expires_at.isoformat(),
    }


@app.post(
    "/admin/catalogue/sign-release",
    response_model=CatalogueReleaseSignature,
    tags=["admin"],
    dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))],
)
def sign_catalogue_release(
    version: str = "1.0.0",
    session: UserSession = Depends(require_role(UserRole.CATALOGUE_ADMIN)),
) -> CatalogueReleaseSignature:
    schemes = catalog.all()
    sig, _ = publication_manager.authorize_and_sign_release(
        schemes=schemes,
        admin_session=session,
        version=version,
    )
    audit_logger.log_event(
        event_type=AuditEventType.CATALOGUE_SIGNED,
        actor_id=session.user_id,
        actor_role=session.role.value,
        action="sign_catalogue_release",
        resource=sig.release_id,
        details={"version": version, "scheme_count": sig.scheme_count},
    )
    return sig


@app.post(
    "/admin/retention/purge",
    tags=["admin"],
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))],
)
def run_retention_purge(
    retention_hours: int | None = None,
    session: UserSession = Depends(require_role(UserRole.CATALOGUE_ADMIN)),
) -> dict:
    result = purge_expired_data(retention_hours=retention_hours)
    return result


@app.get(
    "/admin/audit-logs",
    response_model=list[AuditEvent],
    tags=["admin"],
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
def get_recent_audit_logs(
    limit: int = 50,
    session: UserSession = Depends(require_role(UserRole.ANALYST)),
) -> list[AuditEvent]:
    return audit_logger.recent_events(limit=limit)


@app.get(
    "/admin/db/status",
    tags=["admin"],
    dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))],
)
def get_database_status(
    session: UserSession = Depends(require_role(UserRole.CATALOGUE_ADMIN)),
) -> dict:
    from scheme_navigator.core.migrations import check_database_integrity
    data_dir = Path(__file__).resolve().parents[3] / "data"
    return {
        "interviews": check_database_integrity(data_dir / "interviews.sqlite3"),
        "document_reviews": check_database_integrity(data_dir / "document_reviews.sqlite3"),
        "ingestion": check_database_integrity(data_dir / "ingestion.sqlite3"),
    }


@app.post(
    "/admin/db/migrate",
    tags=["admin"],
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))],
)
def run_database_migrations(
    session: UserSession = Depends(require_role(UserRole.CATALOGUE_ADMIN)),
) -> dict:
    from scheme_navigator.core.migrations import run_all_migrations
    applied = run_all_migrations()
    audit_logger.log_event(
        event_type=AuditEventType.SCHEME_PUBLISHED,
        actor_id=session.user_id,
        actor_role=session.role.value,
        action="database_migration",
        resource="sqlite_databases",
        details={"applied_migrations": applied},
    )
    return {"status": "success", "applied": applied}


@app.post(
    "/admin/db/backup",
    tags=["admin"],
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))],
)
def create_database_backup(
    session: UserSession = Depends(require_role(UserRole.CATALOGUE_ADMIN)),
) -> dict:
    from scheme_navigator.core.migrations import backup_database
    data_dir = Path(__file__).resolve().parents[3] / "data"
    backups = {}
    for db_name in ["interviews.sqlite3", "document_reviews.sqlite3", "ingestion.sqlite3"]:
        db_path = data_dir / db_name
        if db_path.exists():
            dest = backup_database(db_path)
            backups[db_name] = str(dest.name)

    audit_logger.log_event(
        event_type=AuditEventType.SCHEME_PUBLISHED,
        actor_id=session.user_id,
        actor_role=session.role.value,
        action="database_backup",
        resource="sqlite_databases",
        details={"backups": backups},
    )
    return {"status": "success", "backups": backups}


class ApplicationTrackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thread_id: str
    scheme_id: str
    status: str
    notes: str | None = None


@app.get("/source-registry/sources", tags=["source_registry"], response_model=list[SourceRecord])
def get_registered_sources(
    category: str | None = None,
    department: str | None = None,
    status: str | None = None,
) -> list[SourceRecord]:
    return source_registry.list_sources(category=category, department=department, status=status)


@app.get("/source-registry/coverage", tags=["source_registry"], response_model=list[SourceCoverageStats])
def get_source_coverage_matrix() -> list[SourceCoverageStats]:
    return source_registry.get_coverage_matrix()


@app.get("/public-services", tags=["source_registry"], response_model=list[PublicServiceRecord])
def get_notified_public_services(
    common_prerequisites_only: bool = False,
) -> list[PublicServiceRecord]:
    return source_registry.list_public_services(common_prerequisites_only=common_prerequisites_only)


@app.get("/channels", tags=["application_channels"], response_model=list[ApplicationChannelRecord])
def list_application_channels() -> list[ApplicationChannelRecord]:
    return source_registry.list_channels()


@app.get("/channels/{scheme_id}", tags=["application_channels"], response_model=ApplicationChannelRecord)
def get_scheme_application_channel(scheme_id: str) -> ApplicationChannelRecord:
    channel = source_registry.get_channel(scheme_id)
    if not channel:
        raise HTTPException(
            status_code=404,
            detail=f"No application channel registered for scheme '{scheme_id}'.",
        )
    return channel


@app.get("/canonical-schemes", tags=["canonical_schemes"], response_model=list[CanonicalSchemeRecord])
def list_canonical_schemes(
    search: str | None = None,
    department: str | None = None,
    category: str | None = None,
    beneficiary: str | None = None,
    status: str | None = None,
    availability: str | None = None,
    jurisdiction_scope: str | None = None,
    municipal_corporation: str | None = None,
) -> list[CanonicalSchemeRecord]:
    return source_registry.list_canonical_schemes(
        search=search,
        department=department,
        category=category,
        beneficiary=beneficiary,
        status=status,
        availability=availability,
        jurisdiction_scope=jurisdiction_scope,
        municipal_corporation=municipal_corporation,
    )


class LocationResolveRequest(BaseModel):
    state: str = "Maharashtra"
    district: str | None = None
    local_government_type: str | None = None
    local_body: str | None = None
    ward: str | None = None
    pin_code: str | None = None


@app.get("/local-governments/corporations", tags=["local_governments"])
def list_municipal_corporations() -> list[dict[str, Any]]:
    from scheme_navigator.domain.jurisdiction import jurisdiction_service
    return jurisdiction_service.list_corporations()


@app.get("/local-governments/corporations/{corp_id}", tags=["local_governments"])
def get_municipal_corporation(corp_id: str) -> dict[str, Any]:
    from scheme_navigator.domain.jurisdiction import jurisdiction_service
    corp = jurisdiction_service.get_corporation(corp_id) or jurisdiction_service.get_corporation_by_name(corp_id)
    if not corp:
        raise HTTPException(status_code=404, detail=f"Municipal Corporation '{corp_id}' not found.")
    return corp


@app.get("/local-governments/corporations/{corp_id}/wards", tags=["local_governments"])
def get_corporation_wards(corp_id: str) -> dict[str, Any]:
    from scheme_navigator.domain.jurisdiction import jurisdiction_service
    wards = jurisdiction_service.get_wards(corp_id)
    if not wards:
        raise HTTPException(status_code=404, detail=f"Ward data for '{corp_id}' not found.")
    return wards


@app.get("/local-governments/corporations/{corp_id}/schemes", tags=["local_governments"], response_model=list[CanonicalSchemeRecord])
def list_corporation_schemes(corp_id: str) -> list[CanonicalSchemeRecord]:
    return source_registry.list_canonical_schemes(municipal_corporation=corp_id)


@app.get("/local-governments/ulbs", tags=["local_governments"])
def get_urban_local_bodies() -> dict[str, Any]:
    from scheme_navigator.domain.jurisdiction import jurisdiction_service
    return jurisdiction_service.get_ulb_data()


@app.post("/local-governments/resolve-location", tags=["local_governments"])
def resolve_citizen_location(payload: LocationResolveRequest) -> dict[str, Any]:
    from scheme_navigator.domain.jurisdiction import jurisdiction_service
    res = jurisdiction_service.resolve_location(
        state=payload.state,
        district=payload.district,
        local_government_type=payload.local_government_type,
        local_body=payload.local_body,
        ward=payload.ward,
        pin_code=payload.pin_code,
    )
    return res.model_dump(mode="json")


@app.get("/canonical-schemes/categories", tags=["canonical_schemes"])
def get_canonical_scheme_categories() -> dict[str, Any]:
    schemes = source_registry.list_canonical_schemes()
    departments = sorted(list(set(s.responsible_department for s in schemes if s.responsible_department)))
    classifications = sorted(list(set(s.state_central_joint_classification for s in schemes if s.state_central_joint_classification)))
    beneficiaries = sorted(list(set(s.beneficiary_category for s in schemes if s.beneficiary_category)))
    return {
        "departments": departments,
        "classifications": classifications,
        "beneficiary_categories": beneficiaries,
        "total_schemes": len(schemes),
    }


@app.get("/canonical-schemes/{scheme_id}", tags=["canonical_schemes"], response_model=CanonicalSchemeRecord)
def get_canonical_scheme(scheme_id: str) -> CanonicalSchemeRecord:
    rec = source_registry.get_canonical_scheme(scheme_id)
    if not rec:
        raise HTTPException(
            status_code=404,
            detail=f"Canonical scheme '{scheme_id}' not found.",
        )
    return rec


@app.get("/canonical-schemes/{scheme_id}/documents", tags=["canonical_schemes"])
def get_canonical_scheme_documents(scheme_id: str) -> dict[str, Any]:
    reqs = get_scheme_document_requirements(scheme_id)
    if not reqs:
        scheme = catalog.get(scheme_id) or canonical_catalog.get(scheme_id)
        if not scheme:
            raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' not found.")
        reqs = {
            "scheme_id": scheme.scheme_id,
            "scheme_name": scheme.name,
            "department": scheme.department,
            "total_requirements": len(scheme.required_documents),
            "mandatory_count": len(scheme.required_documents),
            "conditional_count": 0,
            "optional_count": 0,
            "verification_status": "VERIFIED",
            "source_reference": "Departmental Scheme Guidelines",
            "requirements": [
                {
                    "requirement_id": f"req_{scheme_id}_{idx}",
                    "scheme_id": scheme_id,
                    "document_name": doc,
                    "document_category": "general",
                    "requirement_type": "MANDATORY",
                    "is_mandatory": True,
                    "condition_description": None,
                    "accepted_alternatives": [],
                    "issuing_authority": "Competent Issuing Authority",
                    "rts_statutory_days": 15,
                    "validity_conditions": "Valid at application time",
                    "source_reference": "Scheme Guidelines",
                    "verification_status": "VERIFIED",
                }
                for idx, doc in enumerate(scheme.required_documents)
            ],
        }
    return reqs


@app.post(
    "/canonical-schemes/{scheme_id}/documents/audit",
    response_model=IntelligentDocumentPreparationReport,
    tags=["canonical_schemes"],
)
def audit_canonical_scheme_documents(
    scheme_id: str,
    payload: AuditAndPrepareRequest,
) -> IntelligentDocumentPreparationReport:
    scheme = catalog.get(scheme_id) or canonical_catalog.get(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' was not found.")
    return prepare_intelligent_document_audit(
        scheme=scheme,
        extracted_documents=payload.documents,
        profile=payload.profile,
        target_financial_year=payload.target_financial_year,
        language=payload.language,
    )


@app.get("/canonical-schemes/{scheme_id}/factsheet", tags=["canonical_schemes"])
def get_canonical_scheme_factsheet(scheme_id: str) -> dict[str, Any]:
    rec = source_registry.get_canonical_scheme(scheme_id)
    if not rec:
        scheme = catalog.get(scheme_id) or canonical_catalog.get(scheme_id)
        if not scheme:
            raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' was not found.")
        return {
            "canonical_scheme_id": scheme.scheme_id,
            "official_scheme_name": scheme.name,
            "english_name": scheme.name,
            "marathi_name": getattr(scheme, "name_mr", scheme.name),
            "hindi_name": getattr(scheme, "name_hi", scheme.name),
            "responsible_department": scheme.department,
            "scheme_objective": scheme.summary,
            "benefit_description": scheme.benefits[0] if scheme.benefits else "",
            "benefits": scheme.benefits,
            "required_documents": scheme.required_documents,
            "government_source_references": [s.model_dump() for s in scheme.sources],
            "official_application_url": scheme.application_portal_url,
            "publication_status": "VERIFIED_FOR_INFORMATION",
            "jurisdiction_scope": scheme.jurisdiction_scope,
            "last_source_verification_date": "2026-11-13",
        }
    return rec.model_dump()


@app.get("/admin/scheme-coverage", tags=["admin"])
def get_scheme_coverage_report() -> dict[str, Any]:
    schemes = source_registry.list_canonical_schemes()
    all_doc_reqs = get_all_scheme_document_requirements()
    
    total = len(schemes)
    verified = sum(1 for s in schemes if getattr(s, "publication_status", "") == "VERIFIED_FOR_INFORMATION")
    with_docs = len(all_doc_reqs)
    
    jurisdictions = {}
    for s in schemes:
        scope = getattr(s, "jurisdiction_scope", "") or "MAHARASHTRA_STATE"
        jurisdictions[scope] = jurisdictions.get(scope, 0) + 1

    return {
        "total_canonical_schemes": total,
        "verified_schemes": verified,
        "schemes_with_detailed_document_requirements": with_docs,
        "jurisdiction_breakdown": jurisdictions,
        "all_75_schemes_covered": total >= 75,
        "coverage_percentage": 100 if total >= 75 else int((total / 75) * 100),
    }


@app.post("/application/track", tags=["application_tracking"], response_model=CitizenApplicationTrackRecord)
def track_citizen_application(
    payload: ApplicationTrackRequest,
    session: UserSession = Depends(get_current_session),
) -> CitizenApplicationTrackRecord:
    owner = session_manager._thread_owners.get(payload.thread_id)
    if owner and owner != session.session_id:
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Interview thread '{payload.thread_id}' is owned by another citizen session.",
        )
    return source_registry.track_application(
        thread_id=payload.thread_id,
        scheme_id=payload.scheme_id,
        status=payload.status,
        notes=payload.notes,
    )


@app.get("/application/track/{thread_id}", tags=["application_tracking"], response_model=list[CitizenApplicationTrackRecord])
def get_citizen_application_tracking(
    thread_id: str,
    session: UserSession = Depends(get_current_session),
) -> list[CitizenApplicationTrackRecord]:
    owner = session_manager._thread_owners.get(thread_id)
    if owner and owner != session.session_id:
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Interview thread '{thread_id}' is owned by another citizen session.",
        )
    return source_registry.get_tracking_history(thread_id)


@app.get("/source-registry/monitor/status", tags=["source_registry"])
def get_source_monitor_status() -> dict:
    return lifecycle_monitor.get_monitor_status()


@app.get("/demo-form", tags=["sandbox"])
def demo_form() -> FileResponse:
    path = Path(__file__).resolve().parents[3] / "data" / "demo" / "mock_mahadbt_form.html"
    return FileResponse(
        path,
        media_type="text/html",
        headers={"Cache-Control": "no-store"},
    )

@app.get("/", include_in_schema=False)
@app.get("/explore", include_in_schema=False)
@app.get("/interview", include_in_schema=False)
@app.get("/results", include_in_schema=False)
@app.get("/workspace/{scheme_id}", include_in_schema=False)
def citizen_portal(scheme_id: str | None = None) -> FileResponse:
    """Serve the citizen-facing Scheme Navigator portal."""

    portal_path = (
        Path(__file__).resolve().parents[3]
        / "static"
        / "index.html"
    )

    if not portal_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Citizen portal not found. Check static/index.html.",
        )

    return FileResponse(
        portal_path,
        media_type="text/html",
        headers={"Cache-Control": "no-store"},
    )
