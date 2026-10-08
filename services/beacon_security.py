"""Signed tokens, rate limiting and visitor hashing for the public MVP beacon."""

import hashlib
import hmac
import os
import threading
import time
from collections import defaultdict, deque


def _secret() -> bytes:
    secret = os.getenv("BEACON_SECRET")
    if not secret:
        from services.auth import SECRET_KEY
        secret = SECRET_KEY
    return secret.encode()


def sign_build_id(build_id) -> str:
    """Token embedded in a generated MVP's beacon URL; proves it came from our pipeline."""
    message = f"mvp-beacon:{int(build_id)}".encode()
    return hmac.new(_secret(), message, hashlib.sha256).hexdigest()[:32]


def verify_token(build_id, token) -> bool:
    return bool(token) and hmac.compare_digest(sign_build_id(build_id), str(token))


def unsigned_allowed() -> bool:
    """Escape hatch for MVPs deployed before tokens existed."""
    return os.getenv("BEACON_ALLOW_UNSIGNED", "false").strip().lower() in ("1", "true", "yes")


def hash_visitor(client_ip: str, user_agent: str) -> str:
    """Keyed hash so stored visitor ids cannot be reversed by brute-forcing IPv4."""
    return hmac.new(_secret(), f"visitor:{client_ip}:{user_agent}".encode(), hashlib.sha256).hexdigest()


class SlidingWindowLimiter:
    """In-memory per-key request limiter (per process)."""

    MAX_KEYS = 50000

    def __init__(self, limit: int = 30, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            if len(self._hits) > self.MAX_KEYS:
                self._hits.clear()
            hits = self._hits[key]
            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()


beacon_limiter = SlidingWindowLimiter()
