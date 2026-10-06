"""In-memory sliding-window rate limiter for the tracking endpoint.

Protects against brute-force case code enumeration.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request


class RateLimiter:
    """Simple in-memory rate limiter using a sliding time window."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def _client_key(self, request: Request) -> str:
        """Derive a key from the client's IP address."""
        if request.client:
            return request.client.host
        return "unknown"

    def check(self, request: Request) -> None:
        """Raise HTTP 429 if the client has exceeded the rate limit."""
        key = self._client_key(request)
        now = time.monotonic()
        window_start = now - self.window_seconds

        # Prune expired timestamps
        self._hits[key] = [t for t in self._hits[key] if t > window_start]

        if len(self._hits[key]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
            )

        self._hits[key].append(now)

    def reset(self) -> None:
        """Clear all tracked hits (useful for testing)."""
        self._hits.clear()


# Singleton used by the tracking endpoint
tracking_limiter = RateLimiter(max_requests=10, window_seconds=60)
