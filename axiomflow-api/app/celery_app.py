"""
Celery 应用配置

用于任务队列和异步处理，支持多 worker、任务持久化、失败重试、分布式扩展。
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from .core.config import settings

# 创建 Celery 应用
celery_app = Celery(
    "axiomflow",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.translate", "app.tasks.batch", "app.tasks.observability", "app.tasks.parse"],
)

# 显式导入任务模块以确保在 Windows 上正确注册
# 这可以解决 "not enough values to unpack" 错误
# 在 Windows 上，Celery 需要显式导入任务模块才能正确识别
try:
    from .tasks import parse  # noqa: F401
    from .tasks import translate  # noqa: F401
    from .tasks import batch  # noqa: F401
    from .tasks import observability  # noqa: F401
except ImportError:
    pass

# Celery 配置
celery_app.conf.update(
    # 序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # 任务路由（可以按任务类型分配到不同队列）
    task_routes={
        "app.tasks.translate.*": {"queue": "translation"},
        "app.tasks.batch.*": {"queue": "batch"},
    },
    # 默认队列配置
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    # 结果过期时间（秒）
    result_expires=3600,
    # 任务确认配置
    task_acks_late=True,  # 任务完成后才确认
    task_reject_on_worker_lost=True,  # Worker 崩溃时重新入队
    # 任务超时
    task_time_limit=3600,  # 1 小时硬超时
    task_soft_time_limit=3300,  # 55 分钟软超时
    # Worker 预取限制（防止任务堆积在单个 worker）
    worker_prefetch_multiplier=1,  # 一次只取一个任务
    # 任务重试策略（全局默认）
    task_autoretry_for=(Exception,),
    task_max_retries=3,
    task_default_retry_delay=60,  # 默认重试延迟 60 秒
    # 结果后端配置
    result_backend_transport_options={
        "visibility_timeout": 3600,  # 结果可见性超时
    },
    # 开发环境：同步执行（可选）
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
)

# Periodic tasks (requires running celery beat)
if getattr(settings, "obs_health_check_enabled", True):
    celery_app.conf.beat_schedule = {
        "axiomflow_observability_health_check": {
            "task": "app.tasks.observability.observability_health_check",
            # default every 60s
            "schedule": float(getattr(settings, "obs_health_check_interval_s", 60.0)),
        }
    }

