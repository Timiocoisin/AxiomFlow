from __future__ import annotations

from fastapi import APIRouter, Response

from ..core.config import settings
from ..core.observability import CONTENT_TYPE_LATEST, metrics_text

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
def get_metrics() -> Response:
    if not getattr(settings, "metrics_enabled", True):
        return Response(content="metrics_disabled\n", media_type="text/plain")
    data = metrics_text()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


