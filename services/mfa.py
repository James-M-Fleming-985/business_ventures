"""TOTP (RFC 6238) two-factor helpers, recovery codes and a login throttle.

Standard library only so it adds no deployment dependency.
"""

import base64
import hashlib
import hmac
import json
import secrets
import struct
import threading
import time
from collections import defaultdict, deque
from typing import List, Optional
from urllib.parse import quote

STEP_SECONDS = 30
DIGITS = 6
RECOVERY_CODE_COUNT = 8


def generate_secret() -> str:
    """Return a random base32 secret (160 bits)."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii")


def _hotp(secret: str, counter: int, digits: int = DIGITS) -> str:
    padded = secret.replace(" ", "").upper()
    padded += "=" * (-len(padded) % 8)
    key = base64.b32decode(padded)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(value % (10 ** digits)).zfill(digits)


def current_step(now: Optional[float] = None) -> int:
    return int((time.time() if now is None else now) // STEP_SECONDS)


def totp_code(secret: str, step: int) -> str:
    return _hotp(secret, step)


def verify_totp(
    secret: str,
    code: str,
    last_step: int = 0,
    now: Optional[float] = None,
    window: int = 1,
) -> Optional[int]:
    """Return the matched time step, or None.

    Steps at or before ``last_step`` are rejected so a code cannot be replayed.
    """
    code = "".join(ch for ch in (code or "") if ch.isdigit())
    if len(code) != DIGITS:
        return None
    current = current_step(now)
    matched = None
    for step in range(current - window, current + window + 1):
        if step > (last_step or 0) and hmac.compare_digest(_hotp(secret, step), code):
            matched = step
    return matched


def provisioning_uri(secret: str, account: str, issuer: str = "Causal Affect") -> str:
    return (
        f"otpauth://totp/{quote(issuer)}:{quote(account)}"
        f"?secret={secret}&issuer={quote(issuer)}"
        f"&algorithm=SHA1&digits={DIGITS}&period={STEP_SECONDS}"
    )


def _normalise_recovery(code: str) -> str:
    return "".join(ch for ch in (code or "").lower() if ch in "0123456789abcdef")


def _hash_recovery(code: str) -> str:
    return hashlib.sha256(_normalise_recovery(code).encode("ascii")).hexdigest()


def generate_recovery_codes(count: int = RECOVERY_CODE_COUNT) -> List[str]:
    return ["-".join(secrets.token_hex(2) for _ in range(3)) for _ in range(count)]


def serialise_recovery_hashes(codes: List[str]) -> str:
    return json.dumps([_hash_recovery(c) for c in codes])


def consume_recovery_code(stored: Optional[str], code: str) -> Optional[str]:
    """If ``code`` is a valid unused recovery code, return the updated stored
    value with it removed; otherwise None."""
    if not stored or len(_normalise_recovery(code)) != 12:
        return None
    try:
        hashes = json.loads(stored)
    except ValueError:
        return None
    candidate = _hash_recovery(code)
    for existing in hashes:
        if hmac.compare_digest(existing, candidate):
            hashes.remove(existing)
            return json.dumps(hashes)
    return None


class LoginThrottle:
    """In-memory failed-login limiter (per process)."""

    def __init__(self, max_failures: int = 5, window_seconds: int = 900):
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque:
        attempts = self._failures[key]
        while attempts and now - attempts[0] > self.window_seconds:
            attempts.popleft()
        return attempts

    def is_blocked(self, key: str) -> bool:
        with self._lock:
            return len(self._prune(key, time.time())) >= self.max_failures

    def record_failure(self, key: str) -> None:
        with self._lock:
            now = time.time()
            self._prune(key, now).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._failures.clear()


login_throttle = LoginThrottle()
