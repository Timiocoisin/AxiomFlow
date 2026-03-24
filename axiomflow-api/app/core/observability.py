from __future__ import annotations

import asyncio
import json
import logging
import logging.handlers
import os
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


# ---- Logging (structured) ----


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # include any extra fields attached via `extra=...`
        for k, v in record.__dict__.items():
            if k in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            ):
                continue
            if k.startswith("_"):
                continue
            # avoid overwriting base keys
            if k in base:
                continue
            base[k] = v

        if record.exc_info:
            base["exc_type"] = str(record.exc_info[0].__name__)
            base["exc"] = "".join(traceback.format_exception(*record.exc_info))[-4000:]

        return json.dumps(base, ensure_ascii=False)


def setup_logging(*, json_logs: bool, log_type: str = "app") -> None:
    """
    Setup logging formatter with file handlers.
    
    Args:
        json_logs: 是否使用JSON格式日志
        log_type: 日志类型，"app" 为主程序日志，"celery" 为Celery任务日志
    
    Logs are written to separate directories:
    - logs/app/: 主程序日志 (app_info.log, app_warning.log, app_error.log)
    - logs/celery/: Celery日志 (celery_info.log, celery_warning.log, celery_error.log)
    
    Console output is completely disabled.
    """
    # 创建日志根目录
    logs_root = Path(__file__).resolve().parents[2] / "logs"
    logs_root.mkdir(parents=True, exist_ok=True)
    
    # 根据日志类型创建对应的子目录
    if log_type == "app":
        log_dir = logs_root / "app"
        log_dir.mkdir(parents=True, exist_ok=True)
    elif log_type == "celery":
        log_dir = logs_root / "celery"
        log_dir.mkdir(parents=True, exist_ok=True)
    else:
        raise ValueError(f"Unknown log_type: {log_type}, must be 'app' or 'celery'")
    
    # 定义日志格式
    if json_logs:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s")
    
    if log_type == "app":
        # 主程序日志配置
        _setup_app_logging(log_dir, formatter)
    elif log_type == "celery":
        # Celery日志配置
        _setup_celery_logging(log_dir, formatter)


def _setup_app_logging(log_dir: Path, formatter: logging.Formatter) -> None:
    """配置主程序（FastAPI/Uvicorn）的日志"""
    # 获取根日志记录器和相关logger
    root = logging.getLogger()
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    fastapi_logger = logging.getLogger("fastapi")
    
    # 清除所有现有处理器
    for logger in [root, uvicorn_logger, uvicorn_access_logger, uvicorn_error_logger, fastapi_logger]:
        logger.handlers.clear()
        logger.propagate = False  # 防止传播到根logger
    
    # 设置日志级别
    root.setLevel(logging.DEBUG)
    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_access_logger.setLevel(logging.INFO)
    # uvicorn.error 设置为 WARNING，过滤掉 KeyboardInterrupt 等正常关闭异常
    uvicorn_error_logger.setLevel(logging.WARNING)
    fastapi_logger.setLevel(logging.INFO)
    
    # 创建自定义过滤器，过滤掉 KeyboardInterrupt 和 CancelledError
    class IgnoreKeyboardInterruptFilter(logging.Filter):
        def filter(self, record):
            # 检查异常类型和值
            if record.exc_info and len(record.exc_info) >= 2:
                exc_type = record.exc_info[0]
                exc_value = record.exc_info[1] if len(record.exc_info) > 1 else None
                
                # 直接检查异常类型（使用 is 和 isinstance）
                if exc_type is KeyboardInterrupt:
                    return False
                if exc_type is asyncio.CancelledError:
                    return False
                if isinstance(exc_value, KeyboardInterrupt):
                    return False
                if isinstance(exc_value, asyncio.CancelledError):
                    return False
                
                # 检查异常类型名称（处理继承情况）
                exc_type_name = getattr(exc_type, '__name__', '')
                if exc_type_name in ('KeyboardInterrupt', 'CancelledError'):
                    return False
                
                # 检查异常类型的完整限定名
                exc_type_module = getattr(exc_type, '__module__', '')
                if exc_type_module == 'asyncio.exceptions' and exc_type_name == 'CancelledError':
                    return False
                if exc_type_module == 'asyncio' and exc_type_name == 'CancelledError':
                    return False
            
            # 检查消息内容（包括格式化后的完整消息）
            try:
                msg = record.getMessage()
                if msg:
                    # 检查各种可能的异常名称变体
                    msg_lower = msg.lower()
                    if any(keyword.lower() in msg_lower for keyword in [
                        'KeyboardInterrupt',
                        'CancelledError',
                        'asyncio.exceptions.CancelledError',
                        'asyncio.CancelledError'
                    ]):
                        return False
            except Exception:
                pass
            
            # 检查格式化后的异常文本（如果存在）
            if hasattr(record, 'exc_text') and record.exc_text:
                exc_text_lower = record.exc_text.lower()
                if any(keyword.lower() in exc_text_lower for keyword in [
                    'KeyboardInterrupt',
                    'CancelledError',
                    'asyncio.exceptions.CancelledError',
                    'asyncio.CancelledError'
                ]):
                    return False
            
            # 如果记录包含 traceback，也检查格式化后的完整记录
            # 这需要格式化记录，但只在必要时进行（性能考虑）
            if record.exc_info:
                try:
                    # 使用格式化器格式化异常部分（如果可能）
                    # 注意：这里我们不格式化整个记录，只检查异常部分
                    formatted_exc = ''.join(traceback.format_exception(*record.exc_info))
                    if formatted_exc:
                        formatted_exc_lower = formatted_exc.lower()
                        if any(keyword.lower() in formatted_exc_lower for keyword in [
                            'KeyboardInterrupt',
                            'CancelledError',
                            'asyncio.exceptions.CancelledError',
                            'asyncio.CancelledError'
                        ]):
                            return False
                except Exception:
                    pass
            
            return True
    
    ignore_filter = IgnoreKeyboardInterruptFilter()
    
    # 创建文件处理器
    handlers = []
    
    # 1. INFO日志文件
    info_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "info.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    handlers.append(info_handler)
    
    # 2. WARNING日志文件
    warning_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "warning.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(formatter)
    handlers.append(warning_handler)
    
    # 3. ERROR日志文件
    error_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "error.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,  # 错误日志保留更多备份
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    handlers.append(error_handler)
    
    # 为所有logger添加处理器和过滤器
    for logger in [root, uvicorn_logger, uvicorn_access_logger, uvicorn_error_logger, fastapi_logger]:
        for handler in handlers:
            handler.addFilter(ignore_filter)  # 添加过滤器
            logger.addHandler(handler)
    
    # 完全禁用控制台输出
    # 移除任何StreamHandler（控制台输出），只保留文件处理器
    for logger in [root, uvicorn_logger, uvicorn_access_logger, uvicorn_error_logger, fastapi_logger]:
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                # 只保留文件处理器
                if not isinstance(handler, (logging.handlers.RotatingFileHandler, logging.FileHandler)):
                    logger.removeHandler(handler)


def _setup_celery_logging(log_dir: Path, formatter: logging.Formatter) -> None:
    """配置Celery的日志"""
    # 获取Celery相关的logger
    root = logging.getLogger()
    celery_logger = logging.getLogger("celery")
    celery_task_logger = logging.getLogger("celery.task")
    celery_worker_logger = logging.getLogger("celery.worker")
    
    # 清除所有现有处理器
    for logger in [root, celery_logger, celery_task_logger, celery_worker_logger]:
        logger.handlers.clear()
        logger.propagate = False  # 防止传播到根logger
    
    # 设置日志级别
    root.setLevel(logging.DEBUG)
    celery_logger.setLevel(logging.INFO)
    celery_task_logger.setLevel(logging.INFO)
    celery_worker_logger.setLevel(logging.INFO)
    
    # 创建文件处理器
    handlers = []
    
    # 1. INFO日志文件
    info_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "info.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    handlers.append(info_handler)
    
    # 2. WARNING日志文件
    warning_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "warning.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(formatter)
    handlers.append(warning_handler)
    
    # 3. ERROR日志文件
    error_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "error.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,  # 错误日志保留更多备份
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    handlers.append(error_handler)
    
    # 为所有logger添加处理器
    for logger in [root, celery_logger, celery_task_logger, celery_worker_logger]:
        for handler in handlers:
            logger.addHandler(handler)
    
    # 完全禁用控制台输出
    # 移除任何StreamHandler（控制台输出），只保留文件处理器
    for logger in [root, celery_logger, celery_task_logger, celery_worker_logger]:
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                # 只保留文件处理器
                if not isinstance(handler, (logging.handlers.RotatingFileHandler, logging.FileHandler)):
                    logger.removeHandler(handler)


def log_event(name: str, **fields: Any) -> None:
    logger.info(name, extra={"event": name, **fields})


# ---- Metrics (Prometheus optional) ----


try:  # pragma: no cover
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

    _PROM_AVAILABLE = True
except Exception:  # noqa: BLE001
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    Counter = Gauge = Histogram = None  # type: ignore[assignment]
    generate_latest = None  # type: ignore[assignment]
    _PROM_AVAILABLE = False


@dataclass
class _InMemMetric:
    name: str
    kind: str
    value: float = 0.0

    def inc(self, amount: float = 1.0) -> None:
        self.value += amount

    def set(self, v: float) -> None:
        self.value = v

    def observe(self, v: float) -> None:
        # store last observed for quick debugging (not a histogram)
        self.value = v


_INMEM: dict[str, _InMemMetric] = {}


def _mem_metric(name: str, kind: str) -> _InMemMetric:
    m = _INMEM.get(name)
    if m is None:
        m = _InMemMetric(name=name, kind=kind)
        _INMEM[name] = m
    return m


def metrics_text() -> bytes:
    """
    Export metrics as Prometheus text if available; otherwise export a minimal text.
    """
    if _PROM_AVAILABLE and generate_latest is not None:  # pragma: no cover
        return generate_latest()

    lines: list[str] = []
    for m in sorted(_INMEM.values(), key=lambda x: x.name):
        lines.append(f"# TYPE {m.name} {m.kind}")
        lines.append(f"{m.name} {m.value}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def get_metric_value(name: str) -> float | None:
    """
    Return current value of in-memory metric; if using Prometheus client,
    this will return None (since values live inside Prom client).
    """
    m = _INMEM.get(name)
    if m:
        return m.value
    return None


def counter(name: str, documentation: str = "", labelnames: tuple[str, ...] = ()) -> Any:
    if _PROM_AVAILABLE and Counter is not None:  # pragma: no cover
        return Counter(name, documentation, labelnames=labelnames)
    return _mem_metric(name, "counter")


def gauge(name: str, documentation: str = "", labelnames: tuple[str, ...] = ()) -> Any:
    if _PROM_AVAILABLE and Gauge is not None:  # pragma: no cover
        return Gauge(name, documentation, labelnames=labelnames)
    return _mem_metric(name, "gauge")


def histogram(name: str, documentation: str = "", labelnames: tuple[str, ...] = ()) -> Any:
    if _PROM_AVAILABLE and Histogram is not None:  # pragma: no cover
        return Histogram(name, documentation, labelnames=labelnames)
    return _mem_metric(name, "histogram")


# ---- Alerting (Webhook optional) ----


def _env_bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def send_alert_webhook(*, url: str, payload: dict[str, Any], timeout: float = 5.0) -> None:
    """
    Send an alert to a webhook URL. Best-effort: never raise.
    """
    if not url:
        return
    try:
        import requests  # type: ignore[import]

        requests.post(url, json=payload, timeout=timeout)
        return
    except Exception:
        pass

    # fallback to urllib
    try:
        import urllib.request

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout):  # noqa: S310
            return
    except Exception:
        # swallow
        return


def default_alert_payload(*, title: str, severity: str, **fields: Any) -> dict[str, Any]:
    return {
        "title": title,
        "severity": severity,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": os.getenv("HOSTNAME") or "",
        **fields,
    }


