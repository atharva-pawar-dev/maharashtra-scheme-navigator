from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse

from scheme_navigator.core.config import settings
from scheme_navigator.security.auth import session_manager
from scheme_navigator.security.models import UserRole
from scheme_navigator.security.rate_limiter import rate_limit

router = APIRouter(tags=["human-review"])


@router.get(
    "/reviewer",
    include_in_schema=False,
    dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60))],
)
def reviewer_dashboard(
    request: Request,
    authorization: str | None = Header(default=None),
) -> FileResponse:
    """Serve the human-review dashboard with strict role authorization."""
    token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].casefold() == "bearer":
            token = parts[1]
        elif len(parts) == 1:
            token = parts[0]
    if not token:
        token = request.cookies.get("sn_session")

    session = session_manager.validate_token(token) if token else None

    # Citizens are strictly forbidden from accessing reviewer dashboard
    if session and not session_manager.has_role(session, UserRole.ANALYST):
        raise HTTPException(
            status_code=403,
            detail="Access denied: citizen accounts are not authorized to access the reviewer dashboard.",
        )

    # In production, unauthenticated access is strictly forbidden
    if settings.app_env.casefold() in {"production", "prod"} and not session:
        raise HTTPException(
            status_code=403,
            detail="Human document review dashboard requires authenticated reviewer access in production.",
        )

    project_root = Path(__file__).resolve().parents[3]
    dashboard_path = project_root / "static" / "reviewer.html"
    if not dashboard_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Reviewer dashboard not found. Restore static/reviewer.html in the project root.",
        )
    return FileResponse(
        dashboard_path,
        media_type="text/html",
        headers={"Cache-Control": "no-store"},
    )
