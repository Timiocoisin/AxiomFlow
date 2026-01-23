"""
错误处理和重试机制工具

提供统一的重试策略、错误分类和详细日志记录。
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, TypeVar

import httpx
from tenacity import (
    RetryCallState,
    Retrying,
    retry,
    retry_if_exception_type,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TranslationError(Exception):
    """翻译相关的基础异常"""

    pass


class NetworkError(TranslationError):
    """网络错误（可重试）"""

    pass


class RateLimitError(TranslationError):
    """API 速率限制错误（可重试）"""

    pass


class AuthenticationError(TranslationError):
    """认证错误（不可重试）"""

    pass


class InvalidResponseError(TranslationError):
    """无效响应错误（不可重试）"""

    pass


class ConfigurationError(TranslationError):
    """配置错误（不可重试）"""

    pass


def classify_error(exc: Exception) -> type[TranslationError]:
    """
    分类异常类型，用于决定重试策略

    Returns:
        对应的 TranslationError 子类
    """
    # 网络相关错误（可重试）
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)):
        return NetworkError
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        if status_code == 429:  # Too Many Requests
            return RateLimitError
        if status_code == 401 or status_code == 403:  # Unauthorized / Forbidden
            return AuthenticationError
        if status_code >= 500:  # 服务器错误（可重试）
            return NetworkError
        return InvalidResponseError

    # 配置错误（不可重试）
    if isinstance(exc, (ValueError, KeyError, AttributeError)) and "not configured" in str(exc).lower():
        return ConfigurationError

    # 默认：不可重试
    return TranslationError


def log_retry_attempt(retry_state: RetryCallState) -> None:
    """记录重试尝试的详细信息"""
    exc = retry_state.outcome.exception()
    attempt = retry_state.attempt_number
    wait_time = retry_state.next_action.sleep if retry_state.next_action else 0

    error_type = classify_error(exc)
    is_retryable = error_type in (NetworkError, RateLimitError)

    if is_retryable:
        logger.warning(
            f"翻译失败（尝试 {attempt}）: {error_type.__name__} - {str(exc)[:100]} | "
            f"等待 {wait_time:.1f}秒后重试..."
        )
    else:
        logger.error(
            f"翻译失败（尝试 {attempt}）: {error_type.__name__} - {str(exc)[:200]} | "
            f"错误不可重试，停止翻译"
        )


# 网络错误重试策略：指数退避 + 随机抖动
network_retry = retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30) + wait_random(0, 2),
    before_sleep=log_retry_attempt,
    reraise=True,
)

# 速率限制重试策略：更长的等待时间
rate_limit_retry = retry(
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=2, min=2, max=60) + wait_random(0, 5),
    before_sleep=lambda retry_state: (
        log_retry_attempt(retry_state) if retry_state.outcome.exception().response.status_code == 429 else None
    ),
    reraise=True,
)

# HTTP 500+ 服务器错误重试策略
server_error_retry = retry(
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1.5, min=2, max=20),
    before_sleep=log_retry_attempt,
    reraise=True,
)


def with_retry(
    func: Callable[..., T],
    *,
    max_attempts: int = 5,
    base_wait: float = 1.0,
    max_wait: float = 30.0,
    exponential_base: float = 2.0,
) -> Callable[..., T]:
    """
    通用的重试装饰器

    Args:
        func: 要重试的异步函数
        max_attempts: 最大重试次数
        base_wait: 基础等待时间（秒）
        max_wait: 最大等待时间（秒）
        exponential_base: 指数退避基数

    Returns:
        包装后的函数
    """
    retry_strategy = Retrying(
        retry=retry_if_exception_type((NetworkError, RateLimitError)),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=base_wait, min=base_wait, max=max_wait),
        before_sleep=log_retry_attempt,
        reraise=True,
    )

    async def wrapper(*args: Any, **kwargs: Any) -> T:
        last_exc: Exception | None = None
        for attempt in retry_strategy:
            try:
                with attempt:
                    return await func(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                error_type = classify_error(exc)
                if error_type not in (NetworkError, RateLimitError):
                    # 不可重试的错误，直接抛出
                    raise

        # 所有重试都失败了
        if last_exc:
            raise last_exc
        raise RuntimeError("Retry exhausted without exception")

    return wrapper


def create_error_context(exc: Exception, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    创建详细的错误上下文信息

    Args:
        exc: 异常对象
        context: 额外的上下文信息

    Returns:
        包含详细错误信息的字典
    """
    error_info: dict[str, Any] = {
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "error_class": classify_error(exc).__name__,
        "timestamp": time.time(),
    }

    # 添加 HTTP 错误详情
    if isinstance(exc, httpx.HTTPStatusError):
        error_info["status_code"] = exc.response.status_code
        error_info["response_headers"] = dict(exc.response.headers)
        try:
            error_info["response_body"] = exc.response.text[:500]  # 限制长度
        except Exception:
            pass

    # 添加额外上下文
    if context:
        error_info["context"] = context

    return error_info

