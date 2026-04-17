from __future__ import annotations

from pathlib import Path

from slowapi import Limiter
from slowapi.util import get_remote_address

# Dedicated UTF-8 file avoids slowapi/Starlette reading a project .env as system default encoding (e.g. GBK on Windows).
_limiter_env = Path(__file__).resolve().parent / ".rate_limit_env"
limiter = Limiter(key_func=get_remote_address, config_filename=str(_limiter_env))
