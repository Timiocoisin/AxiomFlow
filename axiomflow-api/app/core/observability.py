from __future__ import annotations

import json
import logging
import os
import time
import traceback
from dataclasses import dataclass
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


def setup_logging(*, json_logs: bool) -> None:
    """
    Setup root logging formatter.
    Note: keep it minimal, do not interfere with Celery's own logger config.
    """
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=logging.INFO)

    for h in root.handlers:
        if json_logs:
            h.setFormatter(JsonFormatter())
        else:
            # keep default formatter if present
            if h.formatter is None:
                h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))


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


