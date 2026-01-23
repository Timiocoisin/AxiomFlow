from __future__ import annotations

import json
import time
from pathlib import Path

from celery.utils.log import get_task_logger

from ..celery_app import celery_app
from ..core.config import settings
from ..core.observability import (
    default_alert_payload,
    send_alert_webhook,
)
from ..routers.health_observability import observability_health

logger = get_task_logger(__name__)


def _state_path() -> Path | None:
    root = str(getattr(settings, "cache_dir", "") or "").strip()
    if not root:
        return None
    try:
        p = Path(root) / "obs_state.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        return None


def _load_state() -> dict:
    p = _state_path()
    if p is None or not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    p = _state_path()
    if p is None:
        return
    try:
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        tmp.replace(p)
    except Exception:
        return


@celery_app.task(
    name="app.tasks.observability.observability_health_check",
    bind=False,
    ignore_result=True,
)
def observability_health_check() -> None:
    """
    周期性可观测性健康检查（需要 celery beat）。
    - 调用 obs-health 同样的检查逻辑
    - 抖动过滤：连续 N 次 degraded 才告警
    - 冷却：同类告警间隔 cooldown 秒
    - 可选 recovery：恢复到 ok 时发通知
    """
    try:
        now = time.time()
        result = observability_health()
        status = result.get("status")
        issues = result.get("issues") or []

        logger.info(
            f"obs-health status={status} issues={len(issues)}",
            extra={"event": "obs_health_check", **result},
        )

        state = _load_state()
        prev_status = str(state.get("last_status") or "ok")
        degraded_streak = int(state.get("degraded_streak") or 0)
        last_alert_ts = float(state.get("last_alert_ts") or 0.0)

        debounce_n = max(1, int(getattr(settings, "obs_health_debounce_count", 3)))
        cooldown_s = float(getattr(settings, "obs_health_alert_cooldown_s", 600.0))
        recovery_alert = bool(getattr(settings, "obs_health_recovery_alert", True))

        url = str(getattr(settings, "alert_webhook_url", "") or "")

        if status != "ok" and issues:
            degraded_streak += 1
            if url and degraded_streak >= debounce_n and (now - last_alert_ts) >= cooldown_s:
                payload = default_alert_payload(
                    title="AxiomFlow periodic obs-health degraded",
                    severity="warning",
                    degraded_streak=degraded_streak,
                    **result,
                )
                send_alert_webhook(url=url, payload=payload)
                last_alert_ts = now
        else:
            if recovery_alert and url and prev_status != "ok":
                payload = default_alert_payload(
                    title="AxiomFlow periodic obs-health recovered",
                    severity="info",
                    **result,
                )
                send_alert_webhook(url=url, payload=payload)
            degraded_streak = 0

        state["last_status"] = status
        state["degraded_streak"] = degraded_streak
        state["last_alert_ts"] = last_alert_ts
        _save_state(state)
    except Exception as exc:
        logger.error(
            f"obs-health check failed: {type(exc).__name__}: {str(exc)[:300]}",
            exc_info=True,
            extra={"event": "obs_health_check_failed"},
        )


