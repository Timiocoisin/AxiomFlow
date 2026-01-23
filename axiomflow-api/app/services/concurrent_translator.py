"""
并发翻译处理工具

提供批量并发翻译、任务队列管理和进度跟踪功能。
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .providers.base import TranslateMeta

logger = logging.getLogger(__name__)


@dataclass
class TranslationTask:
    """翻译任务"""

    block_id: str
    text: str
    meta: TranslateMeta
    page_index: int
    block_index: int


@dataclass
class TranslationResult:
    """翻译结果"""

    block_id: str
    translation: str | None
    error: Exception | None = None
    retry_count: int = 0


class ConcurrentTranslator:
    """
    并发翻译器

    支持批量并发翻译多个文本块，自动管理并发数和重试。
    """

    def __init__(self, max_workers: int = 5, max_retries: int = 3):
        """
        Args:
            max_workers: 最大并发数
            max_retries: 每个任务的最大重试次数
        """
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(max_workers)

    async def translate_batch(
        self,
        tasks: list[TranslationTask],
        translate_func: Callable[[str, TranslateMeta], Any],
        *,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[TranslationResult]:
        """
        批量并发翻译

        Args:
            tasks: 翻译任务列表
            translate_func: 翻译函数（async，接受 text 和 meta，返回翻译文本）
            progress_callback: 进度回调函数（当前完成数, 总数）

        Returns:
            翻译结果列表（与 tasks 顺序对应）
        """
        total = len(tasks)
        completed = 0
        results: list[TranslationResult] = []

        async def translate_one(task: TranslationTask, index: int) -> TranslationResult:
            """翻译单个任务（带并发控制）"""
            nonlocal completed
            async with self.semaphore:
                retry_count = 0
                last_error: Exception | None = None

                while retry_count <= self.max_retries:
                    try:
                        translation = await translate_func(task.text, task.meta)
                        result = TranslationResult(
                            block_id=task.block_id,
                            translation=translation,
                            retry_count=retry_count,
                        )
                        completed += 1
                        if progress_callback:
                            progress_callback(completed, total)
                        return result

                    except Exception as exc:
                        last_error = exc
                        retry_count += 1
                        if retry_count <= self.max_retries:
                            wait_time = min(2**retry_count, 10)  # 指数退避，最多10秒
                            logger.warning(
                                f"翻译失败 (任务 {index}, 重试 {retry_count}/{self.max_retries}): "
                                f"{type(exc).__name__}: {str(exc)[:100]} | 等待 {wait_time} 秒后重试"
                            )
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error(
                                f"翻译失败 (任务 {index}, 已重试 {retry_count} 次): "
                                f"{type(exc).__name__}: {str(exc)[:200]}"
                            )

                # 所有重试都失败了
                result = TranslationResult(
                    block_id=task.block_id,
                    translation=None,
                    error=last_error,
                    retry_count=retry_count - 1,
                )
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                return result

        # 并发执行所有任务
        coros = [translate_one(task, i) for i, task in enumerate(tasks)]
        results = await asyncio.gather(*coros, return_exceptions=False)

        return results

    async def translate_stream(
        self,
        tasks: list[TranslationTask],
        translate_func: Callable[[str, TranslateMeta], Any],
        *,
        progress_callback: Callable[[int, int], None] | None = None,
        yield_interval: int = 10,
    ) -> list[TranslationResult]:
        """
        流式批量翻译（分批处理，可以更早返回结果）

        Args:
            tasks: 翻译任务列表
            translate_func: 翻译函数
            progress_callback: 进度回调
            yield_interval: 每处理多少个任务后让出控制权

        Returns:
            翻译结果列表
        """
        total = len(tasks)
        completed = 0
        results: list[TranslationResult] = []

        # 分批处理
        for batch_start in range(0, total, self.max_workers):
            batch_end = min(batch_start + self.max_workers, total)
            batch_tasks = tasks[batch_start:batch_end]

            async def translate_one(task: TranslationTask, index: int) -> TranslationResult:
                nonlocal completed
                async with self.semaphore:
                    retry_count = 0
                    last_error: Exception | None = None

                    while retry_count <= self.max_retries:
                        try:
                            translation = await translate_func(task.text, task.meta)
                            result = TranslationResult(
                                block_id=task.block_id,
                                translation=translation,
                                retry_count=retry_count,
                            )
                            completed += 1
                            if progress_callback:
                                progress_callback(completed, total)
                            return result

                        except Exception as exc:
                            last_error = exc
                            retry_count += 1
                            if retry_count <= self.max_retries:
                                wait_time = min(2**retry_count, 10)
                                logger.warning(
                                    f"翻译失败 (任务 {index}, 重试 {retry_count}/{self.max_retries}): "
                                    f"{type(exc).__name__}: {str(exc)[:100]}"
                                )
                                await asyncio.sleep(wait_time)
                            else:
                                logger.error(
                                    f"翻译失败 (任务 {index}): "
                                    f"{type(exc).__name__}: {str(exc)[:200]}"
                                )

                    result = TranslationResult(
                        block_id=task.block_id,
                        translation=None,
                        error=last_error,
                        retry_count=retry_count - 1,
                    )
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total)
                    return result

            batch_coros = [
                translate_one(task, batch_start + i) for i, task in enumerate(batch_tasks)
            ]
            batch_results = await asyncio.gather(*batch_coros, return_exceptions=False)
            results.extend(batch_results)

            # 让出控制权，避免阻塞
            if batch_end % yield_interval == 0:
                await asyncio.sleep(0)

        return results

