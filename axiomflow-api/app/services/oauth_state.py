from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from typing import Dict


@dataclass
class OAuthState:
    provider: str
    expires_at: float


_TTL_SECONDS = 10 * 60
_store: Dict[str, OAuthState] = {}
_lock = threading.Lock()


def _purge_locked(now: float) -> None:
    dead = [k for k, v in _store.items() if v.expires_at <= now]
    for k in dead:
        del _store[k]


def issue_oauth_state(provider: str) -> str:
    s = secrets.token_urlsafe(24)
    with _lock:
        _purge_locked(time.time())
        _store[s] = OAuthState(provider=provider, expires_at=time.time() + _TTL_SECONDS)
    return s


def consume_oauth_state(state: str, provider: str) -> bool:
    with _lock:
        _purge_locked(time.time())
        obj = _store.pop(state, None)
        if not obj:
            return False
        return obj.provider == provider and obj.expires_at > time.time()

