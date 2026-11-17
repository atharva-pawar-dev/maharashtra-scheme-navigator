from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

from scheme_navigator.ingestion.models import (
    DocumentChangeEvent,
    IngestedSnapshot,
    IngestionReviewItem,
    IngestionReviewStatus,
    IngestionSourceKind,
)
from scheme_navigator.ingestion.store import IngestionStore
from scheme_navigator.security.ssrf import SSRFSafeTransport, validate_safe_url

ALLOWED_HOSTS = {
    "mahadbt.maharashtra.gov.in",
    "mahadbt2.maharashtra.gov.in",
    "aaplesarkar.mahaonline.gov.in",
    "myscheme.gov.in",
    "gr.maharashtra.gov.in",
    "maharashtra.gov.in",
    "sjsa.maharashtra.gov.in",
    "womenchild.maharashtra.gov.in",
}
MAX_SOURCE_BYTES = 15 * 1024 * 1024


def _check_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Only HTTPS source URLs are accepted: Security violation: Only secure HTTPS URLs are permitted.")
    host = parsed.hostname.casefold()
    if not any(host == allowed or host.endswith("." + allowed) for allowed in ALLOWED_HOSTS):
        raise ValueError(f"Host is not in the government-source allowlist: {host}")
    validate_safe_url(url, enforce_allowlist=True)


def _classify_source_kind(url: str) -> tuple[IngestionSourceKind, bool]:
    parsed = urlparse(url)
    host = (parsed.hostname or "").casefold()
    if "gr.maharashtra.gov.in" in host:
        return IngestionSourceKind.GOVERNMENT_RESOLUTION, False
    if "myscheme.gov.in" in host:
        return IngestionSourceKind.MYSCHEME_AGGREGATOR, True
    if "mahadbt" in host:
        return IngestionSourceKind.MAHADBT_SCHEME_PAGE, False
    if "aaplesarkar" in host:
        return IngestionSourceKind.AAPLE_SARKAR_PAGE, False
    return IngestionSourceKind.DEPARTMENTAL_PORTAL, False


def _robots_allows(url: str, user_agent: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        validate_safe_url(robots_url, enforce_allowlist=True)
        with httpx.Client(
            transport=SSRFSafeTransport(),
            timeout=8,
            follow_redirects=False,
            headers={"User-Agent": user_agent},
        ) as client:
            response = client.get(robots_url)
            if response.status_code == 404:
                return True
            if response.status_code != 200:
                # Fail closed when robots policy could not be determined.
                return False
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.parse(response.text.splitlines())
            return parser.can_fetch(user_agent, url)
    except (httpx.HTTPError, ValueError):
        return False


def ingest_public_source(
    url: str,
    output_dir: str | Path = "data/ingested",
    *,
    respect_robots: bool = True,
    store: IngestionStore | None = None,
    enqueue_review: bool = True,
) -> tuple[IngestedSnapshot, DocumentChangeEvent | None]:
    """Fetch one explicitly supplied official public URL; no login, CAPTCHA, or access-control bypass.
    
    Stores immutable snapshot, detects changes against previous snapshots of this URL,
    and enqueues the record for human review.
    """
    _check_url(url)
    user_agent = "SchemeNavigatorResearchBot/0.1 (+source-attribution; contact project maintainer)"
    if respect_robots and not _robots_allows(url, user_agent):
        raise PermissionError("Robots policy disallows this fetch or could not be verified")

    time.sleep(0.25)  # modest per-request pacing; batch schedulers should add domain-wide throttling.
    with httpx.Client(
        transport=SSRFSafeTransport(),
        timeout=25,
        follow_redirects=False,
        headers={"User-Agent": user_agent},
    ) as client:
        current_url = url
        redirect_count = 0
        while True:
            _check_url(current_url)
            response = client.get(current_url)
            if response.is_redirect:
                redirect_count += 1
                if redirect_count > 3:
                    raise ValueError("Too many redirects during source ingestion (limit is 3).")
                location = response.headers.get("location")
                if not location:
                    raise ValueError("Redirect response missing Location header.")
                next_url = str(response.url.join(location))
                _check_url(next_url)
                current_url = next_url
            else:
                break
    response.raise_for_status()

    raw = response.content
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError("Source exceeds 15 MiB size limit")

    content_type = response.headers.get("content-type", "application/octet-stream").split(";")[0].lower()
    etag = response.headers.get("etag")
    last_modified = response.headers.get("last-modified")

    title = ""
    text = ""
    if content_type in {"application/pdf", "application/x-pdf"} or str(response.url).lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(raw))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        if reader.metadata and reader.metadata.title:
            title = str(reader.metadata.title)
    elif "html" in content_type or content_type.startswith("text/"):
        soup = BeautifulSoup(raw, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        for tag in soup(["script", "style", "noscript", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text("\n", strip=True)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())[:500_000]
    if len(text) < 50:
        raise ValueError("Extracted source text is too short; inspect manually rather than compiling a rule")

    sha256 = hashlib.sha256(raw).hexdigest()
    snapshot_id = f"snap_{sha256[:16]}"
    now_iso = datetime.now(UTC).isoformat()
    source_kind, is_aggregator = _classify_source_kind(url)

    snapshot = IngestedSnapshot(
        snapshot_id=snapshot_id,
        source_url=url,
        final_url=str(response.url),
        source_kind=source_kind,
        sha256=sha256,
        byte_size=len(raw),
        retrieved_at=now_iso,
        publication_date=None,
        official_reference=None,
        title=title or url,
        extracted_text=text,
        is_aggregator=is_aggregator,
        etag=etag,
        last_modified=last_modified,
        notes="Aggregator source: for discovery only, not primary legal authority" if is_aggregator else None,
    )

    # Immutable filesystem snapshot backup
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / f"{snapshot_id}.json"
    json_path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")

    # Ingestion store integration
    active_store = store or IngestionStore()
    saved_snapshot, change_event = active_store.save_snapshot(snapshot)

    if enqueue_review:
        review_item = IngestionReviewItem(
            item_id=f"rev_{snapshot_id}",
            source_url=url,
            source_title=snapshot.title,
            source_kind=source_kind,
            sha256=sha256,
            retrieved_at=now_iso,
            review_status=IngestionReviewStatus.PENDING_REVIEW,
            extracted_scheme_data={
                "snapshot_id": snapshot_id,
                "title": snapshot.title,
                "is_aggregator": is_aggregator,
                "text_sample": text[:1000],
            },
            reviewer_id=None,
            review_notes=None,
            created_at=now_iso,
            updated_at=now_iso,
        )
        active_store.enqueue_for_review(review_item)

    return saved_snapshot, change_event
