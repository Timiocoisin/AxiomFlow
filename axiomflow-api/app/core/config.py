from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AxiomFlow API"
    environment: str = "development"

    cors_allow_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Database
    # MySQL 连接格式: mysql+pymysql://user:password@host:port/database
    # 示例: mysql+pymysql://root:password@localhost:3306/axiomflow
    database_url: str = "mysql+pymysql://root:password@localhost:3306/axiomflow?charset=utf8mb4"

    # Celery 配置（仅用 MySQL，不依赖 Redis）
    # Celery SQLAlchemy broker 示例：sqla+mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4
    # Celery result backend 示例：db+mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4
    celery_broker_url: str = "sqla+mysql+pymysql://root:password@localhost:3306/axiomflow?charset=utf8mb4"
    celery_result_backend: str = "db+mysql+pymysql://root:password@localhost:3306/axiomflow?charset=utf8mb4"
    celery_task_always_eager: bool = False  # 开发环境可以设置为 True 以同步执行

    # Translation runtime
    # 最大并发翻译数（影响 API & Celery 翻译吞吐）
    translation_max_concurrent: int = 5

    # Observability
    # 是否启用 /metrics（Prometheus 格式，若未安装 prometheus_client 会输出简化格式）
    metrics_enabled: bool = True
    # 是否输出 JSON 结构化日志
    log_json: bool = False
    # 失败告警 webhook（可选，如飞书/钉钉/自建 webhook）
    alert_webhook_url: str = ""
    # 是否启用周期性 obs-health 检查（需要 celery beat）
    obs_health_check_enabled: bool = True
    # 周期性检查间隔（秒）
    obs_health_check_interval_s: float = 60.0
    # 告警抖动过滤：连续 N 次 degraded 才告警
    obs_health_debounce_count: int = 3
    # 告警冷却时间（秒）：避免同一类问题频繁刷屏
    obs_health_alert_cooldown_s: float = 600.0
    # 是否在恢复到 ok 时发送 recovery 通知
    obs_health_recovery_alert: bool = True
    # 批处理自适应调优：目标平均响应时间（秒）
    batch_target_avg_latency_s: float = 1.2
    # 批处理自适应调优：允许的失败率（0~1）
    batch_target_error_rate: float = 0.05
    # 批处理大小上限（避免极端情况）
    batch_max_size: int = 32
    # 健康检查阈值
    cache_hit_min_ratio: float = 0.5
    batch_error_max_ratio: float = 0.1
    celery_fail_max_ratio: float = 0.05

    # Local cache
    # 通用缓存根目录（可选）
    cache_dir: str = ""
    # PDF 解析缓存
    pdf_cache_enabled: bool = True
    pdf_parse_cache_dir: str = ""  # 若为空且 cache_dir 不为空，则使用 {cache_dir}/pdf_parse

    # PDF export / fonts
    # 注意：为了兼容历史环境变量名，这里用 alias 支持 AXIOMFLOW_PDF_FONT
    pdf_font: str = Field(default="", validation_alias="AXIOMFLOW_PDF_FONT")

    # Optional provider overrides (ignored if未配置)
    ollama_api_base: str | None = Field(default=None, validation_alias="OLLAMA_API_BASE")
    ollama_model: str | None = Field(default=None, validation_alias="OLLAMA_MODEL")

    # JWT 配置
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        validation_alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7天


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


