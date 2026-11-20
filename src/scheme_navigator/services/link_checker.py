"""TRIMURTI v3 Official Source Link Verification Service.

Enforces Invariant I-09 (Lawful and Polite Research) and Section 24.1:
Checks official source, GR, and application URLs.
Distinguishes:
- VALID_URL
- REDIRECTED_URL
- TEMPORARILY_UNAVAILABLE
- FORBIDDEN
- AUTH_REQUIRED
- CHANGED_PORTAL
- DEAD_URL
- UNKNOWN
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, List
import httpx

logger = logging.getLogger("scheme_navigator.link_checker")


class LinkStatus(StrEnum):
    VALID_URL = "VALID_URL"
    REDIRECTED_URL = "REDIRECTED_URL"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
    FORBIDDEN = "FORBIDDEN"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    CHANGED_PORTAL = "CHANGED_PORTAL"
    DEAD_URL = "DEAD_URL"
    UNKNOWN = "UNKNOWN"


@dataclass
class LinkCheckResult:
    url: str
    status: LinkStatus
    http_code: int | None = None
    final_url: str | None = None
    error_message: str | None = None
    latency_ms: float = 0.0


class SourceLinkChecker:
    def __init__(
        self,
        user_agent: str = "MaharashtraSchemeNavigator/3.0 (Research & Compliance)",
        timeout_seconds: float = 5.0,
        mock_mode: bool = False,
    ) -> None:
        self.user_agent = user_agent
        self.timeout = timeout_seconds
        self.mock_mode = mock_mode

    def check_url(self, url: str) -> LinkCheckResult:
        if not url or not url.startswith(("http://", "https://")):
            return LinkCheckResult(url=url, status=LinkStatus.UNKNOWN, error_message="Malformed URL")

        if self.mock_mode:
            # Deterministic simulation mode for offline/sandboxed execution
            if "404" in url or "dead" in url:
                return LinkCheckResult(url=url, status=LinkStatus.DEAD_URL, http_code=404)
            if "redirect" in url:
                return LinkCheckResult(url=url, status=LinkStatus.REDIRECTED_URL, http_code=302, final_url=url + "/v2")
            return LinkCheckResult(url=url, status=LinkStatus.VALID_URL, http_code=200, final_url=url, latency_ms=45.0)

        headers = {"User-Agent": self.user_agent}
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                resp = client.head(url)
                if resp.status_code == 405:
                    # If HEAD is not allowed, try a light GET
                    resp = client.get(url, headers={"Range": "bytes=0-1024"})
                latency = round((time.perf_counter() - start) * 1000, 2)

                final_url = str(resp.url)
                status_code = resp.status_code

                if status_code == 200:
                    if final_url != url:
                        return LinkCheckResult(url=url, status=LinkStatus.REDIRECTED_URL, http_code=status_code, final_url=final_url, latency_ms=latency)
                    return LinkCheckResult(url=url, status=LinkStatus.VALID_URL, http_code=status_code, final_url=final_url, latency_ms=latency)
                elif status_code in (301, 302, 307, 308):
                    return LinkCheckResult(url=url, status=LinkStatus.REDIRECTED_URL, http_code=status_code, final_url=final_url, latency_ms=latency)
                elif status_code == 401:
                    return LinkCheckResult(url=url, status=LinkStatus.AUTH_REQUIRED, http_code=status_code, final_url=final_url, latency_ms=latency)
                elif status_code == 403:
                    return LinkCheckResult(url=url, status=LinkStatus.FORBIDDEN, http_code=status_code, final_url=final_url, latency_ms=latency)
                elif status_code in (404, 410):
                    return LinkCheckResult(url=url, status=LinkStatus.DEAD_URL, http_code=status_code, final_url=final_url, latency_ms=latency)
                elif status_code >= 500:
                    return LinkCheckResult(url=url, status=LinkStatus.TEMPORARILY_UNAVAILABLE, http_code=status_code, final_url=final_url, latency_ms=latency)
                else:
                    return LinkCheckResult(url=url, status=LinkStatus.UNKNOWN, http_code=status_code, final_url=final_url, latency_ms=latency)

        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            latency = round((time.perf_counter() - start) * 1000, 2)
            return LinkCheckResult(url=url, status=LinkStatus.TEMPORARILY_UNAVAILABLE, error_message=str(exc), latency_ms=latency)
        except Exception as exc:
            latency = round((time.perf_counter() - start) * 1000, 2)
            return LinkCheckResult(url=url, status=LinkStatus.UNKNOWN, error_message=str(exc), latency_ms=latency)
