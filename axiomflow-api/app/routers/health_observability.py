from __future__ import annotations

from fastapi import APIRouter

from ..core.config import settings
from ..core.observability import (
    get_metric_value,
    default_alert_payload,
    send_alert_webhook,
)

router = APIRouter(prefix="/obs-health", tags=["metrics"])


def _ratio(num: float, den: float) -> float | None:
    if den <= 0:
        return None
    return num / den


@router.get("")
def observability_health() -> dict:
    """
    轻量健康检查：
    - PDF 解析缓存命中率
    - Smart batch 错误率
    - Celery 任务失败率
    - 发现异常时可选 webhook 告警（best-effort）

    注：若使用 Prometheus 客户端导出，需在外部做规则告警；此处只在使用内置 in-memory 计数器时生效。
    """
    # thresholds from settings
    cache_min_ratio = float(getattr(settings, "cache_hit_min_ratio", 0.5))
    batch_max_err = float(getattr(settings, "batch_error_max_ratio", 0.1))
    celery_max_fail = float(getattr(settings, "celery_fail_max_ratio", 0.05))

    # fetch in-memory metric values (may be None if prom client used)
    cache_hit = get_metric_value("axiomflow_pdf_parse_cache_hit_total") or 0.0
    cache_miss = get_metric_value("axiomflow_pdf_parse_cache_miss_total") or 0.0
    batch_total = get_metric_value("axiomflow_smart_batch_tasks_total") or 0.0
    batch_err = get_metric_value("axiomflow_smart_batch_errors_total") or 0.0
    celery_succ = get_metric_value("axiomflow_celery_task_success_total") or 0.0
    celery_fail = get_metric_value("axiomflow_celery_task_failure_total") or 0.0

    cache_ratio = _ratio(cache_hit, cache_hit + cache_miss)
    batch_err_ratio = _ratio(batch_err, batch_total)
    celery_fail_ratio = _ratio(celery_fail, celery_succ + celery_fail)

    issues: list[str] = []

    if cache_ratio is not None and cache_ratio < cache_min_ratio:
        issues.append(f"cache_hit_ratio {cache_ratio:.2%} < {cache_min_ratio:.0%}")
    if batch_err_ratio is not None and batch_err_ratio > batch_max_err:
        issues.append(f"batch_error_rate {batch_err_ratio:.2%} > {batch_max_err:.0%}")
    if celery_fail_ratio is not None and celery_fail_ratio > celery_max_fail:
        issues.append(f"celery_fail_rate {celery_fail_ratio:.2%} > {celery_max_fail:.0%}")

    status = "ok" if not issues else "degraded"

    # optional alert
    if issues:
        url = str(getattr(settings, "alert_webhook_url", "") or "")
        if url:
            payload = default_alert_payload(
                title="AxiomFlow observability health degraded",
                severity="warning",
                issues=issues,
                cache_hit_ratio=cache_ratio,
                batch_error_rate=batch_err_ratio,
                celery_fail_rate=celery_fail_ratio,
            )
            send_alert_webhook(url=url, payload=payload)

    return {
        "status": status,
        "issues": issues,
        "cache_hit_ratio": cache_ratio,
        "batch_error_rate": batch_err_ratio,
        "celery_fail_rate": celery_fail_ratio,
    }


