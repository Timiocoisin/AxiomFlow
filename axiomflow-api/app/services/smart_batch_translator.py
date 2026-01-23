"""
智能批处理翻译模块

提供按类型分组、优先级队列、动态批次调整等功能，提升翻译吞吐量。
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import IntEnum
from collections import defaultdict
from typing import Any, Callable

from ..core.config import settings
from ..core.observability import counter, gauge, histogram
from .providers.base import TranslateMeta
from .concurrent_translator import TranslationTask, TranslationResult

logger = logging.getLogger(__name__)

SMART_BATCH_TASKS = counter(
    "axiomflow_smart_batch_tasks_total",
    "Total translation tasks processed by smart batch translator.",
)
SMART_BATCH_ERRORS = counter(
    "axiomflow_smart_batch_errors_total",
    "Total translation task errors in smart batch translator.",
)
SMART_BATCH_LATENCY = histogram(
    "axiomflow_smart_batch_task_latency_seconds",
    "Per-task latency (seconds) observed in smart batch translator.",
)
SMART_BATCH_SIZE = gauge(
    "axiomflow_smart_batch_current_batch_size",
    "Current adaptive batch size used by smart batch translator.",
)


class BlockPriority(IntEnum):
    """块优先级（数值越小优先级越高）"""

    TITLE = 1  # 标题（最高优先级）
    HEADING = 2  # 章节标题
    CAPTION = 3  # 图表标题
    PARAGRAPH = 4  # 段落
    FOOTNOTE = 5  # 脚注（最低优先级）


@dataclass
class PrioritizedTask:
    """带优先级的翻译任务"""

    task: TranslationTask
    priority: int = field(default=BlockPriority.PARAGRAPH)
    created_at: float = field(default_factory=time.time)


def get_block_priority(block_type: str | None) -> int:
    """
    根据块类型获取优先级

    Args:
        block_type: 块类型

    Returns:
        优先级值（越小越高）
    """
    type_priority_map = {
        "title": BlockPriority.TITLE,
        "heading": BlockPriority.HEADING,
        "caption": BlockPriority.CAPTION,
        "paragraph": BlockPriority.PARAGRAPH,
        "footnote": BlockPriority.FOOTNOTE,
    }
    return type_priority_map.get(block_type or "", BlockPriority.PARAGRAPH)


def group_tasks_by_type(tasks: list[TranslationTask]) -> dict[str, list[TranslationTask]]:
    """
    按块类型对任务进行分组

    Args:
        tasks: 翻译任务列表

    Returns:
        分组后的任务字典 {block_type: [tasks]}
    """
    groups: dict[str, list[TranslationTask]] = defaultdict(list)
    
    for task in tasks:
        block_type = task.meta.block_type or "paragraph"
        groups[block_type].append(task)
    
    return dict(groups)


def prioritize_tasks(tasks: list[TranslationTask]) -> list[PrioritizedTask]:
    """
    对任务进行优先级排序

    Args:
        tasks: 翻译任务列表

    Returns:
        按优先级排序的任务列表
    """
    prioritized = [
        PrioritizedTask(
            task=t,
            priority=get_block_priority(t.meta.block_type),
        )
        for t in tasks
    ]
    
    # 按优先级和创建时间排序
    prioritized.sort(key=lambda x: (x.priority, x.created_at))
    
    return prioritized


class SmartBatchTranslator:
    """智能批处理翻译器"""

    def __init__(
        self,
        max_workers: int = 5,
        max_retries: int = 3,
        *,
        adaptive_batch_size: bool = True,
        initial_batch_size: int = 5,
    ):
        """
        Args:
            max_workers: 最大并发数
            max_retries: 最大重试次数
            adaptive_batch_size: 是否启用自适应批次大小
            initial_batch_size: 初始批次大小
        """
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.adaptive_batch_size = adaptive_batch_size
        self.current_batch_size = initial_batch_size
        self.semaphore = asyncio.Semaphore(max_workers)
        
        # 性能统计（用于自适应调整）
        self.response_times: list[float] = []
        self.max_response_times = 100  # 保留最近100次响应时间
        self.error_flags: list[int] = []
        self.max_error_flags = 200
        self._last_tune_ts = 0.0

    def _update_batch_size(self, response_time: float, *, is_error: bool) -> None:
        """根据响应时间 + 错误率动态调整批次大小（调优回路）"""
        if not self.adaptive_batch_size:
            return
        
        self.response_times.append(response_time)
        if len(self.response_times) > self.max_response_times:
            self.response_times.pop(0)

        self.error_flags.append(1 if is_error else 0)
        if len(self.error_flags) > self.max_error_flags:
            self.error_flags.pop(0)

        # 调参节流：避免每个请求都调整
        now = time.time()
        if now - self._last_tune_ts < 1.0:
            try:
                SMART_BATCH_SIZE.set(float(self.current_batch_size))
            except Exception:
                pass
            return
        self._last_tune_ts = now
        
        # 计算平均响应时间
        if len(self.response_times) >= 10:
            avg_response_time = sum(self.response_times) / len(self.response_times)
            err_rate = 0.0
            if len(self.error_flags) >= 20:
                err_rate = sum(self.error_flags) / len(self.error_flags)

            target_latency = float(getattr(settings, "batch_target_avg_latency_s", 1.2))
            target_err = float(getattr(settings, "batch_target_error_rate", 0.05))
            max_size = int(getattr(settings, "batch_max_size", max(1, self.max_workers * 2)))
            max_size = max(1, max_size)
            
            # 如果错误率太高，优先降 batch size（减轻 provider 压力/限流）
            if err_rate > target_err:
                self.current_batch_size = max(self.current_batch_size - 1, 1)
            # 如果响应时间快，可以增加 batch size；如果慢，减少 batch size
            elif avg_response_time < target_latency * 0.7:
                # 响应很快，可以增加批次大小
                self.current_batch_size = min(
                    self.current_batch_size + 1,
                    max_size,
                )
            elif avg_response_time > target_latency * 1.7:
                # 响应较慢，减少批次大小
                self.current_batch_size = max(
                    self.current_batch_size - 1,
                    1,
                )

        try:
            SMART_BATCH_SIZE.set(float(self.current_batch_size))
        except Exception:
            pass

    async def translate_batch_smart(
        self,
        tasks: list[TranslationTask],
        translate_func: Callable[[str, TranslateMeta], Any],
        *,
        progress_callback: Callable[[int, int], None] | None = None,
        use_priority: bool = True,
        use_grouping: bool = True,
    ) -> list[TranslationResult]:
        """
        智能批量翻译

        Args:
            tasks: 翻译任务列表
            translate_func: 翻译函数
            progress_callback: 进度回调
            use_priority: 是否使用优先级排序
            use_grouping: 是否按类型分组处理

        Returns:
            翻译结果列表
        """
        total = len(tasks)
        completed = 0
        results: list[TranslationResult] = []
        
        # 如果使用优先级，先排序
        if use_priority:
            prioritized = prioritize_tasks(tasks)
            # 按优先级分批处理
            current_batch: list[PrioritizedTask] = []
            current_priority = None
            
            for p_task in prioritized:
                if current_priority is None:
                    current_priority = p_task.priority
                
                if p_task.priority == current_priority and len(current_batch) < self.current_batch_size:
                    current_batch.append(p_task)
                else:
                    # 处理当前批次
                    if current_batch:
                        batch_results = await self._translate_prioritized_batch(
                            current_batch,
                            translate_func,
                            progress_callback,
                            total,
                            completed,
                        )
                        results.extend(batch_results)
                        completed += len(batch_results)
                    
                    # 开始新批次
                    current_batch = [p_task]
                    current_priority = p_task.priority
            
            # 处理最后一批
            if current_batch:
                batch_results = await self._translate_prioritized_batch(
                    current_batch,
                    translate_func,
                    progress_callback,
                    total,
                    completed,
                )
                results.extend(batch_results)
                completed += len(batch_results)
        else:
            # 不使用优先级，直接分组处理
            if use_grouping:
                groups = group_tasks_by_type(tasks)
                
                # 按优先级顺序处理各组
                group_order = ["title", "heading", "caption", "paragraph", "footnote"]
                for group_type in group_order:
                    if group_type in groups:
                        group_tasks = groups[group_type]
                        # 分批处理该组
                        for i in range(0, len(group_tasks), self.current_batch_size):
                            batch = group_tasks[i : i + self.current_batch_size]
                            batch_results = await self._translate_batch_simple(
                                batch,
                                translate_func,
                                progress_callback,
                                total,
                                completed,
                            )
                            results.extend(batch_results)
                            completed += len(batch_results)
            else:
                # 完全不分组，直接处理
                results = await self._translate_batch_simple(
                    tasks,
                    translate_func,
                    progress_callback,
                    total,
                    completed,
                )
        
        return results

    async def _translate_prioritized_batch(
        self,
        prioritized_tasks: list[PrioritizedTask],
        translate_func: Callable[[str, TranslateMeta], Any],
        progress_callback: Callable[[int, int], None] | None,
        total: int,
        base_completed: int,
    ) -> list[TranslationResult]:
        """翻译一个优先级的批次"""
        tasks = [p.task for p in prioritized_tasks]
        return await self._translate_batch_simple(
            tasks,
            translate_func,
            progress_callback,
            total,
            base_completed,
        )

    async def _translate_batch_simple(
        self,
        tasks: list[TranslationTask],
        translate_func: Callable[[str, TranslateMeta], Any],
        progress_callback: Callable[[int, int], None] | None,
        total: int,
        base_completed: int,
    ) -> list[TranslationResult]:
        """简单批次翻译（带性能统计）"""
        completed = base_completed
        results: list[TranslationResult] = []
        
        async def translate_one(task: TranslationTask, index: int) -> TranslationResult:
            nonlocal completed
            start_time = time.time()
            
            async with self.semaphore:
                retry_count = 0
                last_error: Exception | None = None
                
                while retry_count <= self.max_retries:
                    try:
                        translation = await translate_func(task.text, task.meta)
                        response_time = time.time() - start_time
                        
                        # 更新批次大小
                        self._update_batch_size(response_time, is_error=False)
                        try:
                            SMART_BATCH_TASKS.inc()
                            SMART_BATCH_LATENCY.observe(response_time)
                        except Exception:
                            pass
                        
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
                        response_time = time.time() - start_time
                        self._update_batch_size(response_time, is_error=True)
                        try:
                            SMART_BATCH_TASKS.inc()
                            SMART_BATCH_ERRORS.inc()
                            SMART_BATCH_LATENCY.observe(response_time)
                        except Exception:
                            pass
                        if retry_count <= self.max_retries:
                            wait_time = min(2**retry_count, 10)
                            logger.warning(
                                f"翻译失败 (任务 {index}, 重试 {retry_count}/{self.max_retries}): "
                                f"{type(exc).__name__}: {str(exc)[:100]}"
                            )
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error(
                                f"翻译失败 (任务 {index}, 已重试 {retry_count} 次): "
                                f"{type(exc).__name__}: {str(exc)[:200]}"
                            )
                
                # 所有重试都失败
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
        
        # 并发执行
        coros = [translate_one(task, i) for i, task in enumerate(tasks)]
        batch_results = await asyncio.gather(*coros, return_exceptions=False)
        
        return list(batch_results)

