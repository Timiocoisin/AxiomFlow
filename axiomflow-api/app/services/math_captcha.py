from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class MathChallenge:
    answer: int
    expires_at: float


_TTL_SECONDS = 300
_store: Dict[str, MathChallenge] = {}
_lock = threading.Lock()


def _purge_locked(now: float) -> None:
    dead = [k for k, v in _store.items() if v.expires_at <= now]
    for k in dead:
        del _store[k]


def issue_math_challenge() -> Tuple[str, int, int]:
    """Return captcha_id and two addends (2–9) for display; answer is stored server-side only."""
    a = secrets.randbelow(8) + 2
    b = secrets.randbelow(8) + 2
    cid = secrets.token_urlsafe(16)
    exp = time.time() + _TTL_SECONDS
    with _lock:
        _purge_locked(time.time())
        _store[cid] = MathChallenge(answer=a + b, expires_at=exp)
    return cid, a, b


def validate_and_consume_math(*, captcha_id: str, answer: int) -> bool:
    now = time.time()
    with _lock:
        _purge_locked(now)
        ch = _store.pop(captcha_id, None)
        if not ch or ch.expires_at <= now:
            return False
        return int(answer) == ch.answer
