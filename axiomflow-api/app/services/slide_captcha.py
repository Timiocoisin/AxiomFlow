from __future__ import annotations

import io
import secrets
import threading
import time
from urllib.request import Request, urlopen
from dataclasses import dataclass
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageOps
from app.core.config import get_settings


@dataclass
class SlideChallenge:
    target_x: int
    target_y: int
    expires_at: float


_TTL_SECONDS = 300
_store: Dict[str, SlideChallenge] = {}
_lock = threading.Lock()


def _purge_locked(now: float) -> None:
    dead = [k for k, v in _store.items() if v.expires_at <= now]
    for k in dead:
        del _store[k]


def _render_slide_png(
    scene_w: int,
    scene_h: int,
    target_x: int,
    target_y: int,
    *,
    piece_size: int = 52,
) -> Tuple[bytes, bytes]:
    """
    PNG with opaque noise background and a fully transparent circular hole.
    Target (target_x, target_y) is the top-left of the square that bounds the puzzle piece / hole.
    Coordinates are not exposed in JSON; clients infer the gap from alpha.
    """
    base_img = _load_background_from_api(scene_w, scene_h)
    if base_img is None:
        gray = Image.effect_noise((scene_w, scene_h), 72)
        rch = gray.point(lambda p: min(255, int(p * 1.15 + 35)))
        gch = gray.point(lambda p: min(255, int(p * 0.95 + 28)))
        bch = gray.point(lambda p: min(255, int(p * 1.05 + 45)))
        alpha = Image.new("L", (scene_w, scene_h), 255)
        base_img = Image.merge("RGBA", (rch, gch, bch, alpha))

    img = base_img.copy()

    cx = target_x + piece_size // 2
    cy = target_y + piece_size // 2
    radius = piece_size // 2 - 1
    draw = ImageDraw.Draw(img, "RGBA")
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=(0, 0, 0, 0),
        outline=(0, 0, 0, 0),
    )

    # Build piece image from original background (before punching hole)
    piece_img = base_img.crop((target_x, target_y, target_x + piece_size, target_y + piece_size)).copy()
    mask = Image.new("L", (piece_size, piece_size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse((1, 1, piece_size - 1, piece_size - 1), fill=255)
    piece_img.putalpha(mask)

    hole_buf = io.BytesIO()
    img.save(hole_buf, format="PNG", compress_level=9, optimize=True)
    piece_buf = io.BytesIO()
    piece_img.save(piece_buf, format="PNG", compress_level=9, optimize=True)
    return hole_buf.getvalue(), piece_buf.getvalue()


def _load_background_from_api(scene_w: int, scene_h: int) -> Image.Image | None:
    """
    Fetch background image from configured interface and resize/crop to scene size.
    Returns RGBA image or None when fetch/parse fails.
    """
    settings = get_settings()
    url = (settings.CAPTCHA_IMAGE_URL or "").strip()
    if not url:
        return None
    try:
        req = Request(
            url,
            headers={
                "User-Agent": "AxiomFlow-Captcha/1.0",
                "Accept": "image/*,*/*;q=0.8",
            },
        )
        with urlopen(req, timeout=8) as resp:
            data = resp.read()
        with Image.open(io.BytesIO(data)) as raw:
            base = raw.convert("RGBA")
        return ImageOps.fit(base, (scene_w, scene_h), method=Image.Resampling.LANCZOS)
    except Exception:
        return None


def issue_slide_challenge(*, scene_width: int = 320, scene_height: int = 160) -> Tuple[str, bytes, bytes, int, int]:
    """
    Create challenge; returns captcha_id, PNG bytes, and scene dimensions.
    Gap position is not returned in JSON—clients must infer from the image (e.g. transparent region).
    """
    piece_size = 52
    min_x = 96
    max_x = max(min_x + 24, scene_width - piece_size - 20)
    min_y = 16
    max_y = max(min_y + 8, scene_height - piece_size - 26)

    target_x = secrets.randbelow(max_x - min_x + 1) + min_x
    target_y = secrets.randbelow(max_y - min_y + 1) + min_y
    cid = secrets.token_urlsafe(24)
    exp = time.time() + _TTL_SECONDS

    hole_png, piece_png = _render_slide_png(scene_width, scene_height, target_x, target_y, piece_size=piece_size)

    with _lock:
        _purge_locked(time.time())
        _store[cid] = SlideChallenge(target_x=target_x, target_y=target_y, expires_at=exp)

    return cid, hole_png, piece_png, scene_width, scene_height


def validate_and_consume_slide(*, captcha_id: str, piece_final_x: int, tolerance: int = 14) -> bool:
    """Return True if piece_final_x matches. Challenge is always consumed (one attempt)."""
    now = time.time()
    with _lock:
        _purge_locked(now)
        ch = _store.pop(captcha_id, None)
        if not ch or ch.expires_at <= now:
            return False
        if abs(int(piece_final_x) - ch.target_x) > tolerance:
            return False
        return True
