from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter per client identifier."""

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check_limit(
        self,
        key: str,
        max_requests: int = 60,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """Check if request exceeds rate limit.

        Returns (is_allowed, retry_after_seconds).
        """
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            timestamps = self._requests[key]
            # Prune timestamps outside current window
            pruned = [ts for ts in timestamps if ts > window_start]
            self._requests[key] = pruned

            if len(pruned) >= max_requests:
                earliest = pruned[0]
                retry_after = max(1, int(window_seconds - (now - earliest)))
                return False, retry_after

            pruned.append(now)
            return True, 0

    def purge_idle(self, idle_seconds: int = 300) -> int:
        now = time.time()
        with self._lock:
            idle_keys = [
                k for k, timestamps in self._requests.items()
                if not timestamps or (now - timestamps[-1]) > idle_seconds
            ]
            for k in idle_keys:
                self._requests.pop(k, None)
            return len(idle_keys)

    def reset(self) -> None:
        """Clear all recorded rate limit windows (useful for test isolation)."""
        with self._lock:
            self._requests.clear()


rate_limiter = InMemoryRateLimiter()


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """FastAPI dependency for endpoint-specific rate limiting."""

    def _limiter_dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        # Combine IP and endpoint path for granular throttling
        key = f"{client_ip}:{request.url.path}"
        allowed, retry_after = rate_limiter.check_limit(
            key, max_requests=max_requests, window_seconds=window_seconds
        )
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please wait before making more requests.",
                headers={"Retry-After": str(retry_after)},
            )

    return _limiter_dependency
